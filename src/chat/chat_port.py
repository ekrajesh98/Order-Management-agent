from abc import ABC, abstractmethod


class ChatServiceABC(ABC):
    @abstractmethod
    def process_user_chat_request(
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
