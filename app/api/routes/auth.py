from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas import user as user_schema
from app.services import auth_service
from app.utils import security
from app.config import settings
from app.api.dependencies import get_current_user

router = APIRouter()

@router.post("/register", response_model=user_schema.User, status_code=status.HTTP_201_CREATED)
async def register_user(user: user_schema.UserCreate):
    """Register a new user."""
    try:
        # The create_user function now includes a check for existing users
        return await auth_service.create_user(user=user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/token", response_model=user_schema.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """OAuth2 compatible token login, get an access token for future requests."""
    # Authenticate user
    user = await auth_service.authenticate_user(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with an expiration time
    access_token_expires = security.create_access_token_expiration()
    access_token = security.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=user_schema.User)
async def read_users_me(current_user = Depends(get_current_user)):
    """Gets the current authenticated user's details."""
    # The get_current_user dependency already fetches and returns the user model
    # FastAPI handles the conversion to the response_model (user_schema.User)
    return current_user