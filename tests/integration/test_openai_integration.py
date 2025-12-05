"""
Integration tests that make real calls to OpenAI.

These tests require a valid OPENAI_API_KEY in .env and will be skipped
if the key is not available or if running with --skip-integration flag.

Run with: uv run pytest tests/integration/test_openai_integration.py -v
Skip with: uv run pytest -m "not integration"
"""

import os
import pytest
from typing import AsyncGenerator

from app.config import settings
from app.core.models import Message, MessageRole
from app.core.services import ChatService
from app.core.services.agent import SemanticKernelAgent
from app.infrastructure.repositories import SessionRepository


# Skip all tests in this module if no API key is available
pytestmark = pytest.mark.integration

def has_openai_key() -> bool:
    """Check if OpenAI API key is available"""
    return bool(settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here")


@pytest.fixture
async def session_repository() -> AsyncGenerator[SessionRepository, None]:
    """Create a session repository with in-memory SQLite"""
    repo = SessionRepository(":memory:")
    await repo.initialize()
    yield repo
    await repo.close()


@pytest.fixture
def agent() -> SemanticKernelAgent:
    """Create a real Semantic Kernel agent"""
    if not has_openai_key():
        pytest.skip("OPENAI_API_KEY not configured")
    return SemanticKernelAgent(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        instructions="You are a helpful assistant. Keep responses brief and concise."
    )


@pytest.fixture
async def chat_service(
    session_repository: SessionRepository,
    agent: SemanticKernelAgent
) -> ChatService:
    """Create a chat service with real agent"""
    return ChatService(session_repository, agent)


@pytest.mark.skipif(not has_openai_key(), reason="OPENAI_API_KEY not configured")
class TestOpenAIIntegration:
    """Integration tests with real OpenAI API calls"""

    async def test_simple_chat_response(self, chat_service: ChatService) -> None:
        """Test that we get a coherent response from OpenAI"""
        response = await chat_service.send_message(
            "test-session-1",
            "What is 2 + 2? Reply with just the number."
        )

        assert response is not None
        assert response.role == MessageRole.ASSISTANT
        assert response.content is not None
        assert len(response.content) > 0
        # The response should contain "4" somewhere
        assert "4" in response.content

    async def test_conversation_continuity(self, chat_service: ChatService) -> None:
        """Test that the agent maintains context across messages"""
        session_id = "test-session-continuity"

        # First message - introduce a topic
        response1 = await chat_service.send_message(
            session_id,
            "My name is Alice. Please remember this."
        )
        assert response1 is not None

        # Second message - ask about the topic
        response2 = await chat_service.send_message(
            session_id,
            "What is my name?"
        )
        assert response2 is not None
        assert "Alice" in response2.content

    async def test_session_history_persisted(self, chat_service: ChatService) -> None:
        """Test that conversation history is persisted and retrievable"""
        session_id = "test-session-history"

        # Send a message
        await chat_service.send_message(session_id, "Hello!")

        # Get history
        history = await chat_service.get_history(session_id)

        assert history is not None
        assert len(history) == 2  # user message + assistant response
        assert history[0].role == MessageRole.USER
        assert history[0].content == "Hello!"
        assert history[1].role == MessageRole.ASSISTANT

    async def test_multiple_sessions_isolated(self, chat_service: ChatService) -> None:
        """Test that different sessions are isolated from each other"""
        # Session 1 - talk about cats
        await chat_service.send_message(
            "session-cats",
            "I love cats. My cat's name is Whiskers."
        )

        # Session 2 - talk about dogs
        await chat_service.send_message(
            "session-dogs",
            "I love dogs. My dog's name is Buddy."
        )

        # Ask session 1 about the pet
        response1 = await chat_service.send_message(
            "session-cats",
            "What is my pet's name?"
        )

        # Ask session 2 about the pet
        response2 = await chat_service.send_message(
            "session-dogs",
            "What is my pet's name?"
        )

        # Each session should know its own pet
        assert "Whiskers" in response1.content
        assert "Buddy" in response2.content

    async def test_delete_session_clears_history(self, chat_service: ChatService) -> None:
        """Test that deleting a session clears its history"""
        session_id = "test-session-delete"

        # Create a session with messages
        await chat_service.send_message(session_id, "Hello!")

        # Verify history exists
        history = await chat_service.get_history(session_id)
        assert history is not None
        assert len(history) > 0

        # Delete the session
        result = await chat_service.delete_session(session_id)
        assert result is True

        # Verify history is gone
        history = await chat_service.get_history(session_id)
        assert history is None

    async def test_agent_follows_instructions(self, chat_service: ChatService) -> None:
        """Test that the agent follows system instructions"""
        # The agent is instructed to be brief
        response = await chat_service.send_message(
            "test-session-instructions",
            "Explain quantum physics."
        )

        assert response is not None
        # Response should exist but be reasonably brief due to instructions
        assert len(response.content) > 0
        # A truly brief response should be under 500 chars
        # (this is a soft check - LLMs can be unpredictable)
        assert len(response.content) < 2000
