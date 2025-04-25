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
    Returns a configuration for Groq API - this is only used internally now,
    as the agent_config function has been simplified to avoid compatibility issues.
    
    Args:
        model_name: The name of the Groq model to use (defaults to settings)
        temperature: The temperature setting for the model (default: 0.1)
        
    Returns:
        LLMConfiguration object with Groq settings
    """
    groq_api_key = os.getenv("GROQ_API_KEY", settings.groq_api_key)
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in environment variables or settings")
    
    # Use a hardcoded known-working model to ensure compatibility
    model = "llama3-70b-8192"  # Using a currently supported model (as of April 2025)
    
    # NOTE: This function is mainly kept for backwards compatibility
    # The actual agent configuration is now handled in get_agent_config()
    # to avoid parameters being incorrectly passed to the OpenAI client
    
    return LLMConfiguration(
        model=model,
        temperature=temperature,
        config_list=[]  # Empty config list to avoid issues
    )

def get_agent_config(model_name: str = None, temperature: float = 0.1) -> Dict[str, Any]:
    """
    Returns a configuration for AutoGen agents compatible with the OpenAI client
    
    Args:
        model_name: The name of the model to use (defaults to settings)
        temperature: The temperature setting for the model (default: 0.1)
        
    Returns:
        Dictionary with LLM configuration compatible with AutoGen's OAI client
    """
    groq_api_key = os.getenv("GROQ_API_KEY", settings.groq_api_key)
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in environment variables or settings")
    
    # Use a hardcoded known-working model to ensure compatibility
    model = "llama3-70b-8192"  # Using a currently supported model (as of April 2025)
    
    # This is the format that works with AutoGen's OpenAI client
    # Note: api_type must be set to "openai" and api_base parameters must be handled with care
    return {
        "model": model,
        "temperature": temperature,
        "api_key": groq_api_key,
        # Use OpenAI format client with custom base URL
        "api_type": "openai",
        # Don't include api_base here, it causes issues with the completions client
    }
