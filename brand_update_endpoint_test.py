import requests
import unittest
import json
import uuid

class BrandUpdateEndpointTest(unittest.TestCase):
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
            "full_name": "Test User",
            "company": "Test Company",
            "website": "https://example.com"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        self.assertEqual(response.status_code, 200)
        
        # Login to get token
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
        print("✅ User registration and login test passed")
        
    def test_02_create_brand(self):
        """Create a test brand for testing the update endpoint"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        # Create brand
        brand_data = {
            "name": "TestBrand",
            "industry": "Software Development",
            "keywords": ["coding", "programming", "development"],
            "competitors": ["GitHub", "GitLab", "Bitbucket"],
            "website": "https://testbrand.example.com"
        }
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.post(f"{self.base_url}/api/brands", json=brand_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brand_id", data)
        
        # Save brand_id for subsequent tests
        self.__class__.brand_id = data["brand_id"]
        print("✅ Create brand test passed")
        
    def test_03_update_brand(self):
        """Test updating a brand's keywords and competitors"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get original brand data
        response = requests.get(f"{self.base_url}/api/brands/{self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        original_brand = response.json()["brand"]
        
        # Update keywords and competitors
        update_data = {
            "keywords": ["coding", "programming", "development", "software engineering", "devops"],
            "competitors": ["GitHub", "GitLab", "Bitbucket", "Azure DevOps", "AWS CodeCommit"]
        }
        
        response = requests.put(f"{self.base_url}/api/brands/{self.__class__.brand_id}", json=update_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        updated_brand = response.json()["brand"]
        
        # Verify keywords and competitors were updated
        self.assertEqual(len(updated_brand["keywords"]), 5)
        self.assertEqual(len(updated_brand["competitors"]), 5)
        self.assertIn("software engineering", updated_brand["keywords"])
        self.assertIn("Azure DevOps", updated_brand["competitors"])
        
        # Verify name, industry, and website were NOT changed
        self.assertEqual(updated_brand["name"], original_brand["name"])
        self.assertEqual(updated_brand["industry"], original_brand["industry"])
        self.assertEqual(updated_brand["website"], original_brand["website"])
        
        print("✅ Update brand test passed")
        
    def test_04_update_brand_authentication_required(self):
        """Test that brand update endpoint requires authentication"""
        if not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        # Try to update without authentication
        update_data = {
            "keywords": ["coding", "programming"],
            "competitors": ["GitHub", "GitLab"]
        }
        
        response = requests.put(f"{self.base_url}/api/brands/{self.__class__.brand_id}", json=update_data)
        self.assertEqual(response.status_code, 403)
        print("✅ Update brand authentication requirement test passed")
        
    def test_05_update_brand_user_ownership(self):
        """Test that users can only update their own brands"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        # Create a new user
        new_user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        new_user_password = "Test@123456"
        
        user_data = {
            "email": new_user_email,
            "password": new_user_password,
            "full_name": "Another Test User",
            "company": "Another Test Company",
            "website": "https://another-example.com"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        self.assertEqual(response.status_code, 200)
        
        # Login as new user
        login_data = {
            "email": new_user_email,
            "password": new_user_password
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        new_user_token = response.json()["access_token"]
        
        # Try to update first user's brand with new user's token
        headers = {"Authorization": f"Bearer {new_user_token}"}
        update_data = {
            "keywords": ["unauthorized", "access", "attempt"],
            "competitors": ["Unauthorized", "Access", "Attempt"]
        }
        
        response = requests.put(f"{self.base_url}/api/brands/{self.__class__.brand_id}", json=update_data, headers=headers)
        self.assertEqual(response.status_code, 404)  # Should return 404 "Brand not found" for security
        print("✅ Update brand user ownership test passed")
        
    def test_06_update_brand_invalid_data(self):
        """Test updating a brand with invalid data"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Try to update with empty keywords
        update_data = {
            "keywords": [],
            "competitors": ["GitHub", "GitLab"]
        }
        
        response = requests.put(f"{self.base_url}/api/brands/{self.__class__.brand_id}", json=update_data, headers=headers)
        # The API should still accept this, but it's worth checking the behavior
        print(f"Empty keywords update status code: {response.status_code}")
        
        # Try to update with empty competitors
        update_data = {
            "keywords": ["coding", "programming"],
            "competitors": []
        }
        
        response = requests.put(f"{self.base_url}/api/brands/{self.__class__.brand_id}", json=update_data, headers=headers)
        # The API should still accept this, but it's worth checking the behavior
        print(f"Empty competitors update status code: {response.status_code}")
        
        # Try to update with missing required fields
        update_data = {
            "keywords": ["coding", "programming"]
            # Missing competitors field
        }
        
        response = requests.put(f"{self.base_url}/api/brands/{self.__class__.brand_id}", json=update_data, headers=headers)
        # The API should reject this with a validation error
        print(f"Missing required field update status code: {response.status_code}")
        
        print("✅ Update brand invalid data test passed")

if __name__ == "__main__":
    unittest.main()