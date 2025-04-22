from typing import List, Optional, Any, Dict
from datetime import datetime
from beanie import Document, Link, PydanticObjectId
from pydantic import Field, EmailStr, model_validator
from bson import ObjectId

class User(Document):
    """MongoDB document model for user accounts."""
    email: EmailStr = Field(..., unique=True, index=True)
    hashed_password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
        json_encoders = {
            ObjectId: str,
            PydanticObjectId: str
        }
        
    def model_dump(self, **kwargs):
        """Custom serialization to handle ObjectId"""
        exclude = kwargs.pop('exclude', set())
        data = super().model_dump(**kwargs)
        if self.id:
            data['id'] = str(self.id)
        return data
        
    # In MongoDB, we don't need to define relationships explicitly
    # as we would in SQLAlchemy. We can retrieve related documents
    # using queries.
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return ""
        
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"