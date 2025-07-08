import requests
import unittest
import json
import uuid
from datetime import datetime
import time

class AIBrandVisibilityAPITest(unittest.TestCase):
    def setUp(self):
        # Get the backend URL from the frontend .env file
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.strip().split('=')[1].strip('"\'')
                    break
        
        print(f"Using backend URL: {self.base_url}")
        
        # Login with existing credentials
        self.login_with_existing_user()
        
    def login_with_existing_user(self):
        """Login with an existing user account"""
        # Try a few common test accounts
        test_accounts = [
            {"email": "admin@futureseo.io", "password": "admin123"},
            {"email": "test@example.com", "password": "test123"},
            {"email": "demo@futureseo.io", "password": "demo123"}
        ]
        
        for account in test_accounts:
            login_data = {
                "email": account["email"],
                "password": account["password"]
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                print(f"Successfully logged in as {account['email']}")
                return
        
        # If no existing account works, create a new one
        self.create_new_test_user()
    
    def create_new_test_user(self):
        """Create a new test user if login fails"""
        self.user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        self.user_password = "Test@123456"
        
        user_data = {
            "email": self.user_email,
            "password": self.user_password,
            "full_name": "Test User",
            "company": "Test Company",
            "website": "https://example.com"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        if response.status_code == 200:
            # Login with new user
            login_data = {
                "email": self.user_email,
                "password": self.user_password
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                print(f"Created and logged in as new user {self.user_email}")
                return
        
        # If all else fails, skip tests
        self.skipTest("Could not login or create a user")
    
    def test_01_scan_progress_endpoint(self):
        """Test the scan progress endpoint structure"""
        if not hasattr(self, 'token'):
            self.skipTest("Login failed, skipping this test")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create a dummy scan ID to test the endpoint structure
        # This will likely return a 404, but we can check the error structure
        dummy_scan_id = str(uuid.uuid4())
        
        response = requests.get(f"{self.base_url}/api/scans/{dummy_scan_id}/progress", headers=headers)
        print(f"Scan progress response: {response.status_code}")
        
        # If we get a 404, that's expected for a dummy scan ID
        if response.status_code == 404:
            print("Scan not found (expected for dummy scan ID)")
            
            # Check if the error message is properly formatted
            error_data = response.json()
            self.assertIn("detail", error_data)
            self.assertEqual(error_data["detail"], "Scan not found")
            
            print("✅ Scan progress endpoint error handling test passed")
        elif response.status_code == 200:
            # If we somehow got a 200 response, verify the structure
            progress_data = response.json()
            
            # Verify progress data structure
            self.assertIn("scan_id", progress_data)
            self.assertIn("status", progress_data)
            self.assertIn("progress", progress_data)
            self.assertIn("total_queries", progress_data)
            
            print("✅ Scan progress endpoint structure test passed")
            print(f"Progress data: {json.dumps(progress_data, indent=2)}")
        else:
            self.fail(f"Unexpected response code: {response.status_code}")
    
    def test_02_weekly_scan_limit_error(self):
        """Test weekly scan limit error message structure"""
        if not hasattr(self, 'token'):
            self.skipTest("Login failed, skipping this test")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get existing brands
        brands_response = requests.get(f"{self.base_url}/api/brands", headers=headers)
        if brands_response.status_code != 200 or "brands" not in brands_response.json() or not brands_response.json()["brands"]:
            self.skipTest("No brands available for testing")
        
        # Get the first brand ID
        brand_id = brands_response.json()["brands"][0]["_id"]
        
        # Try to run a scan
        scan_data = {
            "brand_id": brand_id,
            "scan_type": "quick"
        }
        
        scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        print(f"Scan response: {scan_response.status_code}")
        
        # If we get a 429, that means the weekly scan limit is enforced
        if scan_response.status_code == 429:
            error_data = scan_response.json()
            self.assertIn("detail", error_data)
            error_message = error_data["detail"]
            
            # Verify error message structure
            self.assertIn("Next scan available on", error_message)
            self.assertIn("Monday", error_message)
            self.assertIn("11:00 AM PST", error_message)
            
            print("✅ Weekly scan limit error message test passed")
            print(f"Error message: {error_message}")
        elif scan_response.status_code == 200:
            # If the scan succeeded, try another one immediately
            scan_data_2 = {
                "brand_id": brand_id,
                "scan_type": "quick"
            }
            
            scan_response_2 = requests.post(f"{self.base_url}/api/scans", json=scan_data_2, headers=headers)
            
            # The second scan should fail with 429
            if scan_response_2.status_code == 429:
                error_data = scan_response_2.json()
                self.assertIn("detail", error_data)
                error_message = error_data["detail"]
                
                # Verify error message structure
                self.assertIn("Next scan available on", error_message)
                self.assertIn("Monday", error_message)
                self.assertIn("11:00 AM PST", error_message)
                
                print("✅ Weekly scan limit error message test passed")
                print(f"Error message: {error_message}")
            else:
                self.fail(f"Second scan should have failed with 429, got {scan_response_2.status_code}")
        else:
            self.fail(f"Unexpected response code: {scan_response.status_code}")

if __name__ == "__main__":
    # Create a test suite with our tests
    suite = unittest.TestSuite()
    suite.addTest(AIBrandVisibilityAPITest('test_01_scan_progress_endpoint'))
    suite.addTest(AIBrandVisibilityAPITest('test_02_weekly_scan_limit_error'))
    
    # Run the tests with a text test runner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    print(f"Total tests: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    # Print detailed results
    if result.failures:
        print("\n=== FAILURES ===")
        for test, error in result.failures:
            print(f"\n{test}")
            print(error)
    
    if result.errors:
        print("\n=== ERRORS ===")
        for test, error in result.errors:
            print(f"\n{test}")
            print(error)
    
    if result.skipped:
        print("\n=== SKIPPED ===")
        for test, reason in result.skipped:
            print(f"\n{test}")
            print(reason)