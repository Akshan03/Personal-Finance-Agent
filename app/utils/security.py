from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import settings
from app.schemas.user import TokenData
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# --- Password Hashing --- #

# Use SHA256 for password hashing to avoid bcrypt compatibility issues
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against its hashed version."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)

# --- JWT Handling --- #

# Constants for JWT
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# OAuth2 scheme definition (will be used in API dependencies)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def create_access_token_expiration() -> timedelta:
    """Creates a timedelta for access token expiration."""
    return timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception: HTTPException) -> TokenData:
    """Verifies a JWT token and returns the payload (TokenData)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")  # 'sub' holds the email in our implementation

        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    return token_data

# Dependency to get token data (can be refined later with user fetching)
def get_current_user_token_data(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Dependency to verify token and get token data for the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)