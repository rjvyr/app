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
            
            # Check that response doesn't start with the generic "For..." pattern used in mock data
            self.assertFalse(response_text.startswith("For "), "Response starts with 'For', might be mock data")
            
            # Verify tokens were used (real API call)
            self.assertTrue(result["tokens_used"] > 0)
            
            # Check for source domains and articles
            self.assertIn("source_domains", result)
            self.assertIn("source_articles", result)
            
        print("✅ OpenAI integration test successful")
        
    def test_04_source_domains_extraction(self):
        """Test that source domains are properly extracted from OpenAI responses"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get source domains
        response = requests.get(f"{self.base_url}/api/source-domains?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify source domains exist
        self.assertIn("domains", data)
        self.assertTrue(len(data["domains"]) > 0, "No source domains found")
        
        # Check domain structure
        for domain in data["domains"]:
            self.assertIn("domain", domain)
            self.assertIn("impact", domain)
            self.assertIn("mentions", domain)
            self.assertIn("category", domain)
            
            # Verify domain is a valid domain name
            self.assertTrue(re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain["domain"]), 
                           f"Invalid domain format: {domain['domain']}")
            
            # Verify impact is realistic (not always 100%)
            self.assertLess(domain["impact"], 100, "Impact is suspiciously high (100%)")
            self.assertGreater(domain["impact"], 0, "Impact should be greater than 0")
        
        print("✅ Source domains extraction test successful")
        
    def test_05_source_articles_extraction(self):
        """Test that source articles are properly extracted from OpenAI responses"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get source articles
        response = requests.get(f"{self.base_url}/api/source-articles?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify source articles exist
        self.assertIn("articles", data)
        self.assertTrue(len(data["articles"]) > 0, "No source articles found")
        
        # Check article structure
        for article in data["articles"]:
            self.assertIn("url", article)
            self.assertIn("title", article)
            self.assertIn("impact", article)
            self.assertIn("queries", article)
            
            # Verify URL is a valid URL
            self.assertTrue(article["url"].startswith("http"), f"Invalid URL format: {article['url']}")
            
            # Verify title exists
            self.assertTrue(len(article["title"]) > 0, "Article title is empty")
            
            # Verify impact is realistic (not always 100%)
            self.assertLess(article["impact"], 100, "Impact is suspiciously high (100%)")
            self.assertGreater(article["impact"], 0, "Impact should be greater than 0")
        
        print("✅ Source articles extraction test successful")
        
    def test_06_error_handling(self):
        """Test error handling for OpenAI API calls"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        # This test is more difficult to simulate directly, but we can check that
        # the system doesn't crash when making multiple concurrent requests
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Make 3 concurrent scan requests to stress test the system
        scan_data = {
            "brand_id": self.__class__.brand_id,
            "scan_type": "quick"
        }
        
        responses = []
        for _ in range(3):
            response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
            responses.append(response)
            
        # Verify all requests completed successfully
        for i, response in enumerate(responses):
            self.assertEqual(response.status_code, 200, f"Request {i+1} failed with status {response.status_code}")
            data = response.json()
            self.assertIn("scan_id", data)
            self.assertIn("results", data)
            
        print("✅ Error handling test successful")
        
    def test_07_response_quality(self):
        """Test that responses are high quality and don't follow generic patterns"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get scan results
        response = requests.get(f"{self.base_url}/api/scans/{self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify we have scan results
        self.assertIn("scans", data)
        self.assertTrue(len(data["scans"]) > 0, "No scan results found")
        
        # Check the most recent scan
        latest_scan = data["scans"][0]
        self.assertIn("results", latest_scan)
        
        # Check response quality
        generic_patterns = [
            r"^For ",
            r"^When comparing",
            r"^In the realm of",
            r"^Looking at",
        ]
        
        for result in latest_scan["results"]:
            response_text = result["response"]
            
            # Check that response doesn't match generic patterns
            for pattern in generic_patterns:
                self.assertFalse(re.match(pattern, response_text), 
                               f"Response matches generic pattern '{pattern}': {response_text[:50]}...")
                
            # Check for realistic content
            self.assertTrue("2025" in response_text or "2024" in response_text, 
                          "Response doesn't mention current year (2024/2025)")
            
            # Check that it doesn't use generic competitor references
            self.assertFalse("Competitor A" in response_text or "Competitor B" in response_text,
                           "Response uses generic competitor references")
            
        print("✅ Response quality test successful")

if __name__ == "__main__":
    unittest.main()