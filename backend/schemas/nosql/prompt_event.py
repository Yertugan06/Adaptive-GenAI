from typing import Annotated, Optional
from datetime import datetime, UTC
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator, PlainSerializer, ConfigDict

PyObjectId = Annotated[
    str, 
    BeforeValidator(lambda x: str(x) if ObjectId.is_valid(x) else x),
    PlainSerializer(lambda x: str(x), return_type=str),
]

class PromptEvent(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    prompt_text: str
    rating: Optional[int] = Field(None, ge=1, le=5)

    used_cached_answer: bool = False

    user_id: int        #SQL User table
    company_id: int     #SQL Company table

    ai_response_id: Optional[PyObjectId] = None


    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: int = 1

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )