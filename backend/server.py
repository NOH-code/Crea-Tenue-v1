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
        
        # Build prompt
        atmosphere_desc = ATMOSPHERE_OPTIONS.get(outfit_request.atmosphere, outfit_request.atmosphere)
        
        prompt = f"""Create a professional photo of a future groom using the attached full-length model photo. 

Wedding Setting: {atmosphere_desc}

Groom's Outfit Details:
- Suit: {outfit_request.suit_type}
- Fabric: {outfit_request.fabric_description or "premium fabric"}  
- Lapel: {outfit_request.lapel_type}
- Pockets: {outfit_request.pocket_type}
- Shoes: {outfit_request.custom_shoe_description or outfit_request.shoe_type}
- Accessory: {outfit_request.custom_accessory_description or outfit_request.accessory_type}

Style Requirements:
- Portrait format in 4:3 ratio
- High-quality, professional wedding photography style
- Natural lighting and composition
- Show full body of the groom in the specified setting
- Ensure the outfit details are clearly visible and well-fitted
- Maintain the model's pose and proportions from the original photo

Generate a stunning, photorealistic image that captures the elegance and style of this wedding moment."""
        
        # Prepare file contents
        file_contents = [ImageContent(model_base64)]
        
        # Add fabric image if provided
        if fabric_image_data:
            fabric_base64 = base64.b64encode(fabric_image_data).decode('utf-8')
            file_contents.append(ImageContent(fabric_base64))
            prompt += "\n\nPlease use the fabric pattern/texture from the second uploaded image to design the suit."
        
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
        # Email configuration (use environment variables in production)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.getenv('SENDER_EMAIL', 'noreply@tailorview.com')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        if not sender_password:
            logger.warning("Email credentials not configured")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Your Custom Groom Outfit Visualization"
        
        # Email body
        body = f"""
        Dear Customer,

        Thank you for using our groom outfit visualization service!

        Your custom outfit details:
        - Atmosphere: {outfit_details.get('atmosphere', '')}
        - Suit Type: {outfit_details.get('suit_type', '')}
        - Lapel: {outfit_details.get('lapel_type', '')}
        - Pockets: {outfit_details.get('pocket_type', '')}
        - Shoes: {outfit_details.get('shoe_type', '')}
        - Accessory: {outfit_details.get('accessory_type', '')}

        Please find your generated outfit visualization attached.

        Best regards,
        TailorView Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach image
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(image_data)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename=groom_outfit_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        )
        msg.attach(part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
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
        
        # Read image data
        model_data = await model_image.read()
        fabric_data = await fabric_image.read() if fabric_image else None
        
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
        generated_image = await generate_outfit_image(model_data, fabric_data, outfit_request)
        
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

@api_router.get("/requests", response_model=List[OutfitRequest])
async def get_requests():
    """Get all outfit requests"""
    requests = await db.outfit_requests.find().to_list(1000)
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