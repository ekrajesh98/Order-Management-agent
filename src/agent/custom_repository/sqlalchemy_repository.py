from typing import Any

from sqlalchemy import select
from strands.session.repository_session_manager import RepositorySessionManager
from strands.session.session_repository import SessionRepository
from strands.types.session import Session, SessionMessage
from strands.types.session import SessionAgent as StrandsSessionAgent

from src.models.database import SessionAgent, SessionAgentMessage, UserSession
from src.utils import get_utc_now


class SqlAlchemySessionManager(RepositorySessionManager, SessionRepository):
    """
    Implements Strands SessionRepository using SQLAlchemy and database.
    """

    def __init__(
        self,
        session_id: str,
        session_factory: Any = None,
    ) -> None:
        self._session_factory = session_factory
        if not self._session_factory:
            from src.database import get_sync_db_session

            self._session_factory = get_sync_db_session

        self.session_id = session_id
        super().__init__(session_id=session_id, session_repository=self)

    def create_session(self, session: Session, **kwargs) -> Session:
        with self._session_factory() as db_session:
            user_session_query = select(UserSession).where(
                UserSession.id == int(self.session_id)
            )
            user_session = db_session.execute(user_session_query).scalar_one_or_none()
            if not user_session:
                raise ValueError("Invalid session ID provided")

            return Session(
                str(user_session.id),
                user_session.session_type,
                created_at=user_session.created_at.isoformat(),
                updated_at=user_session.updated_at.isoformat(),
            )

    def read_session(self, session_id: str, **kwargs) -> Session:
        with self._session_factory() as db_session:
            user_session_query = select(UserSession).where(
                UserSession.id == int(session_id)
            )
            user_session = db_session.execute(user_session_query).scalar_one_or_none()
            if not user_session:
                return None

            return Session(
                session_id,
                user_session.session_type,
                created_at=user_session.created_at.isoformat(),
                updated_at=user_session.updated_at.isoformat(),
            )

    def create_agent(
        self, session_id: str, strands_session_agent: StrandsSessionAgent, **kwargs
    ) -> None:
        with self._session_factory() as db_session:
            session_agent_query = select(SessionAgent).where(
                SessionAgent.session_id == int(session_id),
                SessionAgent.id == int(strands_session_agent.agent_id),
            )
            session_agent = db_session.execute(session_agent_query).scalar_one_or_none()

            if not session_agent:
                raise ValueError("Invalid session ID or agent ID provided")

            session_agent.meta = strands_session_agent.to_dict()

            db_session.commit()

    def read_agent(
        self, session_id: str, agent_id: str, **kwargs
    ) -> StrandsSessionAgent | None:
        with self._session_factory() as db_session:
            db_agent_query = select(SessionAgent).where(
                SessionAgent.session_id == int(session_id),
                SessionAgent.id == int(agent_id),
                SessionAgent.meta.isnot(None),
            )
            db_agent = db_session.execute(db_agent_query).scalar_one_or_none()
            if not db_agent:
                return None

            agent_data = db_agent.meta or {}

            agent = StrandsSessionAgent.from_dict(agent_data)
            return agent

    def create_message(
        self,
        session_id: str,
        agent_id: str,
        session_message: SessionMessage,
        **kwargs,
    ) -> None:
        with self._session_factory() as db_session:
            db_message = SessionAgentMessage(
                session_id=int(session_id),
                agent_id=int(agent_id),
                message_index=session_message.message_id,
                message_data=session_message.to_dict(),
            )
            db_session.add(db_message)
            db_session.commit()

    def read_message(
        self, session_id: str, agent_id: str, message_id: int, **kwargs
    ) -> SessionMessage | None:
        with self._session_factory() as db_session:
            db_message_query = select(SessionAgentMessage).where(
                SessionAgentMessage.session_id == int(session_id),
                SessionAgentMessage.agent_id == int(agent_id),
                SessionAgentMessage.message_index == message_id,
            )

            db_message = db_session.execute(db_message_query).scalar_one_or_none()

            if not db_message:
                return None

            return SessionMessage.from_dict(db_message.message_data)

    def list_messages(
        self,
        session_id: str,
        agent_id: str,
        limit: int = 100,
        offset: int = 0,
        **kwargs,
    ) -> list[SessionMessage]:
        with self._session_factory() as db_session:
            db_messages_query = (
                select(SessionAgentMessage)
                .where(
                    SessionAgentMessage.session_id == int(session_id),
                    SessionAgentMessage.agent_id == int(agent_id),
                )
                .offset(offset)
                .limit(limit)
            )

            db_messages = db_session.execute(db_messages_query).scalars().all()
            return [
                SessionMessage.from_dict(message.message_data)
                for message in db_messages
            ]

    def update_agent(
        self, session_id: str, session_agent: StrandsSessionAgent, **kwargs
    ) -> None:
        with self._session_factory() as db_session:
            db_agent = select(SessionAgent).where(
                SessionAgent.session_id == int(session_id),
                SessionAgent.id == int(session_agent.agent_id),
            )
            db_agent_instance = db_session.execute(db_agent).scalar_one_or_none()

            if not db_agent_instance:
                raise ValueError("Agent not found for the given session and agent ID")

            db_agent_instance.meta = session_agent.to_dict()
            db_agent_instance.updated_at = get_utc_now()
            db_session.commit()

    def update_message(
        self,
        session_id: str,
        agent_id: str,
        session_message: SessionMessage,
        **kwargs,
    ) -> None:
        with self._session_factory() as db_session:
            db_message_query = select(SessionAgentMessage).where(
                SessionAgentMessage.session_id == int(session_id),
                SessionAgentMessage.agent_id == int(agent_id),
                SessionAgentMessage.message_index == session_message.message_id,
            )
            db_message = db_session.execute(db_message_query).scalar_one_or_none()

            if not db_message:
                raise ValueError(
                    f"Message with id {session_message.message_id} not found for the given IDs"
                )
            print(
                f"===================updating message with id: {session_message.message_id} with values: {session_message.to_dict()}"
            )
            db_message.message_data = session_message.to_dict()
            db_message.updated_at = get_utc_now()
            db_session.commit()
