from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import Field
from beanie import Document, Link, PydanticObjectId

from app.models.user import User


class TransactionCategory(str, Enum):
    """Enum for transaction categories."""
    INCOME = "income"
    HOUSING = "housing"
    UTILITIES = "utilities"
    FOOD = "food"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    HEALTH = "health"
    EDUCATION = "education"
    SHOPPING = "shopping"
    PERSONAL = "personal"
    DEBT = "debt"
    SAVINGS = "savings"
    INVESTMENT = "investment"
    OTHER = "other"


class Transaction(Document):
    """MongoDB document model for financial transactions."""
    user_id: PydanticObjectId = Field(..., description="Reference to the user who owns this transaction")
    amount: float = Field(..., description="Transaction amount")
    category: TransactionCategory = Field(..., description="Transaction category")
    description: Optional[str] = Field(None, description="Description of the transaction")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the transaction occurred")
    is_fraudulent: bool = Field(default=False, description="Whether this transaction is flagged as fraudulent")
    
    class Settings:
        name = "transactions"
        indexes = [
            "user_id",
            "category",
            "timestamp",
            "is_fraudulent"
        ]
    
    async def get_user(self) -> Optional[User]:
        """Get the user associated with this transaction."""
        return await User.get(self.user_id)
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, category='{self.category}')>"