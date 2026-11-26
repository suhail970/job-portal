from pydantic_settings import BaseSettings
from typing import Optional, List, Union
import os
import logging

logger = logging.getLogger("skillbridge.config")

class Settings(BaseSettings):
    APP_NAME: str = "SkillBridge AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "skillbridge-super-secret-key-change-in-production-2026-xyz"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS Allowed Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

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

    def validate_production_security(self):
        if self.APP_ENV.lower() == "production":
            if "change-in-production" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                logger.warning(
                    "[SECURITY WARNING] Using weak or default SECRET_KEY in production! "
                    "Please set a cryptographically secure SECRET_KEY in .env or environment variables."
                )

settings = Settings()
settings.validate_production_security()


