from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session

router = APIRouter()


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    """Liveness probe with a real database ping.

    Returns db:false (rather than erroring) when the database is unreachable so
    the endpoint stays useful as a diagnostic even when Postgres is down.
    """
    db_ok = False
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok", "db": db_ok}
