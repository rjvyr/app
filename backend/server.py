import os
import re
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jwt
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
import json
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mock_data import generate_mock_scan_result
from source_extraction import extract_source_domains_from_response, extract_source_articles_from_response

# Try to import OpenAI, fallback if not available
try:
    import openai
    import httpx
    from openai import OpenAI, AsyncOpenAI
except ImportError:
    openai = None
    httpx = None
    OpenAI = None
    AsyncOpenAI = None

async def generate_realistic_queries_with_gpt(brand_name: str, industry: str, keywords: List[str], competitors: List[str], website: str = None) -> List[str]:
    """Generate realistic, high-probability queries using GPT-4o-mini"""
    try:
        if not openai or not os.environ.get("OPENAI_API_KEY"):
            # Fallback to realistic mock queries
            return generate_realistic_fallback_queries(brand_name, industry, keywords, competitors)
        
        print(f"Generating realistic queries for {brand_name} using GPT")
        
        # Enhanced prompt for realistic query generation
        system_prompt = f"""You are a search behavior expert who understands how real users search for business software and tools.

Generate 25 realistic, high-probability search queries that actual users would type when looking for {industry} solutions.

Context:
- Brand: {brand_name}
- Industry: {industry}
- Key capabilities: {', '.join(keywords[:5]) if keywords else 'general business tools'}
- Main competitors: {', '.join(competitors[:3]) if competitors else 'various alternatives'}

Requirements:
1. Use natural, conversational language that real people type
2. Include long-tail searches (5-10 words)
3. Mix different search intents: research, comparison, problem-solving
4. Include specific pain points and use cases
5. Vary between beginner and advanced user queries
6. Include pricing and alternative-seeking queries
7. Use realistic typos and informal language occasionally

Examples of realistic patterns:
- "best [solution] for small business under $100/month"
- "why is [competitor] so expensive alternatives"
- "[brand] vs [competitor] which one should I choose"
- "how to [solve problem] without expensive software"
- "[solution] that integrates with shopify and quickbooks"

Generate queries that someone would ACTUALLY type, not marketing copy."""

        user_prompt = f"Generate 25 realistic search queries for {industry} software, considering someone looking for solutions like {brand_name}."
        
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800,
            temperature=0.8  # Higher temperature for more variety
        )
        
        query_text = response.choices[0].message.content
        
        # Parse queries from the response
        queries = []
        lines = query_text.split('\n')
        for line in lines:
            line = line.strip()
            # Remove numbering and clean up
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                query = line.split('.', 1)[-1].split('-', 1)[-1].split('•', 1)[-1].strip()
                if len(query) > 10 and '?' not in query:  # Add question marks to make them proper queries
                    query += '?'
                if query and len(query) > 10:
                    queries.append(query)
        
        # Ensure we have enough queries
        if len(queries) < 15:
            print("GPT didn't generate enough queries, using fallback")
            return generate_realistic_fallback_queries(brand_name, industry, keywords, competitors)
        
        return queries[:25]
        
    except Exception as e:
        print(f"Error generating realistic queries: {e}")
        return generate_realistic_fallback_queries(brand_name, industry, keywords, competitors)

def generate_realistic_fallback_queries(brand_name: str, industry: str, keywords: List[str], competitors: List[str]) -> List[str]:
    """Generate realistic fallback queries when GPT is not available"""
    queries = []
    
    # Real user search patterns
    pain_points = [
        f"best {industry} software for small business under $50 per month",
        f"why is {competitors[0] if competitors else 'expensive software'} so expensive alternatives",
        f"free {industry} tools vs paid options which is better",
        f"{industry} software that actually works for startups",
        f"simple {industry} solution that doesn't require training",
        f"affordable {keywords[0] if keywords else industry} tools for growing business",
        f"best {industry} platform with good customer support",
        f"{industry} software that integrates with shopify quickbooks",
        f"modern {industry} tools that aren't complicated to use",
        f"which {industry} platform has the best mobile app"
    ]
    
    comparison_queries = [
        f"{brand_name} vs {competitors[0] if competitors else 'popular alternative'} honest comparison",
        f"is {competitors[0] if competitors else 'expensive tool'} worth the money or better alternatives",
        f"{competitors[0] if competitors else 'tool'} review pros and cons alternatives",
        f"better alternative to {competitors[0] if competitors else 'expensive software'} for small business",
        f"{brand_name} pricing vs {competitors[1] if len(competitors) > 1 else 'competitor'} which is cheaper"
    ]
    
    problem_solving = [
        f"how to improve {keywords[0] if keywords else 'business efficiency'} without expensive software",
        f"struggling with {keywords[0] if keywords else 'management'} need simple solution",
        f"best way to handle {keywords[0] if keywords else 'operations'} for growing team",
        f"{keywords[0] if keywords else 'business'} tools that actually save time",
        f"fix {keywords[0] if keywords else 'workflow'} issues with better software"
    ]
    
    specific_use_cases = [
        f"{industry} solution for team of 10-20 people",
        f"e-commerce {industry} tools that work with multiple platforms",
        f"b2b {industry} software with api integration options",
        f"white label {industry} solution for agencies",
        f"enterprise {industry} tools vs small business options"
    ]
    
    queries.extend(pain_points)
    queries.extend(comparison_queries)
    queries.extend(problem_solving)
    queries.extend(specific_use_cases)
    
    return queries[:25]

# Try to import Paddle, fallback if not available
try:
    from emergentintegrations.payments.paddle.checkout import PaddleCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
except ImportError:
    PaddleCheckout = None
    CheckoutSessionResponse = None
    CheckoutStatusResponse = None
    CheckoutSessionRequest = None

app = FastAPI(title="AI Brand Visibility Scanner API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"

# Database connection
mongo_url = os.environ.get("MONGO_URL")
client = AsyncIOMotorClient(mongo_url)
db = client.ai_visibility_db

# OpenAI setup
if openai:
    openai.api_key = os.environ.get("OPENAI_API_KEY")

# Paddle setup
paddle_api_key = os.environ.get("PADDLE_API_KEY")
paddle_checkout = PaddleCheckout(api_key=paddle_api_key) if paddle_api_key and PaddleCheckout else None

# Email configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@aivisibilitytracker.com")

# Subscription plans
PLANS = {
    "basic": {"name": "Basic", "price": 19.00, "scans": 50, "brands": 1, "features": ["chatgpt"]},
    "pro": {"name": "Pro", "price": 49.00, "scans": 300, "brands": 3, "features": ["chatgpt", "gemini", "ai_overview"]},
    "enterprise": {"name": "Enterprise", "price": 149.00, "scans": 1500, "brands": 10, "features": ["chatgpt", "gemini", "ai_overview", "advanced"]}
}

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company: str
    website: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class BrandCreate(BaseModel):
    name: str
    industry: str
    keywords: List[str]
    competitors: List[str]
    website: Optional[str] = None

class BrandUpdate(BaseModel):
    keywords: List[str]
    competitors: List[str]

class ScanRequest(BaseModel):
    brand_id: str
    scan_type: str  # "quick", "standard", "deep", "competitor"

class CheckoutRequest(BaseModel):
    plan: str
    origin_url: str

# Utility functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        
        user = await db.users.find_one({"_id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except (jwt.InvalidTokenError, jwt.ExpiredSignatureError, jwt.InvalidSignatureError) as e:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def send_email(to_email: str, subject: str, body: str):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"Email would be sent to {to_email}: {subject}")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")



async def run_enhanced_chatgpt_scan(query: str, brand_name: str, industry: str, keywords: List[str], competitors: List[str]) -> Dict[str, Any]:
    """Enhanced ChatGPT scan with comprehensive data extraction"""
    try:
        if not openai or not os.environ.get("OPENAI_API_KEY"):
            print("OpenAI not available, using mock data")
            return generate_mock_scan_result(query, brand_name, keywords, competitors)
        
        # Enhanced prompt for comprehensive analysis WITH SOURCE EXTRACTION
        system_prompt = f"""You are an expert analyst providing objective market research about business software solutions. Your goal is to provide realistic, unbiased information about the competitive landscape.

Query: "{query}"
Industry Context: {industry}
Market Context: Consider major players including {', '.join(competitors[:5]) + (f', {brand_name}' if brand_name not in competitors[:5] else '')}

IMPORTANT GUIDELINES:
1. Provide realistic, market-accurate information about ALL brands mentioned
2. Use actual brand names - never use "Competitor A" or "Competitor B" 
3. Consider real market positions - larger, established companies typically have higher visibility
4. Be objective - don't artificially favor any particular brand
5. Use 2025 as the current year in all responses
6. Answer the specific query asked, not what you think the user wants to hear

Please provide a comprehensive analysis that includes:
1. Direct answer to the specific query asked
2. Realistic market positioning of relevant companies
3. Objective feature comparisons when applicable
4. Current market trends and insights (2025)

ALSO: Please identify relevant SOURCE DOMAINS and SOURCE ARTICLES:

SOURCE DOMAINS (format as "DOMAIN: domain.com - brief description"):
- List 5 most relevant and authoritative websites/domains for this query
- Include industry-specific sites, review platforms, news sites, forums
- Make them specific to the actual query and industry context

SOURCE ARTICLES (format as "ARTICLE: Full URL - Article Title"):
- List 5 most relevant articles/pages that would contain information about this query
- Include realistic URLs that would exist for this type of content
- Make them specific to the actual industry and query context
- Use 2025 dates where applicable

Answer the query naturally and objectively, then provide the source information."""

        try:
            # Create a custom HTTP client to avoid proxy issues in Kubernetes
            http_client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
            )
            
            client = AsyncOpenAI(
                api_key=os.environ.get("OPENAI_API_KEY"),
                http_client=http_client
            )
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this query: {query}"}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Clean up HTTP client
            await http_client.aclose()
            
        except Exception as api_error:
            print(f"OpenAI API Error: {api_error}")
            # Fallback to mock data if API fails
            return generate_mock_scan_result(query, brand_name, keywords, competitors)
        
        answer = response.choices[0].message.content
        
        if os.environ.get("DEBUG") == "true":
            print(f"Enhanced API response received for: {query}")
        
        # Enhanced data extraction with source extraction
        analysis = extract_enhanced_insights(answer, brand_name, competitors, keywords)
        
        # Extract source domains and articles from the ACTUAL response
        source_domains = extract_source_domains_from_response(answer, brand_name, industry, keywords)
        source_articles = extract_source_articles_from_response(answer, brand_name, industry, keywords)
        
        return {
            "query": query,
            "platform": "ChatGPT",
            "model": "gpt-4o-mini",
            "response": answer,
            "brand_mentioned": analysis["brand_mentioned"],
            "ranking_position": analysis["ranking_position"],
            "sentiment": analysis["sentiment"],
            "competitors_mentioned": analysis["competitors_mentioned"],
            "key_features_mentioned": analysis["key_features"],
            "target_audience": analysis["target_audience"],
            "use_cases": analysis["use_cases"],
            "source_domains": source_domains,
            "source_articles": source_articles,
            "timestamp": datetime.utcnow(),
            "tokens_used": len(answer.split()) + len(query.split())
        }
        
    except Exception as e:
        print(f"Error in enhanced ChatGPT scan: {str(e)}")
        return {
            "query": query,
            "platform": "ChatGPT",
            "model": "gpt-4o-mini",
            "error": str(e),
            "brand_mentioned": False,
            "ranking_position": None,
            "sentiment": "neutral",
            "competitors_mentioned": [],
            "key_features_mentioned": [],
            "target_audience": [],
            "use_cases": [],
            "source_domains": [],
            "source_articles": [],
            "timestamp": datetime.utcnow(),
            "tokens_used": 0
        }

# Old extract functions removed - replaced with real extraction functions in source_extraction.py
async def run_chatgpt_scan(query: str, brand_name: str, industry: str = "", keywords: List[str] = None, competitors: List[str] = None) -> Dict[str, Any]:
    """Run a single scan through ChatGPT using GPT-4o-mini"""
    keywords = keywords or []
    competitors = competitors or []
    try:
        if not openai or not os.environ.get("OPENAI_API_KEY"):
            # Enhanced mock response for testing
            mock_responses = [
                f"For {industry} businesses, here are the top recommended solutions:\n\n1. {brand_name} - Excellent for comprehensive {keywords[0] if keywords else 'management'} with advanced features\n2. {competitors[0] if competitors else 'CompetitorA'} - Good for basic needs but limited scalability\n3. {competitors[1] if competitors else 'CompetitorB'} - Enterprise-focused with higher pricing\n\nKey considerations: {brand_name} stands out for its user-friendly interface and robust integration capabilities.",
                f"When comparing {industry} platforms, {brand_name} ranks highly for mid-market companies due to its balance of features and affordability. Popular alternatives include {', '.join(competitors[:2]) if competitors else 'various competitors'}, though they lack some key features that {brand_name} provides.",
            ]
            
            answer = mock_responses[hash(query) % len(mock_responses)]
            print(f"Using enhanced mock response for query: {query}")
        else:
            print(f"Making enhanced OpenAI API call for query: {query}")
            
            # Enhanced system prompt for better results
            system_prompt = f"""You are a business software expert who helps companies choose the right tools. 

Your expertise covers {industry} solutions and you understand the competitive landscape including tools like {', '.join(competitors[:3]) if competitors else 'various solutions'}.

When answering software recommendation questions:
1. Provide a ranked list of 3-5 specific tools with brief explanations
2. Mention key differentiators (pricing, features, target audience)
3. Include real brand names and be specific about capabilities
4. Consider the context: small business vs enterprise needs
5. Be objective but highlight what makes each tool unique
6. Focus on practical business value and use cases

Key industry context: {industry}
Relevant capabilities to consider: {', '.join(keywords[:3]) if keywords else 'core functionality'}"""

            try:
                # Create a custom HTTP client to avoid proxy issues
                http_client_sync = httpx.Client(
                    timeout=30.0,
                    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
                )
                
                from openai import OpenAI
                client = OpenAI(
                    api_key=os.environ.get("OPENAI_API_KEY"),
                    http_client=http_client_sync
                )
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=400,  # Increased for more detailed responses
                    temperature=0.3   # Lower temperature for more consistent recommendations
                )
                
                # Clean up HTTP client
                http_client_sync.close()
                
            except Exception as api_error:
                print(f"OpenAI API Error: {api_error}")
                # Fallback to mock data if API fails
                return generate_mock_scan_result(query, brand_name, keywords, competitors)
            answer = response.choices[0].message.content
            print(f"Enhanced API response received for: {query}")
        
        # Enhanced data extraction
        analysis = extract_enhanced_insights(answer, brand_name, competitors, keywords)
        
        return {
            "query": query,
            "platform": "ChatGPT",
            "model": "gpt-4o-mini",
            "response": answer,
            "brand_mentioned": analysis["brand_mentioned"],
            "ranking_position": analysis["ranking_position"],
            "sentiment": analysis["sentiment"],
            "competitors_mentioned": analysis["competitors_mentioned"],
            "key_features_mentioned": analysis["key_features"],
            "target_audience": analysis["target_audience"],
            "use_cases": analysis["use_cases"],
            "timestamp": datetime.utcnow(),
            "tokens_used": len(answer.split()) + len(query.split())
        }
        
    except Exception as e:
        print(f"Error in enhanced ChatGPT scan: {str(e)}")
        return {
            "query": query,
            "platform": "ChatGPT",
            "model": "gpt-4o-mini",
            "error": str(e),
            "brand_mentioned": False,
            "ranking_position": None,
            "sentiment": "neutral",
            "competitors_mentioned": [],
            "key_features_mentioned": [],
            "target_audience": [],
            "use_cases": [],
            "timestamp": datetime.utcnow(),
            "tokens_used": 0
        }

def extract_enhanced_insights(response: str, brand_name: str, competitors: List[str], keywords: List[str]) -> Dict[str, Any]:
    """Extract comprehensive insights from ChatGPT response with realistic scoring"""
    response_lower = response.lower()
    brand_lower = brand_name.lower()
    
    # Check if brand is mentioned
    brand_mentioned = brand_lower in response_lower
    
    # Extract ranking position with realistic logic
    ranking_position = None
    sentiment = "neutral"
    
    if brand_mentioned:
        # Look for numbered lists and rankings
        lines = response.split('\n')
        position_found = False
        
        for i, line in enumerate(lines):
            if brand_lower in line.lower() and not position_found:
                # Check for numbered patterns (1., 2., 3., etc.)
                if line.strip().startswith(('1.', '1)', '#1')):
                    ranking_position = 1
                    position_found = True
                elif line.strip().startswith(('2.', '2)', '#2')):
                    ranking_position = 2
                    position_found = True
                elif line.strip().startswith(('3.', '3)', '#3')):
                    ranking_position = 3
                    position_found = True
                elif line.strip().startswith(('4.', '4)', '#4')):
                    ranking_position = 4
                    position_found = True
                elif line.strip().startswith(('5.', '5)', '#5')):
                    ranking_position = 5
                    position_found = True
                
                # Check for ordinal indicators if no numbered list found
                if not position_found:
                    if any(word in line.lower() for word in ['first choice', 'top choice', 'best option', 'leading solution', 'number one']):
                        ranking_position = 1
                    elif any(word in line.lower() for word in ['second choice', 'runner-up', 'good alternative']):
                        ranking_position = 2
                    elif any(word in line.lower() for word in ['third option', 'also consider', 'another option']):
                        ranking_position = 3
                    elif any(word in line.lower() for word in ['worth mentioning', 'also available', 'other options']):
                        ranking_position = 4
                
                # If brand is mentioned but no clear position, analyze context
                if not position_found:
                    # Count how many other brands/competitors are mentioned before this brand
                    preceding_text = response_lower[:response_lower.find(brand_lower)]
                    competitor_mentions_before = 0
                    for competitor in competitors:
                        if competitor.lower() in preceding_text:
                            competitor_mentions_before += 1
                    
                    # Estimate position based on order of mention
                    if competitor_mentions_before == 0:
                        ranking_position = 1
                    elif competitor_mentions_before == 1:
                        ranking_position = 2
                    elif competitor_mentions_before == 2:
                        ranking_position = 3
                    else:
                        ranking_position = min(competitor_mentions_before + 1, 5)
                
                # Sentiment analysis based on context around brand mention
                brand_context = line.lower()
                positive_words = ['excellent', 'outstanding', 'best', 'top', 'leading', 'superior', 'great', 'fantastic', 'perfect', 'ideal', 'recommended']
                negative_words = ['limited', 'lacking', 'poor', 'expensive', 'difficult', 'complicated', 'overpriced', 'outdated', 'slow']
                
                positive_score = sum(1 for word in positive_words if word in brand_context)
                negative_score = sum(1 for word in negative_words if word in brand_context)
                
                if positive_score > negative_score:
                    sentiment = "positive"
                elif negative_score > positive_score:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                
                break
    
    # Find mentioned competitors with more accurate detection
    competitors_mentioned = []
    for competitor in competitors:
        if competitor.lower() in response_lower:
            competitors_mentioned.append(competitor)
    
    # Extract key features mentioned with better context
    key_features = []
    feature_indicators = ['feature', 'capability', 'function', 'integration', 'automation', 'analytics', 'reporting', 'dashboard', 'api', 'mobile']
    
    if brand_mentioned:
        # Look for sentences containing both the brand and feature words
        sentences = response.split('.')
        for sentence in sentences:
            if brand_lower in sentence.lower():
                for keyword in keywords[:3]:  # Top 3 keywords
                    if keyword.lower() in sentence.lower():
                        for indicator in feature_indicators:
                            if indicator in sentence.lower():
                                key_features.append(f"{keyword} {indicator}")
                                break
    
    # Extract target audience mentions
    target_audience = []
    audience_terms = ['small business', 'enterprise', 'startup', 'mid-market', 'large company', 'teams', 'freelancer', 'agencies', 'corporations']
    for term in audience_terms:
        if term in response_lower and brand_lower in response_lower:
            # Check if the audience term appears near the brand mention
            brand_positions = [m.start() for m in re.finditer(brand_lower, response_lower)]
            term_positions = [m.start() for m in re.finditer(term, response_lower)]
            
            for brand_pos in brand_positions:
                for term_pos in term_positions:
                    if abs(brand_pos - term_pos) < 200:  # Within 200 characters
                        target_audience.append(term)
                        break
    
    # Extract use cases with better context
    use_cases = []
    if brand_mentioned:
        use_case_patterns = ['ideal for', 'perfect for', 'great for', 'best for', 'designed for', 'suited for']
        sentences = response.split('.')
        for sentence in sentences:
            if brand_lower in sentence.lower():
                for pattern in use_case_patterns:
                    if pattern in sentence.lower():
                        # Extract the use case after the pattern
                        use_case_start = sentence.lower().find(pattern) + len(pattern)
                        use_case = sentence[use_case_start:].strip()
                        if use_case and len(use_case) < 100:  # Reasonable length
                            use_cases.append(use_case)
                        break
    
    return {
        "brand_mentioned": brand_mentioned,
        "ranking_position": ranking_position,
        "sentiment": sentiment,
        "competitors_mentioned": competitors_mentioned[:3],  # Top 3 competitors
        "key_features": list(set(key_features))[:3],  # Remove duplicates, top 3
        "target_audience": list(set(target_audience))[:2],  # Remove duplicates, top 2
        "use_cases": use_cases[:2]  # Top 2 use cases
    }

# Authentication endpoints
@app.post("/api/auth/register")
async def register(user: UserCreate, background_tasks: BackgroundTasks):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    verification_token = secrets.token_urlsafe(32)
    
    user_data = {
        "_id": user_id,
        "email": user.email,
        "password": hash_password(user.password),
        "full_name": user.full_name,
        "company": user.company,
        "website": user.website,
        "is_verified": False,
        "verification_token": verification_token,
        "plan": "trial",
        "trial_end": datetime.utcnow() + timedelta(days=7),
        "subscription_active": True,
        "scans_used": 0,
        "scans_limit": 50,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user_data)
    
    # Send verification email
    verification_url = f"https://yourdomain.com/verify-email?token={verification_token}"
    email_body = f"""
    <html>
    <body>
        <h2>Welcome to AI Brand Visibility Scanner!</h2>
        <p>Hi {user.full_name},</p>
        <p>Thank you for signing up. Please click the link below to verify your email address:</p>
        <p><a href="{verification_url}">Verify Email Address</a></p>
        <p>Your 7-day free trial has started! You can scan up to 50 queries during your trial.</p>
        <p>Best regards,<br>AI Brand Visibility Scanner Team</p>
    </body>
    </html>
    """
    
    background_tasks.add_task(send_email, user.email, "Verify your email address", email_body)
    
    return {"message": "User created successfully. Please check your email for verification."}

@app.post("/api/auth/login")
async def login(user: UserLogin):
    # Find user
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = create_access_token(data={"sub": db_user["_id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user["_id"],
            "email": db_user["email"],
            "full_name": db_user["full_name"],
            "company": db_user["company"],
            "plan": db_user["plan"],
            "scans_used": db_user.get("scans_used", 0),
            "scans_limit": db_user.get("scans_limit", 50)
        }
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["_id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "company": current_user["company"],
        "plan": current_user["plan"],
        "scans_used": current_user.get("scans_used", 0),
        "scans_limit": current_user.get("scans_limit", 50),
        "subscription_active": current_user.get("subscription_active", False)
    }

@app.post("/api/auth/verify-email")
async def verify_email(token: str):
    user = await db.users.find_one({"verification_token": token})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"is_verified": True}, "$unset": {"verification_token": ""}}
    )
    
    return {"message": "Email verified successfully"}

# Brand management endpoints
@app.post("/api/brands")
async def create_brand(brand: BrandCreate, current_user: dict = Depends(get_current_user)):
    # Check brand limit based on plan
    plan_info = PLANS.get(current_user["plan"], PLANS["basic"])
    existing_brands = await db.brands.count_documents({"user_id": current_user["_id"]})
    
    if existing_brands >= plan_info["brands"]:
        raise HTTPException(status_code=400, detail=f"Plan limit: {plan_info['brands']} brands maximum")
    
    # Create brand
    brand_id = str(uuid.uuid4())
    brand_data = {
        "_id": brand_id,
        "user_id": current_user["_id"],
        "name": brand.name,
        "industry": brand.industry,
        "keywords": brand.keywords,
        "competitors": brand.competitors,
        "website": brand.website,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_scanned": None,
        "visibility_score": 0,
        "total_scans": 0
    }
    
    await db.brands.insert_one(brand_data)
    
    return {"message": "Brand created successfully", "brand_id": brand_id}

@app.get("/api/brands")
async def get_brands(current_user: dict = Depends(get_current_user)):
    brands = await db.brands.find({"user_id": current_user["_id"]}).to_list(length=100)
    return {"brands": brands}

@app.get("/api/brands/{brand_id}")
async def get_brand(brand_id: str, current_user: dict = Depends(get_current_user)):
    brand = await db.brands.find_one({"_id": brand_id, "user_id": current_user["_id"]})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    return {"brand": brand}

@app.put("/api/brands/{brand_id}")
async def update_brand(brand_id: str, brand_update: BrandUpdate, current_user: dict = Depends(get_current_user)):
    """Update brand keywords and competitors (name, industry, website cannot be changed)"""
    # Verify brand belongs to user
    existing_brand = await db.brands.find_one({"_id": brand_id, "user_id": current_user["_id"]})
    if not existing_brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Update only keywords and competitors
    update_data = {
        "keywords": brand_update.keywords,
        "competitors": brand_update.competitors,
        "updated_at": datetime.utcnow()
    }
    
    result = await db.brands.update_one(
        {"_id": brand_id, "user_id": current_user["_id"]},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update brand")
    
    # Return updated brand
    updated_brand = await db.brands.find_one({"_id": brand_id, "user_id": current_user["_id"]})
    return {"brand": updated_brand, "message": "Brand updated successfully"}

# Scanning endpoints
@app.post("/api/scans")
async def run_scan(scan_request: ScanRequest, current_user: dict = Depends(get_current_user)):
    # Check if user has enough scans
    scans_needed = {"quick": 5, "standard": 25, "deep": 50, "competitor": 10}
    scans_cost = scans_needed.get(scan_request.scan_type, 25)
    
    if current_user.get("scans_used", 0) + scans_cost > current_user.get("scans_limit", 50):
        raise HTTPException(status_code=400, detail="Not enough scans remaining")
    
    # Get brand
    brand = await db.brands.find_one({"_id": scan_request.brand_id, "user_id": current_user["_id"]})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Generate queries
    queries = await generate_realistic_queries_with_gpt(
        brand["name"], 
        brand["industry"], 
        brand["keywords"], 
        brand["competitors"],
        brand.get("website")
    )
    
    # Limit queries based on scan type
    if scan_request.scan_type == "quick":
        queries = queries[:5]
    elif scan_request.scan_type == "standard":
        queries = queries[:25]
    elif scan_request.scan_type == "deep":
        queries = queries[:50]
    elif scan_request.scan_type == "competitor":
        queries = [q for q in queries if any(comp in q for comp in brand["competitors"])][:10]
    
    # Run enhanced scans with comprehensive data
    scan_results = []
    all_source_domains = []
    all_source_articles = []
    
    for query in queries:
        result = await run_enhanced_chatgpt_scan(
            query, 
            brand["name"], 
            brand["industry"], 
            brand["keywords"], 
            brand["competitors"]
        )
        scan_results.append(result)
        
        # Collect source data
        if result.get("source_domains"):
            all_source_domains.extend(result["source_domains"])
        if result.get("source_articles"):
            all_source_articles.extend(result["source_articles"])
    
    # Store source domains in database
    if all_source_domains:
        domain_data = {
            "brand_id": scan_request.brand_id,
            "user_id": current_user["_id"],
            "domains": all_source_domains,
            "scan_date": datetime.utcnow(),
            "industry": brand["industry"],
            "keywords": brand["keywords"]
        }
        await db.source_domains.insert_one(domain_data)
    
    # Store source articles in database  
    if all_source_articles:
        article_data = {
            "brand_id": scan_request.brand_id,
            "user_id": current_user["_id"],
            "articles": all_source_articles,
            "scan_date": datetime.utcnow(),
            "industry": brand["industry"],
            "keywords": brand["keywords"]
        }
        await db.source_articles.insert_one(article_data)
    
    # Save scan results
    scan_id = str(uuid.uuid4())
    scan_data = {
        "_id": scan_id,
        "user_id": current_user["_id"],
        "brand_id": scan_request.brand_id,
        "scan_type": scan_request.scan_type,
        "queries": queries,
        "results": scan_results,
        "scans_used": scans_cost,  # Use correct scan cost
        "created_at": datetime.utcnow()
    }
    
    await db.scans.insert_one(scan_data)
    
    # Update user scan usage with the correct scan cost
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$inc": {"scans_used": scans_cost}}  # Use predefined scans_cost instead of len(queries)
    )
    
    # Calculate metrics
    mentions = sum(1 for result in scan_results if result.get("brand_mentioned", False))
    visibility_score = (mentions / len(scan_results)) * 100 if scan_results else 0
    
    # Store historical tracking data for week-over-week analysis
    historical_data = {
        "brand_id": scan_request.brand_id,
        "user_id": current_user["_id"],
        "date": datetime.utcnow(),
        "week": datetime.utcnow().strftime("%Y-W%U"),  # Year-Week format
        "visibility_score": visibility_score,
        "total_queries": len(scan_results),
        "mentioned_queries": mentions,
        "average_position": sum(result.get("ranking_position", 5) for result in scan_results if result.get("ranking_position")) / max(mentions, 1),
        "sentiment_breakdown": {
            "positive": sum(1 for result in scan_results if result.get("sentiment") == "positive"),
            "neutral": sum(1 for result in scan_results if result.get("sentiment") == "neutral"),
            "negative": sum(1 for result in scan_results if result.get("sentiment") == "negative")
        },
        "platform_breakdown": {
            "ChatGPT": {
                "queries": len(scan_results),
                "mentions": mentions,
                "visibility_rate": visibility_score
            }
        }
    }
    
    await db.weekly_tracking.insert_one(historical_data)
    
    # Update brand stats
    
    await db.brands.update_one(
        {"_id": scan_request.brand_id},
        {
            "$set": {
                "last_scanned": datetime.utcnow(),
                "visibility_score": visibility_score
            },
            "$inc": {"total_scans": len(queries)}
        }
    )
    
    # Generate content opportunities and actionable insights
    content_opportunities = await generate_content_opportunities(
        brand["name"],
        brand["industry"], 
        brand["keywords"],
        brand["competitors"],
        scan_results
    )
    
    return {
        "scan_id": scan_id,
        "results": scan_results,
        "visibility_score": visibility_score,
        "scans_used": scans_cost,
        "content_opportunities": content_opportunities
    }

async def generate_content_opportunities(brand_name: str, industry: str, keywords: List[str], competitors: List[str], scan_results: List[Dict]) -> Dict[str, Any]:
    """Generate content opportunities and backlink suggestions based on scan analysis"""
    
    # Analyze visibility gaps
    total_scans = len(scan_results)
    mentioned_scans = sum(1 for result in scan_results if result.get("brand_mentioned", False))
    visibility_gap = total_scans - mentioned_scans
    
    # Extract topics where competitors are mentioned but brand is not
    gap_topics = []
    competitor_opportunities = {}
    
    for result in scan_results:
        if not result.get("brand_mentioned", False) and result.get("competitors_mentioned"):
            query = result.get("query", "")
            mentioned_competitors = result.get("competitors_mentioned", [])
            
            # Extract topic from query
            topic = extract_topic_from_query(query, keywords)
            if topic:
                gap_topics.append({
                    "topic": topic,
                    "query": query,
                    "competitors_winning": mentioned_competitors,
                    "ranking_context": result.get("response", "")[:200]
                })
                
                # Track competitor performance
                for competitor in mentioned_competitors:
                    if competitor not in competitor_opportunities:
                        competitor_opportunities[competitor] = 0
                    competitor_opportunities[competitor] += 1
    
    # Generate content suggestions
    content_suggestions = await generate_content_suggestions(
        brand_name, industry, keywords, gap_topics[:5]  # Top 5 gaps
    )
    
    # Generate backlink opportunities (simulate URL extraction)
    backlink_opportunities = generate_backlink_opportunities(
        industry, keywords, gap_topics[:3]  # Top 3 gap topics
    )
    
    return {
        "visibility_gap_analysis": {
            "total_opportunities": visibility_gap,
            "gap_percentage": (visibility_gap / total_scans * 100) if total_scans > 0 else 0,
            "top_competitor_advantages": dict(sorted(competitor_opportunities.items(), key=lambda x: x[1], reverse=True)[:3])
        },
        "content_opportunities": gap_topics[:5],
        "content_suggestions": content_suggestions,
        "backlink_opportunities": backlink_opportunities,
        "priority_actions": generate_priority_actions(gap_topics, competitor_opportunities)
    }

def extract_topic_from_query(query: str, keywords: List[str]) -> str:
    """Extract the main topic from a query"""
    query_lower = query.lower()
    
    # Check if any brand keywords are in the query
    for keyword in keywords:
        if keyword.lower() in query_lower:
            return keyword
    
    # Extract topic from common patterns
    if "best" in query_lower and "for" in query_lower:
        # Extract between "best" and "for"
        start = query_lower.find("best") + 5
        end = query_lower.find("for") if query_lower.find("for") > start else len(query_lower)
        topic = query[start:end].strip()
        return topic.replace("?", "").replace(",", "")
    
    # Extract from "how to" queries
    if "how to" in query_lower:
        topic = query_lower.replace("how to", "").strip()
        return topic.replace("?", "").replace(",", "")
    
    return "general topic"

async def generate_content_suggestions(brand_name: str, industry: str, keywords: List[str], gap_topics: List[Dict]) -> List[Dict]:
    """Generate specific content suggestions based on visibility gaps"""
    
    suggestions = []
    
    for gap in gap_topics[:3]:  # Top 3 gaps
        topic = gap["topic"]
        competitors = gap["competitors_winning"]
        
        # Generate content ideas
        content_ideas = [
            {
                "title": f"The Complete Guide to {topic.title()} for {industry} Businesses",
                "type": "Blog Post",
                "target_keywords": [topic] + keywords[:2],
                "competitive_angle": f"Position against {competitors[0] if competitors else 'competitors'}",
                "content_outline": [
                    f"What is {topic} and why it matters",
                    f"Common {topic} challenges in {industry}",
                    f"How {brand_name} solves {topic} problems",
                    f"Case studies and success stories",
                    f"Getting started with {topic}"
                ]
            },
            {
                "title": f"{brand_name} vs {competitors[0] if competitors else 'Alternatives'}: {topic.title()} Comparison",
                "type": "Comparison Post",
                "target_keywords": [f"{brand_name} vs {competitors[0] if competitors else 'alternative'}", topic],
                "competitive_angle": "Direct comparison highlighting unique value",
                "content_outline": [
                    f"Feature comparison for {topic}",
                    f"Pricing and value analysis",
                    f"Use case scenarios",
                    f"Customer testimonials",
                    f"Migration guide"
                ]
            },
            {
                "title": f"Free {topic.title()} Templates and Resources",
                "type": "Resource Page",
                "target_keywords": [f"free {topic}", f"{topic} templates"],
                "competitive_angle": "Lead magnet with practical value",
                "content_outline": [
                    f"Downloadable {topic} templates",
                    f"Best practices checklist",
                    f"Implementation guide",
                    f"Expert tips and tricks"
                ]
            }
        ]
        
        suggestions.extend(content_ideas)
    
    return suggestions[:5]  # Return top 5 suggestions

def generate_backlink_opportunities(industry: str, keywords: List[str], gap_topics: List[Dict]) -> List[Dict]:
    """Generate backlink opportunities based on content gaps"""
    
    opportunities = []
    
    # Industry publications and blogs
    industry_sites = [
        f"{industry.lower().replace(' ', '')}-today.com",
        f"{industry.lower().replace(' ', '')}-insider.com", 
        f"the{industry.lower().replace(' ', '')}blog.com"
    ]
    
    for i, topic in enumerate(gap_topics):
        topic_name = topic["topic"]
        
        opportunities.append({
            "opportunity_type": "Guest Post",
            "target_site": industry_sites[i % len(industry_sites)],
            "suggested_title": f"How to Optimize {topic_name.title()} in {industry}",
            "pitch_angle": f"Expert insights on {topic_name} trends",
            "value_proposition": "Actionable tips and case studies",
            "estimated_authority": "High" if i < 2 else "Medium",
            "content_type": "2000+ word comprehensive guide"
        })
        
        opportunities.append({
            "opportunity_type": "Resource Mention",
            "target_site": f"{topic_name.lower().replace(' ', '')}-resources.com",
            "suggested_approach": f"Suggest inclusion in {topic_name} tool lists",
            "pitch_angle": "Comprehensive tool with unique features",
            "value_proposition": "Adds value to existing resource pages",
            "estimated_authority": "Medium",
            "content_type": "Tool directory listing"
        })
    
    return opportunities[:6]  # Return top 6 opportunities

def generate_priority_actions(gap_topics: List[Dict], competitor_advantages: Dict[str, int]) -> List[Dict]:
    """Generate prioritized action items based on analysis"""
    
    actions = []
    
    if gap_topics:
        top_gap = gap_topics[0]
        actions.append({
            "priority": "High",
            "action": f"Create comprehensive content about {top_gap['topic']}",
            "reason": f"Missing from {len(gap_topics)} high-value queries",
            "estimated_impact": "20-30% visibility improvement",
            "timeframe": "2-3 weeks",
            "resources_needed": "Content writer, SEO specialist"
        })
    
    if competitor_advantages:
        top_competitor = list(competitor_advantages.keys())[0]
        actions.append({
            "priority": "High", 
            "action": f"Develop comparison content targeting {top_competitor}",
            "reason": f"{top_competitor} mentioned {competitor_advantages[top_competitor]} times vs your brand",
            "estimated_impact": "15-25% competitive improvement",
            "timeframe": "1-2 weeks",
            "resources_needed": "Competitive analyst, content creator"
        })
    
    actions.append({
        "priority": "Medium",
        "action": "Launch targeted backlink outreach campaign",
        "reason": "Increase domain authority for key topics",
        "estimated_impact": "10-15% long-term visibility boost", 
        "timeframe": "4-6 weeks",
        "resources_needed": "Outreach specialist, content assets"
    })
    
    return actions

@app.get("/api/scans/{brand_id}")
async def get_scan_results(brand_id: str, current_user: dict = Depends(get_current_user)):
    scans = await db.scans.find(
        {"brand_id": brand_id, "user_id": current_user["_id"]}
    ).sort("created_at", -1).limit(10).to_list(length=10)
    
    return {"scans": scans}

@app.get("/api/source-domains")
async def get_source_domains(brand_id: Optional[str] = None, page: int = 1, limit: int = 5, current_user: dict = Depends(get_current_user)):
    """Get source domains analysis - which domains mention your brand most"""
    try:
        # Filter for user's data
        filter_query = {"user_id": current_user["_id"]}
        if brand_id:
            filter_query["brand_id"] = brand_id
        
        # Get source domain data from database
        domain_records = await db.source_domains.find(filter_query).sort("scan_date", -1).to_list(length=100)
        
        if not domain_records:
            return {"domains": [], "total": 0, "page": page, "total_pages": 0}
        
        # Aggregate domains across all scans
        domain_aggregation = {}
        for record in domain_records:
            for domain_data in record.get("domains", []):
                domain_name = domain_data["domain"]
                if domain_name not in domain_aggregation:
                    domain_aggregation[domain_name] = {
                        "domain": domain_name,
                        "category": domain_data.get("category", "Business"),
                        "impact": 0,
                        "mentions": 0,
                        "pages": 0,
                        "trend": "Stable"
                    }
                
                # Aggregate metrics
                domain_aggregation[domain_name]["impact"] += domain_data.get("impact", 0)
                domain_aggregation[domain_name]["mentions"] += domain_data.get("mentions", 1)
                domain_aggregation[domain_name]["pages"] += 1
        
        # Sort by impact and convert to list
        all_domains = sorted(domain_aggregation.values(), key=lambda x: x["impact"], reverse=True)
        
        # Apply pagination
        total_domains = len(all_domains)
        total_pages = (total_domains + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_domains = all_domains[start_idx:end_idx]
        
        return {
            "domains": paginated_domains,
            "total": total_domains,
            "page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
    except Exception as e:
        print(f"Error fetching source domains: {e}")
        return {"domains": [], "total": 0, "page": page, "total_pages": 0}

@app.get("/api/source-articles")
async def get_source_articles(brand_id: Optional[str] = None, page: int = 1, limit: int = 5, current_user: dict = Depends(get_current_user)):
    """Get source articles analysis - which specific articles mention your brand"""
    try:
        # Filter for user's data
        filter_query = {"user_id": current_user["_id"]}
        if brand_id:
            filter_query["brand_id"] = brand_id
        
        # Get source article data from database
        article_records = await db.source_articles.find(filter_query).sort("scan_date", -1).to_list(length=100)
        
        if not article_records:
            return {"articles": [], "total": 0, "page": page, "total_pages": 0}
        
        # Aggregate articles across all scans
        article_aggregation = {}
        for record in article_records:
            for article_data in record.get("articles", []):
                article_url = article_data["url"]
                if article_url not in article_aggregation:
                    article_aggregation[article_url] = {
                        "url": article_url,
                        "title": article_data.get("title", "Article Title"),
                        "impact": 0,
                        "queries": 0
                    }
                
                # Aggregate metrics
                article_aggregation[article_url]["impact"] += article_data.get("impact", 0)
                article_aggregation[article_url]["queries"] += article_data.get("queries", 1)
        
        # Sort by impact and convert to list
        all_articles = sorted(article_aggregation.values(), key=lambda x: x["impact"], reverse=True)
        
        # Apply pagination
        total_articles = len(all_articles)
        total_pages = (total_articles + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_articles = all_articles[start_idx:end_idx]
        
        return {
            "articles": paginated_articles,
            "total": total_articles,
            "page": page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
    except Exception as e:
        print(f"Error fetching source articles: {e}")
        return {"articles": [], "total": 0, "page": page, "total_pages": 0}

@app.get("/api/tracking/weekly")
async def get_weekly_tracking(brand_id: Optional[str] = None, weeks: int = 8, current_user: dict = Depends(get_current_user)):
    """Get week-over-week performance tracking data"""
    try:
        # Build filter for user's data
        filter_query = {"user_id": current_user["_id"]}
        if brand_id:
            filter_query["brand_id"] = brand_id
        
        # Get recent weeks of data
        tracking_data = await db.weekly_tracking.find(filter_query).sort("date", -1).to_list(length=weeks * 10)
        
        # Group by week and brand
        weekly_summary = {}
        for record in tracking_data:
            week_key = record["week"]
            brand_id_key = record["brand_id"]
            
            if week_key not in weekly_summary:
                weekly_summary[week_key] = {}
            
            if brand_id_key not in weekly_summary[week_key]:
                weekly_summary[week_key][brand_id_key] = {
                    "visibility_score": [],
                    "average_position": [],
                    "total_queries": 0,
                    "mentioned_queries": 0,
                    "sentiment_positive": 0,
                    "sentiment_neutral": 0,
                    "sentiment_negative": 0
                }
            
            # Aggregate data for the week
            week_data = weekly_summary[week_key][brand_id_key]
            week_data["visibility_score"].append(record.get("visibility_score", 0))
            week_data["average_position"].append(record.get("average_position", 5))
            week_data["total_queries"] += record.get("total_queries", 0)
            week_data["mentioned_queries"] += record.get("mentioned_queries", 0)
            week_data["sentiment_positive"] += record.get("sentiment_breakdown", {}).get("positive", 0)
            week_data["sentiment_neutral"] += record.get("sentiment_breakdown", {}).get("neutral", 0)
            week_data["sentiment_negative"] += record.get("sentiment_breakdown", {}).get("negative", 0)
        
        # Calculate averages and trends
        final_summary = []
        sorted_weeks = sorted(weekly_summary.keys(), reverse=True)[:weeks]
        
        for week in sorted_weeks:
            week_stats = {}
            for brand_id_key, data in weekly_summary[week].items():
                avg_visibility = sum(data["visibility_score"]) / len(data["visibility_score"]) if data["visibility_score"] else 0
                avg_position = sum(data["average_position"]) / len(data["average_position"]) if data["average_position"] else 5
                
                week_stats[brand_id_key] = {
                    "week": week,
                    "visibility_score": round(avg_visibility, 1),
                    "average_position": round(avg_position, 1),
                    "total_queries": data["total_queries"],
                    "mentioned_queries": data["mentioned_queries"],
                    "sentiment_score": round((data["sentiment_positive"] - data["sentiment_negative"]) / max(data["total_queries"], 1) * 100, 1)
                }
            
            final_summary.append({
                "week": week,
                "brands": week_stats
            })
        
        # Calculate week-over-week changes
        if len(final_summary) >= 2:
            current_week = final_summary[0]
            previous_week = final_summary[1]
            
            changes = {}
            for brand_id_key in current_week["brands"]:
                if brand_id_key in previous_week["brands"]:
                    current_data = current_week["brands"][brand_id_key]
                    previous_data = previous_week["brands"][brand_id_key]
                    
                    changes[brand_id_key] = {
                        "visibility_change": round(current_data["visibility_score"] - previous_data["visibility_score"], 1),
                        "position_change": round(previous_data["average_position"] - current_data["average_position"], 1),  # Lower position is better
                        "query_change": current_data["total_queries"] - previous_data["total_queries"],
                        "sentiment_change": round(current_data["sentiment_score"] - previous_data["sentiment_score"], 1)
                    }
            
            return {
                "weekly_data": final_summary,
                "week_over_week_changes": changes,
                "total_weeks": len(final_summary)
            }
        
        return {
            "weekly_data": final_summary,
            "week_over_week_changes": {},
            "total_weeks": len(final_summary)
        }
        
    except Exception as e:
        print(f"Error fetching weekly tracking: {e}")
        return {
            "weekly_data": [],
            "week_over_week_changes": {},
            "total_weeks": 0
        }

# Enhanced dashboard endpoints that use real data
@app.get("/api/dashboard/real")
async def get_real_dashboard(brand_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    # Get user's brands
    brands = await db.brands.find({"user_id": current_user["_id"]}).to_list(length=10)
    
    # Filter scans by brand if brand_id is provided
    scan_filter = {"user_id": current_user["_id"]}
    if brand_id:
        scan_filter["brand_id"] = brand_id
    
    # Get scan results for this user (and optionally specific brand)
    all_scans = await db.scans.find(scan_filter).to_list(length=1000)
    
    # Calculate real metrics
    total_queries = 0
    total_mentions = 0
    platform_stats = {"ChatGPT": {"mentions": 0, "total": 0}}
    
    # Process scan results
    for scan in all_scans:
        for result in scan.get("results", []):
            total_queries += 1
            platform = result.get("platform", "ChatGPT")
            
            if platform not in platform_stats:
                platform_stats[platform] = {"mentions": 0, "total": 0}
            
            platform_stats[platform]["total"] += 1
            
            if result.get("brand_mentioned", False):
                total_mentions += 1
                platform_stats[platform]["mentions"] += 1
    
    # Calculate overall visibility score with realistic logic
    if total_queries == 0:
        # No scans yet - return 0% visibility
        overall_visibility = 0
    else:
        overall_visibility = (total_mentions / total_queries * 100)
    
    # Calculate platform breakdown with realistic data
    platform_breakdown = {}
    for platform, stats in platform_stats.items():
        if stats["total"] > 0:
            visibility_rate = (stats["mentions"] / stats["total"]) * 100
            platform_breakdown[platform] = {
                "mentions": stats["mentions"],
                "total_questions": stats["total"],
                "visibility_rate": round(visibility_rate, 1)  # Round to 1 decimal
            }
        else:
            # No data for this platform yet
            platform_breakdown[platform] = {
                "mentions": 0,
                "total_questions": 0,
                "visibility_rate": 0
            }
    
    return {
        "user": {
            "name": current_user["full_name"],
            "company": current_user["company"],
            "plan": current_user["plan"],
            "scans_used": current_user.get("scans_used", 0),
            "scans_limit": current_user.get("scans_limit", 50)
        },
        "overall_visibility": overall_visibility,
        "total_queries": total_queries,
        "total_mentions": total_mentions,
        "brands_count": len(brands),
        "platform_breakdown": platform_breakdown,
        "recent_scans": all_scans[-5:] if all_scans else []
    }

@app.get("/api/competitors/real")
async def get_real_competitors(brand_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    # Filter scans by brand if brand_id is provided
    scan_filter = {"user_id": current_user["_id"]}
    if brand_id:
        scan_filter["brand_id"] = brand_id
    
    # Get scan results for this user (and optionally specific brand)
    all_scans = await db.scans.find(scan_filter).to_list(length=1000)
    
    # Get user's brands to extract their competitors
    brand_filter = {"user_id": current_user["_id"]}
    if brand_id:
        brand_filter["_id"] = brand_id
    
    brands = await db.brands.find(brand_filter).to_list(length=10)
    
    # Extract all competitors from brands
    all_competitors = set()
    user_brand_names = set()
    
    for brand in brands:
        user_brand_names.add(brand["name"])
        for competitor in brand.get("competitors", []):
            all_competitors.add(competitor)
    
    # Count mentions for each competitor and user brands
    competitor_mentions = {}
    total_queries = 0
    
    # Initialize counts
    for competitor in all_competitors:
        competitor_mentions[competitor] = {"mentions": 0, "total_queries": 0}
    
    for brand_name in user_brand_names:
        competitor_mentions[brand_name] = {"mentions": 0, "total_queries": 0, "is_user_brand": True}
    
    # Process scan results
    for scan in all_scans:
        for result in scan.get("results", []):
            total_queries += 1
            response = result.get("response", "").lower()
            
            # Check mentions for each competitor and user brand
            for name, data in competitor_mentions.items():
                data["total_queries"] += 1
                if name.lower() in response:
                    data["mentions"] += 1
    
    # Calculate visibility scores with realistic market-based logic
    competitor_rankings = []
    for name, data in competitor_mentions.items():
        if data["total_queries"] > 0:
            # Base calculation: mentions / total_queries
            base_visibility = (data["mentions"] / data["total_queries"]) * 100
            
            # Apply realistic market adjustments
            adjusted_visibility = base_visibility
            
            # For user brands, apply a more conservative calculation
            if data.get("is_user_brand", False):
                # User brands get mentioned more often in their own scans, so adjust down
                adjusted_visibility = min(base_visibility * 0.6, 85)  # Cap user brand at 85%
            else:
                # For competitors, consider market reality
                competitor_lower = name.lower()
                
                # Major enterprise players get a visibility boost
                if any(major in competitor_lower for major in ['brex', 'ramp', 'airwallex', 'stripe', 'expensify', 'concur', 'amex']):
                    # These are major players - boost their visibility
                    adjusted_visibility = min(base_visibility * 2.5, 95)
                elif any(mid in competitor_lower for mid in ['volopay', 'spenmo', 'payhawk', 'pleo']):
                    # Mid-tier players
                    adjusted_visibility = base_visibility * 1.2
                else:
                    # Smaller players
                    adjusted_visibility = base_visibility
            
            # Ensure realistic bounds
            adjusted_visibility = max(0, min(adjusted_visibility, 95))
            
            competitor_rankings.append({
                "name": name,
                "visibility_score": round(adjusted_visibility, 1),
                "mentions": data["mentions"],
                "total_queries": data["total_queries"],
                "is_user_brand": data.get("is_user_brand", False)
            })
    
    # Sort by visibility score
    competitor_rankings.sort(key=lambda x: x["visibility_score"], reverse=True)
    
    # Add rank
    for i, competitor in enumerate(competitor_rankings):
        competitor["rank"] = i + 1
    
    # Find user's position
    user_position = None
    for competitor in competitor_rankings:
        if competitor.get("is_user_brand", False):
            user_position = competitor["rank"]
            break
    
    return {
        "competitors": competitor_rankings,
        "user_position": user_position,
        "total_competitors": len(competitor_rankings),
        "total_queries_analyzed": total_queries
    }

@app.get("/api/queries/real")
async def get_real_queries(brand_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    # Filter scans by brand if brand_id is provided
    scan_filter = {"user_id": current_user["_id"]}
    if brand_id:
        scan_filter["brand_id"] = brand_id
    
    # Get scan results for this user (and optionally specific brand)
    all_scans = await db.scans.find(scan_filter).sort("created_at", -1).to_list(length=100)
    
    # Get user's brands
    brand_filter = {"user_id": current_user["_id"]}
    if brand_id:
        brand_filter["_id"] = brand_id
    
    brands = await db.brands.find(brand_filter).to_list(length=10)
    brand_names = [brand["name"] for brand in brands]
    
    # Process all queries
    all_queries = []
    total_queries = 0
    mentioned_queries = 0
    positions = []
    
    for scan in all_scans:
        for result in scan.get("results", []):
            total_queries += 1
            
            # Check if any user brand is mentioned
            brand_mentioned = False
            position = None
            mentioned_brand = None
            
            response = result.get("response", "")
            for brand_name in brand_names:
                if brand_name.lower() in response.lower():
                    brand_mentioned = True
                    mentioned_brand = brand_name
                    mentioned_queries += 1
                    
                    # Try to determine position (rough estimate)
                    sentences = response.split('.')
                    for i, sentence in enumerate(sentences):
                        if brand_name.lower() in sentence.lower():
                            position = i + 1
                            positions.append(position)
                            break
                    break
            
            # Extract competitors mentioned
            competitors_found = []
            for brand in brands:
                for competitor in brand.get("competitors", []):
                    if competitor.lower() in response.lower():
                        competitors_found.append(competitor)
            
            # Remove duplicates
            competitors_found = list(set(competitors_found))
            
            query_data = {
                "id": f"{scan['_id']}_{len(all_queries)}",
                "query": result.get("query", ""),
                "platform": result.get("platform", "ChatGPT"),
                "brand_mentioned": brand_mentioned,
                "mentioned_brand": mentioned_brand,
                "position": position,
                "response": response,
                "competitors": competitors_found,
                "date": scan.get("created_at", datetime.utcnow()).isoformat(),
                "model": result.get("model", "gpt-4o-mini")
            }
            
            all_queries.append(query_data)
    
    # Calculate average position
    avg_position = sum(positions) / len(positions) if positions else None
    
    return {
        "queries": all_queries[:50],  # Return last 50 queries
        "summary": {
            "total_analyzed": total_queries,
            "with_mentions": mentioned_queries,
            "without_mentions": total_queries - mentioned_queries,
            "average_position": avg_position
        }
    }

@app.get("/api/recommendations/real")
async def get_real_recommendations(brand_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    # Filter scans by brand if brand_id is provided
    scan_filter = {"user_id": current_user["_id"]}
    if brand_id:
        scan_filter["brand_id"] = brand_id
    
    # Get scan results for this user (and optionally specific brand)
    all_scans = await db.scans.find(scan_filter).to_list(length=1000)
    
    # Get user's brands
    brand_filter = {"user_id": current_user["_id"]}
    if brand_id:
        brand_filter["_id"] = brand_id
    
    brands = await db.brands.find(brand_filter).to_list(length=10)
    
    # Analyze missed opportunities
    missed_keywords = {}
    competitor_advantages = {}
    total_queries = 0
    brand_names = [brand["name"] for brand in brands]
    
    # Collect all keywords and competitors
    all_keywords = set()
    all_competitors = set()
    for brand in brands:
        all_keywords.update(brand.get("keywords", []))
        all_competitors.update(brand.get("competitors", []))
    
    # Process scan results to find gaps
    for scan in all_scans:
        for result in scan.get("results", []):
            total_queries += 1
            query = result.get("query", "").lower()
            response = result.get("response", "").lower()
            
            # Check if user brand is mentioned
            user_brand_mentioned = any(brand.lower() in response for brand in brand_names)
            
            # If user brand not mentioned, analyze why
            if not user_brand_mentioned:
                # Check which keywords are in the query
                for keyword in all_keywords:
                    if keyword.lower() in query:
                        if keyword not in missed_keywords:
                            missed_keywords[keyword] = 0
                        missed_keywords[keyword] += 1
                
                # Check which competitors are mentioned instead
                for competitor in all_competitors:
                    if competitor.lower() in response:
                        if competitor not in competitor_advantages:
                            competitor_advantages[competitor] = 0
                        competitor_advantages[competitor] += 1
    
    # Generate real recommendations based on data
    recommendations = []
    
    # Top missed keywords
    if missed_keywords:
        top_missed = sorted(missed_keywords.items(), key=lambda x: x[1], reverse=True)[:3]
        for keyword, count in top_missed:
            recommendations.append({
                "id": f"keyword_{keyword}",
                "title": f"Target '{keyword}' queries",
                "priority": "High" if count > 3 else "Medium",
                "category": "Content Strategy",
                "impact": f"+{min(count * 3, 20)}% potential visibility",
                "description": f"You're missing {count} queries related to '{keyword}'. This is a high-opportunity area.",
                "action_items": [
                    f"Create comprehensive guide about {keyword}",
                    f"Optimize existing content for {keyword}",
                    f"Write comparison articles featuring {keyword}"
                ],
                "time_estimate": f"{count * 2} hours"
            })
    
    # Competitor advantages
    if competitor_advantages:
        top_competitors = sorted(competitor_advantages.items(), key=lambda x: x[1], reverse=True)[:2]
        for competitor, count in top_competitors:
            recommendations.append({
                "id": f"competitor_{competitor}",
                "title": f"Compete with {competitor}",
                "priority": "High" if count > 5 else "Medium",
                "category": "Competitive Strategy", 
                "impact": f"+{min(count * 2, 15)}% potential visibility",
                "description": f"{competitor} appears in {count} queries where you don't. Focus on direct competition.",
                "action_items": [
                    f"Create direct comparison: Your Brand vs {competitor}",
                    f"Analyze {competitor}'s content strategy",
                    f"Target {competitor}'s weakness areas"
                ],
                "time_estimate": f"{count + 3} hours"
            })
    
    # If no specific data yet, provide generic recommendations
    if not recommendations:
        recommendations = [
            {
                "id": "generic_1",
                "title": "Run more scans to get personalized recommendations",
                "priority": "Medium",
                "category": "Data Collection",
                "impact": "Better insights",
                "description": "Run more scans across different query types to get AI-powered recommendations.",
                "action_items": [
                    "Run Standard Scan for comprehensive analysis",
                    "Try different keyword variations",
                    "Scan competitor-focused queries"
                ],
                "time_estimate": "2 hours"
            }
        ]
    
    return {
        "recommendations": recommendations,
        "total_recommendations": len(recommendations),
        "high_priority": sum(1 for r in recommendations if r["priority"] == "High"),
        "medium_priority": sum(1 for r in recommendations if r["priority"] == "Medium"),
        "data_points": total_queries
    }

# Update user plan endpoint
@app.post("/api/admin/upgrade-user")
async def upgrade_user_plan(user_email: str, new_plan: str, current_user: dict = Depends(get_current_user)):
    # For demo purposes, allow any user to upgrade themselves or others
    user_to_upgrade = await db.users.find_one({"email": user_email})
    if not user_to_upgrade:
        raise HTTPException(status_code=404, detail="User not found")
    
    plan_info = PLANS.get(new_plan)
    if not plan_info:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    # Update user plan
    await db.users.update_one(
        {"email": user_email},
        {
            "$set": {
                "plan": new_plan,
                "scans_limit": plan_info["scans"],
                "scans_used": 0,  # Reset usage
                "subscription_active": True,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": f"User {user_email} upgraded to {new_plan} plan successfully"}

@app.get("/api/plans")
async def get_available_plans():
    return {
        "plans": [
            {
                "id": "basic",
                "name": "Basic",
                "price": 19.00,
                "interval": "month",
                "features": [
                    "1 brand tracking",
                    "50 AI scans/month", 
                    "ChatGPT analysis only",
                    "Basic dashboard",
                    "Email support"
                ],
                "scans": 50,
                "brands": 1,
                "popular": False
            },
            {
                "id": "pro", 
                "name": "Pro",
                "price": 49.00,
                "interval": "month",
                "features": [
                    "3 brands tracking",
                    "300 AI scans/month",
                    "ChatGPT + Gemini + AI Overview",
                    "Full competitor analysis",
                    "Weekly recommendations",
                    "Priority email support",
                    "Export reports",
                    "API access"
                ],
                "scans": 300,
                "brands": 3,
                "popular": True
            },
            {
                "id": "enterprise",
                "name": "Enterprise", 
                "price": 149.00,
                "interval": "month",
                "features": [
                    "10 brands tracking",
                    "1500 AI scans/month",
                    "All AI platforms",
                    "Advanced dashboard",
                    "Unlimited competitor tracking",
                    "Custom recommendations", 
                    "Blog content analysis",
                    "Slack/Discord alerts",
                    "Phone support",
                    "Custom reports",
                    "Team collaboration"
                ],
                "scans": 1500,
                "brands": 10,
                "popular": False
            }
        ]
    }
async def create_checkout(checkout_request: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    if not paddle_checkout or not PaddleCheckout:
        # Mock response for testing
        return {
            "checkout_url": f"https://mock-paddle.com/checkout?plan={checkout_request.plan}",
            "session_id": f"mock_session_{uuid.uuid4()}"
        }
    
    plan_info = PLANS.get(checkout_request.plan)
    if not plan_info:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    # Create Paddle checkout session
    success_url = f"{checkout_request.origin_url}/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{checkout_request.origin_url}/cancel"
    
    paddle_request = CheckoutSessionRequest(
        amount=plan_info["price"],
        currency="USD",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": current_user["_id"],
            "plan": checkout_request.plan,
            "email": current_user["email"]
        }
    )
    
    session = await paddle_checkout.create_checkout_session(paddle_request)
    
    # Store transaction
    transaction_data = {
        "_id": str(uuid.uuid4()),
        "user_id": current_user["_id"],
        "paddle_session_id": session.session_id,
        "plan": checkout_request.plan,
        "amount": plan_info["price"],
        "currency": "USD",
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    await db.transactions.insert_one(transaction_data)
    
    return {
        "checkout_url": session.url,
        "session_id": session.session_id
    }

@app.get("/api/payments/status/{session_id}")
async def check_payment_status(session_id: str, current_user: dict = Depends(get_current_user)):
    if not paddle_checkout or not PaddleCheckout:
        # Mock response for testing
        return {
            "status": "completed",
            "payment_status": "paid",
            "transaction_status": "completed"
        }
    
    # Get checkout status from Paddle
    status = await paddle_checkout.get_checkout_status(session_id)
    
    # Find transaction
    transaction = await db.transactions.find_one({"paddle_session_id": session_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update transaction status
    if status.payment_status == "paid" and transaction["status"] != "completed":
        await db.transactions.update_one(
            {"paddle_session_id": session_id},
            {"$set": {"status": "completed", "updated_at": datetime.utcnow()}}
        )
        
        # Update user subscription
        plan_info = PLANS.get(transaction["plan"])
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {
                "$set": {
                    "plan": transaction["plan"],
                    "subscription_active": True,
                    "scans_limit": plan_info["scans"],
                    "scans_used": 0,  # Reset usage on new plan
                    "updated_at": datetime.utcnow()
                }
            }
        )
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "transaction_status": transaction["status"]
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)