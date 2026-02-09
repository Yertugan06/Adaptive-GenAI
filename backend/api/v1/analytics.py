from fastapi import APIRouter
from backend.crud import analytics_crud
from pydantic import BaseModel

router = APIRouter()

#Response Models
class StatusBreakdown(BaseModel):
    candidate: int = 0
    canonical: int = 0
    quarantine: int = 0

class CompanyDashboard(BaseModel):
    company_id: int
    total_reviews: int
    global_average_rating: float
    status_distribution: StatusBreakdown
    top_performing_response_id: str | None


# --- Endpoints ---

@router.get("/company/{company_id}", response_model=CompanyDashboard)
async def get_company_dashboard(company_id: int):

    stats = await analytics_crud.get_company_dashboard_metrics(company_id)
    if not stats:

        return CompanyDashboard(
            company_id=company_id,
            total_reviews=0,
            global_average_rating=0.0,
            status_distribution=StatusBreakdown(),
            top_performing_response_id=None
        )
    return stats

