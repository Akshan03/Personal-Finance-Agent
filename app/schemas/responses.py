from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel, Field

# Generic type variable for response data
T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """Standard response format for all API endpoints."""
    status: str = Field(..., description="Status of the response (success, error)")
    message: str = Field(..., description="Message describing the result")
    data: Optional[T] = Field(None, description="Response data payload")

class AgentResponse(BaseModel):
    """Base response format for agent interactions."""
    status: str = Field(..., description="Status of the agent execution (completed, error)")
    message: str = Field(..., description="Result message from agent")

class ErrorResponse(BaseModel):
    """Standard error response format."""
    status: str = "error"
    message: str
    detail: Optional[str] = None

class BudgetPlanResponse(AgentResponse):
    """Response schema for budget planning results."""
    budget_plan: Optional[Dict[str, Any]] = Field(None, description="Budget plan data")
    explanation: Optional[str] = Field(None, description="Natural language explanation")

class InvestmentRecommendationResponse(AgentResponse):
    """Response schema for investment recommendations."""
    recommendations: Optional[Dict[str, Any]] = Field(None, description="Investment recommendations")
    explanation: Optional[str] = Field(None, description="Natural language explanation")

class FraudDetectionResponse(AgentResponse):
    """Response schema for fraud detection results."""
    suspicious_transactions: List[Dict[str, Any]] = Field(default_factory=list, description="List of suspicious transactions")
    explanation: Optional[str] = Field(None, description="Natural language explanation")

class ComprehensiveAnalysisResponse(AgentResponse):
    """Response schema for comprehensive financial analysis (all agents)."""
    fraud_analysis: Optional[FraudDetectionResponse] = None
    budget_plan: Optional[BudgetPlanResponse] = None
    investment_recommendations: Optional[InvestmentRecommendationResponse] = None
    integrated_summary: Optional[str] = Field(None, description="Integrated summary of all analyses")