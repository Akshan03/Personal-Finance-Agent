import autogen
import os
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.config import settings
from app.models.transaction import Transaction, TransactionCategory
from app.utils.llm_config import get_groq_config, get_agent_config

# Configuration for the budget planner agent
BUDGET_AGENT_CONFIG = {
    "name": "Budget Planner",
    "description": "I analyze spending patterns and provide personalized budget recommendations."
    # llm_config is now handled dynamically through get_groq_config
}

class BudgetPlanningAgent:
    """Agent responsible for analyzing spending and recommending budgets."""
    
    def __init__(self, model_config=None):
        """Initialize the budget planner agent with optional model configuration."""
        # Use agent configuration with Docker disabled and customizable temperature for budget recommendations
        config = model_config or get_agent_config(temperature=0.2)
        
        # Create the Autogen assistant agent with proper Groq configuration
        self.agent = autogen.AssistantAgent(
            name=BUDGET_AGENT_CONFIG["name"],
            system_message=self._build_system_message(),
            llm_config=config
        )
        
        # Get the Groq API key and configure client
        groq_api_key = os.getenv("GROQ_API_KEY", settings.groq_api_key)
        
        # Configure client to use Groq instead of OpenAI
        import openai
        from openai import OpenAI
        
        # For autogen's OpenAI Client we need to set these environment variables
        # This ensures the client uses the right API endpoint
        os.environ["OPENAI_API_KEY"] = groq_api_key
        os.environ["OPENAI_API_BASE"] = "https://api.groq.com/openai/v1"
        
        # Replace the OpenAI client in the agent with one specifically configured for Groq
        self.agent.llm_config["api_type"] = "openai"  # Must be 'openai' for compatibility
        self.agent.llm_config["api_key"] = groq_api_key
        
        # User proxy agent to interact with the assistant
        self.user_proxy = autogen.UserProxyAgent(
            name="Finance System",
            is_termination_msg=lambda x: "BUDGET_ANALYSIS_COMPLETE" in x.get("content", ""),
            human_input_mode="NEVER"  # No human input needed for system-to-system communication
            # Removed code_execution_config to avoid compatibility issues with Groq API
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
    
    async def generate_budget_plan(self, transaction_data: List[Dict[str, Any]], timeframe: str = "monthly", income: float = 0, expenses: float = 0, savings: float = 0, target_savings_percent: float = 20.0) -> Dict[str, Any]:
        """Generate a personalized budget plan based on transaction data.
        
        This method is called by the API endpoint and returns a structured budget plan.
        """
        # Since we're using the Groq API directly instead of Autogen, let's implement
        # a simpler direct approach for budget planning

        if not transaction_data:
            return {
                "summary": "No transaction data available to create a budget plan.",
                "budget_allocation": {},
                "savings_recommendations": [],
                "spending_insights": [],
                "category_analysis": {}
            }
        
        # Prepare transaction data summary
        categories = {}
        for tx in transaction_data:
            category = tx["category"].lower()
            amount = float(tx["amount"])
            
            if category not in categories:
                categories[category] = 0
            
            categories[category] += amount
        
        # Format the transaction summary for the LLM
        if income == 0 and expenses == 0:
            # Calculate from transactions
            income = sum([amount for category, amount in categories.items() if category == "income"])
            expenses = sum([amount for category, amount in categories.items() if category != "income"])
            savings = income - expenses
        
        # Create a summary of spending by category for the LLM
        category_summary = ""
        for category, amount in categories.items():
            if category != "income":
                percentage = (amount / expenses) * 100 if expenses > 0 else 0
                category_summary += f"{category.capitalize()}: ${amount:.2f} ({percentage:.1f}% of expenses)\n"
        
        # Configure prompt based on timeframe
        timeframe_multiplier = 1  # Default for monthly
        if timeframe.lower() == "quarterly":
            timeframe_multiplier = 3
        elif timeframe.lower() == "yearly":
            timeframe_multiplier = 12
        
        # Prepare the prompt for the LLM
        prompt = f"""
        You are a financial advisor helping create a personalized budget plan.
        
        USER DATA:
        - Income: ${income:.2f} {timeframe}
        - Expenses: ${expenses:.2f} {timeframe}
        - Current Savings: ${savings:.2f} {timeframe}
        - Current Savings Rate: {(savings/income)*100 if income > 0 else 0:.1f}%
        - Target Savings Rate: {target_savings_percent}%
        - Timeframe: {timeframe.capitalize()}
        
        Transaction data by category:
        {{
            {', '.join([f'"{tx["category"]}": {tx["amount"]}' for tx in transaction_data])}
        }}
        
        Please create a detailed budget plan for the user with the following components in JSON format:
        1. A summary of their overall financial situation and a concise overview of the budget
        2. A recommended budget allocation for each spending category with amounts and percentages
        3. Detailed analysis of each spending category compared to benchmarks
        4. Categorization of expenses as fixed vs. discretionary
        5. Specific savings recommendations
        6. Spending insights for each category, including whether they're spending too much or too little
        
        Return ONLY a valid JSON object with the following structure:
        {{
            "summary": {{
                "total_income": 3500,  // Total income amount
                "total_expenses": 2673.25,  // Total expenses amount
                "net_savings": 826.75,  // Amount saved
                "savings_rate": 23.62,  // Percentage of income saved
                "category_breakdown": {{  // Breakdown of expenses by category
                    "category_name": {{
                        "amount": 250.75,  // Actual amount spent
                        "percentage": 9.38  // Percentage of total expenses
                    }}
                    // Additional categories
                }}
            }},
            "insights": [  // General financial insights
                "Your fixed expenses are 37.7% of income, within the recommended 50%.",
                "Your discretionary spending is 24.4% of income, within the recommended 30%.",
                "Your savings rate is 23.6%, above the recommended 20%. Great job!"
                // Additional insights about specific categories
            ],
            "recommendations": [  // Specific actionable recommendations
                "Consider reducing discretionary spending on shopping to increase savings.",
                "Evaluate your housing costs to see if there are opportunities to reduce them."
                // Additional recommendations
            ],
            "fixed_vs_discretionary": {{  // Analysis of fixed vs. discretionary expenses
                "fixed": {{  // Fixed expenses (unavoidable, consistent monthly costs)
                    "total": 1320.5,  // Total amount of fixed expenses
                    "percentage_of_income": 37.73,  // Fixed expenses as percentage of income
                    "breakdown": {{  // Breakdown of fixed expenses by category
                        "housing": {{
                            "amount": 1200,
                            "percentage": 44.89
                        }},
                        "utilities": {{
                            "amount": 120.5,
                            "percentage": 4.51
                        }}
                        // Additional fixed expense categories
                    }}
                }},
                "discretionary": {{  // Discretionary expenses (variable, could be reduced)
                    "total": 852.75,  // Total amount of discretionary expenses
                    "percentage_of_income": 24.36,  // Discretionary expenses as percentage of income
                    "breakdown": {{  // Breakdown of discretionary expenses by category
                        "entertainment": {{
                            "amount": 45.5,
                            "percentage": 1.70
                        }},
                        // Additional discretionary expense categories
                    }}
                }}
            }},
            "benchmarks": {{  // Financial benchmarks based on the 50/30/20 rule
                "needs": 1750,  // 50% of income for needs
                "wants": 1050,  // 30% of income for wants
                "savings": 700,  // 20% of income for savings
                "rule": "50/30/20"  // The budgeting rule being applied
            }},
            "category_analysis": {{  // Detailed analysis of each spending category
                "category_name": {{  // Analysis for each category (e.g., food, housing, etc.)
                    "amount": 250.75,  // Amount spent in this category
                    "percentage_of_income": 7.16,  // Percentage of income spent on this category
                    "benchmark_min": 10,  // Minimum recommended percentage
                    "benchmark_max": 15,  // Maximum recommended percentage
                    "status": "below",  // Status: below, normal, or above recommended range
                    "advice": "Your spending in Food is below typical ranges. This is good if you're being efficient with grocery shopping, but ensure you're meeting nutritional needs."
                }}
                // Additional categories
            }},
            "budget_allocation": {{  // Recommended budget allocation for each category
                "category_name": {{
                    "amount": 350.0,  // Recommended spending amount
                    "percentage": 10.0  // Percentage of total income
                }},
                // Additional categories
            }},
            "savings_recommendations": [  // Specific savings recommendations
                "Set up automatic transfers to a high-yield savings account.",
                "Consider increasing your retirement contributions."
                // Additional savings recommendations
            ],
            "spending_insights": [  // Specific spending insights
                "Housing costs account for nearly 45% of expenses, indicating a potential area for optimization.",
                "Your spending on entertainment is well below average, which is helping your overall budget."
                // Additional spending insights
            ]
        }}
        """
        
        # Get the model configuration with Groq API
        model_config = get_groq_config(temperature=0.2)
        
        # Use the OpenAI client to send the prompt to the Groq API
        try:
            import openai
            from openai import OpenAI
            
            # Get the Groq API key from settings
            groq_api_key = os.getenv("GROQ_API_KEY", settings.groq_api_key)
            
            # Use a hardcoded known valid model to ensure it works
            groq_model = "llama3-70b-8192"  # Using a currently supported model (as of April 2025)
            
            # Create an OpenAI client configured to use Groq
            client = OpenAI(
                api_key=groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            
            # Send the request to the LLM
            response = client.chat.completions.create(
                model=groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2048
            )
            
            # Extract the response content
            llm_response = response.choices[0].message.content
            
            # Parse the JSON response
            import json
            import re
            
            # Extract JSON from the response (it might be embedded in a code block)
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', llm_response, re.DOTALL)
            if json_match:
                budget_plan = json.loads(json_match.group(1))
            else:
                # Try to load the whole response as JSON
                budget_plan = json.loads(llm_response)
            
            # Return the budget plan
            return budget_plan
            
        except Exception as e:
            # If there's an error, return a basic budget plan
            print(f"Error in budget planning: {str(e)}")
            return {
                "summary": f"We encountered an issue generating your budget plan: {str(e)}. Based on your data, you should aim to save ${savings:.2f} ({(savings/income)*100 if income > 0 else 0:.1f}%) each {timeframe}.",
                "budget_allocation": {
                    category: {
                        "amount": amount,
                        "percentage": amount / expenses if expenses > 0 else 0
                    }
                    for category, amount in categories.items()
                    if category != "income"
                },
                "savings_recommendations": [
                    "Try to reduce your largest expense categories.",
                    "Set up automatic transfers to savings accounts.",
                    "Track your expenses regularly to stay on budget."
                ],
                "spending_insights": [
                    f"Your current savings rate is {(savings/income)*100 if income > 0 else 0:.1f}%.",
                    f"Your largest expense category is {max([(category, amount) for category, amount in categories.items() if category != 'income'], key=lambda x: x[1])[0]} at ${max([(category, amount) for category, amount in categories.items() if category != 'income'], key=lambda x: x[1])[1]:.2f}."
                ],
                "category_analysis": {}
            }
    
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