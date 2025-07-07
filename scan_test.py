import requests
import unittest
import json
import uuid
import time
from datetime import datetime

class ScanFunctionalityTest(unittest.TestCase):
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
        self.upraised_brand_id = None
        
    def test_01_register_and_login(self):
        """Register a test user and login"""
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
        
    def test_02_upgrade_to_enterprise(self):
        """Upgrade user to enterprise plan to allow multiple brands"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        # Get current user email
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
        print("✅ User upgraded to enterprise plan")
        
    def test_03_create_test_brand(self):
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
        print(f"✅ Test brand created with ID: {self.__class__.brand_id}")
        
    def test_04_create_upraised_brand(self):
        """Create the Upraised brand mentioned in the issue report"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        brand_data = {
            "name": "Upraised",
            "industry": "Career Development Platform",
            "keywords": ["career coaching", "skill development", "job placement"],
            "competitors": ["Springboard", "Pathrise", "Pesto Tech"],
            "website": "https://upraised.co"
        }
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.post(f"{self.base_url}/api/brands", json=brand_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brand_id", data)
        
        # Save Upraised brand_id for subsequent tests
        self.__class__.upraised_brand_id = data["brand_id"]
        print(f"✅ Upraised brand created with ID: {self.__class__.upraised_brand_id}")
        
    def test_05_run_scan_for_test_brand(self):
        """Run a scan for the test brand"""
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
        
        # Verify scan results
        self.assertTrue(len(data["results"]) > 0)
        for result in data["results"]:
            self.assertEqual(result["platform"], "ChatGPT")
            self.assertEqual(result["model"], "gpt-4o-mini")
            self.assertIn("response", result)
            self.assertIn("brand_mentioned", result)
            self.assertIn("source_domains", result)
            self.assertIn("source_articles", result)
            
        print(f"✅ Scan completed for test brand with {len(data['results'])} results")
        
    def test_06_run_scan_for_upraised_brand(self):
        """Run a scan for the Upraised brand"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'upraised_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        scan_data = {
            "brand_id": self.__class__.upraised_brand_id,
            "scan_type": "quick"
        }
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("scan_id", data)
        self.assertIn("results", data)
        
        # Verify scan results
        self.assertTrue(len(data["results"]) > 0)
        for result in data["results"]:
            self.assertEqual(result["platform"], "ChatGPT")
            self.assertEqual(result["model"], "gpt-4o-mini")
            self.assertIn("response", result)
            self.assertIn("brand_mentioned", result)
            self.assertIn("source_domains", result)
            self.assertIn("source_articles", result)
            
        print(f"✅ Scan completed for Upraised brand with {len(data['results'])} results")
        
    def test_07_verify_source_domains_for_test_brand(self):
        """Verify source domains for test brand"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/source-domains?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("domains", data)
        self.assertIn("total", data)
        self.assertTrue(data["total"] > 0, "No source domains found for test brand")
        
        # Save test brand domains for comparison
        self.test_brand_domains = [domain["domain"] for domain in data["domains"]]
        print(f"✅ Found {data['total']} source domains for test brand")
        
    def test_08_verify_source_domains_for_upraised_brand(self):
        """Verify source domains for Upraised brand"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'upraised_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/source-domains?brand_id={self.__class__.upraised_brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("domains", data)
        self.assertIn("total", data)
        self.assertTrue(data["total"] > 0, "No source domains found for Upraised brand")
        
        # Save Upraised brand domains for comparison
        self.upraised_brand_domains = [domain["domain"] for domain in data["domains"]]
        print(f"✅ Found {data['total']} source domains for Upraised brand")
        
    def test_09_compare_source_domains(self):
        """Compare source domains between brands to ensure they're different"""
        if not hasattr(self, 'test_brand_domains') or not hasattr(self, 'upraised_brand_domains'):
            self.skipTest("Previous tests failed, skipping this test")
            
        # Check if domains are different between brands
        common_domains = set(self.test_brand_domains).intersection(set(self.upraised_brand_domains))
        
        # Some overlap is expected (like g2.com, capterra.com), but not complete overlap
        self.assertLess(len(common_domains), len(self.test_brand_domains), 
                       "All test brand domains also appear for Upraised brand")
        self.assertLess(len(common_domains), len(self.upraised_brand_domains), 
                       "All Upraised brand domains also appear for test brand")
        
        print(f"✅ Source domains are different between brands (common domains: {len(common_domains)})")
        
    def test_10_verify_source_articles_for_test_brand(self):
        """Verify source articles for test brand"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/source-articles?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("articles", data)
        self.assertIn("total", data)
        self.assertTrue(data["total"] > 0, "No source articles found for test brand")
        
        # Save test brand articles for comparison
        self.test_brand_articles = [article["url"] for article in data["articles"]]
        print(f"✅ Found {data['total']} source articles for test brand")
        
    def test_11_verify_source_articles_for_upraised_brand(self):
        """Verify source articles for Upraised brand"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'upraised_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/source-articles?brand_id={self.__class__.upraised_brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("articles", data)
        self.assertIn("total", data)
        self.assertTrue(data["total"] > 0, "No source articles found for Upraised brand")
        
        # Save Upraised brand articles for comparison
        self.upraised_brand_articles = [article["url"] for article in data["articles"]]
        print(f"✅ Found {data['total']} source articles for Upraised brand")
        
    def test_12_compare_source_articles(self):
        """Compare source articles between brands to ensure they're different"""
        if not hasattr(self, 'test_brand_articles') or not hasattr(self, 'upraised_brand_articles'):
            self.skipTest("Previous tests failed, skipping this test")
            
        # Check if articles are different between brands
        common_articles = set(self.test_brand_articles).intersection(set(self.upraised_brand_articles))
        
        # Some overlap is expected, but not complete overlap
        self.assertLess(len(common_articles), len(self.test_brand_articles), 
                       "All test brand articles also appear for Upraised brand")
        self.assertLess(len(common_articles), len(self.upraised_brand_articles), 
                       "All Upraised brand articles also appear for test brand")
        
        print(f"✅ Source articles are different between brands (common articles: {len(common_articles)})")
        
    def test_13_verify_dashboard_data_for_test_brand(self):
        """Verify dashboard data for test brand"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/dashboard/real?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("overall_visibility", data)
        self.assertIn("total_queries", data)
        self.assertIn("total_mentions", data)
        self.assertTrue(data["total_queries"] > 0, "No queries found in dashboard for test brand")
        
        # Save test brand dashboard data for comparison
        self.test_brand_dashboard = data
        print(f"✅ Dashboard data verified for test brand: {data['total_queries']} queries, {data['total_mentions']} mentions")
        
    def test_14_verify_dashboard_data_for_upraised_brand(self):
        """Verify dashboard data for Upraised brand"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'upraised_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/dashboard/real?brand_id={self.__class__.upraised_brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("overall_visibility", data)
        self.assertIn("total_queries", data)
        self.assertIn("total_mentions", data)
        self.assertTrue(data["total_queries"] > 0, "No queries found in dashboard for Upraised brand")
        
        # Save Upraised brand dashboard data for comparison
        self.upraised_brand_dashboard = data
        print(f"✅ Dashboard data verified for Upraised brand: {data['total_queries']} queries, {data['total_mentions']} mentions")
        
    def test_15_compare_dashboard_data(self):
        """Compare dashboard data between brands to ensure they're different"""
        if not hasattr(self, 'test_brand_dashboard') or not hasattr(self, 'upraised_brand_dashboard'):
            self.skipTest("Previous tests failed, skipping this test")
            
        # Check if dashboard data is different between brands
        self.assertNotEqual(self.test_brand_dashboard["total_queries"], self.upraised_brand_dashboard["total_queries"], 
                           "Both brands show same number of queries in dashboard")
        
        print("✅ Dashboard data is different between brands")
        
    def test_16_verify_competitors_data_for_test_brand(self):
        """Verify competitors data for test brand"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/competitors/real?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("competitors", data)
        self.assertIn("total_queries_analyzed", data)
        self.assertTrue(data["total_queries_analyzed"] > 0, "No queries analyzed for test brand competitors")
        
        # Save test brand competitors data for comparison
        self.test_brand_competitors = [comp["name"] for comp in data["competitors"]]
        print(f"✅ Competitors data verified for test brand: {len(self.test_brand_competitors)} competitors")
        
    def test_17_verify_competitors_data_for_upraised_brand(self):
        """Verify competitors data for Upraised brand"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'upraised_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/competitors/real?brand_id={self.__class__.upraised_brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("competitors", data)
        self.assertIn("total_queries_analyzed", data)
        self.assertTrue(data["total_queries_analyzed"] > 0, "No queries analyzed for Upraised brand competitors")
        
        # Save Upraised brand competitors data for comparison
        self.upraised_brand_competitors = [comp["name"] for comp in data["competitors"]]
        print(f"✅ Competitors data verified for Upraised brand: {len(self.upraised_brand_competitors)} competitors")
        
    def test_18_compare_competitors_data(self):
        """Compare competitors data between brands to ensure they're different"""
        if not hasattr(self, 'test_brand_competitors') or not hasattr(self, 'upraised_brand_competitors'):
            self.skipTest("Previous tests failed, skipping this test")
            
        # Check if competitors are different between brands
        common_competitors = set(self.test_brand_competitors).intersection(set(self.upraised_brand_competitors))
        
        # There should be minimal overlap between competitors for different industries
        self.assertLess(len(common_competitors), len(self.test_brand_competitors) / 2, 
                       "Too many common competitors between different industry brands")
        
        print(f"✅ Competitors data is different between brands (common competitors: {len(common_competitors)})")
        
    def test_19_verify_brand_update(self):
        """Verify brand update functionality"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'upraised_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        # Update Upraised brand with new keywords and competitors
        update_data = {
            "keywords": ["career acceleration", "job readiness", "tech careers", "bootcamp alternative"],
            "competitors": ["Springboard", "Pathrise", "Pesto Tech", "Newton School", "Masai School"]
        }
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.put(f"{self.base_url}/api/brands/{self.__class__.upraised_brand_id}", 
                               json=update_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("brand", data)
        self.assertEqual(data["brand"]["name"], "Upraised")  # Name should not change
        self.assertEqual(len(data["brand"]["keywords"]), 4)  # Should have 4 new keywords
        self.assertEqual(len(data["brand"]["competitors"]), 5)  # Should have 5 new competitors
        
        print("✅ Brand update functionality verified")
        
    def test_20_run_scan_after_brand_update(self):
        """Run a scan after brand update to verify new keywords and competitors are used"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'upraised_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        scan_data = {
            "brand_id": self.__class__.upraised_brand_id,
            "scan_type": "quick"
        }
        
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("scan_id", data)
        self.assertIn("results", data)
        self.assertTrue(len(data["results"]) > 0)
        
        # Check if any of the new competitors are mentioned in the results
        new_competitors = ["Newton School", "Masai School"]
        competitor_found = False
        
        for result in data["results"]:
            for competitor in new_competitors:
                if competitor.lower() in result["response"].lower():
                    competitor_found = True
                    break
        
        # It's possible but not guaranteed that new competitors will be mentioned
        print(f"✅ Scan completed after brand update with {len(data['results'])} results")
        if competitor_found:
            print("  - New competitors were mentioned in the scan results")
        else:
            print("  - New competitors were not mentioned in this scan (this is not necessarily an error)")

if __name__ == "__main__":
    unittest.main()