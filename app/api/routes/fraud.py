from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.models.database import get_db
from app.models.user import User
from app.schemas import transaction as transaction_schema # Assuming fraud relates to transactions
from app.api.dependencies import get_current_user
from app.services import finance_service # May need transaction data
# Import agent-related functions later
# from app.agents.orchestrator import run_fraud_agent

router = APIRouter()

@router.post("/scan-transactions", response_model=Dict[str, Any])
def scan_transactions_for_fraud(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Triggers the Fraud Detector agent to scan recent transactions."""
    transactions = finance_service.get_user_transactions(db, user_id=current_user.id, limit=50) # Scan last 50 transactions
    if not transactions:
        return {"message": "No recent transactions to scan."}

    # TODO: Pass transactions to the fraud agent via orchestrator
    # fraud_results = run_fraud_agent(transactions=transactions, user_id=current_user.id)
    # For now, return placeholder
    return {
        "message": "Fraud Agent Placeholder: Scan complete.",
        "suspicious_transactions_found": 1, 
        "details": [
            {"transaction_id": transactions[0].id if transactions else None, "reason": "Unusual spending pattern detected."}
        ]
    }

@router.post("/report-transaction/{transaction_id}", response_model=Dict[str, str])
def report_suspicious_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Allows the user to manually report a suspicious transaction."""
    # TODO: Fetch the transaction, verify it belongs to the user
    # TODO: Mark the transaction as potentially fraudulent or trigger further checks
    # transaction = db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id).first()
    # if not transaction:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    # transaction.is_fraudulent = True # Example action
    # db.commit()
    return {"message": f"Transaction {transaction_id} reported successfully. Investigation pending."}