import requests
import unittest
import json
import uuid
from datetime import datetime
import time

class ScanLimitAndProgressTest(unittest.TestCase):
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
        """Register and login a test user"""
        # Register user
        user_data = {
            "email": self.user_email,
            "password": self.user_password,
            "full_name": "Test User",
            "company": "Test Company",
            "website": "https://example.com"
        }
        
        reg_response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        self.assertEqual(reg_response.status_code, 200)
        
        # Login user
        login_data = {
            "email": self.user_email,
            "password": self.user_password
        }
        
        login_response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(login_response.status_code, 200)
        login_data = login_response.json()
        self.assertIn("access_token", login_data)
        
        # Save token for subsequent tests
        self.token = login_data["access_token"]
        print("✅ User registration and login test passed")
        
    def test_02_create_brand_and_test_scan_limit(self):
        """Create a brand and test weekly scan limit"""
        if not self.token:
            self.skipTest("Login test failed, skipping this test")
            
        # Create brand
        brand_data = {
            "name": "WeeklyScanLimitTestBrand",
            "industry": "E-commerce Platform",
            "keywords": ["online store", "e-commerce", "shopping cart"],
            "competitors": ["Shopify", "WooCommerce", "BigCommerce"],
            "website": "https://weeklyscanlimittest.com"
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        brand_response = requests.post(f"{self.base_url}/api/brands", json=brand_data, headers=headers)
        self.assertEqual(brand_response.status_code, 200)
        brand_data = brand_response.json()
        self.assertIn("brand_id", brand_data)
        self.brand_id = brand_data["brand_id"]
        
        # Run first scan - should succeed
        scan_data = {
            "brand_id": self.brand_id,
            "scan_type": "quick"
        }
        
        first_scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(first_scan_response.status_code, 200)
        first_scan_data = first_scan_response.json()
        self.assertIn("scan_id", first_scan_data)
        
        # Save scan_id for progress tracking test
        self.scan_id = first_scan_data["scan_id"]
        
        # Run second scan immediately - should fail with 429 error
        second_scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(second_scan_response.status_code, 429)
        second_scan_data = second_scan_response.json()
        self.assertIn("detail", second_scan_data)
        
        # Verify error message includes next available scan time
        error_message = second_scan_data["detail"]
        self.assertIn("Next scan available on", error_message)
        self.assertIn("Monday", error_message)
        self.assertIn("11:00 AM PST", error_message)
        
        print("✅ Weekly scan limit test passed")
        print(f"Error message: {error_message}")
        
    def test_03_scan_progress_tracking(self):
        """Test scan progress tracking functionality"""
        if not self.token or not self.scan_id:
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Check progress endpoint
        progress_response = requests.get(f"{self.base_url}/api/scans/{self.scan_id}/progress", headers=headers)
        self.assertEqual(progress_response.status_code, 200)
        progress_data = progress_response.json()
        
        # Verify progress data structure
        self.assertIn("scan_id", progress_data)
        self.assertEqual(progress_data["scan_id"], self.scan_id)
        self.assertIn("status", progress_data)
        self.assertIn("progress", progress_data)
        self.assertIn("total_queries", progress_data)
        self.assertIn("started_at", progress_data)
        
        # Verify status is either "running" or "completed"
        self.assertIn(progress_data["status"], ["running", "completed"])
        
        # If completed, verify progress equals total_queries
        if progress_data["status"] == "completed":
            self.assertEqual(progress_data["progress"], progress_data["total_queries"])
            self.assertIn("completed_at", progress_data)
        
        print("✅ Scan progress tracking test passed")
        print(f"Progress data: {json.dumps(progress_data, indent=2)}")
        
    def test_04_openai_integration(self):
        """Test OpenAI integration for scan results"""
        if not self.token or not self.brand_id:
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get scan results
        scans_response = requests.get(f"{self.base_url}/api/scans/{self.brand_id}", headers=headers)
        self.assertEqual(scans_response.status_code, 200)
        scans_data = scans_response.json()
        self.assertIn("scans", scans_data)
        self.assertTrue(len(scans_data["scans"]) > 0)
        
        # Get the most recent scan
        recent_scan = scans_data["scans"][0]
        self.assertIn("results", recent_scan)
        self.assertTrue(len(recent_scan["results"]) > 0)
        
        # Verify OpenAI integration
        for result in recent_scan["results"]:
            self.assertEqual(result["platform"], "ChatGPT")
            self.assertEqual(result["model"], "gpt-4o-mini")
            self.assertIn("response", result)
            self.assertIn("brand_mentioned", result)
            self.assertIn("competitors_mentioned", result)
            
            # Verify response is not a mock response
            response_text = result["response"]
            self.assertTrue(len(response_text) > 100)
            
            # Check for source domains and articles
            self.assertIn("source_domains", result)
            self.assertIn("source_articles", result)
            
            # Verify source extraction is working
            if len(result["source_domains"]) > 0:
                domain = result["source_domains"][0]
                self.assertIn("domain", domain)
                self.assertIn("impact", domain)
                self.assertIn("category", domain)
            
            if len(result["source_articles"]) > 0:
                article = result["source_articles"][0]
                self.assertIn("url", article)
                self.assertIn("title", article)
                self.assertIn("impact", article)
        
        print("✅ OpenAI integration test passed")

if __name__ == "__main__":
    # Create a test suite with individual test methods
    suite = unittest.TestSuite()
    
    # Add test methods to the suite
    suite.addTest(ScanLimitAndProgressTest('test_01_register_and_login'))
    
    # Run the first test
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # If the first test passed, run the second test
    if result.wasSuccessful():
        print("\nRunning test_02_create_brand_and_test_scan_limit...")
        suite = unittest.TestSuite()
        suite.addTest(ScanLimitAndProgressTest('test_02_create_brand_and_test_scan_limit'))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # If the second test passed, run the third test
    if result.wasSuccessful():
        print("\nRunning test_03_scan_progress_tracking...")
        suite = unittest.TestSuite()
        suite.addTest(ScanLimitAndProgressTest('test_03_scan_progress_tracking'))
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # If the third test passed, run the fourth test
    if result.wasSuccessful():
        print("\nRunning test_04_openai_integration...")
        suite = unittest.TestSuite()
        suite.addTest(ScanLimitAndProgressTest('test_04_openai_integration'))
        result = unittest.TextTestRunner(verbosity=2).run(suite)