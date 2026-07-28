import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env if present
load_dotenv()

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
    
    # OpenRouter API & Multi-Agent Models
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "your_openrouter_api_key_here")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    AGENT_NLP_MODEL: str = os.getenv("AGENT_NLP_MODEL", "google/gemini-2.0-flash-exp:free")
    AGENT_THREAT_MODEL: str = os.getenv("AGENT_THREAT_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
    AGENT_REPORT_MODEL: str = os.getenv("AGENT_REPORT_MODEL", "deepseek/deepseek-chat:free")
    AGENT_ALERT_MODEL: str = os.getenv("AGENT_ALERT_MODEL", "qwen/qwen-2.5-7b-instruct:free")
    USE_REAL_CRAWLER: bool = True
    
    # Telegram MTProto credentials (from https://my.telegram.org/apps)
    TELEGRAM_API_ID: str = os.getenv("TELEGRAM_API_ID", "")
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_SESSION_NAME: str = os.getenv("TELEGRAM_SESSION_NAME", "sentinelai_session")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sentinelai.db")

settings = Settings()
