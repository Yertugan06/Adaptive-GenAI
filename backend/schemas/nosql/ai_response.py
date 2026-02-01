from typing import Annotated, List, Optional
from datetime import datetime, UTC
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator, PlainSerializer, ConfigDict

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

    aliases: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    source_doc_ids: List[str] = Field(default_factory=list)

    model: str
    status: str = "candidate"  # canonical | candidate | quarantine

    reuse_count: int = 0
    avg_rating: float = 0.0

    company_id: int  # SQL Reference

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    schema_version: int = 1

   
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )