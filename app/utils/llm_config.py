"""
Utility functions for configuring LLM services for agents
"""
import os
from typing import Dict, Any, List
from pydantic import BaseModel
from app.config import settings

class LLMConfiguration(BaseModel):
    model: str
    temperature: float = 0.1
    config_list: List[Dict[str, Any]]

def get_groq_config(model_name: str = None, temperature: float = 0.1) -> LLMConfiguration:
    """
    Returns a configuration for Groq API
    
    Args:
        model_name: The name of the Groq model to use (defaults to settings)
        temperature: The temperature setting for the model (default: 0.1)
        
    Returns:
        LLMConfiguration object with Groq settings
    """
    groq_api_key = os.getenv("GROQ_API_KEY", settings.groq_api_key)
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in environment variables or settings")
    
    # Use specified model or fall back to settings
    model = model_name or os.getenv("GROQ_MODEL", settings.groq_model)
    
    # Create configuration for Groq
    config_list = [
        {
            "model": model,
            "api_key": groq_api_key,
            "api_base": "https://api.groq.com/openai/v1",
        }
    ]
    
    return LLMConfiguration(
        model=model,
        temperature=temperature,
        config_list=config_list
    )
