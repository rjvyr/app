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
        print(f"Early access total seats: {early_access['total_seats']}")
        print(f"Early access current users: {early_access['current_users']}")
        
        # Print all plans for verification
        print("\nPlans details:")
        for plan in plans:
            print(f"- {plan['id']}: {plan['name']}, Price: ${plan['price']}, Brands: {plan['brands']}, Weekly Scans: {plan['weekly_scans']}")
            if "regular_price" in plan:
                print(f"  Regular price: ${plan['regular_price']}")

if __name__ == "__main__":
    # Create a test suite with our tests
    suite = unittest.TestSuite()
    suite.addTest(AIBrandVisibilityAPITest('test_01_pricing_plans_structure'))
    
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