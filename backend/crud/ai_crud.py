from backend.core.database import mongo_db
from backend.schemas.nosql.ai_response import AIResponse
from backend.schemas.nosql.prompt_event import PromptEvent
from bson import ObjectId
from typing import List
from datetime import datetime, UTC

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

async def has_pending_feedback(user_id: int) -> bool:

    latest_event = await mongo_db.prompt_events.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)]
    )

    if not latest_event:
        return False


    return latest_event.get("rating") is None # type: ignore


async def update_event_rating(event_id: str, rating: int):
    await prompt_events_col.update_one(
        {"_id": ObjectId(event_id)},
        {"$set": {"rating": rating}}
    )

async def get_event_by_id(event_id: str):
    return await prompt_events_col.find_one({"_id": ObjectId(event_id)})

async def get_ai_response_by_id(res_id: str):
    return await ai_response_col.find_one({"_id": ObjectId(res_id)})

async def delete_ai_response_record(res_id: str):
    await ai_response_col.delete_one({"_id": ObjectId(res_id)})

async def update_ai_response_stats(res_id: str, rating: float, b_score: float, status: str):
    await ai_response_col.update_one(
        {"_id": ObjectId(res_id)},
        {
            "$set": {
                "bayesian_score": b_score,
                "status": status,
                "updated_at": datetime.now(UTC)
            },
            "$inc": {
                "reuse_count": 1,
                "rating_sum": rating
            }
        }
    )

async def get_company_avg_rating(company_id: int) -> float:
    pipeline = [
        {"$match": {"company_id": company_id}},
        {
            "$group": {
                "_id": None,
                "total_ratings_sum": {"$sum": "$rating_sum"},
                "total_reuse_count": {"$sum": "$reuse_count"}
            }
        }
    ]

    result = await ai_response_col.aggregate(pipeline).to_list(1) #type: ignore

    if not result:
        return 3.5  # Neutral-positive baseline for new companies

    data = result[0]
    total_sum = data.get("total_ratings_sum", 0)
    total_count = data.get("total_reuse_count", 0)

    if total_count <= 0:
        return 3.5
    
    avg = total_sum / total_count
    return float(avg) if avg > 0 else 3.5
    
async def get_user_feedback_history(user_id: int, limit: int = 10):

    cursor = prompt_events_col.find(
        {"user_id": user_id, "rating": {"$ne": None}},
        sort=[("created_at", -1)]
    ).limit(limit)
    
    return await cursor.to_list(length=limit)