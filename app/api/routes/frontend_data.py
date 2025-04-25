from typing import Dict, List, Any
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from app.models.user import User
from app.api.dependencies import get_current_user
from bson import ObjectId, json_util
import json
import random
from datetime import datetime

router = APIRouter()

# Sample investment recommendations matching the format from the example
SAMPLE_RECOMMENDATIONS = [
    {
        "symbol": "BND",
        "name": "Total Bond Market ETF",
        "type": "Bond Fund",
        "price": 78.50,
        "growth_potential": "3.1%",
        "risk_level": "Low",
        "description": "Broad exposure to US investment-grade bonds",
        "recommendation_reason": "Your portfolio lacks fixed income exposure for stability"
    },
    {
        "symbol": "VNQ",
        "name": "REIT Index Fund",
        "type": "Real Estate",
        "price": 85.75,
        "growth_potential": "5.5%",
        "risk_level": "Medium",
        "description": "Exposure to real estate investment trusts across various property sectors",
        "recommendation_reason": "Adding real estate can improve diversification and provide income"
    },
    {
        "symbol": "XLE",
        "name": "Energy Sector ETF",
        "type": "Sector Fund",
        "price": 92.25,
        "growth_potential": "6.5%",
        "risk_level": "Medium-High",
        "description": "Focused exposure to energy sector companies",
        "recommendation_reason": "Your portfolio would benefit from energy sector exposure"
    },
    {
        "symbol": "VXUS",
        "name": "International Equity Index Fund",
        "type": "Stock Fund",
        "price": 55.30,
        "growth_potential": "5.8%",
        "risk_level": "Medium",
        "description": "Exposure to developed international markets outside the U.S.",
        "recommendation_reason": "Adding international exposure would reduce geographic concentration"
    },
    {
        "symbol": "VTSMX",
        "name": "Three-Fund Core Portfolio",
        "type": "Portfolio Strategy",
        "price": 120.15,
        "growth_potential": "Varies by allocation",
        "risk_level": "Low",
        "description": "A simple portfolio of Total US Stock Market, International Stock, and Bond index funds",
        "recommendation_reason": "Your portfolio would benefit from a core diversified foundation"
    }
]

# Sample market trends matching the format from the example
SAMPLE_MARKET_TRENDS = {
    "market_summary": "Market sentiment is currently mixed with moderate volatility across major indices.",
    "current_sentiment_score": 0,
    "interest_rate_trend": "Stable with potential for modest decrease in coming months",
    "inflation_outlook": "gradually decreasing, expected to settle around 4.4% annually",
    "economic_indicators": {
        "gdp_growth": "2.0% annual rate",
        "unemployment": "3.9%",
        "consumer_confidence": "strong and declining"
    },
    "sector_performance": {
        "technology": "cooling after recent rally",
        "healthcare": "stable defensive performance",
        "financials": "sensitive to interest rate changes",
        "consumer_staples": "outperforming in defensive rotation",
        "energy": "volatile with focus on renewables",
        "utilities": "defensive in uncertain markets"
    },
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# Sample portfolio assessment matching the format from the example
SAMPLE_PORTFOLIO_ASSESSMENT = {
    "portfolio_assessment": "Your portfolio lacks diversification and is highly concentrated, which increases risk. Your portfolio is missing exposure to: fixed income, real estate, sector diversification. Your holdings in Apple Inc. are considered strong quality assets.",
    "holdings_analysis": [
        {
            "asset_name": "Apple Inc.",
            "asset_type": "stock",
            "value": 1755,
            "percentage_of_portfolio": 100,
            "performance": {
                "percent_change": "0.00%",
                "absolute_change": "$0.00 per share"
            },
            "evaluation": {
                "name": "Apple Inc.",
                "strength": "Strong financials, innovative products, loyal customer base",
                "risk": "Tech sector volatility, product cycle dependency",
                "rating": "Strong"
            }
        }
    ],
    "overall_rating": "Needs Improvement",
    "diversification_score": 0
}

# COMMENTED OUT - Using the real endpoints in investment.py instead
# @router.get("/investment/recommendations", response_model=List[Dict[str, Any]])
# @router.post("/investment/recommendations", response_model=List[Dict[str, Any]])
# async def get_investment_recommendations(
#     current_user: User = Depends(get_current_user),
#     risk_tolerance: str = "low"
# ):
#     """Get investment recommendations in the format needed by the frontend."""
#     # Add some randomness to the recommendations
#     recommendations = SAMPLE_RECOMMENDATIONS.copy()
#     
#     # Adjust prices slightly to simulate market movement
#     for rec in recommendations:
#         if isinstance(rec.get("price"), (int, float)):
#             rec["price"] = round(rec["price"] + random.uniform(-2, 2), 2)
#     
#     return recommendations

# COMMENTED OUT - Using the real endpoints in investment.py instead
# @router.get("/market/trends", response_model=Dict[str, Any])
# async def get_market_trends(
#     current_user: User = Depends(get_current_user)
# ):
#     """Get current market trends in the format needed by the frontend."""
#     # Update the last_updated timestamp
#     market_trends = SAMPLE_MARKET_TRENDS.copy()
#     market_trends["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     
#     return market_trends

# COMMENTED OUT - Using the real endpoints in investment.py instead
# @router.get("/investment/portfolio-quality", response_model=Dict[str, Any])
# async def get_portfolio_quality(
#     current_user: User = Depends(get_current_user)
# ):
#     """Get portfolio quality assessment in the format needed by the frontend."""
#     return SAMPLE_PORTFOLIO_ASSESSMENT
