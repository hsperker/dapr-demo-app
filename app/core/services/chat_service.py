"""
Chat service for handling conversations with an LLM agent.
"""

from typing import Optional, Sequence

from app.core.models import Message, MessageRole
from app.core.protocols import Agent, SessionRepositoryProtocol


class ChatService:
    """Service for handling chat conversations with an LLM agent"""

    def __init__(
        self,
        session_repository: SessionRepositoryProtocol,
        agent: Agent
    ):
        self.session_repository = session_repository
        self.agent = agent

    async def send_message(self, session_id: str, content: str) -> Message:
        """Send a message and get a response from the agent"""
        # Get or create the session
        session = await self.session_repository.get_or_create(session_id)

        # Create and save user message
        user_message = Message(role=MessageRole.USER, content=content)
        await self.session_repository.add_message(session_id, user_message)

        # Get conversation history for context
        history = session.get_history()

        # Invoke the agent - protocol guarantees string return
        response_text = await self.agent.invoke(history, content)

        # Create and save assistant message
        assistant_message = Message(role=MessageRole.ASSISTANT, content=response_text)
        await self.session_repository.add_message(session_id, assistant_message)

        return assistant_message

    async def get_history(self, session_id: str) -> Optional[Sequence[Message]]:
        """Get conversation history for a session"""
        session = await self.session_repository.get(session_id)
        if session is None:
            return None
        return session.messages

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        return await self.session_repository.delete(session_id)
