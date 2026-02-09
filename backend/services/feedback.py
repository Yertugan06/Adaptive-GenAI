import asyncio
from backend.services.math_utils import calculate_bayesian_rating, determine_status
from backend.crud import ai_crud as crud
from sqlalchemy.orm import Session

async def process_ai_feedback(db_sql : Session,event_id: str, rating: int):
    event = await crud.get_event_by_id(event_id)
    if not event or not event.get("ai_response_ids"):
        return
    
    crud.create_generation_audit(
        db_sql, 
        user_id=event.get("user_id"), 
        mongo_id=event_id, 
        rating=rating
    )
    
    company_id = event["company_id"]
    company_baseline = await crud.update_company_stats(company_id, rating)
    

    async def update_single_res(res_id: str):
        ai_res = await crud.get_ai_response_by_id(res_id)
        if not ai_res:
            return

        new_v = ai_res.get("reuse_count", 0) + 1
        new_rating_sum = ai_res.get("rating_sum", 0.0) + rating
        new_R = new_rating_sum / new_v

        new_b_score = calculate_bayesian_rating(
            item_reviews_count=new_v,
            item_avg_rating=new_R,
            global_avg_rating=company_baseline
        )

        status = determine_status(new_v, new_b_score)

        if status == "DELETE":
            await crud.delete_ai_response_record(res_id)
        else:
            await crud.update_ai_response_stats(
                res_id=res_id, 
                rating=float(rating), 
                b_score=new_b_score, 
                status=status
            )


    tasks = [update_single_res(str(rid)) for rid in event["ai_response_ids"]]
    await asyncio.gather(*tasks)