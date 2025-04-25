from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from beanie import PydanticObjectId
from datetime import datetime, timedelta

from app.models.transaction import Transaction, TransactionCategory
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate, TransactionStats
from app.api.dependencies import get_current_user
from app.models.user import User
from app.services import finance_service

router = APIRouter()

@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    category: Optional[TransactionCategory] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Get transactions for the current user with pagination and optional filtering."""
    query = {"user_id": current_user.id}
    
    if category:
        query["category"] = category
    
    if start_date or end_date:
        timestamp_query = {}
        if start_date:
            timestamp_query["$gte"] = start_date
        if end_date:
            timestamp_query["$lte"] = end_date
        query["timestamp"] = timestamp_query
    
    transactions = await Transaction.find(query).sort("-timestamp").skip(skip).limit(limit).to_list()
    
    # Convert PydanticObjectId to string in the response
    transaction_responses = []
    for transaction in transactions:
        transaction_dict = transaction.model_dump()
        transaction_dict["id"] = str(transaction.id)
        transaction_dict["user_id"] = str(transaction.user_id)
        transaction_responses.append(transaction_dict)
    
    return transaction_responses

@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new transaction for the current user."""
    # Create new transaction document
    new_transaction = Transaction(
        user_id=current_user.id,
        amount=transaction.amount,
        category=transaction.category,
        description=transaction.description,
        timestamp=transaction.timestamp or datetime.utcnow()
    )
    
    # Save to database
    await new_transaction.insert()
    
    # Return response with string ID
    response = new_transaction.model_dump()
    response["id"] = str(new_transaction.id)
    response["user_id"] = str(new_transaction.user_id)
    
    return response

@router.get("/stats", response_model=Dict[str, Any])
async def get_transaction_stats(
    period: str = "all",  
    current_user: User = Depends(get_current_user)
):
    """Get transaction statistics for the specified time period."""
    # Define date range based on period
    now = datetime.utcnow()
    start_date = None
    
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    elif period == "year":
        start_date = now - timedelta(days=365)
    # For "all", start_date remains None
    
    # Get all user transactions within the date range
    query = {"user_id": current_user.id}
    if start_date:
        query["timestamp"] = {"$gte": start_date}
    
    transactions = await Transaction.find(query).to_list()
    
    # Calculate statistics
    # Debug exactly what transactions we're working with
    transaction_amounts = [float(t.amount) for t in transactions]  
    print(f"DEBUG - Transaction amounts: {transaction_amounts}")
    print(f"DEBUG - Transaction count: {len(transactions)}")
    
    # Calculate income (only positive transactions)
    total_income = sum(float(t.amount) for t in transactions if float(t.amount) > 0)
    print(f"DEBUG - Total income: {total_income}")
    
    # Calculate expenses (absolute sum of negative transactions)
    total_expenses = abs(sum(float(t.amount) for t in transactions if float(t.amount) < 0))
    print(f"DEBUG - Total expenses: {total_expenses}")
    
    # Initialize category breakdown
    category_breakdown = {}
    
    # Calculate amounts per category - only count expenses in the breakdown
    # This ensures the pie chart represents how money is being spent
    for t in transactions:
        amount = float(t.amount)
        # Only include expenses (negative amounts) in category breakdown
        if amount < 0:
            category = t.category.value
            if category not in category_breakdown:
                category_breakdown[category] = {"amount": 0, "percentage": 0}
            
            # Use absolute value for display but only for expenses
            category_breakdown[category]["amount"] += abs(amount)
    
    # Calculate percentages based on total expenses only
    # This gives the proper breakdown of how expenses are distributed
    if total_expenses > 0:
        for category in category_breakdown:
            category_breakdown[category]["percentage"] = category_breakdown[category]["amount"] / total_expenses
    
    # Calculate net savings and savings rate
    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income) * 100 if total_income > 0 else 0
    
    print(f"DEBUG - Summary: Income={total_income}, Expenses={total_expenses}, Savings={net_savings}, Rate={savings_rate}%")
    
    return {
        "total_income": float(total_income),  
        "total_expenses": float(total_expenses),
        "net_savings": float(net_savings),
        "savings_rate": float(savings_rate),
        "category_breakdown": category_breakdown
    }

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific transaction by ID."""
    try:
        # Convert string ID to PydanticObjectId
        object_id = PydanticObjectId(transaction_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction ID format"
        )
    
    transaction = await Transaction.find_one({"_id": object_id, "user_id": current_user.id})
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Convert IDs to strings
    response = transaction.model_dump()
    response["id"] = str(transaction.id)
    response["user_id"] = str(transaction.user_id)
    
    return response

@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    transaction_update: TransactionUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a specific transaction."""
    try:
        # Convert string ID to PydanticObjectId
        object_id = PydanticObjectId(transaction_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction ID format"
        )
    
    transaction = await Transaction.find_one({"_id": object_id, "user_id": current_user.id})
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Update only provided fields
    update_data = transaction_update.model_dump(exclude_unset=True)
    if update_data:
        await transaction.update({"$set": update_data})
    
    # Get updated transaction
    updated_transaction = await Transaction.get(object_id)
    
    # Convert IDs to strings
    response = updated_transaction.model_dump()
    response["id"] = str(updated_transaction.id)
    response["user_id"] = str(updated_transaction.user_id)
    
    return response

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a specific transaction."""
    try:
        # Convert string ID to PydanticObjectId
        object_id = PydanticObjectId(transaction_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction ID format"
        )
    
    transaction = await Transaction.find_one({"_id": object_id, "user_id": current_user.id})
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Delete the transaction
    await transaction.delete()
    
    return None
