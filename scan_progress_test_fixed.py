import requests
import unittest
import json
import uuid
import time

class ScanProgressEndpointTest(unittest.TestCase):
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
        """Register a user and login to get token"""
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
        """Create a brand for testing"""
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
        print("✅ Brand created successfully")
        
    def test_03_start_scan_and_check_progress(self):
        """Start a scan and check if progress endpoint works"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Start a scan
        scan_data = {
            "brand_id": self.__class__.brand_id,
            "scan_type": "quick"
        }
        
        scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(scan_response.status_code, 200)
        scan_result = scan_response.json()
        self.assertIn("scan_id", scan_result)
        
        scan_id = scan_result["scan_id"]
        print(f"Started scan with ID: {scan_id}")
        
        # Check progress endpoint
        progress_response = requests.get(f"{self.base_url}/api/scans/{scan_id}/progress", headers=headers)
        self.assertEqual(progress_response.status_code, 200)
        progress_data = progress_response.json()
        print(f"Initial progress data: {json.dumps(progress_data, indent=2)}")
        
        # Verify progress data has expected fields
        self.assertIn("status", progress_data)
        self.assertIn("progress", progress_data)
        self.assertIn("total_queries", progress_data)
        
        # Check progress a few times to see if it updates
        initial_progress = progress_data["progress"]
        progress_updated = False
        
        for i in range(5):
            time.sleep(2)
            progress_response = requests.get(f"{self.base_url}/api/scans/{scan_id}/progress", headers=headers)
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                print(f"Progress check {i+1}: {progress_data['progress']}/{progress_data['total_queries']} ({progress_data['status']})")
                
                if progress_data["progress"] > initial_progress or progress_data["status"] == "completed":
                    progress_updated = True
                    break
        
        # Verify progress was updated
        self.assertTrue(progress_updated, "Progress should update during scan execution")
        
        # Wait for scan to complete
        max_wait = 60  # seconds
        start_time = time.time()
        scan_completed = False
        
        while time.time() - start_time < max_wait:
            progress_response = requests.get(f"{self.base_url}/api/scans/{scan_id}/progress", headers=headers)
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                if progress_data["status"] == "completed":
                    scan_completed = True
                    print(f"Scan completed in {time.time() - start_time:.2f} seconds")
                    break
            time.sleep(2)
        
        # Final progress check
        progress_response = requests.get(f"{self.base_url}/api/scans/{scan_id}/progress", headers=headers)
        self.assertEqual(progress_response.status_code, 200)
        progress_data = progress_response.json()
        print(f"Final progress data: {json.dumps(progress_data, indent=2)}")
        
        # Check scan results
        scan_results_response = requests.get(f"{self.base_url}/api/scans/{self.__class__.brand_id}", headers=headers)
        self.assertEqual(scan_results_response.status_code, 200)
        scan_results_data = scan_results_response.json()
        
        # Verify scan results contain expected data
        self.assertIn("scans", scan_results_data)
        self.assertTrue(len(scan_results_data["scans"]) > 0)
        
        print("✅ Scan progress endpoint test passed")

if __name__ == "__main__":
    unittest.main()