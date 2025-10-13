from abc import ABC, abstractmethod
from uuid import UUID

from src.models.database import UserSession


class UserSessionAlreadyExistsError(Exception):
    """Exception raised when a user session already exists."""

    pass


class UserSessionServiceABC(ABC):
    @abstractmethod
    async def create_session(self, user_uuid: UUID) -> UUID:
        """Create a new user session."""
        pass

    @abstractmethod
    async def get_user_session(
        self, user_uuid: UUID, session_uuid: UUID
    ) -> UserSession | None:
        """Get a user session by user UUID and session UUID."""
        pass
