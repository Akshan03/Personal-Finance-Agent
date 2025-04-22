from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any
from datetime import datetime
from app.models.transaction import TransactionCategory # Import Enum from model

# --- Base Schemas --- #

class TransactionBase(BaseModel):
    """Base schema for transaction, common fields."""
    amount: float
    category: TransactionCategory
    description: Optional[str] = None
    timestamp: Optional[datetime] = None

# --- Schemas for Creation/Input --- #

class TransactionCreate(TransactionBase):
    """Schema for creating a transaction (user_id will be added from auth)."""
    timestamp: datetime = Field(default_factory=datetime.now)
    # user_id is not included here, it will be derived from the authenticated user

# --- Schemas for Reading/Output --- #

class Transaction(TransactionBase):
    """Schema for reading transaction data."""
    id: str
    user_id: str
    is_fraudulent: bool = False # Include fraud status
    timestamp: datetime # Ensure timestamp is always present when reading

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )