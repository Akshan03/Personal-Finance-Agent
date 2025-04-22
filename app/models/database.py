from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import asyncio
from typing import Optional, List, Generator, AsyncGenerator
from contextlib import asynccontextmanager

from app.config import settings

# MongoDB client
mongo_client: Optional[AsyncIOMotorClient] = None

async def get_mongo_client() -> AsyncIOMotorClient:
    """Get MongoDB client instance."""
    global mongo_client
    if mongo_client is None:
        mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    return mongo_client

async def initialize_database():
    """Initialize database connections and register document models."""
    client = await get_mongo_client()
    
    # Import document models
    from app.models.user import User
    from app.models.transaction import Transaction
    from app.models.portfolio import Portfolio
    
    # Initialize Beanie with document models
    await init_beanie(
        database=client[settings.mongodb_database],
        document_models=[
            User,
            Transaction,
            Portfolio
        ]
    )

# Initialize DB at startup (called from main.py)
async def connect_to_mongodb():
    """Connect to MongoDB and initialize Beanie ODM."""
    try:
        await initialize_database()
        print(f"Connected to MongoDB: {settings.mongodb_uri}")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

# Shutdown DB connection at app shutdown (called from main.py)
async def close_mongodb_connection():
    """Close MongoDB connection."""
    global mongo_client
    if mongo_client is not None:
        mongo_client.close()
        mongo_client = None
        print("Closed MongoDB connection")

# Dependency for endpoints (non-async compatibility wrapper)
def get_db():
    """Legacy dependency to maintain compatibility with SQLAlchemy-style routes.
    
    This allows FastAPI routes to continue using Depends(get_db) pattern.
    In a new project, you would directly use the document models in endpoints.
    """
    # This is a dummy function that yields None to maintain the same interface
    # In MongoDB with Beanie, we use the document models directly
    yield None