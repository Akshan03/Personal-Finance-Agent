import autogen
from typing import List, Dict, Any
import pandas as pd
import random
from datetime import datetime, timedelta

from app.models.portfolio import Portfolio
from app.services import market_service
from app.utils.llm_config import get_groq_config, get_agent_config

# Configuration for the investment advisor agent
INVESTMENT_AGENT_CONFIG = {
    "name": "Investment Advisor",
    "description": "I analyze market trends and suggest low-risk investment options based on financial goals."
    # llm_config is now handled dynamically through get_groq_config
}

class InvestmentAdvisorAgent:
    """Agent responsible for recommending investment options."""
    
    def __init__(self, model_config=None):
        """Initialize the investment advisor agent with optional model configuration."""
        # Use agent configuration with Docker disabled and low temperature for more conservative investment advice
        config = model_config or get_agent_config(temperature=0.1)
        
        # Create the Autogen assistant agent
        self.agent = autogen.AssistantAgent(
            name=INVESTMENT_AGENT_CONFIG["name"],
            system_message=self._build_system_message(),
            llm_config=config
        )
        
        # User proxy agent to interact with the assistant
        self.user_proxy = autogen.UserProxyAgent(
            name="Finance System",
            is_termination_msg=lambda x: "INVESTMENT_ADVICE_COMPLETE" in x.get("content", ""),
            human_input_mode="NEVER",  # No human input needed for system-to-system communication
            code_execution_config={"use_docker": False}  # Explicitly disable Docker requirement
        )
    
    def _build_system_message(self) -> str:
        """Build the system message that defines the behavior of the investment advisor agent."""
        return f"""You are {INVESTMENT_AGENT_CONFIG['name']}, {INVESTMENT_AGENT_CONFIG['description']}
        
        You will be presented with market data and potentially a user's existing portfolio. Your task is to:
        
        1. Analyze current market conditions and trends
        2. Consider the user's risk tolerance (default to low-risk unless specified otherwise)
        3. Recommend suitable low-risk investment options
        4. Provide clear explanations for your recommendations in simple terms
        5. Include enough detail to help the user make informed decisions
        6. Suggest asset allocation percentages across different recommended options
        
        When providing advice:
        - Prioritize safe, low-risk investments for capital preservation
        - Explain market concepts in simple, non-technical language
        - Be transparent about potential risks and expected returns
        - Consider diversification across different asset classes
        - Show realistic expected returns based on historical performance
        
        Always format your final response with:
        INVESTMENT_ADVICE_COMPLETE to signal the end of your analysis.
        """
    
    def get_investment_recommendations(self, 
                                      savings_amount: float, 
                                      risk_tolerance: str = "low", 
                                      time_horizon: str = "medium", 
                                      current_portfolio: List[Portfolio] = None) -> Dict[str, Any]:
        """Generate personalized investment recommendations."""
        # Get current market data from the market service
        market_trends = market_service.get_market_trends()
        low_risk_options = market_service.get_low_risk_investment_options()
        
        # Format market data for the LLM
        market_data_formatted = self._format_market_data_for_llm(market_trends, low_risk_options)
        portfolio_formatted = self._format_portfolio_for_llm(current_portfolio) if current_portfolio else "No existing portfolio."
        
        # Create a prompt with the formatted data
        prompt = f"""Here's the current market data and trends:
        
        {market_data_formatted}
        
        User profile:
        - Amount available to invest: ${savings_amount:.2f}
        - Risk tolerance: {risk_tolerance}
        - Investment time horizon: {time_horizon}
        
        Current portfolio:
        {portfolio_formatted}
        
        Based on this information, please recommend suitable investment options for this user.
        Include specific allocation percentages and explain your reasoning.
        """
        
        # Initialize chat with the user proxy 
        self.user_proxy.initiate_chat(
            self.agent,
            message=prompt
        )
        
        # Extract the recommendations from the agent's response
        last_message = self.user_proxy.chat_messages[self.agent.name][-1]["content"]
        
        # Process the agent's response into a structured recommendation
        recommendations = self._process_investment_response(last_message, savings_amount)
        
        return {
            "status": "completed",
            "message": "Investment recommendations generated successfully.",
            "recommendations": recommendations
        }
    
    def _format_market_data_for_llm(self, market_trends: Dict[str, Any], low_risk_options: List[Dict[str, Any]]) -> str:
        """Format market data for LLM consumption."""
        formatted = "## Current Market Trends\n"
        
        if 'current_sentiment_score' in market_trends:
            sentiment = market_trends['current_sentiment_score']
            sentiment_desc = "negative" if sentiment < -0.3 else "neutral" if sentiment < 0.3 else "positive"
            formatted += f"Market Sentiment: {sentiment_desc} ({sentiment:.2f})\n"
        
        for key, value in market_trends.items():
            if key != 'current_sentiment_score' and not isinstance(value, dict):
                formatted += f"{key.replace('_', ' ').title()}: {value}\n"
        
        formatted += "\n## Low-Risk Investment Options\n"
        formatted += "Investment | Type | Expected Return | Risk Level\n"
        formatted += "--- | --- | --- | ---\n"
        
        for option in low_risk_options:
            formatted += f"{option['name']} | {option['type']} | {option['expected_return']} | {option['risk_level']}\n"
        
        return formatted
    
    def _format_portfolio_for_llm(self, portfolio: List[Portfolio]) -> str:
        """Format portfolio data for LLM consumption."""
        if not portfolio:
            return "No existing investments."
            
        formatted = "Asset | Type | Quantity | Purchase Price | Current Value\n"
        formatted += "--- | --- | --- | --- | ---\n"
        
        for asset in portfolio:
            current_value = asset.current_value if asset.current_value else asset.purchase_price * asset.quantity
            formatted += f"{asset.asset_name} | {asset.asset_type} | {asset.quantity} | ${asset.purchase_price:.2f} | ${current_value:.2f}\n"
        
        return formatted
    
    def _process_investment_response(self, response: str, total_amount: float) -> Dict[str, Any]:
        """Process the LLM's response into a structured investment recommendation."""
        
        # Default structure
        recommendation = {
            "total_investment_amount": total_amount,
            "allocation": {},
            "reasoning": [],
            "expected_returns": {},
            "risks": {}
        }
        
        # Simple parsing of the response - in production, use more robust methods
        lines = response.split("\n")
        current_section = None
        current_investment = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identify sections (very basic approach)
            lower_line = line.lower()
            if "allocation" in lower_line or "recommend" in lower_line and "%" in line:
                current_section = "allocation"
                current_investment = None
                continue
            elif "reason" in lower_line or "why" in lower_line:
                current_section = "reasoning"
                continue
            elif "return" in lower_line or "expect" in lower_line:
                current_section = "returns"
                continue
            elif "risk" in lower_line:
                current_section = "risks"
                continue
                
            # Process the line based on the current section
            if current_section == "allocation" and (":" in line or "-" in line) and "%" in line:
                # Try to extract investment name and allocation percentage
                parts = line.split(":") if ":" in line else line.split("-")
                investment_name = parts[0].strip()
                
                # Extract percentage
                percentage = None
                for word in parts[1].split():
                    if "%" in word:
                        try:
                            percentage = float(word.replace("%", ""))
                            break
                        except ValueError:
                            pass
                
                if percentage is not None:
                    recommendation["allocation"][investment_name] = percentage / 100
                    current_investment = investment_name
                    
                    # Calculate dollar amount based on percentage
                    amount = total_amount * (percentage / 100)
                    recommendation["expected_returns"][investment_name] = "Unknown"  # Default value
                    recommendation["risks"][investment_name] = "Unknown"  # Default value
            
            elif current_section == "reasoning" and len(line) > 15:
                recommendation["reasoning"].append(line)
            
            elif current_section == "returns" and current_investment:
                # Try to extract expected return for the current investment
                if current_investment in line.lower() and "%" in line:
                    parts = line.split(":") if ":" in line else [line]
                    for word in parts[-1].split():
                        if "%" in word:
                            recommendation["expected_returns"][current_investment] = word
                            break
            
            elif current_section == "risks" and current_investment:
                # Extract risk information for the current investment
                if current_investment in line.lower():
                    parts = line.split(":") if ":" in line else [line]
                    risk_desc = parts[-1].strip() if len(parts) > 1 else line
                    recommendation["risks"][current_investment] = risk_desc
        
        # Normalize allocations to ensure they sum to 100%
        total_allocation = sum(recommendation["allocation"].values())
        if total_allocation > 0 and abs(total_allocation - 1.0) > 0.01:  # If not close to 1.0
            for investment in recommendation["allocation"]:
                recommendation["allocation"][investment] /= total_allocation
        
        return recommendation