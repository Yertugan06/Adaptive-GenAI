from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from backend.api.v1.deps import get_current_user 
from backend.services.rag_pipeline import run_rag_pipeline
from backend.crud.ai_crud import has_pending_feedback
from backend.schemas.sql.user import User 

router = APIRouter()

# Schemas
class PromptRequest(BaseModel):
    prompt_text: str

class PromptResponse(BaseModel):
    ai_response_id: int
    response_text: str
    model: str
    feedback_required: bool = True

# Endpoints 

@router.post("/submit", response_model=PromptResponse)
def submit_prompt(
    data: PromptRequest, 
    current_user: User = Depends(get_current_user)
):

    if has_pending_feedback(current_user.id): # type: ignore
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Feedback required for previous response before submitting a new prompt."
        )


    result = run_rag_pipeline(
        query=data.prompt_text,
        company_id=current_user.company_id # type: ignore
    )

    return {
        "ai_response_id": result.id, # type: ignore
        "response_text": result.text, # type: ignore
        "model": result.model, # type: ignore
        "feedback_required": True
    }