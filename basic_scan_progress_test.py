import requests
import unittest
import json
import uuid

class BasicScanProgressTest(unittest.TestCase):
    def test_scan_progress_endpoint_exists(self):
        """Test if the scan progress endpoint exists"""
        # Get the backend URL from the frontend .env file
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    base_url = line.strip().split('=')[1].strip('"\'')
                    break
        
        print(f"Using backend URL: {base_url}")
        
        # Register a test user
        user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        user_password = "Test@123456"
        
        user_data = {
            "email": user_email,
            "password": user_password,
            "full_name": "Test User",
            "company": "Test Company",
            "website": "https://example.com"
        }
        
        response = requests.post(f"{base_url}/api/auth/register", json=user_data)
        self.assertEqual(response.status_code, 200)
        print("User registered successfully")
        
        # Login
        login_data = {
            "email": user_email,
            "password": user_password
        }
        
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        token = data["access_token"]
        print("User logged in successfully")
        
        # Create a brand
        brand_data = {
            "name": "TestBrand",
            "industry": "Project Management Software",
            "keywords": ["productivity", "team collaboration", "project tracking"],
            "competitors": ["Asana", "Monday.com", "Trello"],
            "website": "https://testbrand.com"
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{base_url}/api/brands", json=brand_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        brand_id = data["brand_id"]
        print("Brand created successfully")
        
        # Start a scan
        scan_data = {
            "brand_id": brand_id,
            "scan_type": "quick"
        }
        
        scan_response = requests.post(f"{base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(scan_response.status_code, 200)
        scan_result = scan_response.json()
        self.assertIn("scan_id", scan_result)
        
        scan_id = scan_result["scan_id"]
        print(f"Started scan with ID: {scan_id}")
        
        # Check if the progress endpoint exists
        progress_response = requests.get(f"{base_url}/api/scans/{scan_id}/progress", headers=headers)
        print(f"Progress endpoint status code: {progress_response.status_code}")
        
        # Verify the endpoint exists and returns 200 OK
        self.assertEqual(progress_response.status_code, 200, "Scan progress endpoint should return 200 OK")
        print("Scan progress endpoint exists and returns 200 OK")
        
        # Verify the response structure
        progress_data = progress_response.json()
        print(f"Progress data: {json.dumps(progress_data, indent=2)}")
        
        self.assertIn("scan_id", progress_data, "Response should include scan_id")
        self.assertIn("status", progress_data, "Response should include status")
        self.assertIn("progress", progress_data, "Response should include progress")
        self.assertIn("total_queries", progress_data, "Response should include total_queries")
        
        print("✅ Scan progress endpoint test passed")

if __name__ == "__main__":
    unittest.main()