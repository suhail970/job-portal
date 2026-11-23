from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    APP_NAME: str = "SkillBridge AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "skillbridge-super-secret-key-change-in-production-2026-xyz"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database (Absolute path so server and CLI scripts share the identical SQLite database)
    DATABASE_URL: str = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'skillbridge.db')).replace(os.sep, '/')}"

    # AI Configuration (Free tiers supported)
    DEFAULT_AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"

    # Code Execution Sandbox
    PISTON_API_URL: str = "https://emkc.org/api/v2/piston/execute"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()

