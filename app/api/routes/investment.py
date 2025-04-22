from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models.database import get_db
from app.models.user import User
from app.schemas import portfolio as portfolio_schema
from app.api.dependencies import get_current_user
from app.services import market_service # Using market service for now
# Import agent-related functions later
# from app.agents.orchestrator import run_investment_agent

router = APIRouter()

@router.get("/recommendations", response_model=List[Dict[str, Any]])
def get_investment_recommendations(
    current_user: User = Depends(get_current_user)
):
    """Triggers the Investment Advisor agent to get low-risk recommendations."""
    # TODO: Fetch user profile, risk tolerance, goals etc.
    # TODO: Call the investment agent via orchestrator
    # recommendations = run_investment_agent(user_id=current_user.id, db=db)
    # For now, return mock recommendations from market service
    return market_service.get_low_risk_investment_options()

@router.get("/market-trends", response_model=Dict[str, Any])
def get_market_trends_info(current_user: User = Depends(get_current_user)):
    """Provides general market trends information."""
    # This might not need an agent, could directly use market service
    return market_service.get_market_trends()

@router.get("/portfolio", response_model=List[portfolio_schema.Portfolio])
def get_user_portfolio(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves the current user's investment portfolio."""
    # TODO: Implement portfolio retrieval logic in a service (e.g., finance_service or dedicated portfolio_service)
    # For now, return empty list
    # portfolios = portfolio_service.get_user_portfolio(db, user_id=current_user.id)
    # return portfolios
    return []

@router.post("/portfolio", response_model=portfolio_schema.Portfolio, status_code=status.HTTP_201_CREATED)
def add_portfolio_asset(
    asset: portfolio_schema.PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Adds a new asset to the user's portfolio."""
    # TODO: Implement portfolio creation logic in a service
    # new_asset = portfolio_service.create_portfolio_asset(db, asset=asset, user_id=current_user.id)
    # return new_asset
    # Placeholder response:
    return portfolio_schema.Portfolio(
        **asset.model_dump(),
        id=1, # Dummy ID
        user_id=current_user.id,
        current_value=asset.purchase_price * asset.quantity # Initial value
    )