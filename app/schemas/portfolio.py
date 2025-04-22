from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any
from datetime import datetime

# --- Base Schemas --- #

class PortfolioBase(BaseModel):
    """Base schema for portfolio asset."""
    asset_name: str = Field(..., max_length=100)
    asset_type: str = Field(..., max_length=50)
    quantity: float
    purchase_price: float
    purchase_date: datetime

# --- Schemas for Creation/Input --- #

class PortfolioCreate(PortfolioBase):
    """Schema for adding a new asset to the portfolio."""
    # user_id will be added from auth
    pass

# --- Schemas for Reading/Output --- #

class Portfolio(PortfolioBase):
    """Schema for reading portfolio data."""
    id: str
    user_id: str
    current_value: Optional[float] = None
    last_updated: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )