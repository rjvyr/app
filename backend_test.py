import requests
import unittest
import json
from datetime import datetime

class AIBrandVisibilityAPITest(unittest.TestCase):
    def setUp(self):
        # Get the backend URL from the frontend .env file
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    self.base_url = line.strip().split('=')[1].strip('"\'')
                    break
        
        print(f"Using backend URL: {self.base_url}")
        
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = requests.get(f"{self.base_url}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
        print("✅ Health endpoint test passed")

    def test_dashboard_endpoint(self):
        """Test the dashboard endpoint"""
        response = requests.get(f"{self.base_url}/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify required fields
        self.assertEqual(data["brand_name"], "Wholesale Helper")
        self.assertIn("visibility_score", data)
        self.assertIn("score_change", data)
        self.assertIn("total_questions_analyzed", data)
        self.assertIn("questions_with_mentions", data)
        self.assertIn("questions_without_mentions", data)
        self.assertIn("ai_platforms", data)
        self.assertIn("last_updated", data)
        self.assertIn("weekly_trend", data)
        
        # Verify visibility score calculation
        self.assertAlmostEqual(data["visibility_score"], 60.0, delta=0.1)
        
        # Verify weekly trend data
        self.assertEqual(len(data["weekly_trend"]), 7)
        
        print("✅ Dashboard endpoint test passed")

    def test_competitors_endpoint(self):
        """Test the competitors endpoint"""
        response = requests.get(f"{self.base_url}/api/competitors")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify required fields
        self.assertIn("competitors", data)
        self.assertIn("market_position", data)
        self.assertIn("total_competitors", data)
        
        # Verify competitor data
        self.assertEqual(len(data["competitors"]), 6)
        self.assertEqual(data["market_position"], 4)
        
        # Verify Wholesale Helper is in the competitors list
        wholesale_helper = next((c for c in data["competitors"] if c["brand_name"] == "Wholesale Helper"), None)
        self.assertIsNotNone(wholesale_helper)
        self.assertAlmostEqual(wholesale_helper["visibility_score"], 72.5, delta=0.1)
        
        print("✅ Competitors endpoint test passed")

    def test_questions_endpoint(self):
        """Test the questions endpoint"""
        response = requests.get(f"{self.base_url}/api/questions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify required fields
        self.assertIn("questions", data)
        self.assertIn("summary", data)
        
        # Verify questions data
        self.assertEqual(len(data["questions"]), 5)
        
        # Verify summary data
        summary = data["summary"]
        self.assertEqual(summary["total_analyzed"], 5)
        self.assertEqual(summary["with_mentions"], 3)
        self.assertEqual(summary["without_mentions"], 2)
        
        # Verify average position calculation
        self.assertAlmostEqual(summary["average_position"], 4/3, delta=0.1)
        
        print("✅ Questions endpoint test passed")

    def test_recommendations_endpoint(self):
        """Test the recommendations endpoint"""
        response = requests.get(f"{self.base_url}/api/recommendations")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify required fields
        self.assertIn("recommendations", data)
        self.assertIn("total_recommendations", data)
        self.assertIn("high_priority", data)
        self.assertIn("medium_priority", data)
        
        # Verify recommendations data
        self.assertEqual(len(data["recommendations"]), 3)
        self.assertEqual(data["high_priority"], 2)
        self.assertEqual(data["medium_priority"], 1)
        
        # Verify recommendation structure
        recommendation = data["recommendations"][0]
        self.assertIn("title", recommendation)
        self.assertIn("description", recommendation)
        self.assertIn("priority", recommendation)
        self.assertIn("category", recommendation)
        self.assertIn("action_items", recommendation)
        
        print("✅ Recommendations endpoint test passed")

    def test_analytics_endpoint(self):
        """Test the analytics endpoint"""
        response = requests.get(f"{self.base_url}/api/analytics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify required fields
        self.assertIn("platform_breakdown", data)
        self.assertIn("monthly_trends", data)
        
        # Verify platform breakdown
        platforms = data["platform_breakdown"]
        self.assertIn("ChatGPT", platforms)
        self.assertIn("Gemini", platforms)
        
        # Verify ChatGPT data
        chatgpt = platforms["ChatGPT"]
        self.assertEqual(chatgpt["mentions"], 3)
        self.assertEqual(chatgpt["total_questions"], 3)
        self.assertAlmostEqual(chatgpt["visibility_rate"], 100.0, delta=0.1)
        
        # Verify Gemini data
        gemini = platforms["Gemini"]
        self.assertEqual(gemini["mentions"], 0)
        self.assertEqual(gemini["total_questions"], 2)
        self.assertAlmostEqual(gemini["visibility_rate"], 0.0, delta=0.1)
        
        # Verify monthly trends
        self.assertEqual(len(data["monthly_trends"]), 6)
        
        print("✅ Analytics endpoint test passed")

if __name__ == "__main__":
    unittest.main()