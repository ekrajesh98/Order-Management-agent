import uuid

from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    session_id: uuid.UUID
