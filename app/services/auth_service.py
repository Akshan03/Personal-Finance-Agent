from typing import Optional
from app.models.user import User
from app.schemas import user as user_schema
from app.utils import security


async def get_user(user_id: str) -> Optional[User]:
    """Get a user by ID."""
    return await User.get(user_id)


async def get_user_by_email(email: str) -> Optional[User]:
    """Get a user by email."""
    return await User.find_one({"email": email})


async def create_user(user: user_schema.UserCreate) -> dict:
    """Create a new user."""
    # Check if user already exists
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise ValueError(f"User with email {user.email} already exists")
    
    # Create new user document
    hashed_password = security.get_password_hash(user.password)
    
    # Extract full name if provided
    first_name = None
    last_name = None
    if hasattr(user, 'full_name') and user.full_name:
        parts = user.full_name.split(maxsplit=1)
        if len(parts) > 0:
            first_name = parts[0]
        if len(parts) > 1:
            last_name = parts[1]
    
    # Create user model
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        first_name=first_name,
        last_name=last_name
    )
    
    # Save to database
    await db_user.insert()
    
    # Convert to dict with string ID for serialization
    user_dict = db_user.model_dump()
    user_dict['id'] = str(db_user.id)
    return user_dict


async def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = await get_user_by_email(email=email)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user