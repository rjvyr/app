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
    
    def test_01_brand_filtering_api_structure(self):
        """Test brand filtering API structure"""
        if not hasattr(self, 'token'):
            self.skipTest("Login failed, skipping this test")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # List of endpoints to test
        endpoints = [
            "/api/dashboard/real",
            "/api/competitors/real",
            "/api/queries/real",
            "/api/recommendations/real",
            "/api/source-domains",
            "/api/source-articles"
        ]
        
        # Test each endpoint with a dummy brand ID
        dummy_brand_id = str(uuid.uuid4())
        
        for endpoint in endpoints:
            # Test endpoint with brand filter
            response = requests.get(f"{self.base_url}{endpoint}?brand_id={dummy_brand_id}", headers=headers)
            
            # We expect either a 200 with empty data or a 404
            if response.status_code == 200:
                data = response.json()
                
                # Verify that the endpoint accepts the brand_id parameter
                if endpoint == "/api/dashboard/real":
                    self.assertIn("total_queries", data)
                elif endpoint == "/api/competitors/real":
                    self.assertIn("competitors", data)
                elif endpoint == "/api/queries/real":
                    self.assertIn("queries", data)
                elif endpoint == "/api/recommendations/real":
                    self.assertIn("recommendations", data)
                elif endpoint == "/api/source-domains":
                    self.assertIn("domains", data)
                elif endpoint == "/api/source-articles":
                    self.assertIn("articles", data)
                
                print(f"✅ Brand filtering API structure test passed for {endpoint}")
            elif response.status_code == 404:
                # 404 is acceptable for a dummy brand ID
                print(f"✅ Brand filtering API structure test passed for {endpoint} (404 for dummy brand)")
            else:
                self.fail(f"Unexpected response code {response.status_code} for {endpoint}")
        
        print("✅ Brand filtering API structure test passed for all endpoints")

if __name__ == "__main__":
    # Create a test suite with our tests
    suite = unittest.TestSuite()
    suite.addTest(AIBrandVisibilityAPITest('test_01_brand_filtering_api_structure'))
    
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