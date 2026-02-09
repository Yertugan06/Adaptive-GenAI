from backend.core.database import mongo_db

ai_response_col = mongo_db.ai_responses
company_stats_col = mongo_db.company_stats

async def get_company_dashboard_metrics(company_id: int) -> dict | None:

    base_stats = await company_stats_col.find_one({"company_id": company_id})
    
    if not base_stats:
        return None

 
    pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    status_cursor = await ai_response_col.aggregate(pipeline).to_list(length=10) #type: ignore
    
    status_map = {item["_id"]: item["count"] for item in status_cursor}
    
    top_doc = await ai_response_col.find_one(
        {"company_id": company_id, "status": "canonical"},
        sort=[("bayesian_score", -1)]
    )

    return {
        "company_id": company_id,
        "total_reviews": base_stats.get("total_review_count", 0),
        "global_average_rating": base_stats.get("company_avg_score", 0.0),
        "status_distribution": {
            "candidate": status_map.get("candidate", 0),
            "canonical": status_map.get("canonical", 0),
            "quarantine": status_map.get("quarantine", 0),
        },
        "top_performing_response_id": str(top_doc["_id"]) if top_doc else None
    }

