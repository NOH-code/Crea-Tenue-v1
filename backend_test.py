import requests
import sys
import os
import io
from datetime import datetime
from PIL import Image

class TailorViewAPITester:
    def __init__(self, base_url="https://tailorview.preview.emergentagent.com"):
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
    print("=" * 60)
    
    tester = TailorViewAPITester()
    
    # Test sequence
    print("\n📋 Testing Basic Endpoints...")
    tester.test_root_endpoint()
    
    print("\n📋 Testing Options Endpoint...")
    options_success, options_data = tester.test_options_endpoint()
    
    print("\n📋 Testing Generate Endpoint...")
    tester.test_generate_endpoint_minimal()
    
    print("\n📋 Testing Generate Endpoint (Full Multi-Image Parameters)...")
    generate_success, generate_data = tester.test_generate_endpoint_full()
    
    print("\n📋 Testing Validation...")
    tester.test_generate_endpoint_validation()
    tester.test_generate_endpoint_invalid_file()
    
    print("\n📋 Testing Download Endpoint...")
    tester.test_download_endpoint()
    
    print("\n📋 Testing Requests Endpoint...")
    tester.test_requests_endpoint()
    
    print("\n📋 Testing Admin Endpoints...")
    tester.test_admin_requests_endpoint()
    admin_stats_success, admin_stats_data = tester.test_admin_stats_endpoint()
    tester.test_delete_request_endpoint()
    
    # Test download with actual filename if generation was successful
    if generate_success and 'image_filename' in generate_data:
        print(f"\n📋 Testing Download with Generated File...")
        download_success, _ = tester.test_download_endpoint(generate_data['image_filename'])
        if download_success:
            print("✅ Download endpoint working with generated file")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())