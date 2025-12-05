"""
Chat API router.

Provides endpoints for chat conversations with the LLM agent.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.models import Message
from app.core.services import ChatService
from app.dependencies import get_chat_service


router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)


class ChatRequest(BaseModel):
    """Request model for sending a message"""
    content: str


class MessageResponse(BaseModel):
    """Response model for a message"""
    id: str
    role: str
    content: str
    created_at: str

    @classmethod
    def from_message(cls, message: Message) -> "MessageResponse":
        return cls(
            id=message.id,
            role=message.role.value,
            content=message.content,
            created_at=message.created_at.isoformat()
        )


@router.post("/{session_id}", response_model=MessageResponse)
async def send_message(
    session_id: str,
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> MessageResponse:
    """Send a message to the chat and get a response"""
    message = await chat_service.send_message(session_id, request.content)
    return MessageResponse.from_message(message)


@router.get("/{session_id}/history", response_model=List[MessageResponse])
async def get_history(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
) -> List[MessageResponse]:
    """Get conversation history for a session"""
    history = await chat_service.get_history(session_id)
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    return [MessageResponse.from_message(msg) for msg in history]


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
) -> None:
    """Delete a chat session"""
    result = await chat_service.delete_session(session_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
