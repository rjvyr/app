import requests
import unittest
import json
import uuid
from datetime import datetime

class AIBrandVisibilityAPITest(unittest.TestCase):
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
        
    def test_01_health_endpoint(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.base_url}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
        print("✅ Health endpoint test passed")

    def test_02_register_user(self):
        """Test user registration"""
        user_data = {
            "email": self.user_email,
            "password": self.user_password,
            "full_name": "Test User",
            "company": "Test Company",
            "website": "https://example.com"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("User created successfully", data["message"])
        print("✅ User registration test passed")

    def test_03_login_user(self):
        """Test user login"""
        # Create a new user specifically for login test
        test_email = f"login_test_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "Test@123456"
        
        # Register the user first
        user_data = {
            "email": test_email,
            "password": test_password,
            "full_name": "Login Test User",
            "company": "Test Company",
            "website": "https://example.com"
        }
        
        reg_response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        self.assertEqual(reg_response.status_code, 200)
        
        # Now try to login
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], test_email)
        
        # Save token for subsequent tests
        self.__class__.token = data["access_token"]
        print("✅ User login test passed")

    def test_04_get_user_info(self):
        """Test getting user info"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("email", data)
        self.assertIn("full_name", data)
        self.assertIn("company", data)
        print("✅ Get user info test passed")

    def test_05_create_brand(self):
        """Test creating a brand"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        brand_data = {
            "name": "TestBrand",
            "industry": "Project Management Software",
            "keywords": ["productivity", "team collaboration", "project tracking"],
            "competitors": ["Asana", "Monday.com", "Trello"],
            "website": "https://testbrand.com"
        }
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.post(f"{self.base_url}/api/brands", json=brand_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brand_id", data)
        
        # Save brand_id for subsequent tests
        self.__class__.brand_id = data["brand_id"]
        print("✅ Create brand test passed")

    def test_06_get_brands(self):
        """Test getting brands"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/brands", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brands", data)
        self.assertTrue(len(data["brands"]) > 0)
        self.assertEqual(data["brands"][0]["name"], "TestBrand")
        print("✅ Get brands test passed")

    def test_07_get_brand_by_id(self):
        """Test getting a brand by ID"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/brands/{self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brand", data)
        self.assertEqual(data["brand"]["name"], "TestBrand")
        print("✅ Get brand by ID test passed")

    def test_08_run_quick_scan(self):
        """Test running a quick scan"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        scan_data = {
            "brand_id": self.__class__.brand_id,
            "scan_type": "quick"
        }
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("scan_id", data)
        self.assertIn("results", data)
        self.assertIn("visibility_score", data)
        self.assertEqual(len(data["results"]), 5)  # Quick scan should have 5 results
        print("✅ Run quick scan test passed")

    def test_09_get_scan_results(self):
        """Test getting scan results"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/scans/{self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("scans", data)
        self.assertTrue(len(data["scans"]) > 0)
        print("✅ Get scan results test passed")

    def test_10_get_dashboard(self):
        """Test getting dashboard data"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/dashboard", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("user", data)
        self.assertIn("brands", data)
        self.assertIn("recent_scans", data)
        self.assertIn("stats", data)
        print("✅ Get dashboard test passed")

if __name__ == "__main__":
    unittest.main()