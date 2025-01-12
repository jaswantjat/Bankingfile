from pydantic_settings import BaseSettings
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///transactions.db")
    
    # UnionBank
    UNIONBANK_USERNAME: str = os.getenv("UNIONBANK_USERNAME", "")
    UNIONBANK_PASSWORD: str = os.getenv("UNIONBANK_PASSWORD", "")
    UNIONBANK_URL: str = os.getenv("UNIONBANK_URL", "")
    
    # API Keys
    GMAIL_API_KEY: str = os.getenv("GMAIL_API_KEY", "")
    SLACK_API_KEY: str = os.getenv("SLACK_API_KEY", "")
    DRIVE_API_KEY: str = os.getenv("DRIVE_API_KEY", "")
    
    # CloudCFO
    CLOUDCFO_URL: str = os.getenv("CLOUDCFO_URL", "")
    CLOUDCFO_USERNAME: str = os.getenv("CLOUDCFO_USERNAME", "")
    CLOUDCFO_PASSWORD: str = os.getenv("CLOUDCFO_PASSWORD", "")
    
    # Monitoring
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ALERT_EMAIL: str = os.getenv("ALERT_EMAIL", "")
    
    # Rate Limiting
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "100"))
    RETRY_MAX_ATTEMPTS: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    RETRY_INITIAL_DELAY: float = float(os.getenv("RETRY_INITIAL_DELAY", "1.0"))

    class Config:
        case_sensitive = True

settings = Settings()
