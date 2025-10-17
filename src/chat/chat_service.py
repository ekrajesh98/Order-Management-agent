import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.agent.agent_service import AgentServiceABC
from src.config import settings
from src.context.dependencies import get_request_context
from src.models.database import SessionAgent, UserChatRequest, UserSession
from src.sensitive_data_handler.data_handler_service import (
    SensitiveDataUnMaskingService,
)

from .chat_port import ChatServiceABC

logger = logging.getLogger(__name__)


class ChatServiceError(Exception):
    """Custom exception for ChatService errors."""

    pass


class ChatService(ChatServiceABC):
    def __init__(
        self,
        db_session: AsyncSession,
        session_id: str,
        agent_service: AgentServiceABC,
    ) -> None:
        self._db_session = db_session
        self.session_id = session_id
        self.agent_service = agent_service

        self.request_context = get_request_context()

    async def process_user_chat_request(self, user_query: str, token: str = "") -> str:
        """
        Process a user chat request.
        Args:
            user_query: The user's chat query.
            token: Optional authorization token.
        Returns:
            The agent's response message.
        """
        try:
            session_exist_query = (
                select(UserSession)
                .options(joinedload(UserSession.agents))
                .where(UserSession.id == int(self.session_id))
            )
            result = await self._db_session.execute(session_exist_query)
            session = result.scalars().first()

            if not session:
                raise ChatServiceError("Invalid session ID")

            agents = session.agents
            if not agents:
                agent = SessionAgent()
                agent.session_id = session.id
                self._db_session.add(agent)
                await self._db_session.commit()
                await self._db_session.refresh(agent)
            else:
                agent = agents[0]

            response = await self.agent_service.process_request(
                user_query, str(session.id), str(agent.id), self.request_context, token
            )

            message = response.message.get("content", [{}])[0].get("text", "")

            for (
                placeholder,
                original,
            ) in self.request_context.sensitive_key_value.items():
                message = message.replace(placeholder, original)

            data_cache = settings.SENSITIVE_DATA_HANDLER.DATA_CACHE

            unmasked_message = await SensitiveDataUnMaskingService(
                data_cache
            ).process_data(
                message, self.session_id, self.request_context.sensitive_key_value
            )

            return unmasked_message, self.request_context.sensitive_key_value

        except Exception as e:
            raise ChatServiceError from e

    async def record_user_chat_request(
        self,
        session_id: int,
        user_query: str,
        agent_response: str,
        processing_time: float,
        start_time: datetime,
        end_time: datetime,
        response_status_code: int = 200,
    ) -> None:
        try:
            user_chat_request = UserChatRequest()
            user_chat_request.session_id = session_id
            user_chat_request.user_query = user_query
            user_chat_request.agent_response = agent_response
            user_chat_request.start_time = start_time
            user_chat_request.end_time = end_time
            user_chat_request.processing_time = processing_time
            user_chat_request.response_status_code = response_status_code

            self._db_session.add(user_chat_request)
            await self._db_session.commit()
            await self._db_session.refresh(user_chat_request)

        except Exception as e:
            logger.exception("Error recording user chat request in database: %s", e)
