import json
from pydantic_settings import BaseSettings
from typing import Dict, Optional
import os
from dotenv import load_dotenv
from pydantic import validator

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///transactions.db"
    
    # UnionBank
    UNIONBANK_USERNAME: str
    UNIONBANK_PASSWORD: str
    UNIONBANK_URL: str
    
    # Google API
    GMAIL_API_KEY: str
    DRIVE_API_KEY: str
    
    # Slack
    SLACK_API_KEY: str
    
    # CloudCFO
    CLOUDCFO_URL: str
    CLOUDCFO_USERNAME: str
    CLOUDCFO_PASSWORD: str
    
    # Monitoring
    LOG_LEVEL: str = "INFO"
    ALERT_EMAIL: str
    
    # Rate Limiting
    API_RATE_LIMIT: int = 100
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_INITIAL_DELAY: int = 1

    @validator('GMAIL_API_KEY', 'DRIVE_API_KEY')
    def validate_json_credentials(cls, v):
        try:
            if isinstance(v, str):
                return json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in credentials: {str(e)}")
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
