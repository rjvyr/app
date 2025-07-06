from typing import List, Dict, Any
from datetime import datetime

def generate_mock_scan_result(query: str, brand_name: str, keywords: List[str], competitors: List[str]) -> Dict[str, Any]:
    """Generate mock scan result when OpenAI is not available"""
    mock_response = f"For {query}, {brand_name} appears to be a strong solution with key features like {', '.join(keywords[:2])}. Competitors like {', '.join(competitors[:2])} also offer similar capabilities."
    
    return {
        "query": query,
        "platform": "ChatGPT",
        "model": "gpt-4o-mini",
        "response": mock_response,
        "brand_mentioned": True,
        "ranking_position": 1,
        "sentiment": "positive",
        "competitors_mentioned": competitors[:2],
        "key_features_mentioned": keywords[:2],
        "target_audience": ["small business", "enterprise"],
        "use_cases": ["general business", "team collaboration"],
        "source_domains": [],
        "source_articles": [],
        "timestamp": datetime.utcnow(),
        "tokens_used": len(mock_response.split())
    }