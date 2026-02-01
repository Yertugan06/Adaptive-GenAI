from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENV: str = "development"

    # API
    GEMINI_API_KEY: str

    # Databases
    POSTGRES_URI: str
    MONGO_URI: str
    MONGO_DB_NAME: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
