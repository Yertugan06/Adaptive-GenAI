from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.core.database import check_database_health
from backend.api import auth, prompts, feedback, responses, analytics
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Check DBs
    print("🔍 Checking database connections...")
    status = await check_database_health()
    print(f"Database Status: {status}")
    
    if "🔴" in status.values():
        print("⚠️ Warning: One or more databases are unreachable.")
    
    yield
    # Shutdown logic (if any) goes here


app = FastAPI(lifespan=lifespan, title="Adaptive GenAI API")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(prompts.router, prefix="/api/v1/prompts", tags=["Prompts"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
app.include_router(responses.router, prefix="/api/v1/responses", tags=["Responses"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)