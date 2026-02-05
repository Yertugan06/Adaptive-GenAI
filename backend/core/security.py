from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict
from backend.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
class TokenPayload(BaseModel):
    sub: str        # user_id
    company_id: int
    role: str
    exp: Optional[datetime] = None

    model_config = ConfigDict(extra="ignore")

#Password Functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

#JWT Functions

def create_access_token(payload: TokenPayload) -> str:
    to_encode = payload.model_dump()
    
    if not to_encode.get("exp"):
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
        to_encode["exp"] = expire

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)