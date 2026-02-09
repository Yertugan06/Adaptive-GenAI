from typing import Annotated, List, Optional
from datetime import datetime, UTC
from bson import ObjectId
from pydantic import BaseModel, Field, BeforeValidator, PlainSerializer, ConfigDict

PyObjectId = Annotated[
    str, 
    BeforeValidator(lambda x: str(x) if ObjectId.is_valid(x) else x),
    PlainSerializer(lambda x: str(x), return_type=str),
]

class DocumentChunk(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)

    parent_doc_id: PyObjectId = Field(description="Link to the original DocumentMetadata")
    company_id: int           
    
    chunk_index: int           
    content: str               
    embedding: List[float]     

    page_number: Optional[int] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: int = 1

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )