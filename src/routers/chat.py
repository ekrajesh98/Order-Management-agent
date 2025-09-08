from fastapi import APIRouter, FastAPI, Header
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models.openai import OpenAIModel
from strands.session.file_session_manager import FileSessionManager
from strands.tools.mcp import MCPClient

from src.config import settings
from src.models.pydantic import ChatRequest

app = FastAPI()

router = APIRouter()


@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    authorization: str | None = Header(None),
):
    client = MCPClient(
        lambda: streamablehttp_client(
            settings.MCP_SERVER.URL,
            headers={"Authorization": f"Bearer {authorization.split(" ", 1)[1]}"},
        )
    )
    with client:
        tools = client.list_tools_sync()

    llm = OpenAIModel(
        client_args={"api_key": settings.MODEL.API_KEY}, model_id=settings.MODEL.NAME
    )
    prompt = """
        You are an order management assistant chatbot. Follow these steps:

        1. If any required input field is missing, respond with an error message specifying the missing field.
        2. If the user request is about creating an order, include the unique order ID in the response. Clearly state the order ID in the natural language response.

        """

    session_id = str(request.session_id)

    session_manager = FileSessionManager(
        session_id=session_id, storage_dir=settings.FILE_SESSION.STORAGE_DIR
    )

    agent = Agent(
        model=llm,
        tools=tools,
        conversation_manager=SlidingWindowConversationManager(),
        system_prompt=prompt,
        session_manager=session_manager,
    )
    with client:
        response = agent(request.query)
        message = response.message.get("content", [{}])[0].get("text", "")

        return {"message": message}
