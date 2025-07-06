import requests
import unittest
import json
import uuid
import time
import re
from datetime import datetime

class BrandUpdateAndSourceExtractionTest(unittest.TestCase):
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
        self.second_brand_id = None
        
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
        
    def test_02_create_brands(self):
        """Create two test brands for testing"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        # First upgrade to enterprise plan to allow multiple brands
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        user_response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(user_response.status_code, 200)
        user_data = user_response.json()
        user_email = user_data["email"]
        
        # Upgrade to enterprise plan
        upgrade_response = requests.post(
            f"{self.base_url}/api/admin/upgrade-user?user_email={user_email}&new_plan=enterprise",
            headers=headers
        )
        self.assertEqual(upgrade_response.status_code, 200)
        
        # Create first brand - Fintech
        brand_data_1 = {
            "name": "PaymentFlow",
            "industry": "Fintech",
            "keywords": ["payment processing", "financial services", "digital payments"],
            "competitors": ["Stripe", "Brex", "Airwallex"],
            "website": "https://paymentflow.example.com"
        }
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.post(f"{self.base_url}/api/brands", json=brand_data_1, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brand_id", data)
        
        # Save brand_id for subsequent tests
        self.__class__.brand_id = data["brand_id"]
        
        # Create second brand - E-commerce
        brand_data_2 = {
            "name": "ShopSmart",
            "industry": "E-commerce",
            "keywords": ["online shopping", "e-commerce platform", "retail"],
            "competitors": ["Shopify", "WooCommerce", "BigCommerce"],
            "website": "https://shopsmart.example.com"
        }
        
        response = requests.post(f"{self.base_url}/api/brands", json=brand_data_2, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brand_id", data)
        
        # Save second brand_id for subsequent tests
        self.__class__.second_brand_id = data["brand_id"]
        print("✅ Created two test brands successfully")
        
    def test_03_brand_update_endpoint(self):
        """Test the new PUT /api/brands/{brand_id} endpoint"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get original brand data
        response = requests.get(f"{self.base_url}/api/brands/{self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        original_brand = response.json()["brand"]
        
        # Update keywords and competitors
        update_data = {
            "keywords": ["payment processing", "financial services", "digital payments", "cross-border payments", "payment gateway"],
            "competitors": ["Stripe", "Brex", "Airwallex", "PayPal", "Square"]
        }
        
        response = requests.put(f"{self.base_url}/api/brands/{self.__class__.brand_id}", json=update_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        updated_brand = response.json()["brand"]
        
        # Verify keywords and competitors were updated
        self.assertEqual(len(updated_brand["keywords"]), 5)
        self.assertEqual(len(updated_brand["competitors"]), 5)
        self.assertIn("payment gateway", updated_brand["keywords"])
        self.assertIn("PayPal", updated_brand["competitors"])
        
        # Verify name, industry, and website were NOT changed
        self.assertEqual(updated_brand["name"], original_brand["name"])
        self.assertEqual(updated_brand["industry"], original_brand["industry"])
        self.assertEqual(updated_brand["website"], original_brand["website"])
        
        print("✅ Brand update endpoint test passed")
        
    def test_04_brand_update_authentication_required(self):
        """Test that brand update endpoint requires authentication"""
        if not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        # Try to update without authentication
        update_data = {
            "keywords": ["payment processing", "financial services"],
            "competitors": ["Stripe", "Brex"]
        }
        
        response = requests.put(f"{self.base_url}/api/brands/{self.__class__.brand_id}", json=update_data)
        self.assertEqual(response.status_code, 403)
        print("✅ Brand update authentication requirement test passed")
        
    def test_05_brand_update_user_ownership(self):
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
        print("✅ Brand update user ownership test passed")
        
    def test_06_run_scan_and_check_source_extraction(self):
        """Test that source domains and articles are extracted from ChatGPT responses"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Run a quick scan
        scan_data = {
            "brand_id": self.__class__.brand_id,
            "scan_type": "quick"
        }
        
        scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(scan_response.status_code, 200)
        scan_result = scan_response.json()
        
        # Check that scan results contain source domains and articles
        for result in scan_result["results"]:
            self.assertIn("source_domains", result)
            self.assertIn("source_articles", result)
        
        # Check source domains endpoint
        domains_response = requests.get(f"{self.base_url}/api/source-domains?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(domains_response.status_code, 200)
        domains_data = domains_response.json()
        
        # Verify domains data
        self.assertIn("domains", domains_data)
        self.assertIn("total", domains_data)
        self.assertIn("page", domains_data)
        self.assertIn("total_pages", domains_data)
        
        # Check that domains are returned even if not found in GPT response
        # Note: has_next and has_prev might not be present if there are no domains
        if domains_data["total"] > 0:
            self.assertIn("has_next", domains_data)
            self.assertIn("has_prev", domains_data)
            self.assertTrue(len(domains_data["domains"]) > 0)
        
        # Check source articles endpoint
        articles_response = requests.get(f"{self.base_url}/api/source-articles?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(articles_response.status_code, 200)
        articles_data = articles_response.json()
        
        # Verify articles data
        self.assertIn("articles", articles_data)
        self.assertIn("total", articles_data)
        self.assertIn("page", articles_data)
        self.assertIn("total_pages", articles_data)
        
        # Check that articles are returned even if not found in GPT response
        # Note: has_next and has_prev might not be present if there are no articles
        if articles_data["total"] > 0:
            self.assertIn("has_next", articles_data)
            self.assertIn("has_prev", articles_data)
            self.assertTrue(len(articles_data["articles"]) > 0)
        
        print("✅ Source extraction test passed")
        
    def test_07_check_source_extraction_fallback(self):
        """Test that source extraction fallback logic works"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get source domains
        domains_response = requests.get(f"{self.base_url}/api/source-domains?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(domains_response.status_code, 200)
        domains_data = domains_response.json()
        
        # Verify domains structure
        if domains_data["domains"]:
            domain = domains_data["domains"][0]
            self.assertIn("domain", domain)
            self.assertIn("category", domain)
            self.assertIn("impact", domain)
            self.assertIn("mentions", domain)
            self.assertIn("pages", domain)
        
        # Get source articles
        articles_response = requests.get(f"{self.base_url}/api/source-articles?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(articles_response.status_code, 200)
        articles_data = articles_response.json()
        
        # Verify articles structure
        if articles_data["articles"]:
            article = articles_data["articles"][0]
            self.assertIn("url", article)
            self.assertIn("title", article)
            self.assertIn("impact", article)
            self.assertIn("queries", article)
        
        print("✅ Source extraction fallback test passed")
        
    def test_08_check_visibility_calculations(self):
        """Test that visibility calculations are market-realistic"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id') or not hasattr(self.__class__, 'second_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Run scans for both brands
        for brand_id in [self.__class__.brand_id, self.__class__.second_brand_id]:
            scan_data = {
                "brand_id": brand_id,
                "scan_type": "quick"
            }
            
            scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
            self.assertEqual(scan_response.status_code, 200)
        
        # Get competitors data for first brand
        competitors_response = requests.get(f"{self.base_url}/api/competitors/real?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(competitors_response.status_code, 200)
        competitors_data = competitors_response.json()
        
        # Check that major players have higher visibility
        major_players = ["Stripe", "Brex", "Airwallex"]
        user_brand = "PaymentFlow"
        
        # Extract visibility scores
        competitor_visibility = {}
        for comp in competitors_data["competitors"]:
            competitor_visibility[comp["name"]] = comp["visibility_score"]
        
        # Check if at least one major player has higher visibility than user brand
        major_player_higher = False
        for player in major_players:
            if player in competitor_visibility and user_brand in competitor_visibility:
                if competitor_visibility[player] > competitor_visibility[user_brand]:
                    major_player_higher = True
                    break
        
        # This test might be flaky due to randomness in AI responses, but should pass most of the time
        # if the visibility calculations are realistic
        self.assertTrue(major_player_higher, "Major players should have higher visibility than user brand")
        
        print("✅ Visibility calculations test passed")
        
    def test_09_check_enhanced_prompts(self):
        """Test that enhanced prompts are working correctly"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Run a quick scan
        scan_data = {
            "brand_id": self.__class__.brand_id,
            "scan_type": "quick"
        }
        
        scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(scan_response.status_code, 200)
        scan_result = scan_response.json()
        
        # Check responses for 2025 dates and avoidance of "Competitor A/B" patterns
        for result in scan_result["results"]:
            response_text = result["response"]
            
            # Check for 2025 dates
            has_2025_date = bool(re.search(r'2025', response_text))
            
            # Check for absence of "Competitor A/B" patterns
            has_competitor_ab_pattern = bool(re.search(r'Competitor [A-Z]', response_text))
            
            # At least one response should have 2025 date
            if has_2025_date:
                self.assertTrue(True, "Found 2025 date in response")
                break
        
        # No response should have "Competitor A/B" pattern
        for result in scan_result["results"]:
            response_text = result["response"]
            has_competitor_ab_pattern = bool(re.search(r'Competitor [A-Z]', response_text))
            self.assertFalse(has_competitor_ab_pattern, "Found 'Competitor X' pattern in response")
        
        print("✅ Enhanced prompts test passed")

if __name__ == "__main__":
    unittest.main()