import autogen
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.models.transaction import Transaction, TransactionCategory
from app.utils.llm_config import get_groq_config

# Configuration for the budget planner agent
BUDGET_AGENT_CONFIG = {
    "name": "Budget Planner",
    "description": "I analyze spending patterns and provide personalized budget recommendations."
    # llm_config is now handled dynamically through get_groq_config
}

class BudgetPlannerAgent:
    """Agent responsible for analyzing spending and recommending budgets."""
    
    def __init__(self, model_config=None):
        """Initialize the budget planner agent with optional model configuration."""
        # Use Groq configuration with customizable temperature for budget recommendations
        config = model_config or get_groq_config(temperature=0.2).dict()
        
        # Create the Autogen assistant agent
        self.agent = autogen.AssistantAgent(
            name=BUDGET_AGENT_CONFIG["name"],
            system_message=self._build_system_message(),
            llm_config=config
        )
        
        # User proxy agent to interact with the assistant
        self.user_proxy = autogen.UserProxyAgent(
            name="Finance System",
            is_termination_msg=lambda x: "BUDGET_ANALYSIS_COMPLETE" in x.get("content", ""),
            human_input_mode="NEVER"  # No human input needed for system-to-system communication
        )
    
    def _build_system_message(self) -> str:
        """Build the system message that defines the behavior of the budget planner agent."""
        return f"""You are {BUDGET_AGENT_CONFIG['name']}, {BUDGET_AGENT_CONFIG['description']}
        
        You will be presented with a user's financial transactions and spending patterns. Your task is to:
        
        1. Analyze the user's spending habits across different categories
        2. Identify areas where the user might be overspending
        3. Suggest realistic budget limits for each spending category
        4. Provide practical tips on how to reduce expenses in problem areas
        5. Suggest savings goals based on the user's income and spending patterns
        
        When providing advice:
        - Be specific with numbers and percentages
        - Use simple, non-technical language
        - Be empathetic and encouraging
        - Provide actionable suggestions that are realistic
        - Consider the user's lifestyle and spending patterns
        
        Always format your final response with:
        BUDGET_ANALYSIS_COMPLETE to signal the end of your analysis.
        """
    
    def create_budget_plan(self, transactions: List[Transaction], target_savings_percent: float = 20.0) -> Dict[str, Any]:
        """Create a personalized budget plan based on transaction history."""
        if not transactions:
            return {
                "status": "error",
                "message": "No transaction data available to create a budget plan.",
                "budget_plan": None
            }
        
        # Prepare transaction data for analysis
        spending_summary = self._analyze_spending_patterns(transactions)
        
        # Format the transaction data for the LLM
        transactions_formatted = self._format_transactions_for_llm(transactions)
        spending_summary_formatted = self._format_spending_summary_for_llm(spending_summary)
        
        # Create a prompt with the formatted transaction data
        prompt = f"""Here is the user's transaction history:
        
        {transactions_formatted}
        
        Here is a summary of their spending by category:
        
        {spending_summary_formatted}
        
        Based on this data, please create a personalized budget plan with the goal of saving at least {target_savings_percent}% of income.
        Include specific limits for each spending category, and provide practical tips to help the user stick to the budget.
        """
        
        # Initialize chat with the user proxy (system-to-system, no human needed)
        self.user_proxy.initiate_chat(
            self.agent,
            message=prompt
        )
        
        # Extract the budget plan from the agent's response
        last_message = self.user_proxy.chat_messages[self.agent.name][-1]["content"]
        
        # Process the agent's response into a structured budget plan
        budget_plan = self._process_budget_response(last_message, spending_summary)
        
        return {
            "status": "completed",
            "message": "Budget plan created successfully.",
            "budget_plan": budget_plan
        }
    
    def _analyze_spending_patterns(self, transactions: List[Transaction]) -> Dict[str, Any]:
        """Analyze spending patterns from transaction history."""
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([
            {
                "id": t.id,
                "amount": t.amount,
                "category": str(t.category.value) if hasattr(t.category, "value") else str(t.category),
                "timestamp": t.timestamp
            } 
            for t in transactions
        ])
        
        # Analyze income vs. expenses
        income_df = df[df["category"] == "income"]
        expenses_df = df[df["category"] != "income"]
        
        total_income = income_df["amount"].sum()
        total_expenses = expenses_df["amount"].sum()
        net_savings = total_income - total_expenses
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
        
        # Analyze spending by category
        category_spending = expenses_df.groupby("category")["amount"].sum().to_dict()
        category_percentage = {}
        for category, amount in category_spending.items():
            category_percentage[category] = (amount / total_expenses * 100) if total_expenses > 0 else 0
        
        # Time-based analysis (trends over time)
        expenses_df["month"] = expenses_df["timestamp"].dt.to_period("M").astype(str)
        monthly_spending = expenses_df.groupby("month")["amount"].sum().to_dict()
        
        # Category trends over time
        category_trend = {}
        for category in expenses_df["category"].unique():
            category_data = expenses_df[expenses_df["category"] == category]
            category_trend[category] = category_data.groupby("month")["amount"].sum().to_dict()
        
        return {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_savings": net_savings,
            "savings_rate": savings_rate,
            "category_spending": category_spending,
            "category_percentage": category_percentage,
            "monthly_spending": monthly_spending,
            "category_trend": category_trend
        }
    
    def _format_transactions_for_llm(self, transactions: List[Transaction], limit: int = 20) -> str:
        """Format transaction data for LLM consumption (limited to recent transactions)."""
        # Sort transactions by date (most recent first) and limit to the most recent ones
        sorted_transactions = sorted(transactions, key=lambda t: t.timestamp, reverse=True)[:limit]
        
        formatted = "Date | Amount | Category | Description\n"
        formatted += "--- | --- | --- | ---\n"
        
        for t in sorted_transactions:
            date_str = t.timestamp.strftime("%Y-%m-%d")
            amount_str = f"${t.amount:.2f}" if str(t.category) != "income" else f"${t.amount:.2f} (income)"
            category = t.category.value if hasattr(t.category, "value") else t.category
            description = t.description if t.description else "(No description)"
            formatted += f"{date_str} | {amount_str} | {category} | {description}\n"
        
        return formatted
    
    def _format_spending_summary_for_llm(self, spending_summary: Dict[str, Any]) -> str:
        """Format spending summary for LLM consumption."""
        formatted = "## Income and Savings\n"
        formatted += f"Total Income: ${spending_summary['total_income']:.2f}\n"
        formatted += f"Total Expenses: ${spending_summary['total_expenses']:.2f}\n"
        formatted += f"Net Savings: ${spending_summary['net_savings']:.2f}\n"
        formatted += f"Savings Rate: {spending_summary['savings_rate']:.1f}%\n\n"
        
        formatted += "## Spending by Category\n"
        formatted += "Category | Amount | % of Expenses\n"
        formatted += "--- | --- | ---\n"
        
        for category, amount in spending_summary["category_spending"].items():
            percentage = spending_summary["category_percentage"][category]
            formatted += f"{category} | ${amount:.2f} | {percentage:.1f}%\n"
        
        return formatted
    
    def _process_budget_response(self, response: str, spending_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process the LLM's response into a structured budget plan."""
        # Default structure for the budget plan
        budget_plan = {
            "total_income": spending_summary["total_income"],
            "recommended_savings": spending_summary["total_income"] * 0.2,  # Default 20% savings
            "category_limits": {},
            "general_advice": [],
            "category_advice": {}
        }
        
        # Very simple extraction - in production would use more robust parsing
        lines = response.split("\n")
        current_section = None
        current_category = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            lower_line = line.lower()
            if "budget limit" in lower_line or "category limit" in lower_line or "spending limit" in lower_line:
                current_section = "limits"
                current_category = None
                continue
            elif "advice" in lower_line or "tip" in lower_line or "recommendation" in lower_line and "category" not in lower_line:
                current_section = "general_advice"
                current_category = None
                continue
            elif "category" in lower_line and ("tip" in lower_line or "advice" in lower_line):
                current_section = "category_advice"
                current_category = None
                continue
                
            # Process content based on current section
            if current_section == "limits":
                # Try to extract category and amount
                if ":" in line and ("$" in line or "%" in line):
                    parts = line.split(":")
                    category = parts[0].strip().lower()
                    amount_text = parts[1].strip()
                    
                    # Extract the dollar amount
                    amount = None
                    for word in amount_text.split():
                        if "$" in word:
                            try:
                                amount = float(word.replace("$", "").replace(",", ""))
                                break
                            except ValueError:
                                pass
                    
                    if amount and category:
                        budget_plan["category_limits"][category] = amount
            
            elif current_section == "general_advice":
                # Add the line as a piece of general advice if it looks like one
                if len(line) > 15 and not line.startswith("#"):
                    budget_plan["general_advice"].append(line)
            
            elif current_section == "category_advice":
                # Try to identify the category first
                if ":" in line and not current_category:
                    category_part = line.split(":")[0].strip().lower()
                    for category in spending_summary["category_spending"].keys():
                        if category.lower() in category_part:
                            current_category = category
                            budget_plan["category_advice"][current_category] = []
                            advice_part = line.split(":", 1)[1].strip()
                            if advice_part:
                                budget_plan["category_advice"][current_category].append(advice_part)
                            break
                elif current_category and len(line) > 10:
                    # Add more advice to the current category
                    budget_plan["category_advice"][current_category].append(line)
        
        # If we couldn't extract category limits from the response, set reasonable defaults
        if not budget_plan["category_limits"]:
            remaining_budget = budget_plan["total_income"] - budget_plan["recommended_savings"]
            for category, percentage in spending_summary["category_percentage"].items():
                if category != "income":
                    # Set limit to slightly less than historical spending
                    historical_spending = spending_summary["category_spending"].get(category, 0)
                    budget_plan["category_limits"][category] = historical_spending * 0.9  # 10% reduction
        
        return budget_plan