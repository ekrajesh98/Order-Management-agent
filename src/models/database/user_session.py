import uuid

from sqlalchemy import BigInteger, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.utils import get_utc_now

from .base import Base


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = {"comment": "Stores information about user sessions"}

    id = Column(
        "session_id", BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    session_uuid = Column(
        "session_uuid",
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
        default=uuid.uuid4,
    )

    user_uuid = Column("user_uuid", UUID(as_uuid=True), nullable=False, index=True)

    session_type = Column("session_type", String, nullable=False)

    created_at = Column(
        "session_created_at",
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        server_default=func.current_timestamp(),
    )

    updated_at = Column(
        "session_updated_at",
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now,
        server_default=func.current_timestamp(),
    )

    requests = relationship("UserRequest", back_populates="session")
    agents = relationship("SessionAgent", back_populates="session")
    messages = relationship("SessionAgentMessage", back_populates="session")
