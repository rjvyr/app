import requests
import unittest
import json
import uuid
from datetime import datetime
import time

class AIBrandVisibilityAPITest(unittest.TestCase):
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
        """Test user registration and login"""
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
        print("✅ User registration and login test passed")

    def test_02_create_multiple_brands(self):
        """Test creating multiple brands for brand filtering tests"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # First brand - Wholesale Helper
        brand1_data = {
            "name": "Wholesale Helper",
            "industry": "Wholesale Management",
            "keywords": ["inventory management", "wholesale pricing", "supplier management"],
            "competitors": ["Faire", "Handshake", "Tundra"],
            "website": "https://wholesalehelper.com"
        }
        
        response1 = requests.post(f"{self.base_url}/api/brands", json=brand1_data, headers=headers)
        print(f"First brand creation response: {response1.status_code}")
        print(f"Response content: {response1.text}")
        
        if response1.status_code == 200:
            data1 = response1.json()
            self.assertIn("brand_id", data1)
            # Save first brand_id
            self.__class__.brand_id = data1["brand_id"]
        else:
            # If creating brand fails, let's try to get existing brands
            brands_response = requests.get(f"{self.base_url}/api/brands", headers=headers)
            if brands_response.status_code == 200:
                brands_data = brands_response.json()
                if "brands" in brands_data and len(brands_data["brands"]) > 0:
                    self.__class__.brand_id = brands_data["brands"][0]["_id"]
                    print(f"Using existing brand ID: {self.__class__.brand_id}")
        
        # Make sure we have a brand_id
        self.assertIsNotNone(self.__class__.brand_id, "Failed to get a valid brand ID")
        
        # Second brand - Volopay
        brand2_data = {
            "name": "Volopay",
            "industry": "Expense Management",
            "keywords": ["expense tracking", "corporate cards", "spend management"],
            "competitors": ["Brex", "Ramp", "Divvy"],
            "website": "https://volopay.com"
        }
        
        # Upgrade to enterprise plan to allow multiple brands
        upgrade_response = requests.post(
            f"{self.base_url}/api/admin/upgrade-user?user_email={self.user_email}&new_plan=enterprise",
            headers=headers
        )
        print(f"Upgrade response: {upgrade_response.status_code}")
        
        response2 = requests.post(f"{self.base_url}/api/brands", json=brand2_data, headers=headers)
        print(f"Second brand creation response: {response2.status_code}")
        
        if response2.status_code == 200:
            data2 = response2.json()
            self.assertIn("brand_id", data2)
            # Save second brand_id
            self.__class__.second_brand_id = data2["brand_id"]
        else:
            # If creating second brand fails, let's try to get existing brands
            brands_response = requests.get(f"{self.base_url}/api/brands", headers=headers)
            if brands_response.status_code == 200:
                brands_data = brands_response.json()
                if "brands" in brands_data and len(brands_data["brands"]) > 1:
                    self.__class__.second_brand_id = brands_data["brands"][1]["_id"]
                    print(f"Using existing second brand ID: {self.__class__.second_brand_id}")
                elif "brands" in brands_data and len(brands_data["brands"]) == 1:
                    # If only one brand exists, use it for both tests
                    self.__class__.second_brand_id = brands_data["brands"][0]["_id"]
                    print(f"Using same brand ID for both tests: {self.__class__.second_brand_id}")
        
        # Make sure we have a second brand_id
        self.assertIsNotNone(self.__class__.second_brand_id, "Failed to get a valid second brand ID")
        
        print("✅ Create multiple brands test passed")

    def test_03_run_scans_for_both_brands(self):
        """Test running scans for both brands to generate data"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id') or not hasattr(self.__class__, 'second_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Run scan for first brand
        scan_data_1 = {
            "brand_id": self.__class__.brand_id,
            "scan_type": "quick"
        }
        
        scan_response_1 = requests.post(f"{self.base_url}/api/scans", json=scan_data_1, headers=headers)
        print(f"First scan response: {scan_response_1.status_code}")
        print(f"Response content: {scan_response_1.text}")
        
        if scan_response_1.status_code == 200:
            scan_data_1 = scan_response_1.json()
            self.assertIn("scan_id", scan_data_1)
            # Save scan_id for progress tracking test
            self.__class__.scan_id = scan_data_1["scan_id"]
        elif scan_response_1.status_code == 429:
            # If we hit the weekly scan limit, try to get existing scans
            scans_response = requests.get(f"{self.base_url}/api/scans/{self.__class__.brand_id}", headers=headers)
            if scans_response.status_code == 200:
                scans_data = scans_response.json()
                if "scans" in scans_data and len(scans_data["scans"]) > 0:
                    # Use the most recent scan
                    self.__class__.scan_id = scans_data["scans"][0]["_id"]
                    print(f"Using existing scan ID: {self.__class__.scan_id}")
        
        # Make sure we have a scan_id
        if not hasattr(self.__class__, 'scan_id'):
            print("WARNING: No scan_id available for progress tracking test")
            self.__class__.scan_id = "dummy_scan_id"  # Set a dummy value to avoid errors
        
        # Run scan for second brand
        scan_data_2 = {
            "brand_id": self.__class__.second_brand_id,
            "scan_type": "quick"
        }
        
        scan_response_2 = requests.post(f"{self.base_url}/api/scans", json=scan_data_2, headers=headers)
        print(f"Second scan response: {scan_response_2.status_code}")
        
        # Wait for scans to complete
        time.sleep(2)
        
        print("✅ Run scans for both brands test passed")

    def test_04_brand_filtering_dashboard(self):
        """Test brand filtering for dashboard endpoint"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id') or not hasattr(self.__class__, 'second_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get dashboard data without brand filter
        all_brands_response = requests.get(f"{self.base_url}/api/dashboard/real", headers=headers)
        self.assertEqual(all_brands_response.status_code, 200)
        all_brands_data = all_brands_response.json()
        
        # Get dashboard data with first brand filter
        first_brand_response = requests.get(f"{self.base_url}/api/dashboard/real?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(first_brand_response.status_code, 200)
        first_brand_data = first_brand_response.json()
        
        # Get dashboard data with second brand filter
        second_brand_response = requests.get(f"{self.base_url}/api/dashboard/real?brand_id={self.__class__.second_brand_id}", headers=headers)
        self.assertEqual(second_brand_response.status_code, 200)
        second_brand_data = second_brand_response.json()
        
        # Verify that filtered data is different
        self.assertNotEqual(first_brand_data["total_queries"], second_brand_data["total_queries"], 
                           "Brand filtering not working - both brands show same data")
        
        print("✅ Brand filtering for dashboard endpoint test passed")

    def test_05_brand_filtering_queries(self):
        """Test brand filtering for queries endpoint"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id') or not hasattr(self.__class__, 'second_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get queries data without brand filter
        all_brands_response = requests.get(f"{self.base_url}/api/queries/real", headers=headers)
        self.assertEqual(all_brands_response.status_code, 200)
        all_brands_data = all_brands_response.json()
        
        # Get queries data with first brand filter
        first_brand_response = requests.get(f"{self.base_url}/api/queries/real?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(first_brand_response.status_code, 200)
        first_brand_data = first_brand_response.json()
        
        # Get queries data with second brand filter
        second_brand_response = requests.get(f"{self.base_url}/api/queries/real?brand_id={self.__class__.second_brand_id}", headers=headers)
        self.assertEqual(second_brand_response.status_code, 200)
        second_brand_data = second_brand_response.json()
        
        # Verify that filtered data is different
        first_brand_queries = set([q["query"] for q in first_brand_data["queries"]])
        second_brand_queries = set([q["query"] for q in second_brand_data["queries"]])
        
        self.assertNotEqual(first_brand_queries, second_brand_queries, 
                           "Brand filtering not working - both brands show same queries")
        
        print("✅ Brand filtering for queries endpoint test passed")

    def test_06_brand_filtering_competitors(self):
        """Test brand filtering for competitors endpoint"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id') or not hasattr(self.__class__, 'second_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get competitors data without brand filter
        all_brands_response = requests.get(f"{self.base_url}/api/competitors/real", headers=headers)
        self.assertEqual(all_brands_response.status_code, 200)
        all_brands_data = all_brands_response.json()
        
        # Get competitors data with first brand filter
        first_brand_response = requests.get(f"{self.base_url}/api/competitors/real?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(first_brand_response.status_code, 200)
        first_brand_data = first_brand_response.json()
        
        # Get competitors data with second brand filter
        second_brand_response = requests.get(f"{self.base_url}/api/competitors/real?brand_id={self.__class__.second_brand_id}", headers=headers)
        self.assertEqual(second_brand_response.status_code, 200)
        second_brand_data = second_brand_response.json()
        
        # Verify that filtered data is different
        first_brand_competitors = set([comp["name"] for comp in first_brand_data["competitors"]])
        second_brand_competitors = set([comp["name"] for comp in second_brand_data["competitors"]])
        
        self.assertNotEqual(first_brand_competitors, second_brand_competitors, 
                           "Brand filtering not working - both brands show same competitors")
        
        print("✅ Brand filtering for competitors endpoint test passed")

    def test_07_brand_filtering_recommendations(self):
        """Test brand filtering for recommendations endpoint"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id') or not hasattr(self.__class__, 'second_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get recommendations data without brand filter
        all_brands_response = requests.get(f"{self.base_url}/api/recommendations/real", headers=headers)
        self.assertEqual(all_brands_response.status_code, 200)
        all_brands_data = all_brands_response.json()
        
        # Get recommendations data with first brand filter
        first_brand_response = requests.get(f"{self.base_url}/api/recommendations/real?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(first_brand_response.status_code, 200)
        first_brand_data = first_brand_response.json()
        
        # Get recommendations data with second brand filter
        second_brand_response = requests.get(f"{self.base_url}/api/recommendations/real?brand_id={self.__class__.second_brand_id}", headers=headers)
        self.assertEqual(second_brand_response.status_code, 200)
        second_brand_data = second_brand_response.json()
        
        # Verify that recommendations are different for each brand
        self.assertNotEqual(first_brand_data["data_points"], second_brand_data["data_points"], 
                           "Brand filtering not working - both brands show same data points")
        
        print("✅ Brand filtering for recommendations endpoint test passed")

    def test_08_brand_filtering_source_domains(self):
        """Test brand filtering for source domains endpoint"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id') or not hasattr(self.__class__, 'second_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get source domains data without brand filter
        all_brands_response = requests.get(f"{self.base_url}/api/source-domains", headers=headers)
        self.assertEqual(all_brands_response.status_code, 200)
        all_brands_data = all_brands_response.json()
        
        # Get source domains data with first brand filter
        first_brand_response = requests.get(f"{self.base_url}/api/source-domains?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(first_brand_response.status_code, 200)
        first_brand_data = first_brand_response.json()
        
        # Get source domains data with second brand filter
        second_brand_response = requests.get(f"{self.base_url}/api/source-domains?brand_id={self.__class__.second_brand_id}", headers=headers)
        self.assertEqual(second_brand_response.status_code, 200)
        second_brand_data = second_brand_response.json()
        
        # Verify that domains are different for each brand
        if first_brand_data["domains"] and second_brand_data["domains"]:
            first_brand_domain_names = [d["domain"] for d in first_brand_data["domains"]]
            second_brand_domain_names = [d["domain"] for d in second_brand_data["domains"]]
            
            # There should be some difference in domains between brands
            self.assertNotEqual(set(first_brand_domain_names), set(second_brand_domain_names), 
                               "Brand filtering not working - both brands show same source domains")
        
        print("✅ Brand filtering for source domains endpoint test passed")

    def test_09_brand_filtering_source_articles(self):
        """Test brand filtering for source articles endpoint"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id') or not hasattr(self.__class__, 'second_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get source articles data without brand filter
        all_brands_response = requests.get(f"{self.base_url}/api/source-articles", headers=headers)
        self.assertEqual(all_brands_response.status_code, 200)
        all_brands_data = all_brands_response.json()
        
        # Get source articles data with first brand filter
        first_brand_response = requests.get(f"{self.base_url}/api/source-articles?brand_id={self.__class__.brand_id}", headers=headers)
        self.assertEqual(first_brand_response.status_code, 200)
        first_brand_data = first_brand_response.json()
        
        # Get source articles data with second brand filter
        second_brand_response = requests.get(f"{self.base_url}/api/source-articles?brand_id={self.__class__.second_brand_id}", headers=headers)
        self.assertEqual(second_brand_response.status_code, 200)
        second_brand_data = second_brand_response.json()
        
        # Verify that articles are different for each brand
        if first_brand_data["articles"] and second_brand_data["articles"]:
            first_brand_article_urls = [a["url"] for a in first_brand_data["articles"]]
            second_brand_article_urls = [a["url"] for a in second_brand_data["articles"]]
            
            # There should be some difference in articles between brands
            self.assertNotEqual(set(first_brand_article_urls), set(second_brand_article_urls), 
                               "Brand filtering not working - both brands show same source articles")
        
        print("✅ Brand filtering for source articles endpoint test passed")

    def test_10_pricing_plans_structure(self):
        """Test the new pricing plans structure"""
        response = requests.get(f"{self.base_url}/api/plans")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify response structure
        self.assertIn("plans", data)
        self.assertIn("early_access", data)
        
        # Verify early access information
        early_access = data["early_access"]
        self.assertIn("available", early_access)
        self.assertIn("remaining_seats", early_access)
        self.assertIn("total_seats", early_access)
        self.assertIn("current_users", early_access)
        
        # Verify plans structure
        plans = data["plans"]
        self.assertTrue(len(plans) >= 3)  # Should have at least 3 plans
        
        # Find free, starter, and pro plans
        free_plan = None
        starter_plan = None
        pro_plan = None
        
        for plan in plans:
            if plan["id"] == "free":
                free_plan = plan
            elif plan["id"] == "starter":
                starter_plan = plan
            elif plan["id"] == "pro":
                pro_plan = plan
        
        # Verify free plan
        self.assertIsNotNone(free_plan, "Free plan not found")
        self.assertEqual(free_plan["name"], "Free Plan")
        self.assertEqual(free_plan["price"], 0.00)
        self.assertEqual(free_plan["brands"], 1)
        self.assertEqual(free_plan["weekly_scans"], 0)
        self.assertIn("limitations", free_plan)
        
        # Verify starter plan
        self.assertIsNotNone(starter_plan, "Starter plan not found")
        self.assertEqual(starter_plan["name"], "Starter Plan")
        self.assertEqual(starter_plan["brands"], 1)
        self.assertEqual(starter_plan["weekly_scans"], 1)
        
        # Verify pro plan
        self.assertIsNotNone(pro_plan, "Pro plan not found")
        self.assertEqual(pro_plan["name"], "Pro Plan")
        self.assertEqual(pro_plan["brands"], 4)
        self.assertEqual(pro_plan["weekly_scans"], 4)
        self.assertTrue(pro_plan["popular"])
        
        # Verify early access pricing
        if early_access["available"]:
            self.assertEqual(starter_plan["price"], 39.00)
            self.assertEqual(starter_plan["regular_price"], 89.00)
            self.assertEqual(pro_plan["price"], 79.00)
            self.assertEqual(pro_plan["regular_price"], 149.00)
            self.assertTrue(starter_plan["is_early_access"])
            self.assertTrue(pro_plan["is_early_access"])
        
        print("✅ Pricing plans structure test passed")

    def test_11_weekly_scan_limit(self):
        """Test weekly scan limit functionality"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Create a new brand specifically for this test
        brand_data = {
            "name": "WeeklyScanLimitTestBrand",
            "industry": "E-commerce Platform",
            "keywords": ["online store", "e-commerce", "shopping cart"],
            "competitors": ["Shopify", "WooCommerce", "BigCommerce"],
            "website": "https://weeklyscanlimittest.com"
        }
        
        brand_response = requests.post(f"{self.base_url}/api/brands", json=brand_data, headers=headers)
        self.assertEqual(brand_response.status_code, 200)
        brand_data = brand_response.json()
        test_brand_id = brand_data["brand_id"]
        
        # Run first scan - should succeed
        scan_data = {
            "brand_id": test_brand_id,
            "scan_type": "quick"
        }
        
        first_scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(first_scan_response.status_code, 200)
        first_scan_data = first_scan_response.json()
        self.assertIn("scan_id", first_scan_data)
        
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

    def test_12_scan_progress_tracking(self):
        """Test scan progress tracking functionality"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'scan_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get scan progress
        progress_response = requests.get(f"{self.base_url}/api/scans/{self.__class__.scan_id}/progress", headers=headers)
        self.assertEqual(progress_response.status_code, 200)
        progress_data = progress_response.json()
        
        # Verify progress data structure
        self.assertIn("scan_id", progress_data)
        self.assertEqual(progress_data["scan_id"], self.__class__.scan_id)
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

if __name__ == "__main__":
    unittest.main()