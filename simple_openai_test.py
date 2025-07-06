import requests
import unittest
import json
import uuid
import re
from datetime import datetime
import time

class OpenAIIntegrationTest(unittest.TestCase):
    def setUp(self):
        # Get the backend URL from the frontend .env file
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.strip().split('=')[1].strip('"\'')
                    break
        
        print(f"Using backend URL: {self.base_url}")
        self.token = None
        self.user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        self.user_password = "Test@123456"
        self.brand_id = None
        
    def test_01_register_and_login(self):
        """Register a test user and login to get authentication token"""
        # Register user
        user_data = {
            "email": self.user_email,
            "password": self.user_password,
            "full_name": "OpenAI Test User",
            "company": "Test Company",
            "website": "https://example.com"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        self.assertEqual(response.status_code, 200)
        
        # Login
        login_data = {
            "email": self.user_email,
            "password": self.user_password
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        
        # Save token for subsequent tests
        self.__class__.token = data["access_token"]
        print("✅ User registration and login successful")
        
    def test_02_create_brand(self):
        """Create a test brand for scanning"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        brand_data = {
            "name": "Volopay",  # Using the brand mentioned in the review request
            "industry": "Expense Management Software",
            "keywords": ["expense tracking", "corporate cards", "spend management", "approval workflows", "receipt scanning"],
            "competitors": ["Brex", "Ramp", "Divvy", "Expensify", "Concur"],
            "website": "https://volopay.com"
        }
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.post(f"{self.base_url}/api/brands", json=brand_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brand_id", data)
        
        # Save brand_id for subsequent tests
        self.__class__.brand_id = data["brand_id"]
        print("✅ Brand creation successful")
        
    def test_03_run_scan_with_openai(self):
        """Test running a scan with real OpenAI integration"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        scan_data = {
            "brand_id": self.__class__.brand_id,
            "scan_type": "quick"  # Quick scan to save time
        }
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify scan completed successfully
        self.assertIn("scan_id", data)
        self.assertIn("results", data)
        self.assertIn("visibility_score", data)
        
        # Verify we have results
        self.assertTrue(len(data["results"]) > 0)
        
        # Check for real OpenAI responses (not mock data)
        for result in data["results"]:
            # Verify it's using the right model
            self.assertEqual(result["platform"], "ChatGPT")
            self.assertEqual(result["model"], "gpt-4o-mini")
            
            # Verify response is not a mock response
            response_text = result["response"]
            self.assertTrue(len(response_text) > 100, "Response too short, might be mock data")
            
            # Verify tokens were used (real API call)
            self.assertTrue(result["tokens_used"] > 0)
            
        print("✅ OpenAI integration test successful")

if __name__ == "__main__":
    unittest.main()