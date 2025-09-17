#!/usr/bin/env python3
"""
URGENT: Diagnose image generation failure - user reports generation crashes.
Focus on authentication system and image generation with new atmosphere options.
"""

import requests
import sys
import os
import io
import base64
from datetime import datetime
from PIL import Image
import json

class UrgentTailorViewTester:
    def __init__(self, base_url="https://outfit-preview-43.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.admin_token = None
        self.test_user_data = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, auth_token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        # Add authorization header if token provided
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
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
            elif method == 'PUT':
                headers['Content-Type'] = 'application/json'
                response = requests.put(url, json=data, headers=headers, timeout=30)
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

    def test_admin_login(self):
        """Test admin login with default admin credentials"""
        print("\n🔍 URGENT: Testing Admin Login...")
        
        admin_login_data = {
            "email": "charles@blandindelloye.com",
            "password": "114956Xp"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=admin_login_data
        )
        
        if success:
            if 'access_token' in response and 'user' in response:
                user_data = response['user']
                if user_data.get('role') == 'admin':
                    print("✅ Admin login successful")
                    self.admin_token = response['access_token']
                    print(f"   Admin Email: {user_data.get('email', 'N/A')}")
                    print(f"   Admin Role: {user_data.get('role', 'N/A')}")
                    print(f"   Admin Image Limit: {user_data.get('images_limit_total', 'N/A')}")
                    return True, response
                else:
                    print(f"❌ User logged in but role is '{user_data.get('role')}', not 'admin'")
                    return False, {}
            else:
                print("❌ Admin login response missing required fields")
                return False, {}
        else:
            print("❌ Admin login failed")
            return False, {}

    def test_jwt_token_validation(self):
        """Test JWT token validation"""
        print("\n🔍 URGENT: Testing JWT Token Validation...")
        
        if not self.admin_token:
            print("⚠️  No admin token available, logging in first...")
            admin_success, admin_response = self.test_admin_login()
            if not admin_success:
                return False, {}
        
        success, response = self.run_test(
            "Get Current User with JWT Token",
            "GET",
            "auth/me",
            200,
            auth_token=self.admin_token
        )
        
        if success:
            print("✅ JWT token validation working")
            print(f"   User: {response.get('nom', 'N/A')} ({response.get('email', 'N/A')})")
            print(f"   Role: {response.get('role', 'N/A')}")
            return True, response
        else:
            print("❌ JWT token validation failed")
            return False, {}

    def test_generate_without_auth(self):
        """Test that generate endpoint fails without authentication (401 error)"""
        print("\n🔍 URGENT: Testing Generate Without Authentication (Should get 401)...")
        
        # Create test image
        model_image = self.create_test_image(400, 600, (200, 150, 100))
        
        data = {
            'atmosphere': 'champetre',
            'suit_type': 'Costume 2 pièces',
            'lapel_type': 'Revers cran droit standard',
            'pocket_type': 'En biais, sans rabat',
            'shoe_type': 'Mocassins noirs',
            'accessory_type': 'Nœud papillon'
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg')
        }
        
        success, response = self.run_test(
            "Generate Without Authentication",
            "POST",
            "generate",
            401,  # Expecting unauthorized
            data=data,
            files=files
        )
        
        if success:
            print("✅ Generate endpoint correctly requires authentication (401 error)")
            print("   This confirms the authentication requirement is working")
            return True, response
        else:
            print("❌ Generate endpoint should require authentication")
            return False, {}

    def test_generate_with_admin_auth(self):
        """Test image generation with admin authentication"""
        print("\n🔍 URGENT: Testing Image Generation with Admin Authentication...")
        
        if not self.admin_token:
            print("⚠️  No admin token available, logging in first...")
            admin_success, admin_response = self.test_admin_login()
            if not admin_success:
                return False, {}
        
        # Create test image
        model_image = self.create_test_image(400, 600, (200, 150, 100))
        
        data = {
            'atmosphere': 'champetre',
            'suit_type': 'Costume 2 pièces',
            'lapel_type': 'Revers cran droit standard',
            'pocket_type': 'En biais, sans rabat',
            'shoe_type': 'Mocassins noirs',
            'accessory_type': 'Nœud papillon',
            'fabric_description': 'Laine bleu marine de qualité premium'
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg')
        }
        
        success, response = self.run_test(
            "Generate with Admin Authentication",
            "POST",
            "generate",
            200,
            data=data,
            files=files,
            auth_token=self.admin_token
        )
        
        if success:
            print("✅ Image generation working with admin authentication")
            if 'user_credits' in response:
                credits = response['user_credits']
                print(f"   Credits Used: {credits.get('used', 'N/A')}")
                print(f"   Credits Limit: {credits.get('limit', 'N/A')}")
                print(f"   Credits Remaining: {credits.get('remaining', 'N/A')}")
            if 'image_filename' in response:
                print(f"   Generated Image: {response['image_filename']}")
            return True, response
        else:
            print("❌ Image generation failed with admin authentication")
            return False, {}

    def test_new_atmosphere_options(self):
        """Test NEW atmosphere options: rue_paris and rue_new_york"""
        print("\n🔍 URGENT: Testing NEW Atmosphere Options (rue_paris, rue_new_york)...")
        
        if not self.admin_token:
            print("⚠️  No admin token available, logging in first...")
            admin_success, admin_response = self.test_admin_login()
            if not admin_success:
                return False, {}
        
        # Test rue_paris atmosphere
        print("\n📋 1. Testing rue_paris atmosphere...")
        model_image1 = self.create_test_image(400, 600, (200, 150, 100))
        
        data_paris = {
            'atmosphere': 'rue_paris',  # NEW atmosphere option
            'suit_type': 'Costume 3 pièces',
            'lapel_type': 'Revers cran aigu standard',
            'pocket_type': 'En biais avec rabat',
            'shoe_type': 'Richelieu noires',
            'accessory_type': 'Cravate',
            'fabric_description': 'Costume gris anthracite avec fines rayures'
        }
        
        files1 = {
            'model_image': ('model.jpg', model_image1, 'image/jpeg')
        }
        
        success_paris, response_paris = self.run_test(
            "Generate with rue_paris atmosphere",
            "POST",
            "generate",
            200,
            data=data_paris,
            files=files1,
            auth_token=self.admin_token
        )
        
        if success_paris:
            print("✅ rue_paris atmosphere working")
        else:
            print("❌ rue_paris atmosphere failed")
        
        # Test rue_new_york atmosphere
        print("\n📋 2. Testing rue_new_york atmosphere...")
        model_image2 = self.create_test_image(400, 600, (200, 150, 100))
        
        data_ny = {
            'atmosphere': 'rue_new_york',  # NEW atmosphere option
            'suit_type': 'Costume 2 pièces',
            'lapel_type': 'Veste croisée cran aigu standard',
            'pocket_type': 'Droites avec rabat',
            'shoe_type': 'Richelieu marrons',
            'accessory_type': 'Nœud papillon',
            'fabric_description': 'Costume bleu marine avec texture subtile'
        }
        
        files2 = {
            'model_image': ('model.jpg', model_image2, 'image/jpeg')
        }
        
        success_ny, response_ny = self.run_test(
            "Generate with rue_new_york atmosphere",
            "POST",
            "generate",
            200,
            data=data_ny,
            files=files2,
            auth_token=self.admin_token
        )
        
        if success_ny:
            print("✅ rue_new_york atmosphere working")
        else:
            print("❌ rue_new_york atmosphere failed")
        
        # Summary
        both_working = success_paris and success_ny
        if both_working:
            print("\n✅ Both new atmosphere options working correctly")
            return True, {'paris': response_paris, 'new_york': response_ny}
        else:
            print("\n❌ One or both new atmosphere options failed")
            return False, {}

    def test_options_endpoint_new_atmospheres(self):
        """Test that options endpoint includes new atmosphere options"""
        print("\n🔍 URGENT: Testing Options Endpoint for New Atmospheres...")
        
        success, response = self.run_test(
            "Get Options (Check New Atmospheres)",
            "GET",
            "options",
            200
        )
        
        if success:
            atmospheres = response.get('atmospheres', [])
            
            # Check for new atmosphere options
            atmosphere_values = []
            if isinstance(atmospheres, list):
                for atm in atmospheres:
                    if isinstance(atm, dict):
                        atmosphere_values.append(atm.get('value', ''))
                    else:
                        atmosphere_values.append(str(atm))
            
            print(f"   Available atmospheres: {atmosphere_values}")
            
            # Check for new options
            has_rue_paris = 'rue_paris' in atmosphere_values
            has_rue_new_york = 'rue_new_york' in atmosphere_values
            
            if has_rue_paris:
                print("✅ rue_paris atmosphere option found")
            else:
                print("❌ rue_paris atmosphere option missing")
            
            if has_rue_new_york:
                print("✅ rue_new_york atmosphere option found")
            else:
                print("❌ rue_new_york atmosphere option missing")
            
            if has_rue_paris and has_rue_new_york:
                print("✅ Both new atmosphere options available in options endpoint")
                return True, response
            else:
                print("❌ Missing new atmosphere options in options endpoint")
                return False, {}
        else:
            print("❌ Failed to get options")
            return False, {}

    def test_full_generation_workflow(self):
        """Test complete generation workflow as admin user"""
        print("\n🔍 URGENT: Testing Full Generation Workflow...")
        
        # Step 1: Admin Login
        print("\n📋 1. Admin Login...")
        if not self.admin_token:
            admin_success, admin_response = self.test_admin_login()
            if not admin_success:
                print("❌ Admin login failed - cannot proceed with workflow")
                return False, {}
        
        # Step 2: Get Options
        print("\n📋 2. Get Available Options...")
        options_success, options_data = self.test_options_endpoint_new_atmospheres()
        if not options_success:
            print("❌ Options endpoint failed - cannot proceed")
            return False, {}
        
        # Step 3: Upload Model Image and Generate
        print("\n📋 3. Upload Model Image and Generate...")
        model_image = self.create_test_image(400, 600, (200, 150, 100))
        
        # Use one of the new atmosphere options
        data = {
            'atmosphere': 'rue_paris',  # NEW atmosphere
            'suit_type': 'Costume 3 pièces',
            'lapel_type': 'Revers cran droit standard',
            'pocket_type': 'En biais, sans rabat',
            'shoe_type': 'Mocassins noirs',
            'accessory_type': 'Nœud papillon',
            'fabric_description': 'Costume charbon avec motif discret',
            'email': 'charles@blandindelloye.com'  # Test email functionality
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg')
        }
        
        success, response = self.run_test(
            "Full Generation Workflow",
            "POST",
            "generate",
            200,
            data=data,
            files=files,
            auth_token=self.admin_token
        )
        
        if success:
            print("✅ Full generation workflow successful")
            
            # Check all expected response fields
            expected_fields = ['success', 'request_id', 'image_filename', 'download_url', 'user_credits']
            missing_fields = [field for field in expected_fields if field not in response]
            
            if missing_fields:
                print(f"⚠️  Missing response fields: {missing_fields}")
            else:
                print("✅ All expected response fields present")
            
            # Check user credits
            if 'user_credits' in response:
                credits = response['user_credits']
                print(f"   Credits after generation: {credits}")
            
            # Check if image was generated
            if 'image_filename' in response:
                print(f"   Generated image: {response['image_filename']}")
                
                # Try to download the image
                download_success, download_data = self.run_test(
                    "Download Generated Image",
                    "GET",
                    f"download/{response['image_filename']}",
                    200
                )
                
                if download_success:
                    print("✅ Generated image is downloadable")
                else:
                    print("❌ Generated image download failed")
            
            return True, response
        else:
            print("❌ Full generation workflow failed")
            return False, {}

    def test_error_diagnostics(self):
        """Diagnose specific error conditions"""
        print("\n🔍 URGENT: Error Diagnostics...")
        
        # Test 1: Invalid token
        print("\n📋 1. Testing with Invalid Token...")
        model_image = self.create_test_image(400, 600, (200, 150, 100))
        
        data = {
            'atmosphere': 'champetre',
            'suit_type': 'Costume 2 pièces',
            'lapel_type': 'Revers cran droit standard',
            'pocket_type': 'En biais, sans rabat',
            'shoe_type': 'Mocassins noirs',
            'accessory_type': 'Nœud papillon'
        }
        
        files = {
            'model_image': ('model.jpg', model_image, 'image/jpeg')
        }
        
        invalid_token_success, invalid_token_response = self.run_test(
            "Generate with Invalid Token",
            "POST",
            "generate",
            401,  # Expecting unauthorized
            data=data,
            files=files,
            auth_token="invalid_token_12345"
        )
        
        if invalid_token_success:
            print("✅ Invalid token correctly rejected (401)")
        else:
            print("❌ Invalid token handling issue")
        
        # Test 2: Missing required fields
        print("\n📋 2. Testing with Missing Required Fields...")
        incomplete_data = {
            'atmosphere': 'champetre'
            # Missing other required fields
        }
        
        missing_fields_success, missing_fields_response = self.run_test(
            "Generate with Missing Fields",
            "POST",
            "generate",
            422,  # Expecting validation error
            data=incomplete_data,
            files=files,
            auth_token=self.admin_token if self.admin_token else None
        )
        
        if missing_fields_success:
            print("✅ Missing fields correctly rejected (422)")
        else:
            print("❌ Missing fields validation issue")
        
        return True, {
            'invalid_token': invalid_token_response,
            'missing_fields': missing_fields_response
        }

def main():
    """Run urgent diagnostic tests"""
    print("=" * 80)
    print("🚨 URGENT: Image Generation Failure Diagnosis")
    print("=" * 80)
    print("User reports: Image generation crashes with 401 Unauthorized errors")
    print("Focus: Authentication system and new atmosphere options")
    print("=" * 80)
    
    tester = UrgentTailorViewTester()
    
    # Critical tests in order of priority
    tests = [
        ("Admin Login Test", tester.test_admin_login),
        ("JWT Token Validation", tester.test_jwt_token_validation),
        ("Generate Without Auth (401 Check)", tester.test_generate_without_auth),
        ("Options Endpoint (New Atmospheres)", tester.test_options_endpoint_new_atmospheres),
        ("Generate With Admin Auth", tester.test_generate_with_admin_auth),
        ("New Atmosphere Options Test", tester.test_new_atmosphere_options),
        ("Full Generation Workflow", tester.test_full_generation_workflow),
        ("Error Diagnostics", tester.test_error_diagnostics)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🔍 {test_name}")
        print(f"{'='*60}")
        
        try:
            success, data = test_func()
            results.append((test_name, success, data))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False, str(e)))
    
    # Final Summary
    print(f"\n{'='*80}")
    print("🎯 URGENT DIAGNOSTIC SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"📊 Tests Passed: {passed}/{total}")
    print(f"📊 Success Rate: {(passed/total)*100:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for test_name, success, data in results:
        status = "✅" if success else "❌"
        print(f"   {status} {test_name}")
    
    # Critical Issues Analysis
    print(f"\n🔍 CRITICAL ISSUES ANALYSIS:")
    
    auth_issues = []
    generation_issues = []
    
    for test_name, success, data in results:
        if not success:
            if "Auth" in test_name or "Login" in test_name or "Token" in test_name:
                auth_issues.append(test_name)
            elif "Generate" in test_name or "Atmosphere" in test_name:
                generation_issues.append(test_name)
    
    if auth_issues:
        print(f"   🚨 AUTHENTICATION ISSUES: {', '.join(auth_issues)}")
    
    if generation_issues:
        print(f"   🚨 GENERATION ISSUES: {', '.join(generation_issues)}")
    
    if not auth_issues and not generation_issues:
        print("   ✅ No critical issues found - system appears to be working")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if auth_issues:
        print("   1. Check JWT token generation and validation")
        print("   2. Verify admin credentials are correct")
        print("   3. Check authentication middleware configuration")
    
    if generation_issues:
        print("   1. Check Emergent LLM API key configuration")
        print("   2. Verify new atmosphere options are properly configured")
        print("   3. Check image processing pipeline")
    
    if not auth_issues and not generation_issues:
        print("   1. System appears functional - user may need to login properly")
        print("   2. Check frontend authentication token handling")
        print("   3. Verify user is using correct login credentials")
    
    print(f"\n{'='*80}")
    
    return 0 if passed >= total * 0.7 else 1

if __name__ == "__main__":
    sys.exit(main())