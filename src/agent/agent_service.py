from typing import Any

from src.agent.agent_factory import MCPClientFactory, OrderManagementAgentFactory
from src.config import settings
from src.context.request_context import RequestContext

from .agent_port import AgentServiceABC


class OrderManagementAgentServiceError(Exception):
    """Custom exception for OrderManagementAgentService errors."""

    pass


class OrderManagementAgentService(AgentServiceABC):
    """Service for handling order management agent operations."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.agent_factory = OrderManagementAgentFactory(
            settings.MODEL.NAME,
            settings.MODEL.API_KEY,
            settings.SESSION_REPOSITORY.get_session_manager(self.session_id),
        )
        self.client_factory = MCPClientFactory(settings.MCP_SERVER.URL)

    async def process_request(
        self,
        user_query: str,
        session_id: str,
        agent_id: str,
        context: RequestContext,
        authorization_token: str = "",
    ) -> dict[str, Any]:
        try:
            client = await self.client_factory.create_client(authorization_token)
            with client:
                tools = client.list_tools_sync()

                agent = await self.agent_factory.create_agent(
                    session_id=session_id,
                    agent_id=agent_id,
                    tools=tools,
                    context=context,
                    authorization_token=authorization_token,
                )

                response = await agent.invoke_async(user_query)

                return response

        except Exception as e:
            raise OrderManagementAgentServiceError from e
