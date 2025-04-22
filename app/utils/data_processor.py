import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from app.models.transaction import Transaction, TransactionCategory
from app.models.portfolio import Portfolio


def transactions_to_dataframe(transactions: List[Transaction]) -> pd.DataFrame:
    """Convert a list of Transaction objects to a pandas DataFrame.
    
    This makes it easier to perform analysis using pandas functions.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        DataFrame with transaction data
    """
    if not transactions:
        # Return empty DataFrame with expected columns
        return pd.DataFrame({
            'id': [],
            'user_id': [],
            'amount': [],
            'category': [],
            'description': [],
            'timestamp': [],
            'is_fraudulent': []
        })
    
    # Extract data from Transaction objects
    data = [{
        'id': t.id,
        'user_id': t.user_id,
        'amount': t.amount,
        'category': t.category.value if hasattr(t.category, 'value') else str(t.category),
        'description': t.description,
        'timestamp': t.timestamp,
        'is_fraudulent': t.is_fraudulent
    } for t in transactions]
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    return df


def portfolio_to_dataframe(portfolio_items: List[Portfolio]) -> pd.DataFrame:
    """Convert a list of Portfolio objects to a pandas DataFrame.
    
    Args:
        portfolio_items: List of Portfolio objects
        
    Returns:
        DataFrame with portfolio data
    """
    if not portfolio_items:
        # Return empty DataFrame with expected columns
        return pd.DataFrame({
            'id': [],
            'user_id': [],
            'asset_name': [],
            'asset_type': [],
            'quantity': [],
            'purchase_price': [],
            'purchase_date': [],
            'current_value': [],
            'last_updated': []
        })
    
    # Extract data from Portfolio objects
    data = [{
        'id': p.id,
        'user_id': p.user_id,
        'asset_name': p.asset_name,
        'asset_type': p.asset_type,
        'quantity': p.quantity,
        'purchase_price': p.purchase_price,
        'purchase_date': p.purchase_date,
        'current_value': p.current_value,
        'last_updated': p.last_updated
    } for p in portfolio_items]
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    return df


def calculate_spending_by_category(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate spending by category from transaction DataFrame.
    
    Args:
        df: DataFrame with transaction data
        
    Returns:
        Dictionary with spending by category and other insights
    """
    # Separate income and expenses
    income_df = df[df['category'] == 'income']
    expense_df = df[df['category'] != 'income']
    
    # Calculate totals
    total_income = income_df['amount'].sum() if not income_df.empty else 0
    total_expenses = expense_df['amount'].sum() if not expense_df.empty else 0
    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
    
    # Calculate spending by category
    category_spending = {}
    category_percentages = {}
    
    if not expense_df.empty:
        category_spending = expense_df.groupby('category')['amount'].sum().to_dict()
        
        # Calculate percentage of total expenses for each category
        for category, amount in category_spending.items():
            category_percentages[category] = (amount / total_expenses * 100) if total_expenses > 0 else 0
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_savings': net_savings,
        'savings_rate': savings_rate,
        'category_spending': category_spending,
        'category_percentages': category_percentages
    }


def identify_spending_anomalies(df: pd.DataFrame, threshold: float = 2.0) -> List[Dict[str, Any]]:
    """Identify anomalies in spending patterns.
    
    Args:
        df: DataFrame with transaction data
        threshold: Z-score threshold for flagging anomalies (default: 2.0)
        
    Returns:
        List of anomalies with details
    """
    anomalies = []
    
    # Need enough data for meaningful analysis
    if len(df) < 5:
        return anomalies
    
    # Filter to expenses only
    expense_df = df[df['category'] != 'income'].copy()
    if expense_df.empty:
        return anomalies
    
    # Calculate z-scores for amounts within each category
    categories = expense_df['category'].unique()
    
    for category in categories:
        cat_df = expense_df[expense_df['category'] == category]
        
        # Need enough data points in this category
        if len(cat_df) < 3:
            continue
        
        # Calculate mean and standard deviation for this category
        mean_amount = cat_df['amount'].mean()
        std_amount = cat_df['amount'].std()
        
        # Skip if std is zero or very small
        if std_amount < 0.0001:
            continue
        
        # Calculate z-scores
        cat_df['z_score'] = (cat_df['amount'] - mean_amount) / std_amount
        
        # Find anomalies
        anomaly_rows = cat_df[cat_df['z_score'].abs() > threshold]
        
        for _, row in anomaly_rows.iterrows():
            anomalies.append({
                'transaction_id': row['id'],
                'category': category,
                'amount': row['amount'],
                'timestamp': row['timestamp'],
                'z_score': row['z_score'],
                'avg_amount': mean_amount,
                'is_high': row['z_score'] > 0,
                'percent_deviation': abs(row['amount'] - mean_amount) / mean_amount * 100
            })
    
    return anomalies


def calculate_monthly_budget(spending_data: Dict[str, Any], savings_target_percent: float = 20.0) -> Dict[str, Any]:
    """Calculate a recommended monthly budget based on spending history.
    
    Args:
        spending_data: Dictionary with spending analysis from calculate_spending_by_category()
        savings_target_percent: Target percentage of income to save (default: 20.0%)
        
    Returns:
        Dictionary with recommended budget limits by category
    """
    # Extract key values from spending data
    total_income = spending_data.get('total_income', 0)
    total_expenses = spending_data.get('total_expenses', 0)
    category_spending = spending_data.get('category_spending', {})
    
    # Calculate target savings amount
    target_savings = total_income * (savings_target_percent / 100)
    
    # Calculate available budget after savings
    available_budget = total_income - target_savings
    
    # If current expenses exceed available budget, we need to reduce proportionally
    reduction_factor = 1.0
    if total_expenses > available_budget and total_expenses > 0:
        reduction_factor = available_budget / total_expenses
    
    # Calculate budget limits for each category
    budget_limits = {}
    for category, amount in category_spending.items():
        # Apply reduction factor to each category's spending
        budget_limits[category] = amount * reduction_factor
    
    return {
        'total_income': total_income,
        'target_savings': target_savings,
        'available_budget': available_budget,
        'reduction_needed': total_expenses > available_budget,
        'reduction_factor': reduction_factor,
        'budget_limits': budget_limits
    }