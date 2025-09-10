from fastapi import FastAPI, APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import logging
import uuid
import base64
import asyncio
import aiofiles
from datetime import datetime, timezone
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
    "rustic": "mixing flowers and wood, with a beautiful floral arch in the background, bright ambiance",
    "seaside": "coastal, with the sea in the background; the ceremony takes place on a beach, with carpets on the sand and chairs for guests",
    "chic_elegant": "in a renovated castle, the wedding ceremony takes place in a hall resembling the Hall of Mirrors at Versailles",
    "hangover": "like in the movie The Hangover, the wedding happens on the Las Vegas Strip; a small improvised ceremony. The scene shows signs of a big party the night before: bottles, cans, trash, people sleeping, and a messy environment"
}

SUIT_TYPES = ["2-piece suit", "3-piece suit"]

LAPEL_TYPES = [
    "Standard notch lapel",
    "Wide notch lapel", 
    "Standard peak lapel",
    "Wide peak lapel",
    "Shawl collar with satin lapel",
    "Standard double-breasted peak lapel",
    "Wide double-breasted peak lapel"
]

POCKET_TYPES = [
    "Slanted, no flaps",
    "Slanted with flaps", 
    "Straight with flaps",
    "Straight, no flaps",
    "Patch pockets"
]

SHOE_TYPES = [
    "Black loafers",
    "Brown loafers",
    "Black one-cut", 
    "Brown one-cut",
    "White sneakers",
    "Custom"
]

ACCESSORY_TYPES = ["Bow tie", "Tie", "Custom"]

async def apply_watermark(image_data: bytes) -> bytes:
    """Apply watermark to generated image"""
    try:
        # Open the generated image
        image = Image.open(io.BytesIO(image_data))
        
        # Open watermark
        watermark_path = Path("/app/logo_watermark.png")
        if watermark_path.exists():
            watermark = Image.open(watermark_path)
            
            # Calculate watermark size (10% of image width)
            img_width, img_height = image.size
            watermark_width = int(img_width * 0.1)
            watermark_height = int(watermark.size[1] * (watermark_width / watermark.size[0]))
            
            # Resize watermark
            watermark = watermark.resize((watermark_width, watermark_height), Image.Resampling.LANCZOS)
            
            # Position watermark at bottom center
            x = (img_width - watermark_width) // 2
            y = img_height - watermark_height - 20
            
            # Apply watermark
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

async def send_email_with_image(email: str, image_data: bytes, outfit_details: dict):
    """Send generated image via email"""
    try:
        # Email configuration - Add these to .env file for production
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        if not sender_email or not sender_password:
            logger.warning("Email credentials not configured in environment variables")
            logger.info("To enable email delivery, add SENDER_EMAIL and SENDER_PASSWORD to .env file")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Votre Visualisation de Tenue de Marié Personnalisée"
        
        # Email body in French
        body = f"""
        Cher Client,

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
        L'équipe de Visualisation de Tenue de Marié
        """
        
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
        
        # Send email with better error handling
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP Authentication failed - check email credentials")
            return False
        except smtplib.SMTPRecipientsRefused:
            logger.error(f"Recipient email rejected: {email}")
            return False
        except smtplib.SMTPServerDisconnected:
            logger.error("SMTP server disconnected")
            return False
        except Exception as smtp_error:
            logger.error(f"SMTP error: {smtp_error}")
            return False
        
    except Exception as e:
        logger.error(f"Error preparing email: {e}")
        return False

# API Routes
@api_router.get("/")
async def root():
    return {"message": "TailorView - Groom Outfit Generator API"}

@api_router.get("/options")
async def get_options():
    """Get all available customization options"""
    return {
        "atmospheres": list(ATMOSPHERE_OPTIONS.keys()),
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
    email: Optional[str] = Form(None)
):
    """Generate groom outfit visualization"""
    
    try:
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
        
        # Save to database
        outfit_record = OutfitRequest(**outfit_request.dict())
        await db.outfit_requests.insert_one(outfit_record.dict())
        
        # Save generated image
        image_filename = f"generated_{outfit_record.id}.png"
        image_path = Path(f"/app/generated_images/{image_filename}")
        image_path.parent.mkdir(exist_ok=True)
        
        async with aiofiles.open(image_path, 'wb') as f:
            await f.write(generated_image)
        
        # Send email if requested
        email_sent = False
        if email:
            email_sent = await send_email_with_image(email, generated_image, outfit_request.dict())
        
        return {
            "success": True,
            "request_id": outfit_record.id,
            "image_filename": image_filename,
            "download_url": f"/api/download/{image_filename}",
            "email_sent": email_sent,
            "message": "Outfit generated successfully!"
        }
        
    except Exception as e:
        logger.error(f"Error in generate_outfit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()