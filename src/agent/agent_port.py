from abc import ABC, abstractmethod
from typing import Any

from src.context.request_context import RequestContext


class AgentServiceABC(ABC):
    @abstractmethod
    def process_request(
        self,
        user_query: str,
        session_id: str,
        agent_id: str,
        context: RequestContext,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        Process a user chat request.
        Args:
            user_query: The user's chat query.
            session_id: The session identifier.
            agent_id: The agent identifier.
            context: Request context containing session-specific information
            token: Optional authorization token.
        Returns:
            Dictionary containing the agent's response message
        """
