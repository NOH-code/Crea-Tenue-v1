#!/usr/bin/env python3
"""
Test script to verify Google Gemini API integration for image generation
"""
import os
import sys
import base64
from io import BytesIO
from PIL import Image
import asyncio

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from server import generate_outfit_image, OutfitRequestCreate

async def test_google_api_integration():
    """Test the Google Gemini API integration for image generation"""

    print("🔍 Testing Google Gemini API Integration for Image Generation")
    print("=" * 60)

    try:
        # Check if GOOGLE_API_KEY is set
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("❌ GOOGLE_API_KEY environment variable not set")
            return False

        print(f"✅ GOOGLE_API_KEY found: {api_key[:20]}...")

        # Create a simple test image (400x600 gray rectangle)
        test_image = Image.new('RGB', (400, 600), (128, 128, 128))
        img_buffer = BytesIO()
        test_image.save(img_buffer, format='JPEG')
        model_image_data = img_buffer.getvalue()

        print("✅ Test image created (400x600 JPEG)")

        # Create a test outfit request
        outfit_request = OutfitRequestCreate(
            atmosphere="elegant",
            suit_type="Costume 2 pièces",
            lapel_type="Standard notch lapel",
            pocket_type="Slanted, no flaps",
            shoe_type="Black loafers",
            accessory_type="Tie",
            fabric_description="Navy blue wool",
            gender="homme"
        )

        print("✅ Test outfit request created")
        print(f"   Suit Type: {outfit_request.suit_type}")
        print(f"   Atmosphere: {outfit_request.atmosphere}")
        print(f"   Gender: {outfit_request.gender}")

        # Test image generation
        print("\n🔄 Generating image with Google Gemini API...")
        generated_image = await generate_outfit_image(
            model_image_data=model_image_data,
            fabric_image_data=None,
            shoe_image_data=None,
            accessory_image_data=None,
            outfit_request=outfit_request
        )

        if generated_image:
            print("✅ Image generation successful!")

            # Verify the image data
            try:
                # Try to open the generated image
                generated_img = Image.open(BytesIO(generated_image))
                width, height = generated_img.size
                print(f"✅ Generated image dimensions: {width}x{height}")
                print(f"✅ Image format: {generated_img.format}")
                print(f"✅ Image mode: {generated_img.mode}")

                # Save the test image for verification
                output_path = "test_generated_image.png"
                generated_img.save(output_path)
                print(f"✅ Test image saved as: {output_path}")

                # Check file size
                file_size = len(generated_image)
                print(f"✅ Generated image file size: {file_size} bytes")

                if file_size > 1000:  # Reasonable minimum size
                    print("✅ Image generation test PASSED!")
                    return True
                else:
                    print("❌ Generated image file size too small")
                    return False

            except Exception as img_error:
                print(f"❌ Error processing generated image: {img_error}")
                return False
        else:
            print("❌ Image generation returned None")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🚀 Starting Google Gemini API Integration Test")
    print("This test will verify that the image generation works with Google API")
    print()

    success = await test_google_api_integration()

    print()
    print("=" * 60)
    if success:
        print("🎉 GOOGLE GEMINI API INTEGRATION TEST PASSED!")
        print("✅ The application now uses Google Gemini API for image generation")
        print("✅ Emergent integration has been successfully replaced")
    else:
        print("❌ GOOGLE GEMINI API INTEGRATION TEST FAILED!")
        print("🔧 Please check your GOOGLE_API_KEY and network connection")

    return success

if __name__ == "__main__":
    # Load environment variables from backend/.env if it exists
    env_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)
        print(f"📄 Loaded environment variables from {env_path}")

    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)