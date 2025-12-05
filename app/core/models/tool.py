from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, HttpUrl


class ToolStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ERROR = "error"


class Tool(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    openapi_url: str
    description: Optional[str] = None
    status: ToolStatus = ToolStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("openapi_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        # Basic URL validation
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v
