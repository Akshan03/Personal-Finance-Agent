from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime

from app.models.user import User
from app.schemas import portfolio as portfolio_schema
from app.api.dependencies import get_current_user
from app.services import market_service, portfolio_service
from beanie import PydanticObjectId
# Import agent-related functions later
# from app.agents.orchestrator import run_investment_agent

router = APIRouter()

@router.get("/recommendations", response_model=List[Dict[str, Any]])
async def get_investment_recommendations(
    current_user: User = Depends(get_current_user),
    risk_tolerance: str = "low"
):
    """Get personalized investment recommendations based on portfolio analysis and market conditions."""
    # First, get the user's portfolio
    portfolio_items = await portfolio_service.get_user_portfolio(user_id=PydanticObjectId(current_user.id))
    
    # Convert portfolio models to dictionaries with string IDs for processing
    portfolio_dicts = []
    for item in portfolio_items:
        portfolio_dicts.append({
            "id": str(item.id),
            "user_id": str(item.user_id),
            "asset_name": item.asset_name,
            "asset_type": item.asset_type.value,
            "quantity": item.quantity,
            "purchase_price": item.purchase_price,
            "purchase_date": item.purchase_date,
            "current_value": item.current_value if item.current_value else item.purchase_price * item.quantity,
            "last_updated": item.last_updated
        })
    
    # Get personalized recommendations based on portfolio analysis
    return await market_service.get_personalized_investment_recommendations(
        user_id=str(current_user.id),
        risk_tolerance=risk_tolerance,
        portfolio_items=portfolio_dicts
    )

@router.get("/market-trends", response_model=Dict[str, Any])
async def get_market_trends_info(current_user: User = Depends(get_current_user)):
    """Provides real-time market trends information with fallback to cached data."""
    return await market_service.get_market_trends()

@router.get("/portfolio", response_model=List[portfolio_schema.Portfolio])
async def get_user_portfolio(
    current_user: User = Depends(get_current_user)
):
    """Retrieves the current user's investment portfolio."""
    # Get raw portfolios from service
    db_portfolios = await portfolio_service.get_user_portfolio(user_id=PydanticObjectId(current_user.id))
    
    # Convert MongoDB documents to response model (handling ObjectId conversion)
    return [
        portfolio_schema.Portfolio(
            id=str(item.id),
            user_id=str(item.user_id),
            asset_name=item.asset_name,
            asset_type=item.asset_type.value,
            quantity=item.quantity,
            purchase_price=item.purchase_price,
            purchase_date=item.purchase_date,
            current_value=item.current_value,
            last_updated=item.last_updated
        ) for item in db_portfolios
    ]

@router.get("/portfolio/assessment", response_model=Dict[str, Any])
async def get_portfolio_assessment(
    current_user: User = Depends(get_current_user)
):
    """Get a comprehensive assessment of the user's investment portfolio quality."""
    # Get the user's portfolio
    portfolio_items = await portfolio_service.get_user_portfolio(user_id=PydanticObjectId(current_user.id))
    
    # Convert portfolio models to dictionaries for processing
    portfolio_dicts = []
    for item in portfolio_items:
        portfolio_dicts.append({
            "id": str(item.id),
            "user_id": str(item.user_id),
            "asset_name": item.asset_name,
            "asset_type": item.asset_type.value,
            "quantity": item.quantity,
            "purchase_price": item.purchase_price,
            "purchase_date": item.purchase_date,
            "current_value": item.current_value if item.current_value else item.purchase_price * item.quantity,
            "last_updated": item.last_updated
        })
    
    # Get portfolio assessment
    return await market_service.analyze_portfolio_quality(portfolio_dicts)

@router.post("/portfolio", response_model=portfolio_schema.Portfolio, status_code=status.HTTP_201_CREATED)
async def add_portfolio_asset(
    asset: portfolio_schema.PortfolioCreate,
    current_user: User = Depends(get_current_user)
):
    """Adds a new asset to the user's portfolio."""
    # Create the portfolio item using our service
    new_asset = await portfolio_service.create_portfolio_asset(
        user_id=PydanticObjectId(current_user.id),
        asset_name=asset.asset_name,
        asset_type=asset.asset_type,
        quantity=asset.quantity,
        purchase_price=asset.purchase_price,
        purchase_date=asset.purchase_date,
        current_value=asset.purchase_price * asset.quantity  # Initial value calculation
    )
    
    # Convert to response model
    return portfolio_schema.Portfolio(
        id=str(new_asset.id),
        user_id=str(new_asset.user_id),
        asset_name=new_asset.asset_name,
        asset_type=new_asset.asset_type.value,
        quantity=new_asset.quantity,
        purchase_price=new_asset.purchase_price,
        purchase_date=new_asset.purchase_date,
        current_value=new_asset.current_value,
        last_updated=new_asset.last_updated
    )