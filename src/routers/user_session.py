import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db_session
from src.routers.dependencies import get_user_uuid
from src.user_session.user_session_port import UserSessionServiceABC
from src.user_session.user_session_service import (
    UserSessionService,
    UserSessionServiceError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def _build_session_service(
    db_session: AsyncSession,
) -> UserSessionServiceABC:
    return UserSessionService(db_session)


@router.post("/session")
async def create_session(
    user_uuid: UUID = Depends(get_user_uuid),
    db_session: AsyncSession = Depends(get_db_session),
) -> dict[str, UUID]:
    """
    Create a new user session.
    Args:
        session_create_request: Request containing user UUID
        db_session: Database session dependency

    Returns:
        UUID of the newly created session

    """
    try:
        session_service = await _build_session_service(db_session)
        session_uuid = await session_service.create_session(user_uuid)
        return {"session_uuid": session_uuid}

    except UserSessionServiceError as e:
        logger.exception("Error creating user session: %s", e)
        raise e
