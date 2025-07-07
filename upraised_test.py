import requests
import unittest
import json
import uuid
import time
from datetime import datetime

class UpraisedBrandScanTest(unittest.TestCase):
    def setUp(self):
        # Get the backend URL from the frontend .env file
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.strip().split('=')[1].strip('"\'')
                    break
        
        print(f"Using backend URL: {self.base_url}")
        
        # Login with existing credentials
        login_data = {
            "email": "admin@futureseo.io",
            "password": "admin123"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            print("✅ Login successful with admin account")
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            self.token = None
        
    def test_01_create_upraised_brand(self):
        """Create the Upraised brand mentioned in the issue report"""
        if not self.token:
            self.skipTest("Login failed, skipping this test")
            
        brand_data = {
            "name": "Upraised",
            "industry": "Career Development Platform",
            "keywords": ["career coaching", "skill development", "job placement"],
            "competitors": ["Springboard", "Pathrise", "Pesto Tech"],
            "website": "https://upraised.co"
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{self.base_url}/api/brands", json=brand_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brand_id", data)
        
        # Save Upraised brand_id for subsequent tests
        self.upraised_brand_id = data["brand_id"]
        print(f"✅ Upraised brand created with ID: {self.upraised_brand_id}")
        
    def test_02_run_scan_for_upraised_brand(self):
        """Run a scan for the Upraised brand"""
        if not hasattr(self, 'upraised_brand_id'):
            self.skipTest("Previous test failed, skipping this test")
            
        scan_data = {
            "brand_id": self.upraised_brand_id,
            "scan_type": "quick"
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
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
        
    def test_03_verify_source_domains_for_upraised_brand(self):
        """Verify source domains for Upraised brand"""
        if not hasattr(self, 'upraised_brand_id'):
            self.skipTest("Previous test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/source-domains?brand_id={self.upraised_brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("domains", data)
        self.assertIn("total", data)
        self.assertTrue(data["total"] > 0, "No source domains found for Upraised brand")
        
        # Print domains for inspection
        print(f"✅ Found {data['total']} source domains for Upraised brand:")
        for domain in data["domains"]:
            print(f"  - {domain['domain']}")
        
    def test_04_verify_source_articles_for_upraised_brand(self):
        """Verify source articles for Upraised brand"""
        if not hasattr(self, 'upraised_brand_id'):
            self.skipTest("Previous test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/source-articles?brand_id={self.upraised_brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("articles", data)
        self.assertIn("total", data)
        self.assertTrue(data["total"] > 0, "No source articles found for Upraised brand")
        
        # Print articles for inspection
        print(f"✅ Found {data['total']} source articles for Upraised brand:")
        for article in data["articles"]:
            print(f"  - {article['title']}: {article['url']}")
        
    def test_05_verify_dashboard_data_for_upraised_brand(self):
        """Verify dashboard data for Upraised brand"""
        if not hasattr(self, 'upraised_brand_id'):
            self.skipTest("Previous test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/dashboard/real?brand_id={self.upraised_brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("overall_visibility", data)
        self.assertIn("total_queries", data)
        self.assertIn("total_mentions", data)
        self.assertTrue(data["total_queries"] > 0, "No queries found in dashboard for Upraised brand")
        
        print(f"✅ Dashboard data verified for Upraised brand:")
        print(f"  - Total queries: {data['total_queries']}")
        print(f"  - Total mentions: {data['total_mentions']}")
        print(f"  - Visibility score: {data['overall_visibility']}%")
        
    def test_06_verify_competitors_data_for_upraised_brand(self):
        """Verify competitors data for Upraised brand"""
        if not hasattr(self, 'upraised_brand_id'):
            self.skipTest("Previous test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/competitors/real?brand_id={self.upraised_brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("competitors", data)
        self.assertIn("total_queries_analyzed", data)
        self.assertTrue(data["total_queries_analyzed"] > 0, "No queries analyzed for Upraised brand competitors")
        
        # Print competitors for inspection
        print(f"✅ Competitors data verified for Upraised brand:")
        print(f"  - Total queries analyzed: {data['total_queries_analyzed']}")
        print(f"  - Competitors found:")
        for comp in data["competitors"]:
            print(f"    - {comp['name']} (mentions: {comp['mentions']})")

if __name__ == "__main__":
    unittest.main()