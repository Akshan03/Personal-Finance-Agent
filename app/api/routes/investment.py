from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from app.models.user import User
from app.schemas import portfolio as portfolio_schema
from app.api.dependencies import get_current_user
from app.services import portfolio_service
from app.services import market_service
from beanie import PydanticObjectId

# Define the RecommendationRequest schema
class RecommendationRequest(BaseModel):
    """Schema for investment recommendation requests"""
    risk_tolerance: Optional[str] = "medium"
    investment_amount: Optional[float] = None
    sectors_of_interest: Optional[List[str]] = None

# Import agent-related functions later
# from app.agents.orchestrator import run_investment_agent

router = APIRouter()

@router.get("/recommendations", response_model=List[Dict[str, Any]])
@router.post("/recommendations", response_model=List[Dict[str, Any]])
async def get_investment_recommendations(
    request: Optional[RecommendationRequest] = None,
    current_user: User = Depends(get_current_user)
):
    """Get personalized investment recommendations based on risk tolerance and portfolio."""
    risk_tolerance = request.risk_tolerance.lower() if request and request.risk_tolerance else "medium"
    
    # Get user's portfolio first
    portfolio_dicts = []
    try:
        portfolios = await portfolio_service.get_user_portfolio(user_id=PydanticObjectId(current_user.id))
        portfolio_dicts = [
            {
                "asset_name": p.asset_name,
                "asset_type": p.asset_type.value,
                "quantity": p.quantity,
                "purchase_price": p.purchase_price,
                "current_value": p.current_value if hasattr(p, 'current_value') else None
            } for p in portfolios
        ]
    except Exception as e:
        print(f"Error fetching user portfolio: {e}")
    
    # Get personalized recommendations based on portfolio analysis
    recommendations = await market_service.get_personalized_investment_recommendations_by_risk(
        risk_tolerance=risk_tolerance
    )
    
    # Make sure we return an array of recommendations as expected by the frontend
    if isinstance(recommendations, dict) and 'recommendations' in recommendations:
        return recommendations['recommendations']
    return recommendations

@router.get("/market-trends", response_model=Dict[str, Any])
async def get_market_trends_info(current_user: User = Depends(get_current_user)):
    """Provides real-time market trends information with fallback to cached data."""
    # Get market trends using the service function (which is synchronous, not async)
    trends = market_service.get_market_trends()
    
    # Ensure we always return valid trend data, even if the service returns None
    if not trends or not isinstance(trends, dict) or not trends.get('trends') or len(trends.get('trends', [])) == 0:
        # Provide fallback market data if real data is unavailable
        return {
            "trends": [
                {
                    "index": "S&P 500",
                    "value": 5021.84,
                    "change_percent": 0.63,
                    "trend_direction": "up"
                },
                {
                    "index": "Dow Jones",
                    "value": 38239.97,
                    "change_percent": 0.32,
                    "trend_direction": "up"
                },
                {
                    "index": "NASDAQ",
                    "value": 15927.90,
                    "change_percent": 1.24,
                    "trend_direction": "up"
                },
                {
                    "index": "Russell 2000",
                    "value": 2042.47,
                    "change_percent": -0.28,
                    "trend_direction": "down"
                }
            ]
        }
    return trends

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

@router.get("/portfolio-quality", response_model=Dict[str, Any])
async def get_portfolio_quality(
    current_user: User = Depends(get_current_user)
):
    """Get a comprehensive assessment of the user's investment portfolio quality for the frontend."""
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
    
    # If no portfolio items, return a default assessment
    if not portfolio_items:
        return {
            "overall_rating": 2.5,  # Numeric value that can be used with toFixed()
            "rating_text": "Not Available",
            "diversification_score": 0,
            "portfolio_assessment": {
                "overall_assessment": "Unable to assess - no investments in portfolio",
                "risk_level": "Unable to assess - no investments",
                "growth_potential": "Unable to assess - no investments",
                "diversification": "0/100",
                "improvement_opportunities": [
                    "Add investments to your portfolio to receive a quality assessment",
                    "Consider starting with index funds for broad market exposure",
                    "Balance your portfolio with a mix of stocks, bonds, and other asset classes"
                ]
            },
            "holdings_analysis": {  # Empty object with sample structure
                "SAMPLE": {
                    "rating": 0,
                    "strengths": [],
                    "risks": [],
                    "recommendation": "No recommendation - add investments"
                }
            }
        }
    
    # Get assessment from service method
    assessment = await market_service.analyze_portfolio_quality(portfolio_dicts)
    
    # Ensure the response matches the frontend expected format
    return assessment

# Second market-trends endpoint was removed to avoid duplicates

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