from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models.database import get_db
from app.models.user import User
from app.schemas import transaction as transaction_schema # Assuming fraud relates to transactions
from app.api.dependencies import get_current_user
from app.services import finance_service # May need transaction data
# Import the orchestrator factory
from app.agents.orchestrator import get_orchestrator

router = APIRouter()

@router.post("/scan-transactions", response_model=Dict[str, Any])
async def scan_transactions_for_fraud(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Triggers the Fraud Detector agent to scan recent transactions."""
    transactions = await finance_service.get_user_transactions(user_id=current_user.id, limit=50) # Scan last 50 transactions
    if not transactions:
        return {"message": "No recent transactions to scan."}

    # Get the orchestrator instance and use its fraud agent
    orchestrator = get_orchestrator()
    fraud_results = orchestrator.fraud_agent.analyze_transactions(transactions=transactions)
    
    # Format the response for the API
    suspicious_count = len(fraud_results.get("suspicious_transactions", []))
    details = []
    
    # Format each suspicious transaction for the API response
    for suspicious in fraud_results.get("suspicious_transactions", []):
        details.append({
            "transaction_id": suspicious["transaction_id"],
            "reason": suspicious["reason"],
            "risk_level": suspicious["risk_level"]
        })
    
    from datetime import datetime
    return {
        "message": "Fraud analysis complete.",
        "suspicious_transactions_found": suspicious_count,
        "details": details,
        "last_scan_time": datetime.utcnow().isoformat() + 'Z'
    }

@router.post("/report-transaction/{transaction_id}", response_model=Dict[str, str])
async def report_suspicious_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    """Allows the user to manually report a suspicious transaction."""
    # Convert string ID to PydanticObjectId
    from beanie import PydanticObjectId
    
    try:
        # Validate transaction ID format
        transaction_obj_id = PydanticObjectId(transaction_id)
        
        # Import Transaction model
        from app.models.transaction import Transaction
        
        # Fetch the transaction and verify it belongs to the user
        transaction = await Transaction.find_one({"_id": transaction_obj_id, "user_id": PydanticObjectId(current_user.id)})
        
        if not transaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found or does not belong to you")
        
        # Mark the transaction as potentially fraudulent
        transaction.is_fraudulent = True
        await transaction.save()
        
        # Run additional analysis with the fraud agent
        # This can be done asynchronously in the background in a production environment
        user_transactions = await finance_service.get_user_transactions(user_id=current_user.id, limit=20)
        orchestrator = get_orchestrator()
        orchestrator.fraud_agent.analyze_transactions(transactions=user_transactions)
        
        return {"message": f"Transaction {transaction_id} reported as fraudulent. Investigation initiated."} 
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing transaction report: {str(e)}"
        )