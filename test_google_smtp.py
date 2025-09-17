#!/usr/bin/env python3
import requests
import io
from PIL import Image
import sys

def create_test_image(width=400, height=600, color=(128, 128, 128)):
    """Create a test image for upload"""
    image = Image.new('RGB', (width, height), color)
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    return img_buffer

def test_google_workspace_smtp():
    """Test Google Workspace SMTP with corrected configuration"""
    print("🔍 Testing Google Workspace SMTP with corrected configuration...")
    
    base_url = "https://outfit-preview-43.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Create test image
    model_image = create_test_image(400, 600, (200, 150, 100))
    
    # Use a real email for testing
    test_email = "charles@blandindelloye.com"
    
    data = {
        'atmosphere': 'chic_elegant',
        'suit_type': '3-piece suit',
        'lapel_type': 'Standard peak lapel',
        'pocket_type': 'Straight with flaps',
        'shoe_type': 'Brown loafers',
        'accessory_type': 'Bow tie',
        'fabric_description': 'Premium navy wool with subtle texture',
        'email': test_email
    }
    
    files = {
        'model_image': ('model.jpg', model_image, 'image/jpeg')
    }
    
    print(f"   Sending request to: {api_url}/generate")
    print(f"   Test email: {test_email}")
    
    try:
        response = requests.post(f"{api_url}/generate", data=data, files=files, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print(f"   Response: {result}")
            
            # Check email sending results
            if 'email_sent' in result and 'email_message' in result:
                if result['email_sent']:
                    print("🎉 EMAIL SENT SUCCESSFULLY via Google Workspace SMTP!")
                    print(f"   Success message: {result['email_message']}")
                    print("   🎯 SMTP authentication issue RESOLVED")
                    return True
                else:
                    print("❌ Email sending failed - checking error details...")
                    print(f"   Error message: {result['email_message']}")
                    
                    # Check if it's still an authentication error
                    error_msg = result['email_message'].lower()
                    if "authentication" in error_msg or "login" in error_msg or "password" in error_msg:
                        print("❌ SMTP authentication still failing")
                    elif "enregistrée" in result['email_message'] or "manuellement" in result['email_message']:
                        print("⚠️  Email queued - SMTP authentication may still be failing")
                    else:
                        print("✅ Authentication working, but email delivery failed for other reasons")
                    
                    return False
            else:
                print("❌ Missing email status fields in response")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed with exception: {str(e)}")
        return False

def main():
    print("🚀 Google Workspace SMTP Configuration Test")
    print("=" * 50)
    
    success = test_google_workspace_smtp()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Google Workspace SMTP is working!")
        return 0
    else:
        print("❌ Google Workspace SMTP still has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())