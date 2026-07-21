import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "SentinelAI"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Environment
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Scoring weights
    WEIGHT_SENTIMENT: float = 0.15
    WEIGHT_THREAT_CLASS: float = 0.30
    WEIGHT_HATE_SPEECH: float = 0.20
    WEIGHT_VELOCITY: float = 0.10
    WEIGHT_COORDINATION: float = 0.15
    WEIGHT_BOT: float = 0.10
    
    # Threat Thresholds
    THRESHOLD_LOW: float = 0.30
    THRESHOLD_MEDIUM: float = 0.50
    THRESHOLD_HIGH: float = 0.70
    THRESHOLD_CRITICAL: float = 0.85
    
    # Crawlers
    CRAWL_INTERVAL_MINUTES: int = 5
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sentinelai.db")

settings = Settings()
