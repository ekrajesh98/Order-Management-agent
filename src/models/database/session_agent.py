from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.utils import get_utc_now

from .base import Base


class SessionAgent(Base):
    __tablename__ = "session_agents"
    __table_args__ = {
        "comment": "Stores information about agents associated with user sessions"
    }
    id = Column(
        "agent_id", BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    session_id = Column(
        "session_id",
        BigInteger,
        ForeignKey("user_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(
        "agent_name",
        String(255),
        nullable=False,
        default="default",
        server_default="default",
    )

    meta = Column("agent_metadata", JSONB, nullable=True)

    created_at = Column(
        "agent_created_at",
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
    )

    updated_at = Column(
        "agent_updated_at",
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now,
        server_default=func.current_timestamp(),
    )

    session = relationship("UserSession", back_populates="agents")
    messages = relationship("SessionAgentMessage", back_populates="agent")
