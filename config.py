# config.py
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    """Application configuration settings"""
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bavest Financial Data API"
    DEBUG: bool = Field(default=True)
    
    # CORS Configuration
    CORS_ORIGINS: list[str] = Field(default=["*"])
    
    # AWS Configuration
    AWS_REGION: str = Field(default="eu-central-1")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    AWS_KINESIS_STREAM_NAME: Optional[str] = Field(default=None)
    
    # Google Cloud Configuration
    GCP_PROJECT_ID: Optional[str] = Field(default=None)
    GCP_SERVICE_ACCOUNT_KEY: Optional[str] = Field(default=None)
    
    # Redis/ElasticCache Configuration
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    
    # Cache Configuration
    CACHE_EXPIRATION_SECONDS: int = Field(default=3600)  # 1 hour
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=100)
    
    # Data Source Configuration
    MARKET_DATA_SOURCE: str = Field(default="mock")  # Options: mock, aws, gcp, api
    ALTERNATIVE_DATA_SOURCE: str = Field(default="mock")
    
    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings
    """
    return Settings()