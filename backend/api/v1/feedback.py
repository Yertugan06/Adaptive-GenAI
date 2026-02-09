from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from backend.crud import ai_crud
from backend.services.feedback import process_ai_feedback
from pydantic import BaseModel, Field
from backend.core.database import get_sql_db
from sqlalchemy.orm import Session

router = APIRouter()

class FeedbackSubmit(BaseModel):
    event_id: str
    rating: int = Field(ge=1, le=5)

@router.post("/submit")
async def submit_feedback(data: FeedbackSubmit, background_tasks: BackgroundTasks, db_sql: Session = Depends(get_sql_db)):
    try:
        await ai_crud.update_event_rating(data.event_id, data.rating)
        
        background_tasks.add_task(process_ai_feedback,db_sql, data.event_id, data.rating)
        
        return {"status": "success", "message": "Feedback recorded and AI learning updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Feedback failed: {str(e)}")
    
@router.get("/history")
async def get_history(user_id: int, limit: int = 10):
    try:
        history = await ai_crud.get_user_feedback_history(user_id, limit)
        
        for item in history:
            item["_id"] = str(item["_id"])
            if "ai_response_ids" in item:
                item["ai_response_ids"] = [str(rid) for rid in item["ai_response_ids"]]
        
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not retrieve history")