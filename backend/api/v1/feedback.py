from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.crud import ai_crud
from backend.services.feedback import process_ai_feedback
from pydantic import BaseModel, Field

router = APIRouter()

class FeedbackSubmit(BaseModel):
    event_id: str
    rating: int = Field(ge=1, le=5)

@router.post("/submit")
async def submit_feedback(data: FeedbackSubmit, background_tasks: BackgroundTasks):
    try:
        await ai_crud.update_event_rating(data.event_id, data.rating)
        
        background_tasks.add_task(process_ai_feedback, data.event_id, data.rating)
        
        return {"status": "success", "message": "Feedback recorded and AI learning updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Feedback failed: {str(e)}")