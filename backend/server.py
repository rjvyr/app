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
import openai
from emergentintegrations.payments.paddle.checkout import PaddleCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

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
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Paddle setup
paddle_api_key = os.environ.get("PADDLE_API_KEY")
paddle_checkout = PaddleCheckout(api_key=paddle_api_key) if paddle_api_key else None

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
    """Run a single scan through ChatGPT"""
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides comprehensive answers about software and business tools."},
                {"role": "user", "content": query}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
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
        
        # Extract competitor mentions
        competitors_mentioned = []
        for word in answer.split():
            if word.istitle() and len(word) > 3 and word not in ['Here', 'Some', 'Many', 'Most', 'These', 'Those']:
                competitors_mentioned.append(word)
        
        return {
            "query": query,
            "platform": "ChatGPT",
            "response": answer,
            "brand_mentioned": brand_mentioned,
            "position": position,
            "competitors_mentioned": competitors_mentioned[:5],  # Limit to 5
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        return {
            "query": query,
            "platform": "ChatGPT",
            "error": str(e),
            "brand_mentioned": False,
            "position": None,
            "competitors_mentioned": [],
            "timestamp": datetime.utcnow()
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

# Dashboard endpoints
@app.get("/api/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    # Get user's brands
    brands = await db.brands.find({"user_id": current_user["_id"]}).to_list(length=10)
    
    # Get recent scans
    recent_scans = await db.scans.find(
        {"user_id": current_user["_id"]}
    ).sort("created_at", -1).limit(5).to_list(length=5)
    
    # Calculate overall stats
    total_scans = sum(brand.get("total_scans", 0) for brand in brands)
    avg_visibility = sum(brand.get("visibility_score", 0) for brand in brands) / len(brands) if brands else 0
    
    return {
        "user": {
            "name": current_user["full_name"],
            "company": current_user["company"],
            "plan": current_user["plan"],
            "scans_used": current_user.get("scans_used", 0),
            "scans_limit": current_user.get("scans_limit", 50)
        },
        "brands": brands,
        "recent_scans": recent_scans,
        "stats": {
            "total_scans": total_scans,
            "avg_visibility": avg_visibility,
            "active_brands": len(brands)
        }
    }

# Payment endpoints
@app.post("/api/payments/checkout")
async def create_checkout(checkout_request: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    if not paddle_checkout:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
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
    if not paddle_checkout:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
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