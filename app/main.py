from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
import json

from app.config import settings
from app.api.routes import auth, budget, investment, fraud
from app.models import database # Import database to access MongoDB connections

# MongoDB doesn't need tables/schemas created beforehand
# Collections will be created automatically when documents are inserted

# Custom JSON serialization for MongoDB ObjectId
class MongoJSONResponse(JSONResponse):
    """Custom JSON response class that properly serializes MongoDB ObjectId"""
    def render(self, content) -> bytes:
        # Custom JSON encoder for ObjectId
        def custom_encoder(obj):
            if isinstance(obj, ObjectId):
                return str(obj)
            return jsonable_encoder(obj)
            
        return json.dumps(
            content,
            default=custom_encoder,
            ensure_ascii=False,
            allow_nan=True,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

# --- Application Initialization --- #
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Personal Finance Assistant Agent Swarm API",
    default_response_class=MongoJSONResponse
)

# --- Middleware --- #

# CORS (Cross-Origin Resource Sharing)
# Allows the React frontend (running on a different port/domain) to communicate with the API.
# Adjust origins as needed for production.
origins = [
    "http://localhost",         # Allow local development
    "http://localhost:3000",    # Default React port
    # Add your frontend production domain here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Event Handlers --- # 
@app.on_event("startup")
async def startup_event():
    # Connect to MongoDB on startup
    await database.connect_to_mongodb()

@app.on_event("shutdown")
async def shutdown_event():
    # Close MongoDB connection on shutdown
    await database.close_mongodb_connection()

# --- API Routers --- #

# Include routers from the routes modules
# Use a prefix for versioning or grouping
api_prefix = "/api/v1"

app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["Authentication"])
app.include_router(budget.router, prefix=f"{api_prefix}/budget", tags=["Budget Planning"])
app.include_router(investment.router, prefix=f"{api_prefix}/investment", tags=["Investment Advice"])
app.include_router(fraud.router, prefix=f"{api_prefix}/fraud", tags=["Fraud Detection"])

# --- Root Endpoint --- #
@app.get("/", tags=["Root"])
def read_root():
    return {"message": f"Welcome to the {settings.app_title} API v{settings.app_version}"}