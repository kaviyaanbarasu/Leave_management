import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Explicitly load .env from backend root if present
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Define application settings with defaults and environment variable overrides."""
    PROJECT_NAME: str = "Dynamic PTO & Leave Management System"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:root@localhost:5432/leave_management_db"
    )
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"
    ]
    GOOGLE_CALENDAR_API_KEY: str = os.getenv("GOOGLE_CALENDAR_API_KEY", "")

    # Gmail SMTP Email Notification Configuration
    MAIL_HOST: str = os.getenv("MAIL_HOST", "smtp.gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "leavemanagementsystem45@gmail.com")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "leavemanagementsystem45@gmail.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "Leave Management System")

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")


settings = Settings()
