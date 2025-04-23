from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.models.user import User
from app.schemas import transaction as transaction_schema
from app.api.dependencies import get_current_user
from app.services import finance_service
# Import agent-related functions later when implemented
# from app.agents.orchestrator import run_budget_agent

router = APIRouter()

@router.get("/summary", response_model=Dict[str, Any])
async def get_budget_summary(
    current_user: User = Depends(get_current_user)
):
    """Retrieves a summary of the user's budget (income vs expenses)."""
    transactions = await finance_service.get_user_transactions(user_id=current_user.id, limit=1000) # Get recent transactions
    if not transactions:
        return {"message": "No transaction data available to generate summary."}
    
    summary = finance_service.calculate_budget_summary(transactions)
    return summary

@router.post("/advice", response_model=Dict[str, Any])
async def get_budget_advice(
    current_user: User = Depends(get_current_user)
):
    """Generates comprehensive personalized budget advice based on user's transaction data."""
    # Fetch user's recent transactions
    transactions = await finance_service.get_user_transactions(user_id=current_user.id, limit=100)
    
    if not transactions:
        return {"advice": "We don't have enough transaction data to provide personalized advice yet. Start by adding some transactions."}
    
    # Get advanced spending analysis with fixed/discretionary breakdown and benchmarks
    analysis = finance_service.analyze_spending_patterns(transactions)
    
    # Generate comprehensive personalized advice
    advice_points = []
    insights = []
    recommendations = []
    
    # 1. Income analysis
    if analysis["summary"]["total_income"] <= 0:
        advice_points.append("You don't have any income transactions recorded. Consider adding your income sources to get a complete financial picture.")
    
    # 2. 50/30/20 Rule Analysis
    benchmarks = analysis["benchmarks"]
    fixed = analysis["fixed_expenses"]
    discretionary = analysis["discretionary_expenses"]
    summary = analysis["summary"]
    
    # Compare actual spending to 50/30/20 benchmarks
    if summary["total_income"] > 0:
        # Needs (50%)
        needs_percent = fixed["percentage_of_income"]
        if needs_percent > 50:
            insights.append(f"Your fixed expenses are {needs_percent:.1f}% of income, above the recommended 50%.")
            recommendations.append("Consider reviewing your housing and utilities costs for potential savings.")
        else:
            insights.append(f"Your fixed expenses are {needs_percent:.1f}% of income, within the recommended 50%.")
        
        # Wants (30%)
        wants_percent = discretionary["percentage_of_income"]
        if wants_percent > 30:
            insights.append(f"Your discretionary spending is {wants_percent:.1f}% of income, above the recommended 30%.")
            recommendations.append("Consider cutting back on non-essential purchases in categories like entertainment and shopping.")
        else:
            insights.append(f"Your discretionary spending is {wants_percent:.1f}% of income, within the recommended 30%.")
        
        # Savings (20%)
        savings_percent = summary["savings_rate"]
        if savings_percent < 20:
            insights.append(f"Your savings rate is {savings_percent:.1f}%, below the recommended 20%.")
            recommendations.append("Try to increase your savings rate by reducing expenses or increasing income.")
        else:
            insights.append(f"Your savings rate is {savings_percent:.1f}%, above the recommended 20%. Great job!")
    
    # 3. Category-specific insights
    for category, analysis_data in analysis["category_analysis"].items():
        # Only add advice for categories that are significantly outside benchmarks
        if analysis_data["status"] != "normal":
            insights.append(analysis_data["advice"])
            
            # Add category-specific recommendations
            if category == "housing" and analysis_data["status"] == "above":
                recommendations.append("Housing is your largest expense. Consider if refinancing, roommates, or downsizing could help.")
            elif category == "food" and analysis_data["status"] == "above":
                recommendations.append("Try meal planning and cooking at home more often to reduce food expenses.")
            elif category == "transport" and analysis_data["status"] == "above":
                recommendations.append("Consider using public transportation, carpooling, or combining trips to save on transportation costs.")
            elif category == "shopping" and analysis_data["status"] == "above":
                recommendations.append("Try implementing a 24-hour rule before making non-essential purchases to reduce impulse buying.")
            elif category in ["savings", "investment"] and analysis_data["status"] == "below":
                recommendations.append("Set up automatic transfers to your savings or investment accounts to build your financial security.")
    
    # Combine all advice
    advice_points.extend(insights)
    advice_points.extend(recommendations)
    
    return {
        "summary": analysis["summary"],
        "insights": insights,
        "recommendations": recommendations,
        "fixed_vs_discretionary": {
            "fixed": fixed,
            "discretionary": discretionary
        },
        "benchmarks": benchmarks,
        "category_analysis": analysis["category_analysis"]
    }

@router.post("/transactions", response_model=transaction_schema.Transaction, status_code=status.HTTP_201_CREATED)
async def add_transaction(
    transaction: transaction_schema.TransactionCreate,
    current_user: User = Depends(get_current_user)
):
    """Adds a new transaction record for the current user."""
    # The user_id comes from the authenticated user
    return await finance_service.create_transaction(transaction=transaction, user_id=current_user.id)

@router.get("/transactions", response_model=List[transaction_schema.Transaction])
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Lists transactions for the current user."""
    transactions = await finance_service.get_user_transactions(user_id=current_user.id, skip=skip, limit=limit)
    return transactions