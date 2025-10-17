import logging
from http import HTTPStatus

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.agent_service import OrderManagementAgentService
from src.chat.chat_port import ChatServiceABC
from src.chat.chat_service import ChatService, ChatServiceError
from src.config import settings
from src.database import get_db_session
from src.models.pydantic import ChatRequest
from src.routers.dependencies import resolve_session_id
from src.utils import Stopwatch, get_utc_now

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
    int_session_id: int = Depends(resolve_session_id),
    db_session: AsyncSession = Depends(dependency=get_db_session),
) -> dict[str, str]:
    
    start_time = get_utc_now()
    try:
        async with (stopwatch := Stopwatch()):
            session_id = str(int_session_id)

            token = authorization.split(" ", 1)[1] if authorization else ""

            chat_service = await _build_chat_service(db_session, session_id)

            (
                agent_response,
                sensitive_key_value,
            ) = await chat_service.process_user_chat_request(chat_request.query, token)

    except ChatServiceError as e:
        await chat_service.record_user_chat_request(
            int_session_id,
            chat_request.query,
            None,
            stopwatch.elapsed_ms,
            start_time,
            get_utc_now(),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Error occurred while to process the chat request",
        ) from e

    else:
        if settings.SENSITIVE_DATA_HANDLER.MASK_SENSITIVE_DATA:
            background_tasks.add_task(
                settings.SENSITIVE_DATA_HANDLER.DATA_CACHE.set_many_under,
                session_id,
                sensitive_key_value,
            )

        background_tasks.add_task(
            chat_service.record_user_chat_request,
            int_session_id,
            chat_request.query,
            agent_response,
            stopwatch.elapsed_ms,
            start_time,
            get_utc_now(),
            200,
        )

        return {"message": agent_response}
