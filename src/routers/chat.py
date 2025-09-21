from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, Header, Request

from src.agent.agent_service import OrderManagementAgentService
from src.config import settings
from src.context.dependencies import get_request_context
from src.context.request_context import RequestContext
from src.models.pydantic import ChatRequest
from src.sensitive_data_handler.data_handler_service import (
    SensitiveDataUnMaskingService,
)

app = FastAPI()

router = APIRouter()
agent_service = OrderManagementAgentService()


@router.post("/chat")
async def chat_endpoint(
    request: Request,
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(None),
    context: RequestContext = Depends(get_request_context),
) -> dict:
    """
    Chat endpoint for order management operations.

    Args:
        request: Chat request containing query and session information
        authorization: Optional authorization header with Bearer token

    Returns:
        Dictionary containing the agent's response message
    """
    session_id = str(chat_request.session_id)
    token = authorization.split(" ", 1)[1] if authorization else ""

    response = await agent_service.process_chat_request(chat_request, context, token)

    message = response.message.get("content", [{}])[0].get("text", "")

    for placeholder, original in context.sensitive_key_value.items():
        message = message.replace(placeholder, original)

    data_cache = settings.SENSITIVE_DATA_HANDLER.DATA_CACHE

    unmasked_message = await SensitiveDataUnMaskingService(data_cache).process_data(
        message, session_id, context.sensitive_key_value
    )

    if context.sensitive_key_value:
        background_tasks.add_task(
            settings.SENSITIVE_DATA_HANDLER.DATA_CACHE.set_many_under,
            session_id,
            context.sensitive_key_value,
        )

    return {"message": unmasked_message}
