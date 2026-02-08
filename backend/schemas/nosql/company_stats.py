from typing import Annotated, Optional
from datetime import datetime, UTC
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator, PlainSerializer, ConfigDict

PyObjectId = Annotated[
    str, 
    BeforeValidator(lambda x: str(x) if ObjectId.is_valid(x) else x),
    PlainSerializer(lambda x: str(x), return_type=str),
]

class CompanyStats(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    company_id: int = Field(description="SQL Reference ID for the Company")
    
    total_rating_sum: float = 0.0
    total_review_count: int = 0
    company_avg_score: float = 0.0
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    schema_version: int = 1

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )