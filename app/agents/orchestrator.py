from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import autogen

# Import the agent implementations
from .budget_agent import BudgetPlanningAgent
from .investment_agent import InvestmentAdvisorAgent
from .fraud_agent import FraudDetectionAgent

# Import models for data access
from app.models.transaction import Transaction
from app.models.portfolio import Portfolio
from app.services import finance_service

class AgentOrchestrator:
    """Orchestrates interactions between specialized finance agents.
    
    This class coordinates the Budget Planner, Investment Advisor, and Fraud Detector agents,
    allowing them to work together to provide comprehensive financial guidance.
    """
    
    def __init__(self, enable_multilingual: bool = False, language: str = "en"):
        """Initialize the orchestrator with specialized agents.
        
        Args:
            enable_multilingual: Whether to enable multilingual explanations
            language: The target language code for explanations (if multilingual is enabled)
        """
        self.budget_agent = BudgetPlanningAgent()
        self.investment_agent = InvestmentAdvisorAgent()
        self.fraud_agent = FraudDetectionAgent()
        self.enable_multilingual = enable_multilingual
        self.language = language
    
    def run_budget_agent(self, user_id: int, db: Session, target_savings_percent: float = 20.0) -> Dict[str, Any]:
        """Run the Budget Planner agent to get a personalized budget plan.
        
        Args:
            user_id: The ID of the user to analyze
            db: Database session for data access
            target_savings_percent: Target percentage of income to save
            
        Returns:
            Dict containing the budget plan and explanations
        """
        # Get the user's transaction data
        transactions = finance_service.get_user_transactions(db, user_id=user_id, limit=1000)
        
        if not transactions:
            return {
                "status": "error",
                "message": "Insufficient transaction data to create a budget plan.",
                "budget_plan": None,
                "explanation": "We need transaction history to create a personalized budget plan."
            }
        
        # Run the budget agent
        result = self.budget_agent.create_budget_plan(
            transactions=transactions,
            target_savings_percent=target_savings_percent
        )
        
        # If enabled, translate the explanations
        if self.enable_multilingual and self.language != "en" and result["status"] == "completed":
            result = self._translate_budget_explanations(result)
        
        return result
    
    def run_investment_agent(self, user_id: int, db: Session, 
                            savings_amount: float, 
                            risk_tolerance: str = "low", 
                            time_horizon: str = "medium") -> Dict[str, Any]:
        """Run the Investment Advisor agent to get personalized investment recommendations.
        
        Args:
            user_id: The ID of the user to analyze
            db: Database session for data access
            savings_amount: Amount available to invest
            risk_tolerance: User's risk tolerance (low, medium, high)
            time_horizon: Investment time horizon (short, medium, long)
            
        Returns:
            Dict containing investment recommendations and explanations
        """
        # Get the user's portfolio if it exists
        # In a real application, you would implement a service to retrieve this
        # For now, we'll just pass an empty list
        current_portfolio = []  # portfolio_service.get_user_portfolio(db, user_id=user_id)
        
        # Run the investment agent
        result = self.investment_agent.get_investment_recommendations(
            savings_amount=savings_amount,
            risk_tolerance=risk_tolerance,
            time_horizon=time_horizon,
            current_portfolio=current_portfolio
        )
        
        # If enabled, translate the explanations
        if self.enable_multilingual and self.language != "en" and result["status"] == "completed":
            result = self._translate_investment_explanations(result)
        
        return result
    
    def run_fraud_agent(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Run the Fraud Detection agent to scan for suspicious transactions.
        
        Args:
            user_id: The ID of the user to analyze
            db: Database session for data access
            
        Returns:
            Dict containing fraud detection results and explanations
        """
        # Get the user's recent transactions
        transactions = finance_service.get_user_transactions(db, user_id=user_id, limit=100)
        
        if not transactions:
            return {
                "status": "error",
                "message": "No transaction data available for fraud analysis.",
                "suspicious_transactions": [],
                "explanation": "We need transaction history to detect suspicious activities."
            }
        
        # Run the fraud agent
        result = self.fraud_agent.analyze_transactions(transactions=transactions)
        
        # If enabled, translate the explanations
        if self.enable_multilingual and self.language != "en" and result["status"] == "completed":
            result = self._translate_fraud_explanations(result)
        
        return result
    
    def comprehensive_financial_analysis(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Run a comprehensive analysis using all three agents.
        
        This method coordinates the three specialized agents to perform a holistic
        analysis of the user's financial situation, detecting fraud, recommending
        a budget, and suggesting investments based on the budget's recommended savings.
        
        Args:
            user_id: The ID of the user to analyze
            db: Database session for data access
            
        Returns:
            Dict containing results from all three agents and an integrated summary
        """
        # Step 1: Run fraud detection first for safety
        fraud_results = self.run_fraud_agent(user_id=user_id, db=db)
        
        # Step 2: Run budget analysis
        budget_results = self.run_budget_agent(user_id=user_id, db=db)
        
        # Step 3: If budget analysis succeeded, use the recommended savings for investment advice
        if budget_results["status"] == "completed" and budget_results.get("budget_plan"):
            # Extract the recommended savings amount from the budget plan
            recommended_savings = budget_results["budget_plan"].get("recommended_savings", 0)
            
            # Only proceed with investment recommendations if there's money to invest
            if recommended_savings > 0:
                investment_results = self.run_investment_agent(
                    user_id=user_id,
                    db=db,
                    savings_amount=recommended_savings
                )
            else:
                investment_results = {
                    "status": "error",
                    "message": "No funds available for investment.",
                    "recommendations": None
                }
        else:
            investment_results = {
                "status": "error",
                "message": "Could not generate budget plan required for investment advice.",
                "recommendations": None
            }
        
        # Step 4: Generate an integrated summary
        summary = self._generate_integrated_summary(
            fraud_results=fraud_results,
            budget_results=budget_results,
            investment_results=investment_results
        )
        
        return {
            "status": "completed",
            "fraud_analysis": fraud_results,
            "budget_plan": budget_results,
            "investment_recommendations": investment_results,
            "integrated_summary": summary
        }
    
    def _generate_integrated_summary(self, 
                                    fraud_results: Dict[str, Any], 
                                    budget_results: Dict[str, Any], 
                                    investment_results: Dict[str, Any]) -> str:
        """Generate an integrated summary from the results of all three agents.
        
        This would typically use an LLM to create a cohesive narrative from the separate analyses.
        For now, we'll use a template-based approach for simplicity.
        
        Args:
            fraud_results: Results from the fraud detection agent
            budget_results: Results from the budget planner agent
            investment_results: Results from the investment advisor agent
            
        Returns:
            A string containing the integrated summary
        """
        summary_parts = []
        
        # Fraud summary
        if fraud_results["status"] == "completed":
            suspicious_count = len(fraud_results.get("suspicious_transactions", []))
            if suspicious_count > 0:
                summary_parts.append(f"⚠️ Found {suspicious_count} suspicious transactions that need your attention.")
            else:
                summary_parts.append("✅ No suspicious transactions detected in your recent activity.")
        
        # Budget summary
        if budget_results["status"] == "completed" and budget_results.get("budget_plan"):
            budget_plan = budget_results["budget_plan"]
            income = budget_plan.get("total_income", 0)
            savings = budget_plan.get("recommended_savings", 0)
            savings_percent = (savings / income * 100) if income > 0 else 0
            
            summary_parts.append(f"💰 Based on your monthly income of ${income:.2f}, we recommend saving ${savings:.2f} ({savings_percent:.1f}%).")
            
            # Add some of the general advice
            if "general_advice" in budget_plan and budget_plan["general_advice"]:
                top_advice = budget_plan["general_advice"][0] if len(budget_plan["general_advice"]) > 0 else ""
                if top_advice:
                    summary_parts.append(f"💡 Budget tip: {top_advice}")
        
        # Investment summary
        if investment_results["status"] == "completed" and investment_results.get("recommendations"):
            recommendations = investment_results["recommendations"]
            investments = recommendations.get("allocation", {})
            
            if investments:
                investment_text = "📈 Recommended investments: " + ", ".join(
                    f"{name} ({percentage*100:.1f}%)" 
                    for name, percentage in list(investments.items())[:3]  # Show top 3
                )
                if len(investments) > 3:
                    investment_text += ", and others"
                summary_parts.append(investment_text)
                
                # Add a piece of reasoning if available
                if "reasoning" in recommendations and recommendations["reasoning"]:
                    top_reason = recommendations["reasoning"][0] if len(recommendations["reasoning"]) > 0 else ""
                    if top_reason:
                        summary_parts.append(f"💡 Investment insight: {top_reason}")
        
        # Combine all parts with line breaks
        if summary_parts:
            return "\n\n".join(summary_parts)
        else:
            return "No comprehensive analysis could be generated at this time."
    
    def _translate_budget_explanations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Translate budget explanations to the target language.
        
        In a real implementation, this would use a translation service or model.
        For now, we'll just add a placeholder.
        """
        # This is a placeholder - in a real application, you would use a translation API or model
        if "budget_plan" in results and results["budget_plan"] and "general_advice" in results["budget_plan"]:
            results["budget_plan"]["general_advice"] = [
                f"[Translated to {self.language}] {advice}" 
                for advice in results["budget_plan"]["general_advice"]
            ]
        return results
    
    def _translate_investment_explanations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Translate investment explanations to the target language.
        
        In a real implementation, this would use a translation service or model.
        For now, we'll just add a placeholder.
        """
        # This is a placeholder - in a real application, you would use a translation API or model
        if "recommendations" in results and results["recommendations"] and "reasoning" in results["recommendations"]:
            results["recommendations"]["reasoning"] = [
                f"[Translated to {self.language}] {reason}" 
                for reason in results["recommendations"]["reasoning"]
            ]
        return results
    
    def _translate_fraud_explanations(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Translate fraud explanations to the target language.
        
        In a real implementation, this would use a translation service or model.
        For now, we'll just add a placeholder.
        """
        # This is a placeholder - in a real application, you would use a translation API or model
        if "suspicious_transactions" in results:
            for txn in results["suspicious_transactions"]:
                if "reason" in txn:
                    txn["reason"] = f"[Translated to {self.language}] {txn['reason']}"
        return results

# Create a factory function to get the orchestrator on demand
def get_orchestrator():
    """Returns a singleton instance of the AgentOrchestrator."""
    return AgentOrchestrator()