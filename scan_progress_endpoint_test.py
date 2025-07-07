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
        
    def test_03_check_scan_progress_endpoint(self):
        """Check if scan progress endpoint exists"""
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
        
        # Check if progress endpoint exists
        progress_response = requests.get(f"{self.base_url}/api/scans/{scan_id}/progress", headers=headers)
        print(f"Progress endpoint status code: {progress_response.status_code}")
        
        # If endpoint doesn't exist, it will return 404
        if progress_response.status_code == 404:
            print("❌ Scan progress endpoint does not exist")
            print("The endpoint /api/scans/{scan_id}/progress is missing in the backend implementation")
        else:
            print(f"Scan progress endpoint returned status code: {progress_response.status_code}")
            if progress_response.status_code == 200:
                progress_data = progress_response.json()
                print(f"Progress data: {json.dumps(progress_data, indent=2)}")
        
        # Check MongoDB directly for scan progress data
        print("\nChecking scan_progress collection in MongoDB...")
        mongo_check_response = requests.get(f"{self.base_url}/api/debug/scan-progress/{scan_id}", headers=headers)
        if mongo_check_response.status_code == 200:
            mongo_data = mongo_check_response.json()
            print(f"MongoDB scan_progress data: {json.dumps(mongo_data, indent=2)}")
        else:
            print(f"MongoDB debug endpoint returned status code: {mongo_check_response.status_code}")
            print("Debug endpoint /api/debug/scan-progress/{scan_id} is not implemented")
            
        # Wait for scan to complete
        print("\nWaiting for scan to complete...")
        time.sleep(10)
        
        # Check scan results
        scan_results_response = requests.get(f"{self.base_url}/api/scans/{self.__class__.brand_id}", headers=headers)
        self.assertEqual(scan_results_response.status_code, 200)
        scan_results_data = scan_results_response.json()
        
        # Verify scan results contain expected data
        self.assertIn("scans", scan_results_data)
        if len(scan_results_data["scans"]) > 0:
            latest_scan = scan_results_data["scans"][0]
            print(f"\nLatest scan data: {json.dumps({k: v for k, v in latest_scan.items() if k != 'results'}, indent=2)}")
            self.assertIn("results", latest_scan)
            print(f"Scan has {len(latest_scan['results'])} results")
        else:
            print("No scan results found")

if __name__ == "__main__":
    unittest.main()