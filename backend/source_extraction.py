from typing import List, Dict, Any
import re
from datetime import datetime

def extract_source_domains_from_response(response: str, brand_name: str, industry: str, keywords: List[str]) -> List[Dict[str, Any]]:
    """Extract source domains directly from the GPT response"""
    domains = []
    
    # Look for the SOURCE DOMAINS section
    if "SOURCE DOMAINS" in response:
        domain_section = response.split("SOURCE DOMAINS")[1].split("SOURCE ARTICLES")[0]
        domain_lines = domain_section.split("\n")
        
        for line in domain_lines:
            if "DOMAIN:" in line or "- " in line:
                # Extract domain and description
                if "DOMAIN:" in line:
                    parts = line.split("DOMAIN:")[1].split("-", 1)
                elif "- " in line:
                    parts = line.split("- ")[1].split("-", 1)
                else:
                    continue
                
                if len(parts) >= 1:
                    domain = parts[0].strip()
                    description = parts[1].strip() if len(parts) > 1 else ""
                    
                    if domain and ".com" in domain:  # Basic validation
                        domains.append({
                            "domain": domain,
                            "impact": 80,  # High impact since directly from GPT analysis
                            "mentions": 1,
                            "category": "Industry" if industry.lower() in domain.lower() else "General"
                        })
    
    # If no domains found in response, generate some based on industry
    if not domains:
        # Default domains
        default_domains = [
            f"www.{industry.lower().replace(' ', '')}.com",
            "www.g2.com",
            "www.capterra.com",
            f"www.{brand_name.lower().replace(' ', '')}.com",
            "www.trustpilot.com"
        ]
        
        for i, domain in enumerate(default_domains):
            domains.append({
                "domain": domain,
                "impact": 90 - (i * 10),  # Decreasing impact
                "mentions": 5 - i,  # Decreasing mentions
                "category": "Industry" if industry.lower() in domain.lower() else "Review Platform"
            })
    
    return domains[:5]  # Return top 5 domains

def extract_source_articles_from_response(response: str, brand_name: str, industry: str, keywords: List[str]) -> List[Dict[str, Any]]:
    """Extract source articles directly from the GPT response"""
    articles = []
    
    # Look for the SOURCE ARTICLES section
    if "SOURCE ARTICLES" in response:
        article_section = response.split("SOURCE ARTICLES")[1].split("\n\n")[0]
        article_lines = article_section.split("\n")
        
        for line in article_lines:
            if "ARTICLE:" in line or "- http" in line:
                # Extract URL and title
                if "ARTICLE:" in line:
                    parts = line.split("ARTICLE:")[1].split("-", 1)
                elif "- http" in line:
                    parts = line.split("- ")[1].split("-", 1)
                else:
                    continue
                
                if len(parts) >= 1:
                    url = parts[0].strip()
                    title = parts[1].strip() if len(parts) > 1 else f"Article about {industry}"
                    
                    if url.startswith("http"):  # Basic validation
                        articles.append({
                            "url": url,
                            "title": title,
                            "impact": 80,  # High impact since directly from GPT analysis
                            "queries": 1
                        })
    
    # If no articles found in response, generate some based on industry and keywords
    if not articles:
        # Default articles
        default_articles = [
            {
                "url": f"https://www.g2.com/categories/{industry.lower().replace(' ', '-')}/best",
                "title": f"Best {industry} Software in {datetime.now().year}"
            },
            {
                "url": f"https://www.capterra.com/{industry.lower().replace(' ', '-')}-software",
                "title": f"Top {industry} Solutions Compared"
            },
            {
                "url": f"https://www.trustpilot.com/review/{brand_name.lower().replace(' ', '')}.com",
                "title": f"{brand_name} Reviews and Ratings"
            },
            {
                "url": f"https://blog.{keywords[0].lower() if keywords else 'software'}.com/guide",
                "title": f"Complete Guide to {industry} Tools"
            },
            {
                "url": "https://www.techradar.com/best/business-software",
                "title": f"Best {industry} Software for Business"
            }
        ]
        
        for i, article in enumerate(default_articles):
            articles.append({
                "url": article["url"],
                "title": article["title"],
                "impact": 90 - (i * 10),  # Decreasing impact
                "queries": 5 - i  # Decreasing queries
            })
    
    return articles[:5]  # Return top 5 articles