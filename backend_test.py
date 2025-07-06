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
        
    def test_01_health_endpoint(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.base_url}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
        print("✅ Health endpoint test passed")

    def test_02_register_user(self):
        """Test user registration"""
        user_data = {
            "email": self.user_email,
            "password": self.user_password,
            "full_name": "Test User",
            "company": "Test Company",
            "website": "https://example.com"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("User created successfully", data["message"])
        print("✅ User registration test passed")

    def test_03_login_user(self):
        """Test user login"""
        # Create a new user specifically for login test
        test_email = f"login_test_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "Test@123456"
        
        # Register the user first
        user_data = {
            "email": test_email,
            "password": test_password,
            "full_name": "Login Test User",
            "company": "Test Company",
            "website": "https://example.com"
        }
        
        reg_response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        self.assertEqual(reg_response.status_code, 200)
        
        # Now try to login
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], test_email)
        
        # Save token for subsequent tests
        self.__class__.token = data["access_token"]
        print("✅ User login test passed")

    def test_04_get_user_info(self):
        """Test getting user info"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("email", data)
        self.assertIn("full_name", data)
        self.assertIn("company", data)
        print("✅ Get user info test passed")

    def test_05_create_brand(self):
        """Test creating a brand"""
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
        print("✅ Create brand test passed")
        
    def test_05b_create_second_brand(self):
        """Test creating a second brand for brand filtering tests"""
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
        
        # Create second brand
        brand_data = {
            "name": "SecondBrand",
            "industry": "E-commerce Platform",
            "keywords": ["online store", "e-commerce", "shopping cart"],
            "competitors": ["Shopify", "WooCommerce", "BigCommerce"],
            "website": "https://secondbrand.com"
        }
        
        response = requests.post(f"{self.base_url}/api/brands", json=brand_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brand_id", data)
        
        # Save second brand_id for subsequent tests
        self.__class__.second_brand_id = data["brand_id"]
        print("✅ Create second brand test passed")

    def test_06_get_brands(self):
        """Test getting brands"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/brands", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brands", data)
        self.assertTrue(len(data["brands"]) > 0)
        self.assertEqual(data["brands"][0]["name"], "TestBrand")
        print("✅ Get brands test passed")

    def test_07_get_brand_by_id(self):
        """Test getting a brand by ID"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/brands/{self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("brand", data)
        self.assertEqual(data["brand"]["name"], "TestBrand")
        print("✅ Get brand by ID test passed")

    def test_08_run_quick_scan(self):
        """Test running a quick scan with real OpenAI GPT-4o-mini integration"""
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
        self.assertIn("visibility_score", data)
        self.assertEqual(len(data["results"]), 5)  # Quick scan should have 5 results
        
        # Verify real OpenAI integration
        for result in data["results"]:
            self.assertEqual(result["platform"], "ChatGPT")
            self.assertEqual(result["model"], "gpt-4o-mini")
            self.assertIn("response", result)
            self.assertIn("brand_mentioned", result)
            self.assertIn("competitors_mentioned", result)
            self.assertIn("tokens_used", result)
            # Check that the response is not a mock response (should be longer and more varied)
            self.assertTrue(len(result["response"]) > 50)
            
        print("✅ Run quick scan with real OpenAI GPT-4o-mini integration test passed")

    def test_09_get_scan_results(self):
        """Test getting scan results"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/scans/{self.__class__.brand_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("scans", data)
        self.assertTrue(len(data["scans"]) > 0)
        print("✅ Get scan results test passed")
        
    def test_10_get_real_dashboard(self):
        """Test getting real dashboard data"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/dashboard/real", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("user", data)
        self.assertIn("overall_visibility", data)
        self.assertIn("total_queries", data)
        self.assertIn("total_mentions", data)
        self.assertIn("platform_breakdown", data)
        print("✅ Get real dashboard test passed")

    def test_11_verify_openai_integration(self):
        """Test to verify OpenAI API integration is working properly"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        # Run a single query to test OpenAI integration
        test_query = "What are the best project management tools for teams?"
        brand_name = "TestBrand"
        
        # Create a custom endpoint to test a single query
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.post(
            f"{self.base_url}/api/scans", 
            json={"brand_id": self.__class__.brand_id, "scan_type": "quick"},
            headers=headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify the results contain real AI responses
        self.assertIn("results", data)
        self.assertTrue(len(data["results"]) > 0)
        
        # Check the first result
        result = data["results"][0]
        self.assertEqual(result["platform"], "ChatGPT")
        self.assertEqual(result["model"], "gpt-4o-mini")
        
        # Verify this is a real response (not a mock)
        self.assertIn("response", result)
        self.assertTrue(len(result["response"]) > 100)  # Real responses are typically longer
        
        # Check for token usage tracking
        self.assertIn("tokens_used", result)
        self.assertTrue(result["tokens_used"] > 0)
        
        print("✅ OpenAI API integration verification test passed")

    def test_12_get_real_competitors(self):
        """Test getting real competitors data"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/competitors/real", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("competitors", data)
        self.assertIn("total_queries_analyzed", data)
        print("✅ Get real competitors test passed")
        
    def test_13_get_real_queries(self):
        """Test getting real queries data"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/queries/real", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("queries", data)
        self.assertIn("summary", data)
        print("✅ Get real queries test passed")
        
    def test_14_get_real_recommendations(self):
        """Test getting real recommendations data"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        response = requests.get(f"{self.base_url}/api/recommendations/real", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recommendations", data)
        self.assertIn("total_recommendations", data)
        print("✅ Get real recommendations test passed")
    
    def test_15_get_plans(self):
        """Test getting available plans"""
        response = requests.get(f"{self.base_url}/api/plans")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("plans", data)
        self.assertTrue(len(data["plans"]) >= 3)  # Should have at least 3 plans
        
        # Verify enterprise plan details
        enterprise_plan = None
        for plan in data["plans"]:
            if plan["id"] == "enterprise":
                enterprise_plan = plan
                break
                
        self.assertIsNotNone(enterprise_plan, "Enterprise plan not found")
        self.assertEqual(enterprise_plan["name"], "Enterprise")
        self.assertEqual(enterprise_plan["price"], 149.00)
        self.assertEqual(enterprise_plan["scans"], 1500)
        self.assertEqual(enterprise_plan["brands"], 10)
        print("✅ Get plans test passed")
    
    def test_16_upgrade_to_enterprise(self):
        """Test upgrading user to Enterprise plan"""
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
        upgrade_data = upgrade_response.json()
        self.assertIn("message", upgrade_data)
        self.assertIn("upgraded to enterprise plan", upgrade_data["message"].lower())
        print("✅ Upgrade to Enterprise plan test passed")
        
    def test_17_verify_enterprise_features(self):
        """Test verifying Enterprise plan features are active"""
        if not hasattr(self.__class__, 'token'):
            self.skipTest("Login test failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Check user info to verify plan and limits
        user_response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(user_response.status_code, 200)
        user_data = user_response.json()
        
        # Verify Enterprise plan is active
        self.assertEqual(user_data["plan"], "enterprise")
        self.assertEqual(user_data["scans_limit"], 1500)  # Enterprise plan has 1,500 scans
        self.assertTrue(user_data["subscription_active"])
        print("✅ Enterprise plan features verification test passed")
        
    def test_18_scan_usage_tracking(self):
        """Test real-time scan usage tracking"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get initial user info to check scan count
        initial_user_response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(initial_user_response.status_code, 200)
        initial_user_data = initial_user_response.json()
        initial_scans_used = initial_user_data["scans_used"]
        
        # Run a quick scan (should use 5 scans)
        scan_data = {
            "brand_id": self.__class__.brand_id,
            "scan_type": "quick"
        }
        
        scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(scan_response.status_code, 200)
        scan_data = scan_response.json()
        self.assertIn("scan_id", scan_data)
        self.assertIn("results", scan_data)
        self.assertEqual(len(scan_data["results"]), 5)  # Quick scan should have 5 results
        
        # Get updated user info to check scan count
        updated_user_response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(updated_user_response.status_code, 200)
        updated_user_data = updated_user_response.json()
        updated_scans_used = updated_user_data["scans_used"]
        
        # Verify scan count increased by 5 (quick scan uses 5 scans)
        self.assertEqual(updated_scans_used, initial_scans_used + 5)
        print(f"✅ Scan usage tracking test passed: Initial scans used: {initial_scans_used}, Updated scans used: {updated_scans_used}")
        
    def test_19_brand_filtering_dashboard(self):
        """Test brand filtering for dashboard endpoint"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id') or not hasattr(self.__class__, 'second_brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Run scans for both brands to generate data
        # First brand scan
        scan_data_1 = {
            "brand_id": self.__class__.brand_id,
            "scan_type": "quick"
        }
        scan_response_1 = requests.post(f"{self.base_url}/api/scans", json=scan_data_1, headers=headers)
        self.assertEqual(scan_response_1.status_code, 200)
        
        # Second brand scan
        scan_data_2 = {
            "brand_id": self.__class__.second_brand_id,
            "scan_type": "quick"
        }
        scan_response_2 = requests.post(f"{self.base_url}/api/scans", json=scan_data_2, headers=headers)
        self.assertEqual(scan_response_2.status_code, 200)
        
        # Wait a moment for data to be processed
        time.sleep(1)
        
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
        
        # Verify that filtered data is different from all data
        # The total queries should be different when filtered
        self.assertNotEqual(first_brand_data["total_queries"], second_brand_data["total_queries"], 
                           "Brand filtering not working - both brands show same data")
        
        # All brands data should include data from both brands
        self.assertGreaterEqual(all_brands_data["total_queries"], 
                              first_brand_data["total_queries"] + second_brand_data["total_queries"])
        
        print("✅ Brand filtering for dashboard endpoint test passed")
        
    def test_20_brand_filtering_competitors(self):
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
        # The competitors should be different for each brand
        first_brand_competitors = set([comp["name"] for comp in first_brand_data["competitors"]])
        second_brand_competitors = set([comp["name"] for comp in second_brand_data["competitors"]])
        
        # There should be some difference in competitors between brands
        self.assertNotEqual(first_brand_competitors, second_brand_competitors, 
                           "Brand filtering not working - both brands show same competitors")
        
        print("✅ Brand filtering for competitors endpoint test passed")
        
    def test_21_brand_filtering_queries(self):
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
        # The queries should be different for each brand
        first_brand_queries = set([q["query"] for q in first_brand_data["queries"]])
        second_brand_queries = set([q["query"] for q in second_brand_data["queries"]])
        
        # There should be some difference in queries between brands
        self.assertNotEqual(first_brand_queries, second_brand_queries, 
                           "Brand filtering not working - both brands show same queries")
        
        print("✅ Brand filtering for queries endpoint test passed")
        
    def test_22_brand_filtering_recommendations(self):
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
        
        # Verify that recommendations are returned for each brand
        self.assertIn("recommendations", first_brand_data)
        self.assertIn("recommendations", second_brand_data)
        
        # Verify that data points are different for each brand
        self.assertNotEqual(first_brand_data["data_points"], second_brand_data["data_points"], 
                           "Brand filtering not working - both brands show same data points")
        
        print("✅ Brand filtering for recommendations endpoint test passed")
        
    def test_23_scan_execution_and_usage_updates(self):
        """Test scan execution and usage updates"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get initial user info to check scan count
        initial_user_response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(initial_user_response.status_code, 200)
        initial_user_data = initial_user_response.json()
        initial_scans_used = initial_user_data["scans_used"]
        
        # Run a standard scan (should use 25 scans)
        scan_data = {
            "brand_id": self.__class__.brand_id,
            "scan_type": "standard"
        }
        
        scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(scan_response.status_code, 200)
        scan_data = scan_response.json()
        self.assertIn("scan_id", scan_data)
        self.assertIn("results", scan_data)
        self.assertIn("scans_used", scan_data)
        
        # Verify the scan results contain real AI responses
        for result in scan_data["results"]:
            self.assertEqual(result["platform"], "ChatGPT")
            self.assertEqual(result["model"], "gpt-4o-mini")
            self.assertIn("response", result)
            self.assertTrue(len(result["response"]) > 50)
            self.assertIn("brand_mentioned", result)
            self.assertIn("competitors_mentioned", result)
            self.assertIn("tokens_used", result)
        
        # Get updated user info to check scan count
        updated_user_response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(updated_user_response.status_code, 200)
        updated_user_data = updated_user_response.json()
        updated_scans_used = updated_user_data["scans_used"]
        
        # Verify scan count increased by the number of queries in the scan
        self.assertEqual(updated_scans_used, initial_scans_used + len(scan_data["results"]))
        print(f"✅ Scan execution and usage updates test passed: Initial scans used: {initial_scans_used}, Updated scans used: {updated_scans_used}")
        
    def test_24_user_data_consistency(self):
        """Test user data consistency after scanning"""
        if not hasattr(self.__class__, 'token') or not hasattr(self.__class__, 'brand_id'):
            self.skipTest("Previous tests failed, skipping this test")
            
        headers = {"Authorization": f"Bearer {self.__class__.token}"}
        
        # Get initial user info
        initial_user_response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(initial_user_response.status_code, 200)
        initial_user_data = initial_user_response.json()
        initial_scans_used = initial_user_data["scans_used"]
        
        # Run a quick scan
        scan_data = {
            "brand_id": self.__class__.brand_id,
            "scan_type": "quick"
        }
        
        scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        self.assertEqual(scan_response.status_code, 200)
        scan_data = scan_response.json()
        scans_used_in_response = scan_data["scans_used"]
        
        # Get updated user info
        updated_user_response = requests.get(f"{self.base_url}/api/auth/me", headers=headers)
        self.assertEqual(updated_user_response.status_code, 200)
        updated_user_data = updated_user_response.json()
        updated_scans_used = updated_user_data["scans_used"]
        
        # Verify scan count in user data matches the expected value
        self.assertEqual(updated_scans_used, initial_scans_used + scans_used_in_response)
        
        # Verify scan count in dashboard matches user data
        dashboard_response = requests.get(f"{self.base_url}/api/dashboard/real", headers=headers)
        self.assertEqual(dashboard_response.status_code, 200)
        dashboard_data = dashboard_response.json()
        self.assertEqual(dashboard_data["user"]["scans_used"], updated_scans_used)
        
        print(f"✅ User data consistency test passed: Scans used in scan response: {scans_used_in_response}, Updated user scans used: {updated_scans_used}")

if __name__ == "__main__":
    unittest.main()
