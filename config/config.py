import json
from pydantic_settings import BaseSettings
from typing import Dict, Optional
import os
from dotenv import load_dotenv
from pydantic import validator, Field

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///transactions.db"
    
    # UnionBank
    UNIONBANK_USERNAME: str = Field(..., description="UnionBank login username")
    UNIONBANK_PASSWORD: str = Field(..., description="UnionBank login password")
    UNIONBANK_URL: str = Field("https://unionbankph.com", description="UnionBank login URL")
    
    # Google API
    GMAIL_API_KEY: Optional[str] = Field(None, description="Gmail API credentials in JSON format")
    DRIVE_API_KEY: Optional[str] = Field(None, description="Google Drive API credentials in JSON format")
    
    # Slack
    SLACK_API_KEY: Optional[str] = Field(None, description="Slack Bot User OAuth Token")
    
    # CloudCFO
    CLOUDCFO_URL: str = Field("https://cloudcfo.com", description="CloudCFO base URL")
    CLOUDCFO_USERNAME: str = Field(..., description="CloudCFO login username")
    CLOUDCFO_PASSWORD: str = Field(..., description="CloudCFO login password")
    
    # Monitoring
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    ALERT_EMAIL: Optional[str] = Field(None, description="Email for alerts")
    API_RATE_LIMIT: int = Field(100, description="API rate limit per minute")
    RETRY_MAX_ATTEMPTS: int = Field(3, description="Maximum retry attempts")
    RETRY_INITIAL_DELAY: int = Field(1, description="Initial retry delay in seconds")

    @validator('GMAIL_API_KEY', 'DRIVE_API_KEY', pre=True)
    def validate_json_credentials(cls, v):
        if v is None:
            return None
        try:
            if isinstance(v, str):
                # Try to parse JSON string
                return json.loads(v)
            elif isinstance(v, dict):
                # If it's already a dict, return as is
                return v
            return v
        except json.JSONDecodeError as e:
            # Return None for invalid JSON instead of raising error
            return None
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings(_env_file='.env', _env_file_encoding='utf-8')
