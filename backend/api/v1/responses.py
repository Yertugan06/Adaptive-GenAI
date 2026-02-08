from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, status
from backend.crud import ai_crud
from backend.schemas.nosql.ai_response import AIResponse

router = APIRouter(prefix="/responses", tags=["AI Responses"])

@router.get("/{res_id}", response_model=AIResponse)
async def get_response(res_id: str):
    response = await ai_crud.get_ai_response_by_id(res_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return response

@router.get("/search", response_model=List[AIResponse])
async def search_responses(
    company_id: int,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = 20,
    skip: int = 0
):
    filters = {"company_id": company_id}
    
    if status:
        filters["status"] = status  # type: ignore
    
    if min_score is not None:
        filters["bayesian_score"] = {"$gte": min_score}  # type: ignore

    return await ai_crud.search_ai_responses(filters, limit, skip)

@router.post("", response_model=AIResponse, status_code=status.HTTP_201_CREATED)
async def create_response(response: AIResponse):
    
    new_id = await ai_crud.create_ai_response(response)

    created_res = await ai_crud.get_ai_response_by_id(str(new_id))
    return created_res


@router.put("/{res_id}", response_model=AIResponse)
async def update_response_content(res_id: str, update_data: dict = Body(...)):
    existing = await ai_crud.get_ai_response_by_id(res_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Response not found")

    protected_fields = ["_id", "company_id", "reuse_count", "rating_sum", "bayesian_score"]
    clean_data = {k: v for k, v in update_data.items() if k not in protected_fields}
    
    await ai_crud.update_ai_response_fields(res_id, clean_data)
    
    return await ai_crud.get_ai_response_by_id(res_id)

@router.patch("/{res_id}/status")
async def patch_status(res_id: str, status: str = Query(..., regex="^(candidate|canonical|quarantine)$")):
    success = await ai_crud.update_ai_response_status(res_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Response not found")
        
    return {"id": res_id, "status": "updated", "new_status": status}

@router.delete("/{res_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_response(res_id: str):
    existing = await ai_crud.get_ai_response_by_id(res_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Response not found")

    await ai_crud.delete_ai_response_record(res_id)
    return None