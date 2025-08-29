from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_ID: int
    GOOGLE_SHEET_NAME: str = "NeuroFlex Requests"
    GOOGLE_CREDS_FILE: str = "google_creds.json"
    USE_SHEETS: bool = True
    DB_PATH: str = str(BASE_DIR / "data" / "neuroflex.db")
    LOCALE_DIR: str = str(BASE_DIR / "locale")
    DEFAULT_LANG: str = "ru"
    RATE_LIMIT_PER_MIN: int = 15
    SENTRY_DSN: str | None = None
    WEBHOOK_URL: str | None = None  # если уйдёшь на вебхуки

    class Config:
        env_file = ".env"

settings = Settings()
