from backend.core.database import mongo_db
from backend.schemas.nosql.ai_response import AIResponse
from backend.schemas.nosql.prompt_event import PromptEvent
from bson import ObjectId
from typing import List

ai_response_col = mongo_db.ai_responses
prompt_events_col = mongo_db.prompt_events

async def create_ai_response(response_data: AIResponse):
    data = response_data.model_dump(by_alias=True, exclude={"id"})
    result = await ai_response_col.insert_one(data)
    return result.inserted_id

async def create_prompt_event(event_data: PromptEvent):
    data = event_data.model_dump(by_alias=True, exclude={"id"})
    result = await prompt_events_col.insert_one(data)
    return result.inserted_id

async def push_ai_response_to_event(event_id: ObjectId, response_ids: List[str]):

    oid_list = [ObjectId(rid) for rid in response_ids]
    
    await prompt_events_col.update_one(
        {"_id": event_id},
        {
            "$addToSet": {
                "ai_response_ids": {"$each": oid_list}
            }
        }
    )

def has_pending_feedback(user_id: int) -> bool:

    latest_event = mongo_db.prompt_events.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)]
    )

    if not latest_event:
        return False


    return latest_event.get("rating") is None # type: ignore