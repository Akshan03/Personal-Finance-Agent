from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import Field
from beanie import Document, Link, PydanticObjectId

from app.models.user import User

class AssetType(str, Enum):
    """Enum for asset types in portfolio."""
    STOCK = "stock"
    BOND = "bond"
    ETF = "etf"
    CRYPTO = "crypto"
    REAL_ESTATE = "real_estate"
    OTHER = "other"

class Portfolio(Document):
    """MongoDB document model for investment portfolio items."""
    user_id: PydanticObjectId = Field(..., description="Reference to the user who owns this asset")
    asset_name: str = Field(..., description="Name of the asset")
    asset_type: AssetType = Field(..., description="Type of asset")
    quantity: float = Field(..., description="Quantity owned")
    purchase_price: float = Field(..., description="Price paid per unit")
    purchase_date: datetime = Field(..., description="When the asset was purchased")
    current_value: Optional[float] = Field(None, description="Current market value (if known)")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="When the asset value was last updated")
    
    class Settings:
        name = "portfolios"
        indexes = [
            "user_id",
            "asset_type"
        ]
    
    async def get_user(self) -> Optional[User]:
        """Get the user associated with this portfolio item."""
        return await User.get(self.user_id)
    
    @property
    def total_purchase_value(self) -> float:
        """Calculate the total purchase value of this asset."""
        return self.purchase_price * self.quantity
    
    @property
    def total_current_value(self) -> Optional[float]:
        """Calculate the total current value of this asset."""
        if self.current_value is not None:
            return self.current_value * self.quantity
        return None
    
    @property
    def gain_loss_percent(self) -> Optional[float]:
        """Calculate the percentage gain or loss on this asset."""
        if self.current_value is not None and self.purchase_price > 0:
            return ((self.current_value - self.purchase_price) / self.purchase_price) * 100
        return None
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, user_id={self.user_id}, asset='{self.asset_name}', type='{self.asset_type}')>"