from typing import Any, Dict

from src.agent.agent_factory import MCPClientFactory, OrderManagementAgentFactory
from src.models.pydantic import ChatRequest


class OrderManagementAgentService:
    """Service for handling order management agent operations."""

    def __init__(self):
        self.agent_factory = OrderManagementAgentFactory()
        self.client_factory = MCPClientFactory()

    async def process_chat_request(
        self, request: ChatRequest, authorization_token: str = ""
    ) -> Dict[str, Any]:
        """
        Process a chat request using the order management agent.

        Args:
            request: Chat request containing query and session info
            authorization_token: Authorization token for MCP tools

        Returns:
            Dictionary containing the agent's response message
        """
        client = self.client_factory.create_client(authorization_token)

        with client:
            tools = client.list_tools_sync()

            agent = self.agent_factory.create_agent(
                session_id=str(request.session_id),
                tools=tools,
                authorization_token=authorization_token,
            )

            response = agent(request.query)
            message = response.message.get("content", [{}])[0].get("text", "")

            return {"message": message}
