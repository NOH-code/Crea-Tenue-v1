#!/usr/bin/env python3
import requests
import io
from PIL import Image
import sys
import json

def create_test_image(width=400, height=600, color=(128, 128, 128)):
    """Create a test image for upload"""
    image = Image.new('RGB', (width, height), color)
    img_buffer = io.BytesIO()
    image.save(img_buffer, format='JPEG')
    img_buffer.seek(0)
    return img_buffer

def test_send_multiple_endpoint():
    """Test send-multiple endpoint"""
    print("🔍 Testing Send Multiple Images Endpoint...")
    
    base_url = "https://outfit-preview-43.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # First generate some images to get IDs
    model_image = create_test_image(400, 600, (200, 150, 100))
    
    # Generate first image
    data1 = {
        'atmosphere': 'rustic',
        'suit_type': '2-piece suit',
        'lapel_type': 'Standard notch lapel',
        'pocket_type': 'Slanted, no flaps',
        'shoe_type': 'Black loafers',
        'accessory_type': 'Tie'
    }
    
    files1 = {
        'model_image': ('model.jpg', model_image, 'image/jpeg')
    }
    
    print("   Generating first image...")
    try:
        response1 = requests.post(f"{api_url}/generate", data=data1, files=files1, timeout=60)
        if response1.status_code != 200:
            print(f"❌ Failed to generate first image: {response1.status_code}")
            return False
        
        result1 = response1.json()
        print(f"   ✅ First image generated: {result1['request_id']}")
        
    except Exception as e:
        print(f"❌ Error generating first image: {e}")
        return False
    
    # Generate second image
    data2 = {
        'atmosphere': 'seaside',
        'suit_type': '3-piece suit',
        'lapel_type': 'Wide peak lapel',
        'pocket_type': 'Straight with flaps',
        'shoe_type': 'Brown loafers',
        'accessory_type': 'Bow tie'
    }
    
    files2 = {
        'model_image': ('model.jpg', create_test_image(400, 600, (150, 200, 100)), 'image/jpeg')
    }
    
    print("   Generating second image...")
    try:
        response2 = requests.post(f"{api_url}/generate", data=data2, files=files2, timeout=60)
        if response2.status_code != 200:
            print(f"❌ Failed to generate second image: {response2.status_code}")
            return False
        
        result2 = response2.json()
        print(f"   ✅ Second image generated: {result2['request_id']}")
        
    except Exception as e:
        print(f"❌ Error generating second image: {e}")
        return False
    
    # Now test send-multiple endpoint
    image_ids = [result1['request_id'], result2['request_id']]
    
    multiple_send_data = {
        'email': 'charles@blandindelloye.com',
        'imageIds': image_ids,
        'subject': 'Your Custom Groom Outfit Variations - Test',
        'body': 'Please find your custom groom outfit variations attached. This is a test email.'
    }
    
    print("   Testing send-multiple endpoint...")
    try:
        response = requests.post(
            f"{api_url}/send-multiple", 
            json=multiple_send_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Send-multiple request successful!")
            print(f"   Response: {result}")
            
            if result.get('success'):
                print("🎉 Multiple images sent successfully!")
                return True
            else:
                print("❌ Multiple image sending failed")
                print(f"   Error: {result.get('message', 'No message')}")
                return False
        else:
            print(f"❌ Send-multiple request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Send-multiple request failed with exception: {str(e)}")
        return False

def main():
    print("🚀 Send Multiple Images Endpoint Test")
    print("=" * 50)
    
    success = test_send_multiple_endpoint()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Send Multiple Images endpoint is working!")
        return 0
    else:
        print("❌ Send Multiple Images endpoint has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())