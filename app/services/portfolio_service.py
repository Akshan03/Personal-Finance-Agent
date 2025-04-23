from typing import List, Optional
from datetime import datetime
from beanie import PydanticObjectId

from app.models.portfolio import Portfolio, AssetType

async def get_user_portfolio(user_id: PydanticObjectId) -> List[Portfolio]:
    """
    Retrieve all portfolio assets for a specific user.
    
    Args:
        user_id: The ObjectID of the user
        
    Returns:
        List of portfolio assets owned by the user
    """
    return await Portfolio.find({"user_id": user_id}).to_list()

async def get_portfolio_item(portfolio_id: PydanticObjectId, user_id: PydanticObjectId) -> Optional[Portfolio]:
    """
    Retrieve a specific portfolio item.
    
    Args:
        portfolio_id: ID of the portfolio item
        user_id: ID of the user (for authorization)
        
    Returns:
        The portfolio item if found and owned by the user, None otherwise
    """
    return await Portfolio.find_one({"_id": portfolio_id, "user_id": user_id})

async def create_portfolio_asset(
    user_id: PydanticObjectId,
    asset_name: str,
    asset_type: str,
    quantity: float,
    purchase_price: float,
    purchase_date: datetime,
    current_value: Optional[float] = None
) -> Portfolio:
    """
    Create a new portfolio asset.
    
    Args:
        user_id: ID of the user who owns the asset
        asset_name: Name of the asset
        asset_type: Type of asset (must match AssetType enum)
        quantity: Quantity owned
        purchase_price: Price paid per unit
        purchase_date: When the asset was purchased
        current_value: Current market value (optional)
        
    Returns:
        The newly created portfolio object
    """
    # Try to convert string asset_type to enum if needed
    if isinstance(asset_type, str):
        try:
            asset_type = AssetType(asset_type.lower())
        except ValueError:
            # Default to "other" if not a recognized type
            asset_type = AssetType.OTHER
    
    # Set current_value to purchase_price if not provided
    if current_value is None:
        current_value = purchase_price

    portfolio_item = Portfolio(
        user_id=user_id,
        asset_name=asset_name,
        asset_type=asset_type,
        quantity=quantity,
        purchase_price=purchase_price,
        purchase_date=purchase_date,
        current_value=current_value,
        last_updated=datetime.utcnow()
    )
    
    await portfolio_item.insert()
    return portfolio_item

async def update_portfolio_asset(
    portfolio_id: PydanticObjectId,
    user_id: PydanticObjectId,
    update_data: dict
) -> Optional[Portfolio]:
    """
    Update an existing portfolio asset.
    
    Args:
        portfolio_id: ID of the portfolio item to update
        user_id: ID of the user (for authorization)
        update_data: Dictionary of fields to update
        
    Returns:
        The updated portfolio item if successful, None otherwise
    """
    portfolio_item = await get_portfolio_item(portfolio_id, user_id)
    if not portfolio_item:
        return None
    
    # Handle asset_type conversion if it's being updated
    if "asset_type" in update_data and isinstance(update_data["asset_type"], str):
        try:
            update_data["asset_type"] = AssetType(update_data["asset_type"].lower())
        except ValueError:
            update_data["asset_type"] = AssetType.OTHER
    
    # Update the last_updated timestamp
    update_data["last_updated"] = datetime.utcnow()
    
    # Apply updates
    for key, value in update_data.items():
        setattr(portfolio_item, key, value)
    
    await portfolio_item.save()
    return portfolio_item

async def delete_portfolio_asset(portfolio_id: PydanticObjectId, user_id: PydanticObjectId) -> bool:
    """
    Delete a portfolio asset.
    
    Args:
        portfolio_id: ID of the portfolio item to delete
        user_id: ID of the user (for authorization)
        
    Returns:
        True if deletion was successful, False otherwise
    """
    portfolio_item = await get_portfolio_item(portfolio_id, user_id)
    if not portfolio_item:
        return False
    
    await portfolio_item.delete()
    return True
