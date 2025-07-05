#!/usr/bin/env python3
"""
Script to upgrade user to Enterprise plan for testing
"""
import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def upgrade_user_to_enterprise():
    # MongoDB connection
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client.ai_visibility_db
    
    try:
        # Update all users to enterprise plan for testing
        result = await db.users.update_many(
            {},  # Update all users
            {
                "$set": {
                    "plan": "enterprise",
                    "scans_limit": 1500,
                    "scans_used": 0,
                    "subscription_active": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        print(f"✅ Successfully upgraded {result.modified_count} user(s) to Enterprise plan!")
        print("🚀 All users now have:")
        print("   - Enterprise plan access")
        print("   - 1,500 scans per month")
        print("   - All features unlocked")
        print("   - Full futureseo.io testing capabilities")
        
    except Exception as e:
        print(f"❌ Error upgrading users: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(upgrade_user_to_enterprise())