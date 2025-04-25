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
    
    # Convert ObjectIds to strings for proper serialization
    for transaction in transactions:
        # We need to convert the id to string in the model_dump method
        transaction_dict = transaction.model_dump()
        transaction_dict['id'] = str(transaction.id)
        transaction_dict['user_id'] = str(transaction.user_id)
        # Update transaction properties to match dictionary
        for key, value in transaction_dict.items():
            setattr(transaction, key, value)
            
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
    
    # Convert ObjectIds to strings for proper serialization
    transaction_dict = db_transaction.model_dump()
    transaction_dict['id'] = str(db_transaction.id)
    transaction_dict['user_id'] = str(db_transaction.user_id)
    
    # Update transaction properties
    for key, value in transaction_dict.items():
        setattr(db_transaction, key, value)
        
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
    # Ensure total_expenses is a positive value representing the sum of expense magnitudes
    total_expenses = abs(expenses["amount"].sum()) if not expenses.empty else 0
    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
    
    # Calculate spending by category
    category_breakdown = {}
    if not expenses.empty:
        # Ensure expense amounts in the breakdown are positive
        for category, group in expenses.groupby("category"):
            # Calculate the sum of negative amounts, then take the absolute value
            category_spending = abs(group["amount"].sum())
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

def classify_fixed_expenses(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Classify and total fixed expenses from the budget summary."""
    fixed_categories = ["housing", "utilities", "debt"]
    fixed_total = 0
    fixed_breakdown = {}
    
    for category, details in summary.get("category_breakdown", {}).items():
        if category in fixed_categories:
            fixed_breakdown[category] = details
            fixed_total += details["amount"]
    
    if summary["total_income"] > 0:
        fixed_percentage = (fixed_total / summary["total_income"]) * 100
    else:
        fixed_percentage = 0
    
    return {
        "total": fixed_total,
        "percentage_of_income": fixed_percentage,
        "breakdown": fixed_breakdown
    }

def classify_discretionary_expenses(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Classify and total discretionary expenses from the budget summary."""
    discretionary_categories = ["entertainment", "shopping", "food", "transport", "health", "education", "personal", "other"]
    discretionary_total = 0
    discretionary_breakdown = {}
    
    for category, details in summary.get("category_breakdown", {}).items():
        if category in discretionary_categories:
            discretionary_breakdown[category] = details
            discretionary_total += details["amount"]
    
    if summary["total_income"] > 0:
        discretionary_percentage = (discretionary_total / summary["total_income"]) * 100
    else:
        discretionary_percentage = 0
    
    return {
        "total": discretionary_total,
        "percentage_of_income": discretionary_percentage,
        "breakdown": discretionary_breakdown
    }

def calculate_budget_benchmarks(total_income: float) -> Dict[str, Any]:
    """Calculate 50/30/20 rule budget benchmarks."""
    # 50% for needs (fixed expenses)
    needs_benchmark = total_income * 0.5
    # 30% for wants (discretionary spending)
    wants_benchmark = total_income * 0.3
    # 20% for savings and debt repayment
    savings_benchmark = total_income * 0.2
    
    return {
        "needs": needs_benchmark,
        "wants": wants_benchmark,
        "savings": savings_benchmark,
        "rule": "50/30/20"
    }

def analyze_categories(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Perform category-specific analysis with benchmarks."""
    category_analysis = {}
    
    # Define typical ranges for each category as percentage of income
    benchmarks = {
        "housing": {"min": 25, "max": 35, "name": "Housing"},
        "utilities": {"min": 5, "max": 10, "name": "Utilities"},
        "food": {"min": 10, "max": 15, "name": "Food"},
        "transport": {"min": 5, "max": 15, "name": "Transportation"},
        "entertainment": {"min": 5, "max": 10, "name": "Entertainment"},
        "health": {"min": 5, "max": 10, "name": "Healthcare"},
        "education": {"min": 2, "max": 5, "name": "Education"},
        "shopping": {"min": 5, "max": 10, "name": "Shopping"},
        "personal": {"min": 5, "max": 10, "name": "Personal Care"},
        "debt": {"min": 0, "max": 15, "name": "Debt Payments"},
        "savings": {"min": 15, "max": 20, "name": "Savings"},
        "investment": {"min": 10, "max": 15, "name": "Investments"},
        "other": {"min": 0, "max": 5, "name": "Other"}
    }
    
    total_income = summary["total_income"]
    if total_income <= 0:
        return {"error": "Income is required for category analysis"}
    
    for category, details in summary.get("category_breakdown", {}).items():
        amount = details["amount"]
        # Calculate percentage of income and round to 1 decimal place for consistent comparison
        percentage_of_income = round((amount / total_income) * 100, 1)
        # Get benchmark or use defaults if category not found in benchmarks dictionary
        benchmark = benchmarks.get(category, {"min": 0, "max": 0, "name": category.capitalize()})
        
        status = "normal"
        advice = ""
        
        # Determine status by comparing percentage_of_income with benchmark range
        # Include tolerance to avoid floating point comparison issues
        if percentage_of_income < benchmark["min"]:
            status = "below"
            advice = f"Your spending in {benchmark['name']} is below typical ranges."
            
            # Special case for certain categories
            if category == "food":
                advice += " This is good if you're being efficient with grocery shopping, but ensure you're meeting nutritional needs."
            elif category in ["savings", "investment"]:
                advice += " Consider allocating more to build financial security."
            elif category in ["transport", "entertainment"]:
                advice += " Consider allocating more to this category if needed."
                
        elif percentage_of_income > benchmark["max"]:
            status = "above"
            advice = f"Your spending in {benchmark['name']} is above typical ranges."
            
            # Special case for certain categories
            if category == "housing":
                advice += " This may limit flexibility in other areas. Consider if downsizing is an option."
            elif category == "entertainment" or category == "shopping":
                advice += " Look for opportunities to reduce discretionary spending here."
        else:
            advice = f"Your spending in {benchmark['name']} is within typical ranges."
        
        # Special case handling for investment benchmarks
        if category == "investment":
            benchmark["max"] = 20  # Adjust investment upper benchmark to 20%

        # Double check the status determination based on precise percentage comparisons
        if percentage_of_income < benchmark["min"]:
            status = "below"
        elif percentage_of_income > benchmark["max"]:
            status = "above"
        else:
            status = "normal"
        
        category_analysis[category] = {
            "amount": amount,
            "percentage_of_income": percentage_of_income,
            "benchmark_min": benchmark["min"],
            "benchmark_max": benchmark["max"],
            "status": status,
            "advice": advice
        }
    
    return category_analysis

def analyze_spending_patterns(transactions: List[Transaction]) -> Dict[str, Any]:
    """Analyzes spending patterns with advanced categorization and benchmarking."""
    if not transactions:
        return {"message": "Not enough data for spending pattern analysis."}
        
    summary = calculate_budget_summary(transactions)
    
    # Classify expenses as fixed or discretionary
    fixed_expenses = classify_fixed_expenses(summary)
    discretionary_expenses = classify_discretionary_expenses(summary)
    
    # Calculate 50/30/20 rule benchmarks
    benchmarks = calculate_budget_benchmarks(summary["total_income"])
    
    # Perform category-specific analysis
    category_analysis = analyze_categories(summary)
    
    return {
        "message": "Advanced spending analysis generated.",
        "summary": summary,
        "fixed_expenses": fixed_expenses,
        "discretionary_expenses": discretionary_expenses,
        "benchmarks": benchmarks,
        "category_analysis": category_analysis
    }