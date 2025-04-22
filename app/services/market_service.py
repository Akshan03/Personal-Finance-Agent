import random
from typing import Dict, List, Any
import json
import os

# Path to mock data file (adjust relative path as needed)
MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'mock_market_data.json')

def _load_mock_data() -> Dict[str, Any]:
    """Loads mock market data from the JSON file."""
    try:
        with open(MOCK_DATA_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Mock market data file not found at {MOCK_DATA_PATH}")
        # Return default structure if file is missing
        return {"stocks": [], "trends": {}}
    except json.JSONDecodeError:
        print(f"Warning: Error decoding JSON from {MOCK_DATA_PATH}")
        return {"stocks": [], "trends": {}}

def get_stock_price(symbol: str) -> float:
    """Placeholder: Simulates fetching a stock price."""
    mock_data = _load_mock_data()
    stocks = mock_data.get('stocks', [])
    
    for stock in stocks:
        if stock.get('symbol') == symbol:
            # Simulate slight random variation around the mock price
            base_price = stock.get('price', 100.0) # Default if price missing
            variation = base_price * random.uniform(-0.05, 0.05) # +/- 5% variation
            return round(base_price + variation, 2)
            
    # Return a default random price if symbol not in mock data
    print(f"Warning: Symbol {symbol} not found in mock data. Returning random price.")
    return round(random.uniform(50, 500), 2)

def get_market_trends() -> Dict[str, Any]:
    """Placeholder: Simulates fetching general market trends."""
    mock_data = _load_mock_data()
    trends = mock_data.get('trends', {})
    
    # Add a dynamic element (e.g., a random sentiment score)
    trends['current_sentiment_score'] = round(random.uniform(-1, 1), 2) # Example: -1 (very negative) to +1 (very positive)
    
    if not trends:
         return {"message": "No trend data available.", "current_sentiment_score": trends['current_sentiment_score']}
         
    return trends

def get_low_risk_investment_options() -> List[Dict[str, Any]]:
    """Placeholder: Simulates fetching low-risk investment options."""
    # In a real scenario, this would involve analyzing market data, risk profiles etc.
    # Here, we just return some hardcoded examples.
    return [
        {"name": "Government Bond Fund A", "type": "Bond Fund", "expected_return": "2.5%", "risk_level": "Low"},
        {"name": "Stable Value Fund B", "type": "Stable Value", "expected_return": "2.0%", "risk_level": "Very Low"},
        {"name": "Certificate of Deposit (CD)", "type": "Fixed Income", "expected_return": "1.8%", "risk_level": "Very Low"},
        {"name": "BlueChip Dividend Stock Fund", "type": "Stock Fund", "expected_return": "4.0%", "risk_level": "Low-Medium"} # Example slightly higher risk
    ]