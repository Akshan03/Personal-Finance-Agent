# Agent initialization

# Import the orchestrator for easy access
from .orchestrator import orchestrator, AgentOrchestrator

# Import individual agents for direct use if needed
from .budget_agent import BudgetPlannerAgent
from .investment_agent import InvestmentAdvisorAgent
from .fraud_agent import FraudDetectionAgent

__all__ = [
    'orchestrator',  # Global instance for easy use
    'AgentOrchestrator',  # Class for custom initialization
    'BudgetPlannerAgent',  # Individual agents
    'InvestmentAdvisorAgent',
    'FraudDetectionAgent',
]