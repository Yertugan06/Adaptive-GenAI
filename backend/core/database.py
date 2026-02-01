from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pymongo import AsyncMongoClient
from typing import Generator
from backend.core.config import settings

engine = create_engine(settings.POSTGRES_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for SQL sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


mongo_client = AsyncMongoClient(settings.MONGO_URI)
mongo_db = mongo_client[settings.MONGO_DB_NAME]

# Collections
ai_responses = mongo_db["ai_responses"]
prompt_events = mongo_db["prompt_events"]
document_chunks = mongo_db["document_chunks"]