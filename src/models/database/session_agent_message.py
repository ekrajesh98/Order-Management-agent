from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.utils import get_utc_now

from .base import Base


class SessionAgentMessage(Base):
    __tablename__ = "session_agent_messages"
    __table_args__ = (
        {
            "comment": "Stores messages exchanged between users and agents within a session"
        },
    )

    id = Column(
        "message_id", BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    agent_id = Column(
        "agent_id",
        BigInteger,
        ForeignKey("session_agents.agent_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    session_id = Column(
        "session_id",
        BigInteger,
        ForeignKey("user_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    message_index = Column(
        "agent_message_index",
        BigInteger,
        nullable=False,
        comment="Index of the message in the conversation history for this agent",
    )

    message_data = Column("message_data", JSONB, nullable=False)

    created_at = Column(
        "message_created_at",
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
    )

    updated_at = Column(
        "message_updated_at",
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now,
        server_default=func.current_timestamp(),
    )

    agent = relationship("SessionAgent", back_populates="messages")
    session = relationship("UserSession", back_populates="messages")
