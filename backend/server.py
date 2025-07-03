import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import json

app = FastAPI(title="AI Brand Visibility API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
mongo_url = os.environ.get("MONGO_URL")
client = AsyncIOMotorClient(mongo_url)
db = client.ai_visibility_db

# Pydantic models
class BrandAnalysis(BaseModel):
    brand_name: str
    visibility_score: float
    total_mentions: int
    ai_platform: str
    last_updated: datetime

class CompetitorData(BaseModel):
    brand_name: str
    visibility_score: float
    total_mentions: int
    market_share: float

class QuestionAnalysis(BaseModel):
    question: str
    ai_platform: str
    mentions_brand: bool
    response_snippet: str
    ranking_position: Optional[int]
    competitors_mentioned: List[str]

class WeeklyRecommendation(BaseModel):
    title: str
    description: str
    priority: str
    category: str
    action_items: List[str]

# Mock data
mock_questions = [
    {
        "question": "What are the best wholesale management platforms for B2B businesses?",
        "ai_platform": "ChatGPT",
        "mentions_brand": True,
        "response_snippet": "Several excellent platforms include TradeGecko, Wholesale Helper, and Wholesale2B. Wholesale Helper offers comprehensive inventory management...",
        "ranking_position": 2,
        "competitors_mentioned": ["TradeGecko", "Wholesale2B"]
    },
    {
        "question": "How to streamline wholesale inventory management?",
        "ai_platform": "Gemini",
        "mentions_brand": False,
        "response_snippet": "Popular solutions include TradeGecko, Wholesale2B, and Cin7. These platforms offer automated inventory tracking...",
        "ranking_position": None,
        "competitors_mentioned": ["TradeGecko", "Wholesale2B", "Cin7"]
    },
    {
        "question": "Best software for wholesale distributors in 2024?",
        "ai_platform": "ChatGPT",
        "mentions_brand": True,
        "response_snippet": "Top recommendations include Wholesale Helper for comprehensive B2B management, TradeGecko for mid-market, and Cin7 for enterprise...",
        "ranking_position": 1,
        "competitors_mentioned": ["TradeGecko", "Cin7"]
    },
    {
        "question": "How to manage wholesale pricing strategies?",
        "ai_platform": "Gemini",
        "mentions_brand": False,
        "response_snippet": "Leading platforms like TradeGecko and Wholesale2B offer dynamic pricing features. Consider factors like volume discounts...",
        "ranking_position": None,
        "competitors_mentioned": ["TradeGecko", "Wholesale2B"]
    },
    {
        "question": "What wholesale platform integrates best with e-commerce?",
        "ai_platform": "ChatGPT",
        "mentions_brand": True,
        "response_snippet": "Wholesale Helper excels in e-commerce integration, particularly with Shopify and WooCommerce. Other options include TradeGecko...",
        "ranking_position": 1,
        "competitors_mentioned": ["TradeGecko"]
    }
]

mock_competitors = [
    {"brand_name": "Wholesale Helper", "visibility_score": 72.5, "total_mentions": 29, "market_share": 15.2},
    {"brand_name": "TradeGecko", "visibility_score": 89.2, "total_mentions": 45, "market_share": 28.7},
    {"brand_name": "Wholesale2B", "visibility_score": 65.8, "total_mentions": 31, "market_share": 18.9},
    {"brand_name": "Cin7", "visibility_score": 78.3, "total_mentions": 38, "market_share": 22.1},
    {"brand_name": "Ordoro", "visibility_score": 52.1, "total_mentions": 18, "market_share": 8.9},
    {"brand_name": "InStock", "visibility_score": 43.7, "total_mentions": 12, "market_share": 6.2}
]

mock_recommendations = [
    {
        "title": "Improve E-commerce Integration Content",
        "description": "Your competitors are dominating queries about e-commerce integration. Create comprehensive guides and case studies.",
        "priority": "High",
        "category": "Content Strategy",
        "action_items": [
            "Create detailed Shopify integration guide",
            "Publish WooCommerce success stories",
            "Optimize for 'e-commerce wholesale' keywords"
        ]
    },
    {
        "title": "Target Inventory Management Queries",
        "description": "You're missing 73% of inventory management related questions. Focus on this high-volume topic.",
        "priority": "Medium",
        "category": "SEO Optimization",
        "action_items": [
            "Create inventory management best practices content",
            "Engage in relevant Reddit discussions",
            "Guest post on inventory management blogs"
        ]
    },
    {
        "title": "Enhance Pricing Strategy Visibility",
        "description": "Zero mentions in pricing strategy queries. This is a key decision factor for wholesale businesses.",
        "priority": "High",
        "category": "Product Positioning",
        "action_items": [
            "Develop pricing strategy templates",
            "Create comparison charts vs competitors",
            "Sponsor pricing strategy webinars"
        ]
    }
]

# API Routes
@app.get("/api/dashboard")
async def get_dashboard():
    # Calculate overall visibility score
    total_questions = len(mock_questions)
    mentioned_questions = sum(1 for q in mock_questions if q["mentions_brand"])
    visibility_score = (mentioned_questions / total_questions) * 100
    
    # Calculate trends (mock data)
    previous_score = 68.2
    score_change = visibility_score - previous_score
    
    return {
        "brand_name": "Wholesale Helper",
        "visibility_score": visibility_score,
        "score_change": score_change,
        "total_questions_analyzed": total_questions,
        "questions_with_mentions": mentioned_questions,
        "questions_without_mentions": total_questions - mentioned_questions,
        "ai_platforms": ["ChatGPT", "Gemini"],
        "last_updated": datetime.now().isoformat(),
        "weekly_trend": [65.2, 68.1, 71.3, 69.8, 72.5, 70.1, visibility_score]
    }

@app.get("/api/competitors")
async def get_competitors():
    return {
        "competitors": mock_competitors,
        "market_position": 4,
        "total_competitors": len(mock_competitors)
    }

@app.get("/api/questions")
async def get_questions():
    return {
        "questions": mock_questions,
        "summary": {
            "total_analyzed": len(mock_questions),
            "with_mentions": sum(1 for q in mock_questions if q["mentions_brand"]),
            "without_mentions": sum(1 for q in mock_questions if not q["mentions_brand"]),
            "average_position": sum(q.get("ranking_position", 0) for q in mock_questions if q.get("ranking_position")) / sum(1 for q in mock_questions if q.get("ranking_position"))
        }
    }

@app.get("/api/recommendations")
async def get_recommendations():
    return {
        "recommendations": mock_recommendations,
        "total_recommendations": len(mock_recommendations),
        "high_priority": sum(1 for r in mock_recommendations if r["priority"] == "High"),
        "medium_priority": sum(1 for r in mock_recommendations if r["priority"] == "Medium"),
        "low_priority": sum(1 for r in mock_recommendations if r["priority"] == "Low")
    }

@app.get("/api/analytics")
async def get_analytics():
    # Platform breakdown
    chatgpt_mentions = sum(1 for q in mock_questions if q["ai_platform"] == "ChatGPT" and q["mentions_brand"])
    gemini_mentions = sum(1 for q in mock_questions if q["ai_platform"] == "Gemini" and q["mentions_brand"])
    
    return {
        "platform_breakdown": {
            "ChatGPT": {
                "mentions": chatgpt_mentions,
                "total_questions": sum(1 for q in mock_questions if q["ai_platform"] == "ChatGPT"),
                "visibility_rate": (chatgpt_mentions / sum(1 for q in mock_questions if q["ai_platform"] == "ChatGPT")) * 100
            },
            "Gemini": {
                "mentions": gemini_mentions,
                "total_questions": sum(1 for q in mock_questions if q["ai_platform"] == "Gemini"),
                "visibility_rate": (gemini_mentions / sum(1 for q in mock_questions if q["ai_platform"] == "Gemini")) * 100
            }
        },
        "monthly_trends": [
            {"month": "Oct 2024", "score": 65.2, "mentions": 22},
            {"month": "Nov 2024", "score": 68.1, "mentions": 25},
            {"month": "Dec 2024", "score": 71.3, "mentions": 28},
            {"month": "Jan 2025", "score": 69.8, "mentions": 27},
            {"month": "Feb 2025", "score": 72.5, "mentions": 29},
            {"month": "Mar 2025", "score": 70.1, "mentions": 29}
        ]
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)