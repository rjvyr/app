import os
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

# Try to import OpenAI, fallback if not available
try:
    import openai
except ImportError:
    openai = None

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
    except jwt.JWTError:
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

def generate_scan_queries(brand_name: str, industry: str, keywords: List[str], competitors: List[str]) -> List[str]:
    """Generate AI scan queries based on brand information"""
    queries = []
    
    # Direct comparison queries
    queries.extend([
        f"What are the best {industry.lower()} platforms?",
        f"Top {industry.lower()} software in 2024?",
        f"Best {industry.lower()} tools for businesses?",
    ])
    
    # Keyword-based queries
    for keyword in keywords[:3]:  # Limit to first 3 keywords
        queries.extend([
            f"Best {keyword} software?",
            f"How to choose {keyword} platform?",
            f"Top {keyword} solutions?",
        ])
    
    # Competitor comparison queries
    for competitor in competitors[:2]:  # Limit to first 2 competitors
        queries.extend([
            f"{brand_name} vs {competitor} comparison?",
            f"Alternative to {competitor}?",
        ])
    
    # Problem-solving queries
    queries.extend([
        f"How to improve {industry.lower()} efficiency?",
        f"Best practices for {industry.lower()}?",
        f"Common {industry.lower()} challenges?",
    ])
    
    return queries[:25]  # Return max 25 queries

async def run_chatgpt_scan(query: str, brand_name: str) -> Dict[str, Any]:
    """Run a single scan through ChatGPT using GPT-4o-mini"""
    try:
        if not openai or not os.environ.get("OPENAI_API_KEY"):
            # Mock response for testing
            mock_responses = [
                f"When looking for the best {brand_name.lower()} solutions, consider {brand_name}, Competitor A, and Competitor B. {brand_name} offers excellent features...",
                f"For {query.lower()}, popular options include Competitor A, Competitor B, and others. Consider factors like pricing and features...",
                f"Top recommendations include {brand_name} for comprehensive features, Competitor A for simplicity, and Competitor B for enterprise needs..."
            ]
            
            answer = mock_responses[hash(query) % len(mock_responses)]
            print(f"Using mock response for query: {query}")
        else:
            print(f"Making real OpenAI API call for query: {query}")
            
            # Use the new OpenAI client format
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using GPT-4o-mini for cost efficiency
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides comprehensive answers about software and business tools. Provide detailed, informative responses that mention relevant brands and tools."},
                    {"role": "user", "content": query}
                ],
                max_tokens=300,
                temperature=0.7
            )
            answer = response.choices[0].message.content
            print(f"Real API response received for: {query}")
        
        # Check if brand is mentioned
        brand_mentioned = brand_name.lower() in answer.lower()
        
        # Find position if mentioned
        position = None
        if brand_mentioned:
            sentences = answer.split('.')
            for i, sentence in enumerate(sentences):
                if brand_name.lower() in sentence.lower():
                    position = i + 1
                    break
        
        # Extract competitor mentions (look for capitalized words that could be brand names)
        competitors_mentioned = []
        words = answer.split()
        for word in words:
            cleaned_word = word.strip('.,!?":;()[]')
            if (cleaned_word.istitle() and len(cleaned_word) > 3 and 
                cleaned_word not in ['Here', 'Some', 'Many', 'Most', 'These', 'Those', 'When', 'While', 'With', 'What', 'Where', 'They', 'This', 'That', 'Than', 'Then'] and
                not cleaned_word.endswith('ly')):
                competitors_mentioned.append(cleaned_word)
        
        # Remove duplicates and limit
        competitors_mentioned = list(dict.fromkeys(competitors_mentioned))[:5]
        
        return {
            "query": query,
            "platform": "ChatGPT",
            "model": "gpt-4o-mini",
            "response": answer,
            "brand_mentioned": brand_mentioned,
            "position": position,
            "competitors_mentioned": competitors_mentioned,
            "timestamp": datetime.utcnow(),
            "tokens_used": len(answer.split()) + len(query.split())  # Rough estimate
        }
        
    except Exception as e:
        print(f"Error in ChatGPT scan: {str(e)}")
        return {
            "query": query,
            "platform": "ChatGPT",
            "model": "gpt-4o-mini",
            "error": str(e),
            "brand_mentioned": False,
            "position": None,
            "competitors_mentioned": [],
            "timestamp": datetime.utcnow(),
            "tokens_used": 0
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
    queries = generate_scan_queries(
        brand["name"], 
        brand["industry"], 
        brand["keywords"], 
        brand["competitors"]
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
    
    # Run scans
    scan_results = []
    for query in queries:
        result = await run_chatgpt_scan(query, brand["name"])
        scan_results.append(result)
    
    # Save scan results
    scan_id = str(uuid.uuid4())
    scan_data = {
        "_id": scan_id,
        "user_id": current_user["_id"],
        "brand_id": scan_request.brand_id,
        "scan_type": scan_request.scan_type,
        "queries": queries,
        "results": scan_results,
        "scans_used": len(queries),
        "created_at": datetime.utcnow()
    }
    
    await db.scans.insert_one(scan_data)
    
    # Update user scan usage
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$inc": {"scans_used": len(queries)}}
    )
    
    # Update brand stats
    mentions = sum(1 for result in scan_results if result.get("brand_mentioned", False))
    visibility_score = (mentions / len(scan_results)) * 100 if scan_results else 0
    
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
    
    return {
        "scan_id": scan_id,
        "results": scan_results,
        "visibility_score": visibility_score,
        "scans_used": len(queries)
    }

@app.get("/api/scans/{brand_id}")
async def get_scan_results(brand_id: str, current_user: dict = Depends(get_current_user)):
    scans = await db.scans.find(
        {"brand_id": brand_id, "user_id": current_user["_id"]}
    ).sort("created_at", -1).limit(10).to_list(length=10)
    
    return {"scans": scans}

# Enhanced dashboard endpoints that use real data
@app.get("/api/dashboard/real")
async def get_real_dashboard(current_user: dict = Depends(get_current_user)):
    # Get user's brands
    brands = await db.brands.find({"user_id": current_user["_id"]}).to_list(length=10)
    
    # Get all scan results for this user
    all_scans = await db.scans.find({"user_id": current_user["_id"]}).to_list(length=1000)
    
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
    
    # Calculate overall visibility score
    overall_visibility = (total_mentions / total_queries * 100) if total_queries > 0 else 0
    
    # Calculate platform breakdown
    platform_breakdown = {}
    for platform, stats in platform_stats.items():
        if stats["total"] > 0:
            platform_breakdown[platform] = {
                "mentions": stats["mentions"],
                "total_questions": stats["total"],
                "visibility_rate": (stats["mentions"] / stats["total"]) * 100
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
async def get_real_competitors(current_user: dict = Depends(get_current_user)):
    # Get all scan results for this user
    all_scans = await db.scans.find({"user_id": current_user["_id"]}).to_list(length=1000)
    
    # Get user's brands to extract their competitors
    brands = await db.brands.find({"user_id": current_user["_id"]}).to_list(length=10)
    
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
    
    # Calculate visibility scores and create rankings
    competitor_rankings = []
    for name, data in competitor_mentions.items():
        if data["total_queries"] > 0:
            visibility_score = (data["mentions"] / data["total_queries"]) * 100
            competitor_rankings.append({
                "name": name,
                "visibility_score": visibility_score,
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
async def get_real_queries(current_user: dict = Depends(get_current_user)):
    # Get all scan results for this user
    all_scans = await db.scans.find({"user_id": current_user["_id"]}).sort("created_at", -1).to_list(length=100)
    
    # Get user's brands
    brands = await db.brands.find({"user_id": current_user["_id"]}).to_list(length=10)
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
async def get_real_recommendations(current_user: dict = Depends(get_current_user)):
    # Get all scan results and brands
    all_scans = await db.scans.find({"user_id": current_user["_id"]}).to_list(length=1000)
    brands = await db.brands.find({"user_id": current_user["_id"]}).to_list(length=10)
    
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