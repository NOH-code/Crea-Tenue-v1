#!/usr/bin/env python3

import requests
import sys
import io
from PIL import Image

class NewFeaturesAPITester:
    def __init__(self, base_url="https://outfit-preview-48.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None

    def create_test_image(self, width=400, height=600, color=(128, 128, 128)):
        """Create a test image for upload"""
        image = Image.new('RGB', (width, height), color)
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        return img_buffer

    def login_admin(self):
        """Login as admin to get token"""
        login_data = {
            "email": "charles@blandindelloye.com",
            "password": "114956Xp"
        }
        
        response = requests.post(f"{self.api_url}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data['access_token']
            print("✅ Admin login successful")
            return True
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return False

    def test_gender_selection_feature(self):
        """Test Gender Selection Feature"""
        print("\n🔍 Testing Gender Selection Feature...")
        
        # 1. Test /api/options endpoint
        print("1. Testing /api/options endpoint...")
        response = requests.get(f"{self.api_url}/options")
        
        if response.status_code == 200:
            data = response.json()
            if 'genders' in data:
                genders = data['genders']
                gender_values = [g.get('value') for g in genders if isinstance(g, dict)]
                if 'homme' in gender_values and 'femme' in gender_values:
                    print("✅ Gender options working correctly")
                    print(f"   Found genders: {genders}")
                else:
                    print(f"❌ Missing gender options. Found: {gender_values}")
                    return False
            else:
                print("❌ No 'genders' field in options response")
                return False
        else:
            print(f"❌ Options endpoint failed: {response.status_code}")
            return False
        
        # 2. Test /api/generate with gender parameter
        print("2. Testing /api/generate with gender parameter...")
        
        if not self.admin_token:
            if not self.login_admin():
                return False
        
        # Test with gender="homme"
        model_image = self.create_test_image(400, 600, (200, 150, 100))
        
        data = {
            'atmosphere': 'elegant',
            'suit_type': 'Costume 2 pièces',
            'lapel_type': 'Revers cran droit standard',
            'pocket_type': 'En biais, sans rabat',
            'shoe_type': 'Mocassins noirs',
            'accessory_type': 'Nœud papillon',
            'gender': 'homme',
            'fabric_description': 'Costume bleu marine'
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg')
        }
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        response = requests.post(f"{self.api_url}/generate", data=data, files=files, headers=headers)
        
        if response.status_code == 200:
            print("✅ Generate with gender=homme successful")
            return True
        else:
            print(f"❌ Generate with gender failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

    def test_image_modification_feature(self):
        """Test Image Modification Feature"""
        print("\n🔍 Testing Image Modification Feature...")
        
        if not self.admin_token:
            if not self.login_admin():
                return False
        
        # 1. Generate an original image first
        print("1. Generating original image...")
        
        model_image = self.create_test_image(400, 600, (200, 150, 100))
        
        data = {
            'atmosphere': 'elegant',
            'suit_type': 'Costume 2 pièces',
            'lapel_type': 'Revers cran droit standard',
            'pocket_type': 'En biais, sans rabat',
            'shoe_type': 'Mocassins noirs',
            'accessory_type': 'Nœud papillon',
            'gender': 'homme',
            'fabric_description': 'Costume bleu marine'
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg')
        }
        
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        response = requests.post(f"{self.api_url}/generate", data=data, files=files, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to generate original image: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
        
        original_data = response.json()
        request_id = original_data.get('request_id')
        
        if not request_id:
            print("❌ No request_id in original generation response")
            return False
        
        print(f"✅ Original image generated with request_id: {request_id}")
        
        # 2. Test /api/modify-image endpoint
        print("2. Testing /api/modify-image endpoint...")
        
        modification_data = {
            "request_id": request_id,
            "modification_description": "Change the tie color to burgundy red"
        }
        
        response = requests.post(f"{self.api_url}/modify-image", json=modification_data, headers=headers)
        
        if response.status_code == 200:
            print("✅ Image modification successful")
            modify_data = response.json()
            print(f"   New request_id: {modify_data.get('request_id', 'N/A')}")
            print(f"   Modification: {modify_data.get('modification_description', 'N/A')}")
            return True
        else:
            print(f"❌ Image modification failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False

    def test_authentication_requirement(self):
        """Test that modify-image requires authentication"""
        print("\n🔍 Testing Authentication Requirement...")
        
        modification_data = {
            "request_id": "test-id",
            "modification_description": "test modification"
        }
        
        response = requests.post(f"{self.api_url}/modify-image", json=modification_data)
        
        if response.status_code == 401:
            print("✅ Authentication requirement working correctly")
            return True
        else:
            print(f"❌ Expected 401, got {response.status_code}")
            return False

def main():
    print("🚀 NEW FEATURES TESTING - FOCUSED TEST")
    print("🎯 Testing Gender Selection and Image Modification Features")
    print("=" * 60)
    
    tester = NewFeaturesAPITester()
    
    # Test results
    results = []
    
    # Test Gender Selection
    print("\n📋 TESTING GENDER SELECTION FEATURE")
    gender_success = tester.test_gender_selection_feature()
    results.append(("Gender Selection Feature", gender_success))
    
    # Test Image Modification
    print("\n📋 TESTING IMAGE MODIFICATION FEATURE")
    modify_success = tester.test_image_modification_feature()
    results.append(("Image Modification Feature", modify_success))
    
    # Test Authentication
    print("\n📋 TESTING AUTHENTICATION REQUIREMENT")
    auth_success = tester.test_authentication_requirement()
    results.append(("Authentication Requirement", auth_success))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 ALL NEW FEATURES WORKING CORRECTLY!")
        return 0
    else:
        print(f"\n❌ {total - passed} feature(s) have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())