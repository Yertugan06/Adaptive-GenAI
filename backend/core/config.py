from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    ENV: str = "development"

    # API
    GEMINI_API_KEY: str

    # Databases
    POSTGRES_URI: str
    MONGO_URI: str
    MONGO_DB_NAME: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
