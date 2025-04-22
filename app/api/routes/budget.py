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

@router.post("/advice", response_model=Dict[str, str])
async def get_budget_advice(
    current_user: User = Depends(get_current_user)
):
    """Triggers the Budget Planner agent to get personalized advice."""
    # TODO: Fetch relevant user data (transactions, goals if any)
    # TODO: Call the budget agent via the orchestrator
    # budget_advice = await run_budget_agent(user_id=current_user.id)
    # For now, return placeholder
    return {"advice": "Budget Agent Placeholder: Consider reducing spending on 'entertainment' by 15% this month."}

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