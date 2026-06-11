from fastapi import APIRouter, Response, status
from sqlalchemy import text

from apps.api.config import settings
from apps.api.db.session import get_engine
from apps.api.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(response: Response) -> HealthResponse:
    db_status = "not_configured"
    overall = "ok"

    if settings.database_url:
        engine = get_engine()
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception:
            db_status = "error"
            overall = "degraded"
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(status=overall, database=db_status, version="1.0.0")
