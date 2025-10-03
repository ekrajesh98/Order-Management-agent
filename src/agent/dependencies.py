from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db_session
from src.models.database import UserSession


async def resolve_session_id(
    request: Request,
    db_session: AsyncSession = Depends(get_db_session),
) -> int:
    session_unique_id = request.headers.get("X-Session-Unique-Id")
    if not session_unique_id:
        raise HTTPException(status_code=400, detail="Missing session ID")

    session_id_query = select(UserSession.id).where(
        UserSession.session_uuid == session_unique_id
    )
    result = await db_session.execute(session_id_query)
    session_id = result.scalar_one_or_none()
    if not session_id:
        raise HTTPException(status_code=404, detail="Session not found")

    request.state.session_id = session_id
    return session_id
