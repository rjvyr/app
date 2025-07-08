import requests
import unittest
import json
import uuid
import time
from datetime import datetime

class ScanProgressTrackingTest(unittest.TestCase):
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
        """Create a test brand"""
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
        print("✅ Brand creation successful")
        
    def test_03_scan_progress_tracking(self):
        """Test scan progress tracking functionality"""
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
        
        # Poll the progress endpoint to track scan progress
        max_attempts = 10
        progress_values = []
        
        for attempt in range(max_attempts):
            progress_response = requests.get(f"{self.base_url}/api/scans/{scan_id}/progress", headers=headers)
            self.assertEqual(progress_response.status_code, 200)
            progress_data = progress_response.json()
            
            print(f"Progress check {attempt+1}: Status={progress_data['status']}, Progress={progress_data['progress']}/{progress_data['total_queries']}")
            progress_values.append(progress_data['progress'])
            
            # If scan is completed or failed, break the loop
            if progress_data['status'] in ['completed', 'failed']:
                break
                
            # Wait before next poll
            time.sleep(2)
        
        # Verify that progress was tracked correctly
        self.assertGreater(len(progress_values), 1, "Progress should have been polled multiple times")
        
        # Check if progress increased over time
        is_progress_increasing = False
        for i in range(1, len(progress_values)):
            if progress_values[i] > progress_values[i-1]:
                is_progress_increasing = True
                break
                
        self.assertTrue(is_progress_increasing, "Progress should increase during scan execution")
        
        # Final progress check
        final_progress_response = requests.get(f"{self.base_url}/api/scans/{scan_id}/progress", headers=headers)
        self.assertEqual(final_progress_response.status_code, 200)
        final_progress_data = final_progress_response.json()
        
        # Verify final status
        self.assertIn(final_progress_data['status'], ['completed', 'failed'], 
                     f"Scan should be completed or failed, but status is {final_progress_data['status']}")
        
        if final_progress_data['status'] == 'completed':
            self.assertEqual(final_progress_data['progress'], final_progress_data['total_queries'],
                           "Progress should equal total queries when scan is completed")
            
        print("✅ Scan progress tracking test passed")
        
    def test_04_openai_integration_with_progress(self):
        """Test OpenAI integration with progress tracking"""
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
        
        # Poll the progress endpoint until completion
        max_attempts = 15
        completed = False
        
        for attempt in range(max_attempts):
            progress_response = requests.get(f"{self.base_url}/api/scans/{scan_id}/progress", headers=headers)
            self.assertEqual(progress_response.status_code, 200)
            progress_data = progress_response.json()
            
            print(f"Progress check {attempt+1}: Status={progress_data['status']}, Progress={progress_data['progress']}/{progress_data['total_queries']}")
            
            if progress_data['status'] == 'completed':
                completed = True
                break
                
            # Wait before next poll
            time.sleep(2)
        
        self.assertTrue(completed, "Scan should complete within the expected time")
        
        # Verify scan results contain OpenAI responses
        scan_results_response = requests.get(f"{self.base_url}/api/scans/{self.__class__.brand_id}", headers=headers)
        self.assertEqual(scan_results_response.status_code, 200)
        scan_results_data = scan_results_response.json()
        
        # Verify scan results contain expected data
        self.assertIn("scans", scan_results_data)
        self.assertTrue(len(scan_results_data["scans"]) > 0)
        
        # Find the scan we just ran
        found_scan = None
        for scan in scan_results_data["scans"]:
            if scan.get("_id") == scan_id:
                found_scan = scan
                break
        
        if not found_scan:
            # Try to find by timestamp (most recent scan)
            found_scan = scan_results_data["scans"][0]
        
        self.assertIsNotNone(found_scan, "Could not find the scan results")
        
        # Check if the scan has results with OpenAI responses
        self.assertIn("results", found_scan)
        self.assertTrue(len(found_scan["results"]) > 0)
        
        # Verify OpenAI integration
        for result in found_scan["results"]:
            self.assertEqual(result["platform"], "ChatGPT")
            self.assertEqual(result["model"], "gpt-4o-mini")
            self.assertIn("response", result)
            self.assertTrue(len(result["response"]) > 100)  # Real responses are typically longer
            self.assertIn("tokens_used", result)
            self.assertTrue(result["tokens_used"] > 0)
            
            # Check for source domains and articles
            self.assertIn("source_domains", result)
            self.assertIn("source_articles", result)
        
        print("✅ OpenAI integration with progress tracking test passed")

if __name__ == "__main__":
    unittest.main()