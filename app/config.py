import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "FitBuddy")

    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'fitbuddy.db').as_posix()}",
    )

    GEMINI_API_KEY: str = os.getenv(
        "GEMINI_API_KEY",
        "",
    ).strip()

    GEMINI_WORKOUT_MODEL: str = os.getenv(
        "GEMINI_WORKOUT_MODEL",
        "gemini-3.8-flash",
    )

    GEMINI_FAST_MODEL: str = os.getenv(
        "GEMINI_FAST_MODEL",
        "gemini-3.5-flash-lite",
    )


settings = Settings()