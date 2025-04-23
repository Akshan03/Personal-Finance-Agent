import random
from typing import Dict, List, Any, Optional
import json
import os
import httpx
import asyncio
from datetime import datetime, timedelta
from app.config import settings

# Path to mock data file as fallback (adjust relative path as needed)
MOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'mock_market_data.json')

# Cache for market data to avoid excessive API calls
_market_cache = {
    'stock_data': {},       # Symbol -> price data
    'market_trends': None,  # Overall market data
    'last_updated': None,   # Last update timestamp
    'recommendations': {}   # Risk level -> recommendations
}

# Cache expiration in seconds (10 minutes for development, could be shorter in production)
CACHE_EXPIRATION = 600

# Default API key to be replaced with environment variable
ALPHAVANTAGE_API_KEY = os.getenv('ALPHAVANTAGE_API_KEY', 'demo')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')

async def _fetch_from_api(url: str) -> Dict[str, Any]:
    """Generic function to fetch data from an API endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        print(f"API request error: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error fetching from API: {e}")
        return {}

def _load_mock_data() -> Dict[str, Any]:
    """Loads mock market data from the JSON file as fallback."""
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

async def get_stock_price(symbol: str) -> float:
    """Get real-time stock price using Alpha Vantage API with fallback to cache and mock data."""
    # Check cache first
    now = datetime.now()
    cache_entry = _market_cache['stock_data'].get(symbol)
    
    if cache_entry and (now - cache_entry['timestamp']).total_seconds() < CACHE_EXPIRATION:
        return cache_entry['price']
    
    # For market index ETFs, use default data if available
    default_etfs = _get_default_etf_data()
    if symbol in default_etfs:
        base_price = default_etfs[symbol]['price']
        # Add small random variation to simulate market movement
        variation = base_price * random.uniform(-0.01, 0.01)
        price = round(base_price + variation, 2)
        
        _market_cache['stock_data'][symbol] = {
            'price': price,
            'timestamp': now,
            'change_percent': f"{default_etfs[symbol]['change']}%"
        }
        return price
    
    # Alpha Vantage API for real-time quotes
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
    data = await _fetch_from_api(url)
    
    # Parse response
    quote_data = data.get('Global Quote', {})
    if quote_data and '05. price' in quote_data:
        price = float(quote_data['05. price'])
        # Update cache
        _market_cache['stock_data'][symbol] = {
            'price': price,
            'timestamp': now,
            'change_percent': quote_data.get('10. change percent', '0%')
        }
        return price
    
    # Fallback to mock data if API fails
    mock_data = _load_mock_data()
    stocks = mock_data.get('stocks', [])
    
    for stock in stocks:
        if stock.get('symbol') == symbol:
            # Simulate slight random variation around the mock price
            base_price = stock.get('price', 100.0)
            variation = base_price * random.uniform(-0.05, 0.05)
            price = round(base_price + variation, 2)
            # Update cache
            _market_cache['stock_data'][symbol] = {
                'price': price,
                'timestamp': now,
                'change_percent': f"{random.uniform(-2, 2):.2f}%"
            }
            return price
    
    # Last resort: return a default price
    price = round(random.uniform(50, 500), 2)
    _market_cache['stock_data'][symbol] = {
        'price': price,
        'timestamp': now,
        'change_percent': f"{random.uniform(-2, 2):.2f}%"
    }
    print(f"Warning: Symbol {symbol} not found in any source. Returning random price.")
    return price

# Add default ETF data to avoid not found warnings
def _get_default_etf_data() -> Dict[str, Dict[str, Any]]:
    """Provide default data for common market index ETFs"""
    return {
        "SPY": {
            "symbol": "SPY",
            "name": "SPDR S&P 500 ETF Trust",
            "price": 470.25,
            "change": 0.67,  # percent
            "description": "Tracks S&P 500 Index"
        },
        "DIA": {
            "symbol": "DIA",
            "name": "SPDR Dow Jones Industrial Average ETF",
            "price": 383.12,
            "change": 0.42,  # percent
            "description": "Tracks Dow Jones Industrial Average"
        },
        "QQQ": {
            "symbol": "QQQ",
            "name": "Invesco QQQ Trust",
            "price": 431.80,
            "change": 0.91,  # percent
            "description": "Tracks Nasdaq-100 Index"
        },
        "IWM": {
            "symbol": "IWM",
            "name": "iShares Russell 2000 ETF",
            "price": 201.45,
            "change": 0.35,  # percent
            "description": "Tracks Russell 2000 Index"
        },
        "VTI": {
            "symbol": "VTI",
            "name": "Vanguard Total Stock Market ETF",
            "price": 238.60,
            "change": 0.58,  # percent
            "description": "Tracks CRSP US Total Market Index"
        }
    }

async def get_market_trends() -> Dict[str, Any]:
    """Get real market trends data with fallback to cached or mock data."""
    # Check if cache is still valid
    now = datetime.now()
    if (_market_cache['market_trends'] and _market_cache['last_updated'] and 
        (now - _market_cache['last_updated']).total_seconds() < CACHE_EXPIRATION):
        return _market_cache['market_trends']
    
    # Attempt to fetch real market data from financial APIs
    market_data = {}
    
    # 1. Try to get index data for overall market performance (S&P 500, Dow, Nasdaq)
    indices = ['SPY', 'DIA', 'QQQ']  # ETFs that track major indices
    index_data = {}
    default_etf_data = _get_default_etf_data()
    
    for idx in indices:
        try:
            # Try to get real price data
            price = await get_stock_price(idx)
            index_data[idx] = price
        except Exception:
            # If any error occurs, use default data
            if idx in default_etf_data:
                index_data[idx] = default_etf_data[idx]["price"]
                # Add small random variation
                variation = index_data[idx] * random.uniform(-0.01, 0.01)
                index_data[idx] += variation
            else:
                # Last resort fallback
                index_data[idx] = random.uniform(100, 500)
    
    # 2. Get Finnhub news sentiment if API key is available
    sentiment_score = 0
    if FINNHUB_API_KEY:
        url = f"https://finnhub.io/api/v1/news-sentiment?symbol=AAPL&token={FINNHUB_API_KEY}"
        sentiment_data = await _fetch_from_api(url)
        if sentiment_data and 'sentiment' in sentiment_data:
            sentiment_score = sentiment_data['sentiment']
    else:
        # Fallback to random but realistic sentiment
        sentiment_score = round(random.uniform(-1, 1), 2)
    
    # 3. Get economic indicators - in a real app would use specialized APIs
    # For now, we're generating plausible values with slight randomness
    gdp_growth = str(round(random.uniform(1.8, 3.2), 1)) + "% annual rate"
    unemployment = str(round(random.uniform(3.5, 4.2), 1)) + "%"
    
    # Construct our market trends response
    market_data = {
        "market_summary": _generate_market_summary(index_data, sentiment_score),
        "current_sentiment_score": sentiment_score,
        "interest_rate_trend": _generate_interest_rate_trend(),
        "inflation_outlook": _generate_inflation_outlook(),
        "economic_indicators": {
            "gdp_growth": gdp_growth,
            "unemployment": unemployment,
            "consumer_confidence": _generate_consumer_confidence()
        },
        "sector_performance": _generate_sector_performance(),
        "last_updated": now.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Update cache
    _market_cache['market_trends'] = market_data
    _market_cache['last_updated'] = now
    
    return market_data

# Helper functions for market trends data generation
def _generate_market_summary(index_data: Dict[str, float], sentiment: float) -> str:
    """Generate a market summary description based on data."""
    if sentiment > 0.5:
        tone = "bullish"
    elif sentiment > 0:
        tone = "cautiously optimistic"
    elif sentiment > -0.5:
        tone = "mixed"
    else:
        tone = "bearish"
        
    return f"Market sentiment is currently {tone} with moderate volatility across major indices."

def _generate_interest_rate_trend() -> str:
    """Generate a plausible interest rate trend description."""
    options = [
        "Stable with potential for modest decrease in coming months",
        "Gradual increasing trend expected to continue through the quarter",
        "Federal Reserve signaling rate stability for the near term",
        "Mixed signals with potential for adjustment based on inflation data"
    ]
    return random.choice(options)

def _generate_inflation_outlook() -> str:
    """Generate a plausible inflation outlook."""
    inflation_rate = round(random.uniform(2.0, 4.5), 1)
    trend = random.choice(["gradually decreasing", "stabilizing", "slightly increasing"])
    return f"{trend}, expected to settle around {inflation_rate}% annually"

def _generate_consumer_confidence() -> str:
    """Generate a consumer confidence description."""
    level = random.choice(["weak", "moderate", "strong"])
    trend = random.choice(["declining", "stable", "improving"])
    return f"{level} and {trend}"

def _generate_sector_performance() -> Dict[str, str]:
    """Generate sector performance descriptions."""
    sectors = {
        "technology": random.choice(["strong growth despite valuation concerns", "moderate growth", "cooling after recent rally"]),
        "healthcare": random.choice(["stable defensive performance", "mixed with policy uncertainty", "outperforming broader market"]),
        "financials": random.choice(["sensitive to interest rate changes", "showing strength on strong earnings", "underperforming due to regulatory concerns"]),
        "consumer_staples": random.choice(["reliable but modest growth", "outperforming in defensive rotation", "facing margin pressure"]),
        "energy": random.choice(["volatile with focus on renewables", "strong on rising commodity prices", "underperforming on demand concerns"]),
        "utilities": random.choice(["defensive in uncertain markets", "pressured by rising rates", "stable with attractive dividends"])
    }
    return sectors

async def get_low_risk_investment_options() -> List[Dict[str, Any]]:
    """Get personalized investment recommendations based on market conditions."""
    # Check if cache is valid
    now = datetime.now()
    cache_entry = _market_cache.get('recommendations', {}).get('low_risk')
    if cache_entry and (now - cache_entry['timestamp']).total_seconds() < CACHE_EXPIRATION:
        return cache_entry['data']
    
    # Get current market trends to inform recommendations
    trends = await get_market_trends()
    sentiment = trends.get('current_sentiment_score', 0)
    
    # Adjust expected returns based on interest rates and market sentiment
    # (In a real implementation, this would use more sophisticated models)
    bond_adjustment = random.uniform(-0.5, 0.5)  # Slight randomization for demo
    stock_adjustment = sentiment * 0.5  # Higher sentiment = higher stock expected returns
    
    # Generate recommendations with dynamic expected returns
    recommendations = [
        {
            "name": "Treasury Bond ETF", 
            "type": "Bond Fund", 
            "expected_return": f"{2.5 + bond_adjustment:.1f}%", 
            "risk_level": "Low",
            "description": "Tracks U.S. Treasury bonds with 7-10 year maturities"
        },
        {
            "name": "Short-Term Corporate Bond Fund", 
            "type": "Bond Fund", 
            "expected_return": f"{3.0 + bond_adjustment:.1f}%", 
            "risk_level": "Low",
            "description": "Investment-grade corporate bonds with 1-5 year duration"
        },
        {
            "name": "High-Yield Savings Account", 
            "type": "Cash Equivalent", 
            "expected_return": f"{1.8 + bond_adjustment/2:.1f}%", 
            "risk_level": "Very Low",
            "description": "FDIC-insured savings with competitive interest rates"
        },
        {
            "name": "Dividend Aristocrats ETF", 
            "type": "Stock Fund", 
            "expected_return": f"{4.0 + stock_adjustment:.1f}%", 
            "risk_level": "Low-Medium",
            "description": "Companies with 25+ years of dividend increases"
        }
    ]
    
    # Add market-specific recommendations based on current conditions
    if sentiment < -0.3:  # Bearish market
        recommendations.append({
            "name": "Treasury Inflation-Protected Securities (TIPS)", 
            "type": "Government Bond", 
            "expected_return": f"{2.2 + bond_adjustment:.1f}%", 
            "risk_level": "Low",
            "description": "Provides protection against inflation with government backing"
        })
    elif sentiment > 0.3:  # Bullish market
        recommendations.append({
            "name": "Blue Chip Dividend Stock Fund", 
            "type": "Stock Fund", 
            "expected_return": f"{4.5 + stock_adjustment:.1f}%", 
            "risk_level": "Medium",
            "description": "Large stable companies with history of dividend payments"
        })
    
    # Update cache
    _market_cache['recommendations']['low_risk'] = {
        'data': recommendations,
        'timestamp': now
    }
    
    return recommendations

async def evaluate_stock_holding(stock_name: str) -> Dict[str, Any]:
    """Evaluate a specific stock and provide an assessment."""
    # This would normally use real financial data APIs to get metrics
    # For demo purposes, we'll use a combination of mock data and logic
    
    # Common large cap tech stocks considered relatively stable
    blue_chip_tech = {
        "AAPL": {
            "name": "Apple Inc.", 
            "strength": "Strong financials, innovative products, loyal customer base",
            "risk": "Tech sector volatility, product cycle dependency",
            "rating": "Strong"
        },
        "MSFT": {
            "name": "Microsoft", 
            "strength": "Cloud business growth, enterprise software dominance",
            "risk": "Competition in cloud services, regulatory concerns",
            "rating": "Strong"
        },
        "GOOG": {
            "name": "Alphabet (Google)", 
            "strength": "Search dominance, diverse revenue streams",
            "risk": "Regulatory challenges, ad market dependency",
            "rating": "Strong"
        },
        "AMZN": {
            "name": "Amazon", 
            "strength": "E-commerce leader, AWS cloud growth",
            "risk": "Thin retail margins, high competition",
            "rating": "Strong"
        }
    }
    
    # Company name to ticker mapping for better matching
    company_name_mapping = {
        "APPLE": "AAPL",
        "MICROSOFT": "MSFT",
        "GOOGLE": "GOOG",
        "ALPHABET": "GOOG",
        "AMAZON": "AMZN",
        "AMAZON.COM": "AMZN",
        "TESLA": "TSLA",
        "NVIDIA": "NVDA",
        "JOHNSON & JOHNSON": "JNJ",
        "VISA": "V",
        "EXXON": "XOM",
        "EXXON MOBIL": "XOM"
    }
    
    # Extract potential ticker from name
    clean_name = stock_name.upper()
    
    # First check exact matches
    if "APPLE" in clean_name or "AAPL" in clean_name:
        return blue_chip_tech["AAPL"]
    elif "MICROSOFT" in clean_name or "MSFT" in clean_name:
        return blue_chip_tech["MSFT"]
    elif ("GOOGLE" in clean_name or "ALPHABET" in clean_name 
          or "GOOG" in clean_name or "GOOGL" in clean_name):
        return blue_chip_tech["GOOG"]
    elif "AMAZON" in clean_name or "AMZN" in clean_name:
        return blue_chip_tech["AMZN"]
    
    # Special case for Apple Inc.
    if stock_name == "Apple Inc.":
        return blue_chip_tech["AAPL"]
    
    # Try to match by company name
    for company, ticker in company_name_mapping.items():
        if company in clean_name:
            if ticker in blue_chip_tech:
                return blue_chip_tech[ticker]
    
    # Try to extract ticker from beginning of name and match
    parts = clean_name.split()
    if parts and parts[0] in blue_chip_tech:
        return blue_chip_tech[parts[0]]
    
    # For unknown stocks, generate a generic assessment
    return {
        "name": stock_name,
        "strength": "Unknown - consider researching its competitive advantage and growth prospects",
        "risk": "Unknown - evaluate its financial stability and market position",
        "rating": "Needs Research"
    }

async def analyze_portfolio_composition(portfolio_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze a user's portfolio to determine asset allocation and diversification needs."""
    if not portfolio_items:
        return {
            "diversification_score": 0,
            "asset_allocation": {},
            "sector_exposure": {},
            "recommendations": ["Build a starter portfolio with core asset classes"]
        }
    
    # Initialize counters
    total_value = 0
    asset_types = {}
    sectors = {}
    individual_stocks = {}
    
    # Asset type to sector mapping (simplified)
    sector_mapping = {
        "AAPL": "technology",
        "MSFT": "technology",
        "AMZN": "consumer_discretionary",
        "GOOG": "technology",
        "GOOGL": "technology",
        "META": "communication_services",
        "TSLA": "consumer_discretionary",
        "NVDA": "technology",
        "BRK.B": "financials",
        "JPM": "financials",
        "JNJ": "healthcare",
        "V": "financials",
        "PG": "consumer_staples",
        "UNH": "healthcare",
        "HD": "consumer_discretionary",
        "BAC": "financials",
        "XOM": "energy",
        "AVGO": "technology",
        "MA": "financials",
        "DIS": "communication_services"
    }
    
    # Analyze each portfolio item
    for item in portfolio_items:
        asset_name = item.get("asset_name", "").strip()
        asset_type = item.get("asset_type", "").lower()
        quantity = float(item.get("quantity", 0))
        current_value = float(item.get("current_value", 0))
        
        if current_value == 0 and "purchase_price" in item:
            # If current value not set, use purchase price
            current_value = float(item["purchase_price"]) * quantity
        
        # Accumulate by asset type
        if asset_type not in asset_types:
            asset_types[asset_type] = 0
        asset_types[asset_type] += current_value
        
        # Track individual stocks for concentration analysis
        if asset_type == "stock":
            stock_symbol = asset_name.split(" ")[0].upper()  # Crude extraction of ticker
            individual_stocks[asset_name] = current_value
            
            # Assign to sector if known
            sector = "unknown"
            for ticker, sector_name in sector_mapping.items():
                if ticker in stock_symbol or ticker in asset_name.upper():
                    sector = sector_name
                    break
            
            if sector not in sectors:
                sectors[sector] = 0
            sectors[sector] += current_value
        
        total_value += current_value
    
    # Calculate percentages if total value > 0
    asset_allocation = {}
    sector_exposure = {}
    diversification_score = 0
    
    if total_value > 0:
        asset_allocation = {asset: (value/total_value)*100 for asset, value in asset_types.items()}
        sector_exposure = {sector: (value/total_value)*100 for sector, value in sectors.items()}
        
        # Calculate simple diversification score (0-100)
        # Based on: number of asset types, sector spread, and individual holding concentration
        type_score = min(len(asset_types) * 20, 40)  # Max 40 points for asset types
        sector_score = min(len(sectors) * 10, 30)    # Max 30 points for sectors
        
        # Concentration score - lower is better for individual stocks
        concentration_penalty = 0
        for stock, value in individual_stocks.items():
            stock_percent = (value/total_value) * 100
            if stock_percent > 10:  # Penalty for >10% in single stock
                concentration_penalty += (stock_percent - 10) / 2
        
        # Calculate final score
        diversification_score = type_score + sector_score - min(concentration_penalty, 30)
        diversification_score = max(0, min(diversification_score, 100))  # Clamp to 0-100
    
    # Determine gaps in the portfolio
    gaps = []
    if "stock" not in asset_types or asset_allocation.get("stock", 0) < 20:
        gaps.append("stock exposure")
    if "bond" not in asset_types and "bond_fund" not in asset_types:
        gaps.append("fixed income")
    if "real_estate" not in asset_types:
        gaps.append("real estate")
    if len(sectors) < 3:
        gaps.append("sector diversification")
    
    return {
        "total_value": total_value,
        "diversification_score": diversification_score,
        "asset_allocation": asset_allocation,
        "sector_exposure": sector_exposure,
        "gaps": gaps
    }

async def get_portfolio_based_recommendations(portfolio_items: List[Dict[str, Any]], risk_tolerance: str) -> List[Dict[str, Any]]:
    """Generate investment recommendations based on portfolio analysis."""
    # Get market trends
    trends = await get_market_trends()
    sentiment = trends.get('current_sentiment_score', 0)
    
    # Analyze the portfolio
    analysis = await analyze_portfolio_composition(portfolio_items)
    diversification_score = analysis.get("diversification_score", 0)
    gaps = analysis.get("gaps", [])
    sector_exposure = analysis.get("sector_exposure", {})
    
    # Base recommendations on gaps and portfolio analysis
    recommendations = []
    
    # Recommend based on portfolio gaps
    if "fixed income" in gaps:
        bond_adjustment = random.uniform(-0.3, 0.3)
        recommendations.append({
            "name": "Total Bond Market ETF",
            "type": "Bond Fund",
            "expected_return": f"{3.2 + bond_adjustment:.1f}%",
            "risk_level": "Low",
            "description": "Broad exposure to US investment-grade bonds",
            "recommendation_reason": "Your portfolio lacks fixed income exposure for stability"
        })
    
    if "stock exposure" in gaps:
        stock_adjustment = sentiment * 0.5
        recommendations.append({
            "name": "Total Stock Market Index Fund",
            "type": "Stock Fund",
            "expected_return": f"{6.0 + stock_adjustment:.1f}%",
            "risk_level": "Medium",
            "description": "Broad exposure to the entire U.S. equity market",
            "recommendation_reason": "Adding broad market equity exposure would improve your portfolio"
        })
    
    if "real estate" in gaps:
        recommendations.append({
            "name": "REIT Index Fund",
            "type": "Real Estate",
            "expected_return": f"{5.5 + sentiment*0.4:.1f}%",
            "risk_level": "Medium",
            "description": "Exposure to real estate investment trusts across various property sectors",
            "recommendation_reason": "Adding real estate can improve diversification and provide income"
        })
    
    if "sector diversification" in gaps:
        # Find underrepresented sectors
        low_exposure_sectors = []
        for sector in ["technology", "healthcare", "financials", "consumer_staples", "utilities", "energy"]:
            if sector not in sector_exposure or sector_exposure[sector] < 5:
                low_exposure_sectors.append(sector)
        
        if low_exposure_sectors:
            # Recommend sector funds for diversification
            sector_to_recommend = random.choice(low_exposure_sectors)
            sector_names = {
                "technology": "Technology",
                "healthcare": "Healthcare",
                "financials": "Financial",
                "consumer_staples": "Consumer Staples",
                "utilities": "Utilities",
                "energy": "Energy"
            }
            
            recommendations.append({
                "name": f"{sector_names.get(sector_to_recommend, sector_to_recommend.title())} Sector ETF",
                "type": "Sector Fund",
                "expected_return": f"{6.5 + sentiment*0.8:.1f}%",
                "risk_level": "Medium-High",
                "description": f"Focused exposure to {sector_to_recommend} sector companies",
                "recommendation_reason": f"Your portfolio would benefit from {sector_to_recommend} sector exposure"
            })
    
    # Add international exposure if not present
    has_international = False
    for item in portfolio_items:
        if "international" in item.get("asset_name", "").lower() or "global" in item.get("asset_name", "").lower():
            has_international = True
            break
    
    if not has_international:
        recommendations.append({
            "name": "International Equity Index Fund",
            "type": "Stock Fund",
            "expected_return": f"{5.8 + sentiment*0.6:.1f}%",
            "risk_level": "Medium",
            "description": "Exposure to developed international markets outside the U.S.",
            "recommendation_reason": "Adding international exposure would reduce geographic concentration"
        })
    
    # If diversification score is low, recommend core portfolio building
    if diversification_score < 40:
        recommendations.append({
            "name": "Three-Fund Core Portfolio",
            "type": "Portfolio Strategy",
            "expected_return": "Varies by allocation",
            "risk_level": risk_tolerance.capitalize(),
            "description": "A simple portfolio of Total US Stock Market, International Stock, and Bond index funds",
            "recommendation_reason": "Your portfolio would benefit from a core diversified foundation"
        })
    
    # Add risk-specific recommendations
    if risk_tolerance.lower() == "high" and diversification_score > 50:
        recommendations.append({
            "name": "Emerging Markets ETF",
            "type": "Stock Fund",
            "expected_return": f"{8.5 + sentiment*1.5:.1f}%",
            "risk_level": "High",
            "description": "Exposure to developing economies with high growth potential",
            "recommendation_reason": "Aligns with your high risk tolerance for potentially higher returns"
        })
    
    if risk_tolerance.lower() == "low" and ("bond" not in analysis.get("asset_allocation", {})):
        recommendations.append({
            "name": "Short-Term Treasury Bond Fund",
            "type": "Bond Fund",
            "expected_return": f"{2.8 + (sentiment*0.2):.1f}%",
            "risk_level": "Very Low",
            "description": "Government-backed bonds with short duration and minimal interest rate risk",
            "recommendation_reason": "Provides stability aligned with your low risk preference"
        })
    
    # Ensure we have at least 3 recommendations
    if len(recommendations) < 3:
        # Add some general good recommendations based on risk tolerance
        if risk_tolerance.lower() == "low":
            additional = await get_low_risk_investment_options()
        else:
            additional = await get_personalized_investment_recommendations_by_risk(risk_tolerance)
        
        # Add recommendations we don't already have
        for item in additional:
            if len(recommendations) >= 5:  # Cap at 5 recommendations
                break
                
            # Check if we already have this recommendation
            if not any(r["name"] == item["name"] for r in recommendations):
                # Add the recommendation reason
                item["recommendation_reason"] = "Generally suitable investment for your risk profile"
                recommendations.append(item)
    
    return recommendations[:5]  # Limit to 5 recommendations

async def get_personalized_investment_recommendations_by_risk(risk_tolerance: str = "medium") -> List[Dict[str, Any]]:
    """Get generic risk-based investment recommendations."""
    # Get market trends
    trends = await get_market_trends()
    sentiment = trends.get('current_sentiment_score', 0)
    
    # Generate medium-risk options
    medium_risk = [
        {
            "name": "Total Stock Market Index Fund", 
            "type": "Stock Fund", 
            "expected_return": f"{6.0 + sentiment:.1f}%", 
            "risk_level": "Medium",
            "description": "Broad exposure to the entire U.S. equity market"
        },
        {
            "name": "Growth Stock ETF", 
            "type": "Stock Fund", 
            "expected_return": f"{7.5 + sentiment*1.2:.1f}%", 
            "risk_level": "Medium",
            "description": "Companies with above-average growth potential"
        },
        {
            "name": "International Developed Markets Fund", 
            "type": "Stock Fund", 
            "expected_return": f"{5.5 + sentiment:.1f}%", 
            "risk_level": "Medium",
            "description": "Exposure to established international markets"
        }
    ]
    
    # Generate high-risk options
    high_risk = [
        {
            "name": "Small Cap Growth Fund", 
            "type": "Stock Fund", 
            "expected_return": f"{9.0 + sentiment*1.5:.1f}%", 
            "risk_level": "High",
            "description": "Small companies with high growth potential"
        },
        {
            "name": "Emerging Markets ETF", 
            "type": "Stock Fund", 
            "expected_return": f"{8.5 + sentiment*1.5:.1f}%", 
            "risk_level": "High",
            "description": "Exposure to developing economies with high growth potential"
        },
        {
            "name": "Technology Sector Fund", 
            "type": "Sector Fund", 
            "expected_return": f"{10.0 + sentiment*2:.1f}%", 
            "risk_level": "High",
            "description": "Focused on technology companies with innovation potential"
        }
    ]
    
    risk_levels = {
        "low": await get_low_risk_investment_options(),
        "medium": medium_risk,
        "high": high_risk
    }
    
    return risk_levels.get(risk_tolerance.lower(), medium_risk)

async def analyze_portfolio_quality(portfolio_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the quality of holdings in a portfolio and provide an assessment."""
    if not portfolio_items:
        return {
            "portfolio_assessment": "No holdings to analyze. Consider building a diversified portfolio.",
            "holdings_analysis": [],
            "overall_rating": "N/A"
        }
    
    # Get portfolio composition analysis first
    composition = await analyze_portfolio_composition(portfolio_items)
    
    # Analyze individual holdings
    holdings_analysis = []
    for item in portfolio_items:
        asset_name = item.get("asset_name", "").strip()
        asset_type = item.get("asset_type", "").lower()
        current_value = float(item.get("current_value", 0))
        purchase_price = float(item.get("purchase_price", 0)) 
        quantity = float(item.get("quantity", 0))
        
        # Calculate performance if possible
        performance = {}
        if purchase_price > 0 and current_value > 0:
            percent_change = ((current_value / quantity) - purchase_price) / purchase_price * 100
            performance = {
                "percent_change": f"{percent_change:.2f}%",
                "absolute_change": f"${(current_value / quantity) - purchase_price:.2f} per share"
            }
        
        # Get evaluation based on asset type
        evaluation = {}
        if asset_type == "stock":
            evaluation = await evaluate_stock_holding(asset_name)
        else:
            evaluation = {
                "name": asset_name,
                "strength": f"Typical {asset_type} characteristics",
                "risk": f"Typical {asset_type} risks",
                "rating": "Standard"
            }
        
        holdings_analysis.append({
            "asset_name": asset_name,
            "asset_type": asset_type,
            "value": current_value,
            "percentage_of_portfolio": (current_value / composition.get("total_value", 1)) * 100,
            "performance": performance,
            "evaluation": evaluation
        })
    
    # Generate overall portfolio assessment
    diversification_score = composition.get("diversification_score", 0)
    gaps = composition.get("gaps", [])
    
    # Determine overall portfolio rating
    overall_rating = "Needs Improvement"
    if diversification_score >= 80:
        overall_rating = "Excellent"
    elif diversification_score >= 60:
        overall_rating = "Good"
    elif diversification_score >= 40:
        overall_rating = "Fair"
    
    # Generate human-readable assessment
    assessment_parts = []
    
    # Evaluate diversification
    if diversification_score < 30:
        assessment_parts.append("Your portfolio lacks diversification and is highly concentrated, which increases risk.")
    elif diversification_score < 60:
        assessment_parts.append("Your portfolio has moderate diversification but could be improved to reduce risk.")
    else:
        assessment_parts.append("Your portfolio shows good diversification across multiple assets.")
    
    # Comment on gaps
    if gaps:
        gap_text = ", ".join(gaps)
        assessment_parts.append(f"Your portfolio is missing exposure to: {gap_text}.")
    
    # Comment on individual holdings
    strong_holdings = [h["asset_name"] for h in holdings_analysis if h["evaluation"].get("rating") == "Strong"]
    if strong_holdings:
        strong_text = ", ".join(strong_holdings)
        assessment_parts.append(f"Your holdings in {strong_text} are considered strong quality assets.")
    
    # Overall assessment
    portfolio_assessment = " ".join(assessment_parts)
    
    return {
        "portfolio_assessment": portfolio_assessment,
        "holdings_analysis": holdings_analysis,
        "overall_rating": overall_rating,
        "diversification_score": diversification_score
    }

async def get_personalized_investment_recommendations(user_id: str, risk_tolerance: str = "medium", portfolio_items: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Get personalized investment recommendations based on user profile, market conditions, and portfolio."""
    # If portfolio items were not provided, default to risk-based recommendations
    if not portfolio_items:
        return await get_personalized_investment_recommendations_by_risk(risk_tolerance)
    
    # Generate truly personalized recommendations based on portfolio analysis
    return await get_portfolio_based_recommendations(portfolio_items, risk_tolerance)