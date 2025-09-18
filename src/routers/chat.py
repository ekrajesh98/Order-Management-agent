from fastapi import APIRouter, FastAPI, Header

from src.agent.agent_service import OrderManagementAgentService
from src.models.pydantic import ChatRequest

app = FastAPI()

router = APIRouter()
agent_service = OrderManagementAgentService()


@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    authorization: str | None = Header(None),
) -> dict:
    """
    Chat endpoint for order management operations.

    Args:
        request: Chat request containing query and session information
        authorization: Optional authorization header with Bearer token

    Returns:
        Dictionary containing the agent's response message
    """

    token = authorization.split(" ", 1)[1] if authorization else ""

    response = await agent_service.process_chat_request(request, token)

    return response
