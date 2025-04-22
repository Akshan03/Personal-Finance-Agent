from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from beanie import PydanticObjectId

from app.models.transaction import Transaction, TransactionCategory
from app.schemas import transaction as transaction_schema

async def get_user_transactions(user_id: PydanticObjectId, skip: int = 0, limit: int = 100) -> List[Transaction]:
    """Get transactions for a specific user with pagination."""
    # Use MongoDB aggregation to get paginated results
    transactions = await Transaction.find({"user_id": user_id}).skip(skip).limit(limit).to_list()
    return transactions

async def create_transaction(transaction: transaction_schema.TransactionCreate, user_id: PydanticObjectId) -> Transaction:
    """Create a new transaction for a user."""
    # Create the transaction document
    db_transaction = Transaction(
        user_id=user_id,
        amount=transaction.amount,
        category=transaction.category,
        description=transaction.description,
        timestamp=transaction.timestamp or datetime.utcnow(),
        is_fraudulent=False  # Default value, can be updated by fraud detection
    )
    # Save to database
    await db_transaction.insert()
    return db_transaction

def calculate_budget_summary(transactions: List[Transaction]) -> Dict[str, Any]:
    """Calculate a budget summary from a list of transactions."""
    if not transactions:
        return {
            "total_income": 0,
            "total_expenses": 0,
            "net_savings": 0,
            "savings_rate": 0,
            "category_breakdown": {}
        }
    
    # Use pandas for easier data manipulation
    df = pd.DataFrame([
        {
            "amount": t.amount,
            "category": t.category.value if hasattr(t.category, "value") else str(t.category),
            "timestamp": t.timestamp
        } for t in transactions
    ])
    
    # Separate income and expenses
    income = df[df["category"] == TransactionCategory.INCOME.value]
    expenses = df[df["category"] != TransactionCategory.INCOME.value]
    
    total_income = income["amount"].sum() if not income.empty else 0
    total_expenses = expenses["amount"].sum() if not expenses.empty else 0
    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
    
    # Calculate spending by category
    category_breakdown = {}
    if not expenses.empty:
        for category, group in expenses.groupby("category"):
            category_spending = group["amount"].sum()
            category_breakdown[category] = {
                "amount": category_spending,
                "percentage": (category_spending / total_expenses * 100) if total_expenses > 0 else 0
            }
    
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_savings": net_savings,
        "savings_rate": savings_rate,
        "category_breakdown": category_breakdown
    }

def analyze_spending_patterns(transactions: List[Transaction]) -> Dict[str, Any]:
    """Placeholder: Analyzes spending patterns (e.g., trends, anomalies)."""
    # TODO: Implement more sophisticated analysis (trends, averages, anomaly detection)
    if not transactions:
        return {"message": "Not enough data for spending pattern analysis."}
        
    summary = calculate_budget_summary(transactions)
    return {
        "message": "Basic spending summary generated.",
        "summary": summary
    }