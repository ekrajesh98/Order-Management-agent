from sqlalchemy import (
    DECIMAL,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    SmallInteger,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.utils import get_utc_now

from .base import Base


class UserRequest(Base):
    __tablename__ = "user_requests"
    __table_args__ = {
        "comment": "Stores information about individual user requests within a session"
    }

    request_id = Column(
        "request_id", BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    session_id = Column(
        "session_id",
        BigInteger,
        ForeignKey("user_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    start_time = Column(
        "request_start_time",
        DateTime(timezone=True),
        nullable=False,
        index=True,
        default=get_utc_now,
    )

    end_time = Column(
        "request_end_time", DateTime(timezone=True), nullable=True, index=True
    )

    processing_time = Column("request_processing_time", DECIMAL(10, 3), nullable=True)

    created_at = Column(
        "request_created_at",
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
    )

    updated_at = Column(
        "request_updated_at",
        DateTime(timezone=True),
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now,
        server_default=func.current_timestamp(),
    )

    response_status_code = Column("response_status_code", SmallInteger, nullable=True)

    session = relationship("UserSession", back_populates="requests")
