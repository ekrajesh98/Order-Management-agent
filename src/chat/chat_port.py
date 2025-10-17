from abc import ABC, abstractmethod
from datetime import datetime


class ChatServiceABC(ABC):
    @abstractmethod
    async def process_user_chat_request(
        self, user_query: str, token: str | None = None
    ) -> str:
        """
        Process a user chat request.
        Args:
            user_query: The user's chat query.
            token: Optional authorization token.
        Returns:
            The agent's response message.
        """

    @abstractmethod
    async def record_user_chat_request(
        self,
        session_id: int,
        user_query: str,
        agent_response: str,
        processing_time: float,
        start_time: datetime,
        end_time: datetime,
        response_status_code: int = 200,
    ) -> None:
        """
        Record user query and agent response in a persistent storage.
        Args:
            session_id: Foreign key linking the user_sessions table.
            user_query: The prompt given by user.
            agent_response: The end response given by the agent.
            processing_time: Total time taken to process the request.
            start_time: Time at which server received user request.
            end_time: Time at which request processing completed.
            response_status_code: The status code of the response returned to client. Defaults to 200.
        Returns:
            None
        """
