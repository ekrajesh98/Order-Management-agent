from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import UserSession
from src.user_session.user_session_port import (
    UserSessionServiceABC,
)


class UserSessionServiceError(Exception):
    """Generic exception for user session errors."""

    pass


class UserSessionService(UserSessionServiceABC):
    def __init__(self, db_session: AsyncSession) -> None:
        self._db_session = db_session

    async def create_session(self, user_uuid: UUID) -> UUID:
        try:
            user_session = UserSession()
            user_session.user_uuid = user_uuid
            user_session.session_type = "default"
            self._db_session.add(user_session)
            await self._db_session.commit()
            await self._db_session.refresh(user_session)
            return user_session.session_uuid
        except Exception as e:
            raise UserSessionServiceError(f"Failed to create session: {e}") from e

    async def get_user_session(
        self, user_uuid: UUID, session_uuid: UUID
    ) -> UserSession | None:
        try:
            query = select(UserSession).where(
                UserSession.user_uuid == user_uuid,
                UserSession.session_uuid == session_uuid,
            )
            result = await self._db_session.execute(query)
            session = result.scalars().first()
            return session
        except Exception as e:
            raise UserSessionServiceError(f"Failed to get user session: {e}") from e
