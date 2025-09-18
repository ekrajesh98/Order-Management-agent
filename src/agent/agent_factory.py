from typing import Any, List

from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands.models.openai import OpenAIModel
from strands.session.file_session_manager import FileSessionManager
from strands.tools.mcp import MCPClient

from src.agent.custom_hooks import SensitiveDataMaskingHook
from src.config import settings


class OrderManagementAgentFactory:
    """Factory for creating order management agents with proper configuration."""

    @staticmethod
    def create_agent(
        session_id: str, tools: List[Any], authorization_token: str = ""
    ) -> Agent:
        """
        Create and configure an order management agent.

        Args:
            session_id: Unique session identifier
            tools: List of MCP tools available to the agent
            authorization_token: Bearer token for tool authorization

        Returns:
            Configured Agent instance
        """
        session_manager = FileSessionManager(
            session_id=session_id,
            storage_dir="user-sessions",
        )

        system_prompt = """
            You are an order management assistant chatbot. Follow these steps:
            1. If any required input field is missing, respond with an error message specifying the missing field.
            2. If the user request is about creating an order, include the unique order ID in the response. Clearly state the order ID in the natural language response.
        """

        agent = Agent(
            model=OpenAIModel(
                client_args={"api_key": settings.MODEL.API_KEY},
                model_id=settings.MODEL.NAME,
            ),
            tools=tools,
            conversation_manager=SlidingWindowConversationManager(),
            system_prompt=system_prompt,
            session_manager=session_manager,
            hooks=[SensitiveDataMaskingHook(session_manager)],
        )

        return agent


class MCPClientFactory:
    """Factory for creating MCP clients with proper configuration."""

    @staticmethod
    def create_client(authorization_token: str = "") -> MCPClient:
        """
        Create an MCP client with authorization.

        Args:
            authorization_token: Bearer token for MCP server

        Returns:
            Configured MCPClient instance
        """
        return MCPClient(
            lambda: streamablehttp_client(
                settings.MCP_SERVER.URL,
                headers={"Authorization": f"Bearer {authorization_token}"},
            )
        )
