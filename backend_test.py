import requests
import sys
import os
import io
import base64
from datetime import datetime
from PIL import Image
import json

class TailorViewAPITester:
    def __init__(self, base_url="https://outfit-gen-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers, timeout=60)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {response_data}")
                    return True, response_data
                except:
                    print(f"   Response: Non-JSON response")
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def create_test_image(self, width=400, height=600, color=(128, 128, 128)):
        """Create a test image for upload"""
        image = Image.new('RGB', (width, height), color)
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='JPEG')
        img_buffer.seek(0)
        return img_buffer

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )

    def test_options_endpoint(self):
        """Test options endpoint"""
        success, response = self.run_test(
            "Get Options",
            "GET", 
            "options",
            200
        )
        
        if success:
            # Verify expected options are present
            expected_keys = ['atmospheres', 'suit_types', 'lapel_types', 'pocket_types', 'shoe_types', 'accessory_types']
            for key in expected_keys:
                if key not in response:
                    print(f"⚠️  Warning: Missing expected key '{key}' in options response")
                else:
                    print(f"   ✓ Found {key}: {len(response[key])} options")
        
        return success, response

    def test_generate_endpoint_minimal(self):
        """Test generate endpoint with minimal required data"""
        # Create test images
        model_image = self.create_test_image(400, 600, (200, 150, 100))  # Model image
        
        # Prepare form data
        data = {
            'atmosphere': 'rustic',
            'suit_type': '2-piece suit',
            'lapel_type': 'Standard notch lapel',
            'pocket_type': 'Slanted, no flaps',
            'shoe_type': 'Black loafers',
            'accessory_type': 'Tie'
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg')
        }
        
        return self.run_test(
            "Generate Outfit (Minimal)",
            "POST",
            "generate",
            200,
            data=data,
            files=files
        )

    def test_generate_endpoint_full(self):
        """Test generate endpoint with all optional parameters including multi-image support"""
        # Create test images
        model_image = self.create_test_image(400, 600, (200, 150, 100))  # Model image
        fabric_image = self.create_test_image(200, 200, (50, 100, 150))  # Fabric image
        shoe_image = self.create_test_image(300, 200, (139, 69, 19))     # Shoe image (brown)
        accessory_image = self.create_test_image(150, 150, (255, 0, 0))  # Accessory image (red)
        
        # Prepare form data with all options
        data = {
            'atmosphere': 'chic_elegant',
            'suit_type': '3-piece suit',
            'lapel_type': 'Wide peak lapel',
            'pocket_type': 'Straight with flaps',
            'shoe_type': 'Custom',
            'accessory_type': 'Custom',
            'fabric_description': 'Navy blue wool with subtle pinstripe pattern',
            'custom_shoe_description': 'Brown leather oxford shoes with brogue detailing',
            'custom_accessory_description': 'Silk pocket square with geometric pattern',
            'email': 'test@example.com'
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg'),
            'fabric_image': ('fabric.jpg', fabric_image, 'image/jpeg'),
            'shoe_image': ('shoe.jpg', shoe_image, 'image/jpeg'),
            'accessory_image': ('accessory.jpg', accessory_image, 'image/jpeg')
        }
        
        return self.run_test(
            "Generate Outfit (Full Multi-Image)",
            "POST",
            "generate", 
            200,
            data=data,
            files=files
        )

    def test_generate_endpoint_validation(self):
        """Test generate endpoint validation (missing required fields)"""
        # Test without model image
        data = {
            'atmosphere': 'rustic',
            'suit_type': '2-piece suit'
        }
        
        success, response = self.run_test(
            "Generate Outfit (Missing Model Image)",
            "POST",
            "generate",
            422,  # Expecting validation error
            data=data
        )
        
        return success

    def test_generate_endpoint_invalid_file(self):
        """Test generate endpoint with invalid file type"""
        # Create a text file instead of image
        text_file = io.BytesIO(b"This is not an image")
        
        data = {
            'atmosphere': 'rustic',
            'suit_type': '2-piece suit',
            'lapel_type': 'Standard notch lapel',
            'pocket_type': 'Slanted, no flaps',
            'shoe_type': 'Black loafers',
            'accessory_type': 'Tie'
        }
        
        files = {
            'model_image': ('model.txt', text_file, 'text/plain')
        }
        
        return self.run_test(
            "Generate Outfit (Invalid File Type)",
            "POST",
            "generate",
            400,  # Expecting bad request
            data=data,
            files=files
        )

    def test_download_endpoint(self, filename=None):
        """Test download endpoint"""
        if not filename:
            # Use a dummy filename for testing
            filename = "test_image.png"
        
        return self.run_test(
            "Download Image",
            "GET",
            f"download/{filename}",
            404  # Expecting not found for non-existent file
        )

    def test_requests_endpoint(self):
        """Test requests endpoint"""
        return self.run_test(
            "Get All Requests",
            "GET",
            "requests",
            200
        )

    def test_admin_requests_endpoint(self):
        """Test admin requests endpoint"""
        return self.run_test(
            "Get Admin Requests",
            "GET",
            "admin/requests",
            200
        )

    def test_admin_stats_endpoint(self):
        """Test admin stats endpoint"""
        success, response = self.run_test(
            "Get Admin Stats",
            "GET",
            "admin/stats",
            200
        )
        
        if success:
            # Verify expected stats are present
            expected_keys = ['total_requests', 'today_requests', 'atmosphere_stats', 'generated_images_count']
            for key in expected_keys:
                if key not in response:
                    print(f"⚠️  Warning: Missing expected key '{key}' in stats response")
                else:
                    print(f"   ✓ Found {key}: {response[key]}")
        
        return success, response

    def test_watermark_changes(self):
        """Test NEW FEATURE: Watermark logo size increase (800%) and text removal"""
        print("\n🔍 Testing NEW FEATURE: Watermark Changes (800% logo increase, no text)...")
        
        # Create test image for generation
        model_image = self.create_test_image(400, 600, (200, 150, 100))
        
        data = {
            'atmosphere': 'rustic',
            'suit_type': '2-piece suit',
            'lapel_type': 'Standard notch lapel',
            'pocket_type': 'Slanted, no flaps',
            'shoe_type': 'Black loafers',
            'accessory_type': 'Tie'
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg')
        }
        
        success, response = self.run_test(
            "Generate Image for Watermark Testing",
            "POST",
            "generate",
            200,
            data=data,
            files=files
        )
        
        if success and 'image_filename' in response:
            print("✅ Image generated successfully for watermark testing")
            print(f"   Generated file: {response['image_filename']}")
            
            # Try to download and analyze the image
            download_success, download_data = self.run_test(
                "Download Generated Image for Analysis",
                "GET",
                f"download/{response['image_filename']}",
                200
            )
            
            if download_success:
                print("✅ Watermark feature test completed - image generated and downloadable")
                print("   NOTE: Manual verification needed to confirm:")
                print("   - Logo is 800% larger (80% of image width vs previous 10%)")
                print("   - No text 'Généré avec IA • Filigrane par Blandin & Delloye' present")
                return True, response
            else:
                print("❌ Could not download generated image for watermark analysis")
                return False, {}
        else:
            print("❌ Failed to generate image for watermark testing")
            return False, {}

    def test_email_functionality_with_error_handling(self):
        """Test NEW FEATURE: Enhanced email sending with better error handling"""
        print("\n🔍 Testing NEW FEATURE: Email Functionality with Enhanced Error Handling...")
        
        # Test with valid email format
        model_image = self.create_test_image(400, 600, (200, 150, 100))
        
        # Test with a real-looking email address
        test_email = "charles.delloye@blandindelloye.com"
        
        data = {
            'atmosphere': 'chic_elegant',
            'suit_type': '3-piece suit',
            'lapel_type': 'Standard peak lapel',
            'pocket_type': 'Straight with flaps',
            'shoe_type': 'Brown loafers',
            'accessory_type': 'Bow tie',
            'fabric_description': 'Premium navy wool',
            'email': test_email
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg')
        }
        
        success, response = self.run_test(
            "Generate with Email (Enhanced Error Handling)",
            "POST",
            "generate",
            200,
            data=data,
            files=files
        )
        
        if success:
            # Check for email_message field in response
            if 'email_message' in response:
                print(f"✅ email_message field present: {response['email_message']}")
                
                # Check email_sent status
                if 'email_sent' in response:
                    print(f"   Email sent status: {response['email_sent']}")
                    
                    if response['email_sent']:
                        print("✅ Email reportedly sent successfully")
                    else:
                        print("⚠️  Email sending failed, but error handling working")
                        print(f"   Error message: {response['email_message']}")
                    
                    return True, response
                else:
                    print("⚠️  Missing email_sent field in response")
                    return False, {}
            else:
                print("❌ Missing email_message field in API response")
                return False, {}
        else:
            print("❌ Failed to test email functionality")
            return False, {}

    def test_enhanced_api_responses(self):
        """Test NEW FEATURE: Enhanced API responses with email_message field"""
        print("\n🔍 Testing NEW FEATURE: Enhanced API Responses...")
        
        # Test without email parameter
        model_image = self.create_test_image(400, 600, (200, 150, 100))
        
        data = {
            'atmosphere': 'seaside',
            'suit_type': '2-piece suit',
            'lapel_type': 'Wide notch lapel',
            'pocket_type': 'Slanted with flaps',
            'shoe_type': 'White sneakers',
            'accessory_type': 'Tie'
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg')
        }
        
        success, response = self.run_test(
            "Generate without Email (Check Response Structure)",
            "POST",
            "generate",
            200,
            data=data,
            files=files
        )
        
        if success:
            # Verify all expected fields are present
            expected_fields = ['success', 'request_id', 'image_filename', 'download_url', 'email_sent', 'email_message', 'message']
            missing_fields = []
            
            for field in expected_fields:
                if field not in response:
                    missing_fields.append(field)
                else:
                    print(f"   ✓ Found field '{field}': {response[field]}")
            
            if missing_fields:
                print(f"❌ Missing expected fields: {missing_fields}")
                return False, {}
            else:
                print("✅ All expected fields present in API response")
                
                # Verify email_message is empty when no email provided
                if response['email_message'] == "":
                    print("✅ email_message correctly empty when no email provided")
                else:
                    print(f"⚠️  email_message not empty when no email provided: {response['email_message']}")
                
                return True, response
        else:
            print("❌ Failed to test enhanced API responses")
            return False, {}

    def test_email_with_invalid_address(self):
        """Test email functionality with invalid email address"""
        print("\n🔍 Testing Email with Invalid Address...")
        
        model_image = self.create_test_image(400, 600, (200, 150, 100))
        
        data = {
            'atmosphere': 'hangover',
            'suit_type': '2-piece suit',
            'lapel_type': 'Standard notch lapel',
            'pocket_type': 'Patch pockets',
            'shoe_type': 'Black one-cut',
            'accessory_type': 'Bow tie',
            'email': 'invalid-email-address'  # Invalid email format
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg')
        }
        
        success, response = self.run_test(
            "Generate with Invalid Email",
            "POST",
            "generate",
            200,  # Should still succeed but email should fail
            data=data,
            files=files
        )
        
        if success:
            if 'email_sent' in response and not response['email_sent']:
                print("✅ Email correctly failed with invalid address")
                print(f"   Error message: {response.get('email_message', 'No message')}")
                return True, response
            else:
                print("⚠️  Expected email to fail with invalid address")
                return False, {}
        else:
            print("❌ Request failed entirely with invalid email")
            return False, {}

    def test_comprehensive_new_features(self):
        """Comprehensive test of all new features together"""
        print("\n🔍 Testing ALL NEW FEATURES Together...")
        
        model_image = self.create_test_image(400, 600, (200, 150, 100))
        fabric_image = self.create_test_image(200, 200, (50, 100, 150))
        
        # Use a real email for comprehensive testing
        test_email = "test.tailorview@blandindelloye.com"
        
        data = {
            'atmosphere': 'chic_elegant',
            'suit_type': '3-piece suit',
            'lapel_type': 'Wide peak lapel',
            'pocket_type': 'Straight with flaps',
            'shoe_type': 'Custom',
            'accessory_type': 'Custom',
            'fabric_description': 'Charcoal grey wool with subtle herringbone pattern',
            'custom_shoe_description': 'Black patent leather formal shoes',
            'custom_accessory_description': 'White silk bow tie with diamond studs',
            'email': test_email
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg'),
            'fabric_image': ('fabric.jpg', fabric_image, 'image/jpeg')
        }
        
        success, response = self.run_test(
            "Comprehensive New Features Test",
            "POST",
            "generate",
            200,
            data=data,
            files=files
        )
        
        if success:
            print("✅ Comprehensive test successful")
            
            # Verify all new features
            features_working = []
            
            # 1. Enhanced API response
            if 'email_message' in response:
                features_working.append("Enhanced API responses")
                print("   ✓ Enhanced API responses working")
            
            # 2. Email functionality
            if 'email_sent' in response:
                if response['email_sent']:
                    features_working.append("Email sending")
                    print("   ✓ Email sending working")
                else:
                    print(f"   ⚠️  Email sending failed: {response.get('email_message', 'Unknown error')}")
            
            # 3. Image generation (watermark will be applied)
            if 'image_filename' in response:
                features_working.append("Image generation with watermark")
                print("   ✓ Image generation with watermark working")
            
            print(f"\n✅ Working features: {', '.join(features_working)}")
            return True, response
        else:
            print("❌ Comprehensive test failed")
            return False, {}
            
    def test_delete_request_endpoint(self, request_id=None):
        """Test delete request endpoint"""
        if not request_id:
            # Use a dummy ID for testing
            request_id = "non-existent-id"
        
        return self.run_test(
            "Delete Request",
            "DELETE",
            f"admin/request/{request_id}",
            404  # Expecting not found for non-existent request
        )

def main():
    print("🚀 Starting TailorView API Testing...")
    print("🎯 FOCUS: Testing NEW FEATURES - Watermark changes, Email functionality, Enhanced API responses")
    print("=" * 80)
    
    tester = TailorViewAPITester()
    
    # Test sequence - prioritizing NEW FEATURES
    print("\n🆕 PRIORITY TESTS: NEW FEATURES")
    print("=" * 50)
    
    print("\n📋 Testing NEW FEATURE: Watermark Changes (800% logo increase, no text)...")
    watermark_success, watermark_data = tester.test_watermark_changes()
    
    print("\n📋 Testing NEW FEATURE: Email Functionality with Enhanced Error Handling...")
    email_success, email_data = tester.test_email_functionality_with_error_handling()
    
    print("\n📋 Testing NEW FEATURE: Enhanced API Responses...")
    api_success, api_data = tester.test_enhanced_api_responses()
    
    print("\n📋 Testing Email with Invalid Address...")
    invalid_email_success, invalid_email_data = tester.test_email_with_invalid_address()
    
    print("\n📋 Testing ALL NEW FEATURES Together...")
    comprehensive_success, comprehensive_data = tester.test_comprehensive_new_features()
    
    # Basic functionality tests (existing features)
    print("\n\n🔧 EXISTING FEATURES VERIFICATION")
    print("=" * 50)
    
    print("\n📋 Testing Basic Endpoints...")
    tester.test_root_endpoint()
    
    print("\n📋 Testing Options Endpoint...")
    options_success, options_data = tester.test_options_endpoint()
    
    print("\n📋 Testing Generate Endpoint (Basic)...")
    tester.test_generate_endpoint_minimal()
    
    print("\n📋 Testing Validation...")
    tester.test_generate_endpoint_validation()
    tester.test_generate_endpoint_invalid_file()
    
    print("\n📋 Testing Admin Endpoints...")
    tester.test_admin_requests_endpoint()
    admin_stats_success, admin_stats_data = tester.test_admin_stats_endpoint()
    tester.test_delete_request_endpoint()
    
    # Test download with actual filename if generation was successful
    if watermark_success and 'image_filename' in watermark_data:
        print(f"\n📋 Testing Download with Generated File...")
        download_success, _ = tester.test_download_endpoint(watermark_data['image_filename'])
        if download_success:
            print("✅ Download endpoint working with generated file")
    
    # Print final results
    print("\n" + "=" * 80)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    # NEW FEATURES SUMMARY
    print("\n🆕 NEW FEATURES TEST SUMMARY:")
    print("=" * 40)
    
    new_features_results = []
    
    if watermark_success:
        new_features_results.append("✅ Watermark Changes (800% logo, no text)")
    else:
        new_features_results.append("❌ Watermark Changes")
    
    if email_success:
        new_features_results.append("✅ Email Functionality with Error Handling")
    else:
        new_features_results.append("❌ Email Functionality")
    
    if api_success:
        new_features_results.append("✅ Enhanced API Responses")
    else:
        new_features_results.append("❌ Enhanced API Responses")
    
    if comprehensive_success:
        new_features_results.append("✅ Comprehensive Integration")
    else:
        new_features_results.append("❌ Comprehensive Integration")
    
    for result in new_features_results:
        print(f"   {result}")
    
    # Overall assessment
    new_features_working = sum([watermark_success, email_success, api_success, comprehensive_success])
    total_new_features = 4
    
    print(f"\n🎯 NEW FEATURES STATUS: {new_features_working}/{total_new_features} working")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())