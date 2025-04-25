from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""

    # Database Configuration
    mongodb_host: str = Field("localhost", alias='MONGODB_HOST')
    mongodb_port: int = Field(27017, alias='MONGODB_PORT')
    mongodb_database: str = Field("finance_db", alias='MONGODB_DATABASE')
    mongodb_uri: Optional[str] = Field(None, alias='MONGODB_URI')

    # JWT Configuration
    secret_key: str = Field(
        "your_very_secret_key_for_jwt_minimum_32_characters",
        alias='SECRET_KEY'
    )
    algorithm: str = Field("HS256", alias='ALGORITHM')
    access_token_expire_minutes: int = Field(30, alias='ACCESS_TOKEN_EXPIRE_MINUTES')

    # LLM API Settings
    # Groq AI Configuration
    groq_api_key: Optional[str] = Field(None, alias='GROQ_API_KEY')
    groq_model: str = Field("llama3-70b-8192", alias='GROQ_MODEL')  # Updated to use current supported model (as of April 2025)
    
    # Agent Configuration (Optional)
    huggingface_api_key: Optional[str] = Field(None, alias='HUGGINGFACE_API_KEY')

    # Application Settings
    app_title: str = Field("Personal Finance Assistant", alias='APP_TITLE')
    app_version: str = Field("0.1.0", alias='APP_VERSION')
    debug: bool = Field(True, alias='DEBUG')

    model_config = SettingsConfigDict(
        env_file='.env',      # Load from .env file
        env_file_encoding='utf-8',
        extra='ignore'        # Ignore extra fields from env file
    )

# Create a single instance of the settings to be used throughout the application
settings = Settings()