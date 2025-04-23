# Agent initialization

# Import the orchestrator factory for easy access
from .orchestrator import get_orchestrator, AgentOrchestrator

# Import individual agents for direct use if needed
from .budget_agent import BudgetPlannerAgent
from .investment_agent import InvestmentAdvisorAgent
from .fraud_agent import FraudDetectionAgent

__all__ = [
    'get_orchestrator',  # Factory function for getting orchestrator instance
    'AgentOrchestrator',  # Class for custom initialization
    'BudgetPlannerAgent',  # Individual agents
    'InvestmentAdvisorAgent',
    'FraudDetectionAgent',
]