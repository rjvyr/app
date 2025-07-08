import requests
import json
import uuid
import time
import unittest

class TestWeeklyScanLimit(unittest.TestCase):
    def setUp(self):
        # Get the backend URL from the frontend .env file
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.strip().split('=')[1].strip('"\'')
                    break
        
        print(f"Using backend URL: {self.base_url}")
        
        # Generate unique email for testing
        self.user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        self.user_password = "Test@123456"
        self.token = None
        self.brand_a_id = None
        self.brand_b_id = None
        
        # Register and login
        self._register_and_login()
        
        # Upgrade to enterprise plan
        self._upgrade_to_enterprise()
        
        # Create two brands
        self._create_brands()
    
    def _register_and_login(self):
        # Register user
        user_data = {
            "email": self.user_email,
            "password": self.user_password,
            "full_name": "Test User",
            "company": "Test Company",
            "website": "https://example.com"
        }
        
        reg_response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        self.assertEqual(reg_response.status_code, 200, "Failed to register user")
        
        # Login
        login_data = {
            "email": self.user_email,
            "password": self.user_password
        }
        
        login_response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(login_response.status_code, 200, "Failed to login")
        
        self.token = login_response.json()["access_token"]
        print(f"Registered and logged in as {self.user_email}")
    
    def _upgrade_to_enterprise(self):
        # Check available plans
        plans_response = requests.get(f"{self.base_url}/api/plans")
        if plans_response.status_code == 200:
            print("Available plans:")
            plans_data = plans_response.json()
            for plan in plans_data.get("plans", []):
                print(f"- {plan.get('id')}: {plan.get('name')} ({plan.get('brands')} brands)")
        
        # Try to upgrade to pro plan instead of enterprise
        headers = {"Authorization": f"Bearer {self.token}"}
        upgrade_response = requests.post(
            f"{self.base_url}/api/admin/upgrade-user?user_email={self.user_email}&new_plan=pro",
            headers=headers
        )
        
        # If admin upgrade fails, we'll proceed anyway and see if we can create multiple brands
        if upgrade_response.status_code != 200:
            print(f"Warning: Failed to upgrade to pro plan (status: {upgrade_response.status_code})")
            print("Proceeding with test anyway...")
        else:
            print("Upgraded to pro plan")
    
    def _create_brands(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create Brand A
        brand_a_data = {
            "name": "Brand A",
            "industry": "Project Management Software",
            "keywords": ["productivity", "team collaboration", "project tracking"],
            "competitors": ["Asana", "Monday.com", "Trello"],
            "website": "https://branda.com"
        }
        
        brand_a_response = requests.post(f"{self.base_url}/api/brands", json=brand_a_data, headers=headers)
        self.assertEqual(brand_a_response.status_code, 200, "Failed to create Brand A")
        self.brand_a_id = brand_a_response.json()["brand_id"]
        
        # Create Brand B
        brand_b_data = {
            "name": "Brand B",
            "industry": "E-commerce Platform",
            "keywords": ["online store", "e-commerce", "shopping cart"],
            "competitors": ["Shopify", "WooCommerce", "BigCommerce"],
            "website": "https://brandb.com"
        }
        
        brand_b_response = requests.post(f"{self.base_url}/api/brands", json=brand_b_data, headers=headers)
        self.assertEqual(brand_b_response.status_code, 200, "Failed to create Brand B")
        self.brand_b_id = brand_b_response.json()["brand_id"]
        
        print(f"Created Brand A (ID: {self.brand_a_id}) and Brand B (ID: {self.brand_b_id})")
    
    def test_weekly_scan_limit_per_brand(self):
        """Test weekly scan limit functionality per brand"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Step 1: Run a scan for Brand A - should succeed
        scan_data_a = {
            "brand_id": self.brand_a_id,
            "scan_type": "quick"
        }
        
        print("Running first scan for Brand A...")
        response_a1 = requests.post(f"{self.base_url}/api/scans", json=scan_data_a, headers=headers)
        self.assertEqual(response_a1.status_code, 200, "First scan for Brand A failed")
        print("✅ First scan for Brand A succeeded")
        
        # Step 2: Run a scan for Brand B - should succeed (not affected by Brand A's scan)
        scan_data_b = {
            "brand_id": self.brand_b_id,
            "scan_type": "quick"
        }
        
        print("Running first scan for Brand B...")
        response_b1 = requests.post(f"{self.base_url}/api/scans", json=scan_data_b, headers=headers)
        self.assertEqual(response_b1.status_code, 200, "First scan for Brand B failed")
        print("✅ First scan for Brand B succeeded")
        
        # Step 3: Try to run a second scan for Brand A - should fail with 429 error
        print("Attempting second scan for Brand A (should fail)...")
        response_a2 = requests.post(f"{self.base_url}/api/scans", json=scan_data_a, headers=headers)
        self.assertEqual(response_a2.status_code, 429, "Second scan for Brand A did not fail as expected")
        
        # Verify error message includes Brand A's name
        error_message_a = response_a2.json()["detail"]
        self.assertIn("Brand A", error_message_a, "Error message does not include Brand A's name")
        self.assertIn("Next scan available on", error_message_a, "Error message does not include next available scan time")
        self.assertIn("Monday", error_message_a, "Error message does not include Monday")
        self.assertIn("11:00 AM PST", error_message_a, "Error message does not include 11:00 AM PST")
        print(f"✅ Second scan for Brand A correctly failed with error: {error_message_a}")
        
        # Step 4: Try to run a second scan for Brand B - should fail with 429 error
        print("Attempting second scan for Brand B (should fail)...")
        response_b2 = requests.post(f"{self.base_url}/api/scans", json=scan_data_b, headers=headers)
        self.assertEqual(response_b2.status_code, 429, "Second scan for Brand B did not fail as expected")
        
        # Verify error message includes Brand B's name
        error_message_b = response_b2.json()["detail"]
        self.assertIn("Brand B", error_message_b, "Error message does not include Brand B's name")
        self.assertIn("Next scan available on", error_message_b, "Error message does not include next available scan time")
        self.assertIn("Monday", error_message_b, "Error message does not include Monday")
        self.assertIn("11:00 AM PST", error_message_b, "Error message does not include 11:00 AM PST")
        print(f"✅ Second scan for Brand B correctly failed with error: {error_message_b}")
        
        print("\n=== Weekly Scan Limit Test Results ===")
        print("✅ Brand A first scan: SUCCESS")
        print("✅ Brand B first scan: SUCCESS")
        print(f"✅ Brand A second scan: FAILED WITH 429 - {error_message_a}")
        print(f"✅ Brand B second scan: FAILED WITH 429 - {error_message_b}")
        print("✅ Weekly scan limit is correctly enforced per brand")
        print("✅ Error messages correctly include brand-specific information")

if __name__ == "__main__":
    unittest.main()