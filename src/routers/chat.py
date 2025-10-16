import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.agent_service import OrderManagementAgentService
from src.chat.chat_port import ChatServiceABC
from src.chat.chat_service import ChatService, ChatServiceError
from src.config import settings
from src.database import get_db_session
from src.models.pydantic import ChatRequest
from src.routers.dependencies import resolve_session_id

router = APIRouter()

logger = logging.getLogger(__name__)


async def _build_chat_service(
    db_session: AsyncSession,
    session_id: str,
) -> ChatServiceABC:
    agent_service = OrderManagementAgentService(session_id)
    return ChatService(db_session, session_id, agent_service)


@router.post("/chat")
async def process_chat_request(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(None),
    session_id: int = Depends(resolve_session_id),
    db_session: AsyncSession = Depends(dependency=get_db_session),
) -> dict[str, str]:
    """
    Chat endpoint for order management operations.

    Args:
        request: Chat request containing query and session information
        authorization: Optional authorization header with Bearer token

    Returns:
        Dictionary containing the agent's response message

    """
    try:
        session_id = str(session_id)

        token = authorization.split(" ", 1)[1] if authorization else ""

        chat_service = await _build_chat_service(db_session, session_id)

        response, sensitive_key_value = await chat_service.process_user_chat_request(
            chat_request.query, token
        )

        if settings.SENSITIVE_DATA_HANDLER.MASK_SENSITIVE_DATA:
            background_tasks.add_task(
                settings.SENSITIVE_DATA_HANDLER.DATA_CACHE.set_many_under,
                session_id,
                sensitive_key_value,
            )

        return {"message": response}

    except ChatServiceError as e:
        logger.exception("Chat service error: %s", e)
        raise e
