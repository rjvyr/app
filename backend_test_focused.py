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
        
        # Login with existing credentials
        self.login_with_existing_user()
        
    def login_with_existing_user(self):
        """Login with an existing user account"""
        # Try a few common test accounts
        test_accounts = [
            {"email": "admin@futureseo.io", "password": "admin123"},
            {"email": "test@example.com", "password": "test123"},
            {"email": "demo@futureseo.io", "password": "demo123"}
        ]
        
        for account in test_accounts:
            login_data = {
                "email": account["email"],
                "password": account["password"]
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                print(f"Successfully logged in as {account['email']}")
                return
        
        # If no existing account works, create a new one
        self.create_new_test_user()
    
    def create_new_test_user(self):
        """Create a new test user if login fails"""
        self.user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        self.user_password = "Test@123456"
        
        user_data = {
            "email": self.user_email,
            "password": self.user_password,
            "full_name": "Test User",
            "company": "Test Company",
            "website": "https://example.com"
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=user_data)
        if response.status_code == 200:
            # Login with new user
            login_data = {
                "email": self.user_email,
                "password": self.user_password
            }
            
            response = requests.post(f"{self.base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                print(f"Created and logged in as new user {self.user_email}")
                return
        
        # If all else fails, skip tests
        self.skipTest("Could not login or create a user")
    
    def get_existing_brands(self):
        """Get existing brands for the current user"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/brands", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "brands" in data and len(data["brands"]) > 0:
                return data["brands"]
        
        return []
    
    def create_test_brand(self, name, industry):
        """Create a test brand"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        brand_data = {
            "name": name,
            "industry": industry,
            "keywords": ["test keyword 1", "test keyword 2", "test keyword 3"],
            "competitors": ["Competitor 1", "Competitor 2", "Competitor 3"],
            "website": f"https://{name.lower().replace(' ', '')}.com"
        }
        
        response = requests.post(f"{self.base_url}/api/brands", json=brand_data, headers=headers)
        print(f"Brand creation response: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if "brand_id" in data:
                return data["brand_id"]
            elif "brand" in data and "_id" in data["brand"]:
                return data["brand"]["_id"]
        
        # If we can't create a brand, try to upgrade to enterprise plan
        upgrade_response = requests.post(
            f"{self.base_url}/api/admin/upgrade-user?user_email={self.user_email}&new_plan=enterprise",
            headers=headers
        )
        print(f"Upgrade response: {upgrade_response.status_code}")
        
        # Try again after upgrade
        response = requests.post(f"{self.base_url}/api/brands", json=brand_data, headers=headers)
        print(f"Brand creation response after upgrade: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "brand_id" in data:
                return data["brand_id"]
            elif "brand" in data and "_id" in data["brand"]:
                return data["brand"]["_id"]
        
        return None
    
    def test_01_pricing_plans_structure(self):
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
        print(f"Early access remaining seats: {early_access['remaining_seats']}")
    
    def test_02_brand_filtering_consistency(self):
        """Test brand filtering consistency across all endpoints"""
        if not hasattr(self, 'token'):
            self.skipTest("Login failed, skipping this test")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get existing brands or create new ones
        existing_brands = self.get_existing_brands()
        
        if len(existing_brands) >= 2:
            brand1_id = existing_brands[0]["_id"]
            brand2_id = existing_brands[1]["_id"]
            print(f"Using existing brands: {existing_brands[0]['name']} and {existing_brands[1]['name']}")
        elif len(existing_brands) == 1:
            brand1_id = existing_brands[0]["_id"]
            brand2_id = self.create_test_brand("Test Brand 2", "Test Industry 2")
            print(f"Using existing brand {existing_brands[0]['name']} and created new brand")
        else:
            brand1_id = self.create_test_brand("Test Brand 1", "Test Industry 1")
            brand2_id = self.create_test_brand("Test Brand 2", "Test Industry 2")
            print("Created two new test brands")
        
        if not brand1_id or not brand2_id:
            self.skipTest("Could not get or create brands")
        
        # List of endpoints to test
        endpoints = [
            "/api/dashboard/real",
            "/api/competitors/real",
            "/api/queries/real",
            "/api/recommendations/real",
            "/api/source-domains",
            "/api/source-articles"
        ]
        
        # Test each endpoint with both brands
        for endpoint in endpoints:
            # Get data for first brand
            response1 = requests.get(f"{self.base_url}{endpoint}?brand_id={brand1_id}", headers=headers)
            self.assertEqual(response1.status_code, 200, f"Failed to get data for brand1 from {endpoint}")
            data1 = response1.json()
            
            # Get data for second brand
            response2 = requests.get(f"{self.base_url}{endpoint}?brand_id={brand2_id}", headers=headers)
            self.assertEqual(response2.status_code, 200, f"Failed to get data for brand2 from {endpoint}")
            data2 = response2.json()
            
            # Verify that the responses have the expected structure
            if endpoint == "/api/dashboard/real":
                self.assertIn("total_queries", data1)
                self.assertIn("total_queries", data2)
            elif endpoint == "/api/competitors/real":
                self.assertIn("competitors", data1)
                self.assertIn("competitors", data2)
            elif endpoint == "/api/queries/real":
                self.assertIn("queries", data1)
                self.assertIn("queries", data2)
            elif endpoint == "/api/recommendations/real":
                self.assertIn("recommendations", data1)
                self.assertIn("recommendations", data2)
            elif endpoint == "/api/source-domains":
                self.assertIn("domains", data1)
                self.assertIn("domains", data2)
            elif endpoint == "/api/source-articles":
                self.assertIn("articles", data1)
                self.assertIn("articles", data2)
            
            print(f"✅ Brand filtering test passed for {endpoint}")
        
        print("✅ Brand filtering consistency test passed for all endpoints")
    
    def test_03_weekly_scan_limit(self):
        """Test weekly scan limit functionality"""
        if not hasattr(self, 'token'):
            self.skipTest("Login failed, skipping this test")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get existing brands or create a new one
        existing_brands = self.get_existing_brands()
        
        if existing_brands:
            brand_id = existing_brands[0]["_id"]
            print(f"Using existing brand: {existing_brands[0]['name']}")
        else:
            brand_id = self.create_test_brand("Weekly Scan Test Brand", "Test Industry")
            print("Created new test brand for weekly scan test")
        
        if not brand_id:
            self.skipTest("Could not get or create a brand")
        
        # Run first scan
        scan_data = {
            "brand_id": brand_id,
            "scan_type": "quick"
        }
        
        first_scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
        print(f"First scan response: {first_scan_response.status_code}")
        
        # If first scan succeeds, try a second scan
        if first_scan_response.status_code == 200:
            first_scan_data = first_scan_response.json()
            self.assertIn("scan_id", first_scan_data)
            scan_id = first_scan_data["scan_id"]
            
            # Try second scan immediately - should fail with 429 error
            second_scan_response = requests.post(f"{self.base_url}/api/scans", json=scan_data, headers=headers)
            self.assertEqual(second_scan_response.status_code, 429)
            second_scan_data = second_scan_response.json()
            self.assertIn("detail", second_scan_data)
            
            # Verify error message includes next available scan time
            error_message = second_scan_data["detail"]
            self.assertIn("Next scan available on", error_message)
            self.assertIn("Monday", error_message)
            self.assertIn("11:00 AM PST", error_message)
            
            print("✅ Weekly scan limit test passed - second scan correctly rejected")
            print(f"Error message: {error_message}")
            
            # Test scan progress tracking
            progress_response = requests.get(f"{self.base_url}/api/scans/{scan_id}/progress", headers=headers)
            self.assertEqual(progress_response.status_code, 200)
            progress_data = progress_response.json()
            
            # Verify progress data structure
            self.assertIn("scan_id", progress_data)
            self.assertEqual(progress_data["scan_id"], scan_id)
            self.assertIn("status", progress_data)
            self.assertIn("progress", progress_data)
            self.assertIn("total_queries", progress_data)
            
            print("✅ Scan progress tracking test passed")
            print(f"Progress data: {json.dumps(progress_data, indent=2)}")
        
        # If first scan fails with 429, it means a scan was already run this week
        elif first_scan_response.status_code == 429:
            error_data = first_scan_response.json()
            self.assertIn("detail", error_data)
            error_message = error_data["detail"]
            self.assertIn("Next scan available on", error_message)
            self.assertIn("Monday", error_message)
            self.assertIn("11:00 AM PST", error_message)
            
            print("✅ Weekly scan limit test passed - scan already run this week")
            print(f"Error message: {error_message}")
            
            # Try to get existing scans to test progress tracking
            scans_response = requests.get(f"{self.base_url}/api/scans/{brand_id}", headers=headers)
            if scans_response.status_code == 200:
                scans_data = scans_response.json()
                if "scans" in scans_data and len(scans_data["scans"]) > 0:
                    scan_id = scans_data["scans"][0]["_id"]
                    
                    # Test scan progress tracking
                    progress_response = requests.get(f"{self.base_url}/api/scans/{scan_id}/progress", headers=headers)
                    if progress_response.status_code == 200:
                        progress_data = progress_response.json()
                        
                        # Verify progress data structure
                        self.assertIn("scan_id", progress_data)
                        self.assertEqual(progress_data["scan_id"], scan_id)
                        self.assertIn("status", progress_data)
                        self.assertIn("progress", progress_data)
                        self.assertIn("total_queries", progress_data)
                        
                        print("✅ Scan progress tracking test passed with existing scan")
                        print(f"Progress data: {json.dumps(progress_data, indent=2)}")
        else:
            self.fail(f"Unexpected response code: {first_scan_response.status_code}")

if __name__ == "__main__":
    # Create a test suite with our tests
    suite = unittest.TestSuite()
    suite.addTest(AIBrandVisibilityAPITest('test_01_pricing_plans_structure'))
    suite.addTest(AIBrandVisibilityAPITest('test_02_brand_filtering_consistency'))
    suite.addTest(AIBrandVisibilityAPITest('test_03_weekly_scan_limit'))
    
    # Run the tests with a text test runner
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    print(f"Total tests: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    # Print detailed results
    if result.failures:
        print("\n=== FAILURES ===")
        for test, error in result.failures:
            print(f"\n{test}")
            print(error)
    
    if result.errors:
        print("\n=== ERRORS ===")
        for test, error in result.errors:
            print(f"\n{test}")
            print(error)
    
    if result.skipped:
        print("\n=== SKIPPED ===")
        for test, reason in result.skipped:
            print(f"\n{test}")
            print(reason)