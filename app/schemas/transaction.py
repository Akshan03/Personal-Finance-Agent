from pydantic import BaseModel, Field, ConfigDict, field_validator
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
    
    @field_validator('category', mode='before')
    @classmethod
    def normalize_category(cls, value):
        """Convert category to lowercase to make it case-insensitive."""
        if isinstance(value, str):
            return value.lower()
        return value

# --- Schemas for Creation/Input --- #

class TransactionCreate(TransactionBase):
    """Schema for creating a transaction (user_id will be added from auth)."""
    timestamp: datetime = Field(default_factory=datetime.now)
    # user_id is not included here, it will be derived from the authenticated user

# --- Schemas for Reading/Output --- #

class TransactionResponse(TransactionBase):
    """Schema for reading transaction data."""
    id: str
    user_id: str
    is_fraudulent: bool = False # Include fraud status
    timestamp: datetime # Ensure timestamp is always present when reading

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

# Alias for backward compatibility
Transaction = TransactionResponse

# --- Schema for Updates --- #
class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""
    amount: Optional[float] = None
    category: Optional[TransactionCategory] = None
    description: Optional[str] = None
    timestamp: Optional[datetime] = None
    is_fraudulent: Optional[bool] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra='ignore'
    )

# --- Schema for Statistics --- #
class CategoryStat(BaseModel):
    """Statistics for a single transaction category."""
    amount: float
    percentage: float

class TransactionStats(BaseModel):
    """Overall transaction statistics."""
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate: float
    category_breakdown: dict[str, CategoryStat]