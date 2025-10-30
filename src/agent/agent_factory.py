from typing import Any, List

from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models import Model

# from strands.models.openai import OpenAIModel
from strands.session.file_session_manager import FileSessionManager
from strands.session.s3_session_manager import S3SessionManager
from strands.tools.mcp import MCPClient

from src.agent.custom_hooks import SensitiveDataMaskingHook
from src.agent.custom_repository.sqlalchemy_repository import (
    SqlAlchemySessionManager,
)
from src.config import settings
from src.context.request_context import RequestContext


class OrderManagementAgentFactory:
    """Factory for creating order management agents with proper configuration."""

    def __init__(
        self,
        session_manager: FileSessionManager
        | S3SessionManager
        | SqlAlchemySessionManager,
        model: Model = settings.MODEL.model,
    ) -> None:
        self.session_manager = session_manager
        self.model = model

    async def create_agent(
        self,
        session_id: str,
        agent_id: str,
        tools: List[Any],
        context: RequestContext,
        authorization_token: str = "",
    ) -> Agent:
        """
        Create and configure an order management agent.

        Args:
            session_id: Unique session identifier
            agent_id: Unique agent identifier
            tools: List of MCP tools available to the agent
            authorization_token: Bearer token for tool authorization

        Returns:
            Configured Agent instance
        """

        system_prompt = """
            You are an order management assistant chatbot. Follow these steps:
            1. If any required input field is missing, respond with an error message specifying the missing field.
            2. If the user request is about creating an order, include the unique order ID in the response. Clearly state the order ID in the natural language response.
        """

        agent = Agent(
            model=self.model,
            tools=tools,
            conversation_manager=SlidingWindowConversationManager(),
            system_prompt=system_prompt,
            session_manager=self.session_manager,
            hooks=[SensitiveDataMaskingHook(self.session_manager, context, session_id)],
            agent_id=agent_id,
        )

        return agent


class MCPClientFactory:
    """Factory for creating MCP clients with proper configuration."""

    def __init__(self, mcp_server_url: str) -> None:
        self.mcp_server_url = mcp_server_url

    async def create_client(self, authorization_token: str = "") -> MCPClient:
        """
        Create an MCP client with authorization.

        Args:
            authorization_token: Bearer token for MCP server

        Returns:
            Configured MCPClient instance
        """
        return MCPClient(
            lambda: streamablehttp_client(
                self.mcp_server_url,
                headers={"Authorization": f"Bearer {authorization_token}"},
            )
        )
