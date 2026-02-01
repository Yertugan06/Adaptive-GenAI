from typing import Annotated, Optional
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator, PlainSerializer


PyObjectId = Annotated[
    str, 
    BeforeValidator(lambda x: str(x) if ObjectId.is_valid(x) else x),
    PlainSerializer(lambda x: str(x), return_type=str),
]

class PromptEvent(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    prompt_text: str
    rating: Optional[int] = None

    used_cached_answer: bool = False

    user_id: int        # Reference to SQL users.id
    company_id: int     # Reference to SQL companies.id

    # Reference to the specific AIResponse doc in Mongo
    ai_response_id: Optional[PyObjectId] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: int = 1