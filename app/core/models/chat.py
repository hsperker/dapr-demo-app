from datetime import datetime
from enum import Enum
from typing import Tuple
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Immutable message model"""
    model_config = {"frozen": True}

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class Session(BaseModel):
    """
    Immutable session model.

    Sessions hold conversation messages. Use SessionRepository to add messages.
    """
    model_config = {"frozen": True}

    id: str
    messages: Tuple[Message, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def with_message(self, message: Message) -> "Session":
        """
        Return a new session with the message appended.

        This is the immutable way to 'add' a message - it creates a new session
        rather than mutating the existing one.
        """
        return Session(
            id=self.id,
            messages=(*self.messages, message),
            created_at=self.created_at,
            updated_at=datetime.utcnow()
        )
