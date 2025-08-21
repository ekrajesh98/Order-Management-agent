import os
import uuid
from uuid import UUID

from dotenv import load_dotenv
from fastapi import FastAPI
from mcp.client.streamable_http import streamablehttp_client
from pydantic import BaseModel
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient

from custom_hooks import DebuggingHook, SimplePIIMaskHooks

# Load environment variables from .env file
load_dotenv()

# Fetch OpenAI API key and model from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")

app = FastAPI()


# Request body model
class ChatRequest(BaseModel):
    query: str
    session_id: uuid.UUID


async def get_user_guid():
    # Simulate fetching user GUID from a database or session
    # In a real application, this would be replaced with actual logic
    return "6e66013a-b2fd-4938-bae6-07f44f05afac"


session_clients: dict[UUID, MCPClient] = {}
session_agents: dict[UUID, Agent] = {}


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_guid = await get_user_guid()
    if request.session_id not in session_clients:
        client = MCPClient(lambda: streamablehttp_client("http://0.0.0.0:8000/mcp/"))
        session_clients[request.session_id] = client
        with client:
            tools = client.list_tools_sync()

        llm = OpenAIModel(client_args={"api_key": OPENAI_API_KEY}, model_id=MODEL)
        prompt = f"""
            You are an order management assistant chatbot. Follow these steps:


            1. The current user GUID is {user_guid}. Use it for all requests to MCP.
            2. If any required input field is missing, respond with an error message specifying the missing field.
            3. If the user request is about creating an order, include the unique order ID in the response. Clearly state the order ID in the natural language response.

            IMPORTANT FOR RESPONSE GENERATION:
            1. Some PII data in the input are replaced with placeholders like [PLACEHOLDERNAME-UUID]. It will be reverse engineered to return original value to users, so don't alter the placeholders in your response.
            Example: "Your order with ID [ORDER-1234] has been created successfully" response will be reverse engineered to "Your order with ID 1234 has been created successfully" before returning to user.

            """
        mask_hook = SimplePIIMaskHooks()

        agent = Agent(
            model=llm,
            tools=tools,
            conversation_manager=SlidingWindowConversationManager(),
            system_prompt=prompt,
            hooks=[mask_hook, DebuggingHook()],
        )
        agent.session_id = request.session_id
        session_agents[request.session_id] = agent
        session_agents[request.session_id] = {"agent": agent, "mask_hook": mask_hook}

    client = session_clients[request.session_id]
    session_data = session_agents[request.session_id]

    with client:
        response = session_data["agent"](request.query)
        message = response.message.get("content", [{}])[0].get("text", "")

        # Unmask the response before returning to user
        unmasked_message = session_data["mask_hook"]._unmask_text(
            message, str(request.session_id)
        )

        return {"message": unmasked_message}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
