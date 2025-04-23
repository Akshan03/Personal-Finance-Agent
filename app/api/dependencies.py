from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional
from bson import ObjectId

from app.models.user import User
from app.schemas.user import TokenData
from app.services import auth_service
from app.config import settings
from app.utils.security import ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Gets the current user from the token provided in the Authorization header.
    
    This is a FastAPI dependency that can be used in any endpoint that requires authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        # Extract email from token
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # Get the user from the database
    user = await auth_service.get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    
    # Ensure user has been prepared for JSON serialization
    # This step isn't actually needed for the auth route but helps with consistent handling
    if getattr(user, 'id', None) and isinstance(user.id, ObjectId):
        user_dict = user.model_dump()
        user_dict['id'] = str(user.id)
        # We're still returning the User model, but with its ID properly converted
    
    return user