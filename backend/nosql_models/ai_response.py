from typing import Annotated, List, Optional
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator, PlainSerializer

PyObjectId = Annotated[
    str, 
    BeforeValidator(lambda x: str(x) if ObjectId.is_valid(x) else x),
    PlainSerializer(lambda x: str(x), return_type=str),
]

class AIResponse(BaseModel):
    
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    canonical_prompt: str
    response: str
    embedding: List[float]

    aliases: List[str] = []
    topics: List[str] = []

    model: str
    status: str = "candidate"  # canonical | candidate | quarantine

    reuse_count: int = 0
    avg_rating: float = 0.0

    company_id: int  # Reference to SQL companies.id

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    schema_version: int = 1