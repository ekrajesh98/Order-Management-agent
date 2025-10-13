from uuid import UUID

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db_session
from src.user_session.user_session_port import UserSessionServiceABC
from src.user_session.user_session_service import UserSessionService


async def _build_user_session_service(
    db_session: AsyncSession,
) -> UserSessionServiceABC:
    return UserSessionService(db_session)


async def get_user_uuid(request: Request) -> UUID:
    user_uuid = request.headers.get("X-User-UUID")
    if not user_uuid:
        raise HTTPException(status_code=400, detail="Missing user UUID")
    return user_uuid


async def get_session_uuid(request: Request) -> UUID:
    session_uuid = request.headers.get("X-Session-Unique-Id")
    if not session_uuid:
        raise HTTPException(status_code=400, detail="Missing session UUID")
    return session_uuid


async def resolve_session_id(
    request: Request,
    session_uuid: UUID = Depends(get_session_uuid),
    user_uuid: UUID = Depends(get_user_uuid),
    db_session: AsyncSession = Depends(get_db_session),
) -> int:
    session_service = await _build_user_session_service(db_session)
    user_session = await session_service.get_user_session(user_uuid, session_uuid)

    if not user_session:
        raise HTTPException(status_code=403, detail="Invalid session for user")

    request.state.session_id = user_session.id
    return user_session.id
