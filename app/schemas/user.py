from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Any
from datetime import datetime

# --- Base Schemas --- #

class UserBase(BaseModel):
    """Base schema for user, contains common fields."""
    email: EmailStr
    full_name: Optional[str] = None

# --- Schemas for Creation/Input --- #

class UserCreate(UserBase):
    """Schema used for creating a new user."""
    password: str = Field(min_length=8)

# --- Schemas for Reading/Output --- #

class User(UserBase):
    """Schema used for reading user data (e.g., in API responses)."""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

# --- Schemas for Authentication --- #

class Token(BaseModel):
    """Schema for the JWT access token response."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for data encoded within the JWT token."""
    email: Optional[str] = None