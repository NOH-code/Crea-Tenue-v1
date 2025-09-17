from fastapi import FastAPI, APIRouter, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import os
import logging
import uuid
import base64
import asyncio
import aiofiles
import jwt
import bcrypt
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-this')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# User Models
class UserRole(str):
    CLIENT = "client"
    USER = "user" 
    ADMIN = "admin"

class UserCreate(BaseModel):
    nom: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom: str
    email: EmailStr
    role: str = UserRole.CLIENT
    images_used_total: int = 0
    images_limit_total: int = 5  # Limite par défaut de 5 images
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    verification_token: Optional[str] = None
    is_verified: bool = True  # Default to True for simplicity
    
    class Config:
        extra = "ignore"  # Ignore extra fields from database

class UserUpdate(BaseModel):
    role: Optional[str] = None
    images_limit_total: Optional[int] = None
    images_used_total: Optional[int] = None
    is_active: Optional[bool] = None

# Password utilities
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_password(password: str) -> bool:
    """Validate password: min 8 chars, at least 1 digit and 1 letter"""
    if len(password) < 8:
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[a-zA-Z]', password):
        return False
    return True

# JWT utilities
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(payload: dict = Depends(verify_token)) -> User:
    user_data = await db.users.find_one({"email": payload.get("email")})
    if not user_data:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user_data)

async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def get_user_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in [UserRole.USER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="User or Admin access required")
    return current_user

# Define Models
class OutfitRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    atmosphere: str
    suit_type: str
    lapel_type: str
    pocket_type: str
    shoe_type: str
    accessory_type: str
    fabric_description: Optional[str] = None
    custom_shoe_description: Optional[str] = None
    custom_accessory_description: Optional[str] = None
    email: Optional[str] = None
    user_email: Optional[str] = None  # Track which user created the request
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OutfitRequestCreate(BaseModel):
    atmosphere: str
    suit_type: str
    lapel_type: str
    pocket_type: str
    shoe_type: str
    accessory_type: str
    fabric_description: Optional[str] = None
    custom_shoe_description: Optional[str] = None
    custom_accessory_description: Optional[str] = None
    email: Optional[str] = None

class GenerationStatus(BaseModel):
    id: str
    status: str
    message: str
    image_url: Optional[str] = None

# Configuration for outfit options
ATMOSPHERE_OPTIONS = {
    "champetre": "dans une grange rustique avec des poutres en bois apparent et de la paille au sol. L'ambiance est champêtre avec des décorations de mariage rustiques",
    "bord_de_mer": "sur une plage au coucher du soleil. Le sable fin et les vagues créent une ambiance maritime romantique",
    "elegant": "dans un château rénové, la cérémonie se déroule dans une salle qui ressemble à la Galerie des Glaces de Versailles",
    "very_bad_trip": "comme dans le film Very Bad Trip, le mariage se déroule sur le Las Vegas Strip ; une petite cérémonie improvisée. La scène montre des signes de grande fête la nuit précédente : bouteilles, canettes, déchets, personnes endormies et environnement en désordre",
    "rue_paris": "la photo est prise dans la rue à Paris",
    "rue_new_york": "la photo est prise dans la rue à New York"
}

SUIT_TYPES = ["Costume 2 pièces", "Costume 3 pièces"]

LAPEL_TYPES = [
    "Revers cran droit standard",
    "Revers cran droit large", 
    "Revers cran aigu standard",
    "Revers cran aigu large",
    "Col châle avec revers satin",
    "Veste croisée cran aigu standard",
    "Veste croisée cran aigu large"
]

POCKET_TYPES = [
    "En biais, sans rabat",
    "En biais avec rabat", 
    "Droites avec rabat",
    "Droites, sans rabat",
    "Poches plaquées"
]

SHOE_TYPES = [
    "Mocassins noirs",
    "Mocassins marrons",
    "Richelieu noires", 
    "Richelieu marrons",
    "Baskets blanches",
    "Description texte"
]

ACCESSORY_TYPES = ["Nœud papillon", "Cravate", "Description texte"]

async def apply_watermark(image_data: bytes) -> bytes:
    """Apply watermark to generated image"""
    try:
        # Open the generated image
        image = Image.open(io.BytesIO(image_data))
        
        # Open watermark
        watermark_path = Path("/app/logo_watermark.png")
        if watermark_path.exists():
            watermark = Image.open(watermark_path)
            
            # Calculate watermark size (80% of image width - 800% larger than before)
            img_width, img_height = image.size
            watermark_width = int(img_width * 0.8)  # Changed from 0.1 to 0.8 (800% increase)
            watermark_height = int(watermark.size[1] * (watermark_width / watermark.size[0]))
            
            # Resize watermark
            watermark = watermark.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
            
            # Position watermark at bottom center
            x = (img_width - watermark_width) // 2
            y = img_height - watermark_height - 20
            
            # Apply watermark (no text added, only logo)
            if watermark.mode == 'RGBA':
                image.paste(watermark, (x, y), watermark)
            else:
                image.paste(watermark, (x, y))
        
        # Convert back to bytes
        output = io.BytesIO()
        image.save(output, format='PNG', quality=95)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Error applying watermark: {e}")
        return image_data

async def generate_outfit_image(
    model_image_data: bytes,
    fabric_image_data: Optional[bytes],
    shoe_image_data: Optional[bytes],
    accessory_image_data: Optional[bytes],
    outfit_request: OutfitRequestCreate
) -> bytes:
    """Generate outfit image using Gemini with Nano Banana model"""
    
    try:
        # Get Emergent LLM key
        api_key = os.getenv('EMERGENT_LLM_KEY')
        
        # Create chat instance
        chat = LlmChat(
            api_key=api_key, 
            session_id=f"outfit_gen_{uuid.uuid4()}", 
            system_message="You are a professional fashion designer specializing in wedding attire visualization."
        )
        chat.with_model("gemini", "gemini-2.5-flash-image-preview").with_params(modalities=["image", "text"])
        
        # Convert model image to base64
        model_base64 = base64.b64encode(model_image_data).decode('utf-8')
        
        # Build detailed prompt with specific outfit specifications
        atmosphere_desc = ATMOSPHERE_OPTIONS.get(outfit_request.atmosphere, outfit_request.atmosphere)
        
        # Detailed pocket specifications
        pocket_details = {
            "Slanted, no flaps": "slanted pockets without flaps, clean minimal lines",
            "Slanted with flaps": "slanted pockets with fabric flaps covering the openings",
            "Straight with flaps": "straight horizontal pockets with fabric flaps",
            "Straight, no flaps": "straight horizontal pockets without flaps, welted style",
            "Patch pockets": "patch pockets sewn on top of the jacket exterior"
        }
        
        # Detailed lapel specifications  
        lapel_details = {
            "Standard notch lapel": "standard notch lapel with moderate width, classic business style",
            "Wide notch lapel": "wide notch lapel with broader peak, more dramatic look",
            "Standard peak lapel": "pointed peak lapel extending upward, formal style",
            "Wide peak lapel": "wide pointed peak lapel, very formal and dramatic",
            "Shawl collar with satin lapel": "rounded shawl collar with satin facing, tuxedo style",
            "Standard double-breasted peak lapel": "peak lapel for double-breasted jacket, formal",
            "Wide double-breasted peak lapel": "wide peak lapel for double-breasted jacket, very formal"
        }
        
        # Suit composition details
        suit_composition = ""
        if "2-piece" in outfit_request.suit_type.lower():
            suit_composition = "EXACTLY 2 pieces: jacket and trousers ONLY. NO vest, NO waistcoat, NO third piece visible."
        elif "3-piece" in outfit_request.suit_type.lower():
            suit_composition = "EXACTLY 3 pieces: jacket, trousers, AND waistcoat/vest. The vest MUST be visible under the jacket."
        
        pocket_spec = pocket_details.get(outfit_request.pocket_type, outfit_request.pocket_type)
        lapel_spec = lapel_details.get(outfit_request.lapel_type, outfit_request.lapel_type)
        
        prompt = f"""Create a professional, photorealistic wedding photo of a groom using the attached full-length model photo.

CRITICAL SUIT SPECIFICATIONS - FOLLOW EXACTLY:

SUIT COMPOSITION: {suit_composition}

DETAILED JACKET SPECIFICATIONS:
- Lapel Style: {lapel_spec}
- Side Pockets: {pocket_spec}
- Jacket Fit: Well-tailored, properly fitted to the model's body
- Jacket Length: Appropriate proportion to the groom's height

FABRIC AND COLOR:
- Material: {outfit_request.fabric_description or "premium wedding fabric"}
- Texture: Show realistic fabric texture and drape
- Color: Ensure consistent color throughout all pieces

FOOTWEAR SPECIFICATIONS:
- Shoes: {outfit_request.custom_shoe_description or outfit_request.shoe_type}
- Style: Professional, well-fitted, appropriate for formal wedding

ACCESSORY SPECIFICATIONS:
- Type: {outfit_request.custom_accessory_description or outfit_request.accessory_type}
- Placement: Properly positioned and styled
- Color coordination: Complement the suit color scheme

WEDDING SETTING:
- Environment: {atmosphere_desc}
- Lighting: Natural, professional wedding photography lighting
- Composition: Full-body shot showing all outfit details clearly

TECHNICAL REQUIREMENTS:
- Format: Portrait 4:3 ratio
- Quality: High-resolution, professional wedding photography standard
- Focus: Sharp details on all clothing elements
- Pose: Maintain the model's original pose and proportions
- Background: Appropriate wedding setting as specified

CRITICAL ATTENTION TO DETAILS:
- Ensure {outfit_request.pocket_type} are clearly visible and correctly styled
- Verify {outfit_request.lapel_type} is accurately represented
- Show proper fabric drape and tailoring
- Maintain consistent lighting across all garment pieces

Generate a stunning, photorealistic wedding image with perfect attention to every specified detail."""
        
        # Prepare file contents
        file_contents = [ImageContent(model_base64)]
        
        # Add fabric image if provided
        if fabric_image_data:
            fabric_base64 = base64.b64encode(fabric_image_data).decode('utf-8')
            file_contents.append(ImageContent(fabric_base64))
            prompt += "\n\nUtilisez le motif/texture du tissu de la deuxième image téléchargée pour concevoir le costume."
        
        # Add shoe image if provided  
        if shoe_image_data:
            shoe_base64 = base64.b64encode(shoe_image_data).decode('utf-8')
            file_contents.append(ImageContent(shoe_base64))
            prompt += f"\n\nUtilisez les chaussures montrées dans l'image téléchargée comme référence exacte pour les chaussures du marié."
            
        # Add accessory image if provided
        if accessory_image_data:
            accessory_base64 = base64.b64encode(accessory_image_data).decode('utf-8')
            file_contents.append(ImageContent(accessory_base64))
            prompt += f"\n\nUtilisez l'accessoire montré dans l'image téléchargée comme référence exacte pour l'accessoire du marié."
        
        # Create message
        msg = UserMessage(text=prompt, file_contents=file_contents)
        
        # Generate image
        text, images = await chat.send_message_multimodal_response(msg)
        
        if images and len(images) > 0:
            # Decode base64 image
            image_bytes = base64.b64decode(images[0]['data'])
            
            # Apply watermark
            watermarked_image = await apply_watermark(image_bytes)
            
            return watermarked_image
        else:
            raise HTTPException(status_code=500, detail="Failed to generate image")
            
    except Exception as e:
        logger.error(f"Error generating outfit image: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

async def send_verification_email(email: str, prenom: str, verification_token: str):
    """Send email verification email"""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        if not sender_email or not sender_password:
            logger.warning("Email credentials not configured")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Vérifiez votre compte TailorView"
        
        # Verification URL - adjust domain as needed
        verification_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/verify/{verification_token}"
        
        body = f"""
        Bonjour {prenom},

        Merci de vous être inscrit sur TailorView !

        Pour activer votre compte, veuillez cliquer sur le lien suivant :
        {verification_url}

        Ce lien expirera dans 24 heures.

        Si vous n'avez pas créé de compte, ignorez cet email.

        Cordialement,
        L'équipe TailorView
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Send email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            logger.info(f"Verification email sent to {email}")
            return True
            
        except Exception as smtp_error:
            logger.error(f"SMTP error: {smtp_error}")
            return False
        
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        return False

async def send_invitation_email(email: str, prenom: str, verification_token: str, inviter_name: str):
    """Send invitation email for user created by admin"""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        if not sender_email or not sender_password:
            logger.warning("Email credentials not configured")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Invitation à rejoindre TailorView"
        
        # Setup URL - adjust domain as needed
        setup_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/setup-password/{verification_token}"
        
        body = f"""
        Bonjour {prenom},

        {inviter_name} vous a invité à rejoindre TailorView !

        Pour configurer votre compte et définir votre mot de passe, veuillez cliquer sur le lien suivant :
        {setup_url}

        Ce lien expirera dans 24 heures.

        Cordialement,
        L'équipe TailorView
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Send email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            logger.info(f"Invitation email sent to {email}")
            return True
            
        except Exception as smtp_error:
            logger.error(f"SMTP error: {smtp_error}")
            return False
        
    except Exception as e:
        logger.error(f"Error sending invitation email: {e}")
        return False

async def send_email_with_image(email: str, image_data: bytes, outfit_details: dict):
    """Send generated image via email - with fallback to email queue"""
    try:
        # Email configuration - Try Gmail as fallback
        smtp_server = os.getenv('SMTP_SERVER', 'mail.infomaniak.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        logger.info(f"Attempting to send email to {email} using {smtp_server}:{smtp_port}")
        
        if not sender_email or not sender_password:
            logger.warning("Email credentials not configured in environment variables")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Votre Visualisation de Tenue de Marié Personnalisée"
        
        # Email body in French
        body = f"""Cher Client,

Merci d'avoir utilisé notre service de visualisation de tenue de marié !

Détails de votre tenue personnalisée :
- Ambiance : {outfit_details.get('atmosphere', '')}
- Type de costume : {outfit_details.get('suit_type', '')}
- Revers : {outfit_details.get('lapel_type', '')}
- Poches : {outfit_details.get('pocket_type', '')}
- Chaussures : {outfit_details.get('shoe_type', '')}
- Accessoire : {outfit_details.get('accessory_type', '')}
{f"- Description du tissu : {outfit_details.get('fabric_description', '')}" if outfit_details.get('fabric_description') else ""}

Veuillez trouver votre visualisation de tenue générée en pièce jointe.

Cordialement,
L'équipe Blandin & Delloye"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Attach image
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(image_data)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename=tenue_marie_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        )
        msg.attach(part)
        
        # Try different SMTP configurations - Google Workspace Gmail SMTP first (most reliable)
        smtp_configs = [
            # Primary: Google Workspace Gmail SMTP with App Password (STARTTLS)
            {'server': smtp_server, 'port': smtp_port, 'email': sender_email, 'password': sender_password},
            # Fallback 1: Gmail SMTP with SSL
            {'server': 'smtp.gmail.com', 'port': 465, 'email': sender_email, 'password': sender_password},
            # Fallback 2: Infomaniak SMTP (original)
            {'server': 'mail.infomaniak.com', 'port': 587, 'email': sender_email, 'password': sender_password}
        ]
        
        for config in smtp_configs:
            try:
                logger.info(f"Trying SMTP: {config['server']}:{config['port']}")
                
                if config['port'] == 465:
                    # Use SSL for port 465
                    with smtplib.SMTP_SSL(config['server'], config['port']) as server:
                        server.login(config['email'], config['password'])
                        server.send_message(msg)
                else:
                    # Use STARTTLS for port 587
                    with smtplib.SMTP(config['server'], config['port']) as server:
                        server.starttls()
                        server.login(config['email'], config['password'])
                        server.send_message(msg)
                
                logger.info(f"Email sent successfully to {email} via {config['server']}")
                return True
                
            except smtplib.SMTPAuthenticationError as auth_error:
                logger.warning(f"Auth failed for {config['server']}: {auth_error}")
                continue
            except Exception as smtp_error:
                logger.warning(f"SMTP error for {config['server']}: {smtp_error}")
                continue
        
        # If all SMTP configs fail, save to email queue for manual processing
        await save_email_to_queue(email, outfit_details, image_data)
        logger.info(f"Email queued for manual processing: {email}")
        return False
        
    except Exception as e:
        logger.error(f"Error in send_email_with_image: {e}")
        return False

async def save_email_to_queue(email: str, outfit_details: dict, image_data: bytes):
    """Save email request to database for manual processing"""
    try:
        email_queue_record = {
            "id": str(uuid.uuid4()),
            "email": email,
            "outfit_details": outfit_details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "image_saved": False
        }
        
        # Save image to queue folder
        queue_folder = Path("/app/email_queue")
        queue_folder.mkdir(exist_ok=True)
        
        image_filename = f"queued_{email_queue_record['id']}.png"
        image_path = queue_folder / image_filename
        
        with open(image_path, 'wb') as f:
            f.write(image_data)
        
        email_queue_record["image_path"] = str(image_path)
        email_queue_record["image_saved"] = True
        
        # Save to database
        await db.email_queue.insert_one(email_queue_record)
        
        logger.info(f"Email queued successfully: {email} -> {image_filename}")
        
    except Exception as e:
        logger.error(f"Error saving email to queue: {e}")

# API Routes - Authentication (removed duplicate endpoints)

# Removed duplicate get_current_user_info endpoint

@api_router.post("/auth/create-user")
async def create_user_by_admin(
    user_data: UserCreate, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_user_or_admin)
):
    """Create user by admin or user (with invitation email)"""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Generate temporary password and verification token
        temp_password = str(uuid.uuid4())[:12]  # Temporary password
        verification_token = str(uuid.uuid4())
        
        # Create user (not verified, will need to set password)
        user = User(
            **user_data.dict(exclude={"password"}),
            verification_token=verification_token,
            is_verified=False
        )
        
        # Store user with temp password
        user_dict = user.dict()
        user_dict["password"] = hash_password(temp_password)
        
        await db.users.insert_one(user_dict)
        
        # Send invitation email
        background_tasks.add_task(
            send_invitation_email,
            user_data.email,
            user_data.prenom,
            verification_token,
            current_user.prenom + " " + current_user.nom
        )
        
        return {
            "success": True,
            "message": f"User created! Invitation sent to {user_data.email}."
        }
        
    except Exception as e:
        logger.error(f"User creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# User Management Routes
@api_router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_admin_user)):
    """Get all users (admin only)"""
    users = await db.users.find({}, {"password": 0, "verification_token": 0}).to_list(1000)
    return [User(**user).dict() for user in users]

# Removed duplicate endpoint - using the more comprehensive one below

# Affichage des labels en français
ATMOSPHERE_LABELS = {
    "champetre": "Champêtre",
    "bord_de_mer": "Bord de Mer", 
    "elegant": "Elegant",
    "very_bad_trip": "Very Bad Trip",
    "rue_paris": "Dans la rue à Paris",
    "rue_new_york": "Dans la rue à New York"
}

@api_router.get("/options")
async def get_options():
    """Get all available customization options"""
    return {
        "atmospheres": [{"value": key, "label": ATMOSPHERE_LABELS[key]} for key in ATMOSPHERE_OPTIONS.keys()],
        "suit_types": SUIT_TYPES,
        "lapel_types": LAPEL_TYPES,
        "pocket_types": POCKET_TYPES,
        "shoe_types": SHOE_TYPES,
        "accessory_types": ACCESSORY_TYPES
    }

@api_router.post("/generate")
async def generate_outfit(
    model_image: UploadFile = File(...),
    fabric_image: Optional[UploadFile] = File(None),
    shoe_image: Optional[UploadFile] = File(None),
    accessory_image: Optional[UploadFile] = File(None),
    atmosphere: str = Form(...),
    suit_type: str = Form(...),
    lapel_type: str = Form(...),
    pocket_type: str = Form(...),
    shoe_type: str = Form(...),
    accessory_type: str = Form(...),
    fabric_description: Optional[str] = Form(None),
    custom_shoe_description: Optional[str] = Form(None),
    custom_accessory_description: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Generate groom outfit visualization (requires authentication)"""
    
    try:
        # Check if user has remaining image generation credits
        if current_user.images_used_total >= current_user.images_limit_total:
            raise HTTPException(
                status_code=403, 
                detail=f"Image generation limit exceeded. Used: {current_user.images_used_total}/{current_user.images_limit_total}"
            )
        # Validate file types
        if not model_image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Model file must be an image")
        
        if fabric_image and not fabric_image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Fabric file must be an image")
            
        if shoe_image and not shoe_image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Shoe file must be an image")
            
        if accessory_image and not accessory_image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Accessory file must be an image")
        
        # Read image data
        model_data = await model_image.read()
        fabric_data = await fabric_image.read() if fabric_image else None
        shoe_data = await shoe_image.read() if shoe_image else None
        accessory_data = await accessory_image.read() if accessory_image else None
        
        # Create outfit request
        outfit_request = OutfitRequestCreate(
            atmosphere=atmosphere,
            suit_type=suit_type,
            lapel_type=lapel_type,
            pocket_type=pocket_type,  
            shoe_type=shoe_type,
            accessory_type=accessory_type,
            fabric_description=fabric_description,
            custom_shoe_description=custom_shoe_description,
            custom_accessory_description=custom_accessory_description,
            email=email
        )
        
        # Generate image
        generated_image = await generate_outfit_image(model_data, fabric_data, shoe_data, accessory_data, outfit_request)
        
        # Save to database with user information
        outfit_record = OutfitRequest(**outfit_request.dict())
        outfit_record.user_email = current_user.email  # Add the connected user's email
        await db.outfit_requests.insert_one(outfit_record.dict())
        
        # Save generated image
        image_filename = f"generated_{outfit_record.id}.png"
        image_path = Path(f"/app/generated_images/{image_filename}")
        image_path.parent.mkdir(exist_ok=True)
        
        async with aiofiles.open(image_path, 'wb') as f:
            await f.write(generated_image)
        
        # Increment user's image usage count
        await db.users.update_one(
            {"id": current_user.id},
            {"$inc": {"images_used_total": 1}}
        )
        
        # Get updated user info for response
        updated_user_data = await db.users.find_one({"id": current_user.id})
        updated_user = User(**updated_user_data)
        
        return {
            "success": True,
            "request_id": outfit_record.id,
            "image_filename": image_filename,
            "download_url": f"/api/download/{image_filename}",
            "message": "Outfit generated successfully!",
            "user_credits": {
                "used": updated_user.images_used_total,
                "limit": updated_user.images_limit_total,
                "remaining": updated_user.images_limit_total - updated_user.images_used_total
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_outfit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/send-multiple")
async def send_multiple_images(request: dict):
    """Send multiple generated images via email"""
    try:
        email = request.get('email')
        image_ids = request.get('imageIds', [])
        subject = request.get('subject', 'Vos Visualisations de Tenue de Marié')
        body = request.get('body', 'Veuillez trouver vos visualisations en pièce jointe.')
        
        if not email or not image_ids:
            raise HTTPException(status_code=400, detail="Email et IDs d'images requis")
        
        # Collect all image data
        image_data_list = []
        for image_id in image_ids:
            image_path = Path(f"/app/generated_images/generated_{image_id}.png")
            if image_path.exists():
                with open(image_path, 'rb') as f:
                    image_data_list.append({
                        'data': f.read(),
                        'filename': f"tenue_variante_{len(image_data_list) + 1}.png"
                    })
        
        if not image_data_list:
            raise HTTPException(status_code=404, detail="Aucune image trouvée")
        
        # Send email with multiple attachments
        success = await send_multiple_email_with_images(email, image_data_list, subject, body)
        
        return {
            "success": success,
            "message": f"{len(image_data_list)} images envoyées" if success else "Échec de l'envoi"
        }
        
    except Exception as e:
        logger.error(f"Error sending multiple images: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def send_multiple_email_with_images(email: str, image_data_list: list, subject: str, body: str):
    """Send email with multiple image attachments"""
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'mail.infomaniak.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        if not sender_email or not sender_password:
            logger.warning("Email credentials not configured")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Attach multiple images
        for i, image_data in enumerate(image_data_list):
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(image_data['data'])
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={image_data["filename"]}'
            )
            msg.attach(part)
        
        # Send email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            logger.info(f"Multiple images email sent successfully to {email}")
            return True
            
        except Exception as smtp_error:
            logger.error(f"SMTP error: {smtp_error}")
            return False
        
    except Exception as e:
        logger.error(f"Error preparing multiple email: {e}")
        return False

@api_router.get("/download/{filename}")
async def download_image(filename: str):
    """Download generated image"""
    image_path = Path(f"/app/generated_images/{filename}")
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        path=image_path,
        filename=filename,
        media_type='image/png'
    )

@api_router.get("/admin/requests", response_model=List[OutfitRequest])
async def get_all_requests():
    """Get all outfit requests for admin view"""
    requests = await db.outfit_requests.find().sort("timestamp", -1).to_list(1000)
    return [OutfitRequest(**request) for request in requests]

@api_router.get("/admin/stats")
async def get_admin_stats():
    """Get admin statistics"""
    total_requests = await db.outfit_requests.count_documents({})
    recent_requests = await db.outfit_requests.count_documents({
        "timestamp": {"$gte": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)}
    })
    
    # Get requests by atmosphere
    pipeline = [
        {"$group": {"_id": "$atmosphere", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    atmosphere_stats = await db.outfit_requests.aggregate(pipeline).to_list(10)
    
    return {
        "total_requests": total_requests,
        "today_requests": recent_requests,
        "atmosphere_stats": atmosphere_stats,
        "generated_images_count": len(list(Path("/app/generated_images").glob("*.png"))) if Path("/app/generated_images").exists() else 0
    }

@api_router.get("/admin/email-queue")
async def get_email_queue():
    """Get pending email queue for admin view"""
    try:
        queue_items = await db.email_queue.find({"status": "pending"}).sort("timestamp", -1).to_list(100)
        
        # Convert ObjectId to string for JSON serialization
        for item in queue_items:
            if '_id' in item:
                item['_id'] = str(item['_id'])
        
        return {"success": True, "queue": queue_items}
    except Exception as e:
        logger.error(f"Error fetching email queue: {e}")
        return {"success": False, "queue": []}

@api_router.delete("/admin/request/{request_id}")
async def delete_request(request_id: str):
    """Delete a specific request and its associated image"""
    try:
        # Delete from database
        result = await db.outfit_requests.delete_one({"id": request_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Delete associated image file
        image_path = Path(f"/app/generated_images/generated_{request_id}.png")
        if image_path.exists():
            image_path.unlink()
        
        return {"success": True, "message": "Request deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/requests", response_model=List[OutfitRequest])
async def get_requests():
    """Get all outfit requests"""
    requests = await db.outfit_requests.find().sort("timestamp", -1).to_list(1000)
    return [OutfitRequest(**request) for request in requests]

# Authentication endpoints
@api_router.post("/auth/register")
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate password
        if not validate_password(user_data.password):
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters with 1 digit and 1 letter")
        
        # Create new user
        user = User(
            nom=user_data.nom,
            email=user_data.email,
            role=UserRole.CLIENT,
            images_limit_total=5  # Default limit
        )
        
        user_dict = user.dict()
        user_dict["password"] = hash_password(user_data.password)
        
        await db.users.insert_one(user_dict)
        
        # Create access token
        access_token = create_access_token({"email": user.email, "role": user.role})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    """Login user"""
    try:
        # Find user
        user_data = await db.users.find_one({"email": login_data.email})
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if user is active
        if not user_data.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account deactivated")
        
        # Verify password
        if not bcrypt.checkpw(login_data.password.encode('utf-8'), user_data["password"].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        access_token = create_access_token({"email": user_data["email"], "role": user_data["role"]})
        
        # Convert to User model for response
        user = User(**user_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user.dict()

# User management endpoints (admin only)
@api_router.get("/admin/users", response_model=List[User])
async def get_all_users(admin_user: User = Depends(get_admin_user)):
    """Get all users (admin only)"""
    users = await db.users.find().sort("created_at", -1).to_list(1000)
    return [User(**user) for user in users]

@api_router.put("/admin/users/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate, admin_user: User = Depends(get_admin_user)):
    """Update user (admin only)"""
    try:
        logger.info(f"=== USER UPDATE START ===")
        logger.info(f"Attempting to update user with ID: {user_id}")
        logger.info(f"Update request: {user_update.dict()}")
        
        # Find user by id field
        logger.info(f"Searching for user by id field...")
        user_data = await db.users.find_one({"id": user_id})
        if not user_data:
            logger.info(f"User not found by id, trying email fallback...")
            # Try finding by email as fallback (in case user_id is email)
            user_data = await db.users.find_one({"email": user_id})
            if not user_data:
                logger.warning(f"User not found with ID: {user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            else:
                logger.info(f"User found by email fallback")
        else:
            logger.info(f"User found by id field")
        
        logger.info(f"Found user: {user_data.get('email', 'N/A')} (id: {user_data.get('id', 'N/A')})")
        
        # Prepare update data
        update_data = {}
        if user_update.role is not None:
            update_data["role"] = user_update.role
        if user_update.images_limit_total is not None:
            update_data["images_limit_total"] = user_update.images_limit_total
        if user_update.images_used_total is not None:
            update_data["images_used_total"] = user_update.images_used_total
        if user_update.is_active is not None:
            update_data["is_active"] = user_update.is_active
        
        logger.info(f"Update data prepared: {update_data}")
        
        # Update user using the same identifier that found the user
        query = {"id": user_data["id"]} if "id" in user_data else {"email": user_data["email"]}
        logger.info(f"Update query: {query}")
        
        result = await db.users.update_one(query, {"$set": update_data})
        logger.info(f"Update result: matched={result.matched_count}, modified={result.modified_count}")
        
        if result.matched_count == 0:
            logger.error(f"Update failed: no documents matched query {query}")
            raise HTTPException(status_code=404, detail="User not found during update")
        
        # Get updated user
        logger.info(f"Retrieving updated user data...")
        updated_user_data = await db.users.find_one(query)
        if not updated_user_data:
            logger.error(f"Could not retrieve updated user with query {query}")
            raise HTTPException(status_code=500, detail="Could not retrieve updated user")
        
        logger.info(f"Creating User model from updated data...")
        updated_user = User(**updated_user_data)
        logger.info(f"User model created successfully")
        
        result_dict = updated_user.dict()
        logger.info(f"=== USER UPDATE SUCCESS ===")
        return result_dict
        
    except HTTPException as he:
        logger.error(f"HTTP Exception in user update: {he.detail}")
        logger.error(f"=== USER UPDATE FAILED (HTTP) ===")
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating user: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"=== USER UPDATE FAILED (EXCEPTION) ===")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin_user: User = Depends(get_admin_user)):
    """Delete user (admin only)"""
    try:
        result = await db.users.delete_one({"id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="User deletion failed")

# Include router in main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Create default admin user on startup"""
    try:
        # Check if admin exists
        admin_email = "charles@blandindelloye.com"
        existing_admin = await db.users.find_one({"email": admin_email})
        
        if not existing_admin:
            # Create default admin
            admin_user = User(
                nom="Charles Delloye",
                email=admin_email,
                role=UserRole.ADMIN,
                images_limit_total=999  # Unlimited for admin
            )
            
            admin_dict = admin_user.dict()
            admin_dict["password"] = hash_password("114956Xp")
            
            await db.users.insert_one(admin_dict)
            logger.info("Default admin user created")
        
    except Exception as e:
        logger.error(f"Error creating default admin: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()