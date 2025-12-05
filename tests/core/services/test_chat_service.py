import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

from app.core.models import Message, MessageRole, Session
from app.core.services.chat_service import ChatService
from app.infrastructure.repositories import SessionRepository


@pytest.fixture
def mock_session_repository() -> AsyncMock:
    """Create a mock session repository"""
    repo = AsyncMock(spec=SessionRepository)
    return repo


@pytest.fixture
def mock_agent() -> AsyncMock:
    """Create a mock Semantic Kernel agent"""
    agent = AsyncMock()
    return agent


class TestChatService:
    """Test suite for ChatService"""

    async def test_send_message_creates_session_if_not_exists(
        self,
        mock_session_repository: AsyncMock,
        mock_agent: AsyncMock
    ) -> None:
        """Test that sending a message creates session if needed"""
        session = Session(id="test-session")
        mock_session_repository.get_or_create.return_value = session

        # Mock agent response
        mock_agent.invoke.return_value = "Hello! How can I help you?"

        service = ChatService(mock_session_repository, mock_agent)
        response = await service.send_message("test-session", "Hello")

        mock_session_repository.get_or_create.assert_called_once_with("test-session")
        assert response is not None

    async def test_send_message_adds_user_message(
        self,
        mock_session_repository: AsyncMock,
        mock_agent: AsyncMock
    ) -> None:
        """Test that user message is added to session"""
        session = Session(id="test-session")
        mock_session_repository.get_or_create.return_value = session
        mock_agent.invoke.return_value = "Response"

        service = ChatService(mock_session_repository, mock_agent)
        await service.send_message("test-session", "Hello")

        # Verify user message was added
        calls = mock_session_repository.add_message.call_args_list
        assert len(calls) >= 1
        first_call = calls[0]
        session_id, message = first_call[0]
        assert session_id == "test-session"
        assert message.role == MessageRole.USER
        assert message.content == "Hello"

    async def test_send_message_adds_assistant_response(
        self,
        mock_session_repository: AsyncMock,
        mock_agent: AsyncMock
    ) -> None:
        """Test that assistant response is added to session"""
        session = Session(id="test-session")
        mock_session_repository.get_or_create.return_value = session
        mock_agent.invoke.return_value = "I'm doing well!"

        service = ChatService(mock_session_repository, mock_agent)
        response = await service.send_message("test-session", "How are you?")

        # Verify assistant message was added
        calls = mock_session_repository.add_message.call_args_list
        assert len(calls) == 2  # user + assistant
        second_call = calls[1]
        session_id, message = second_call[0]
        assert session_id == "test-session"
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "I'm doing well!"

        # Verify response
        assert response.content == "I'm doing well!"

    async def test_send_message_passes_history_to_agent(
        self,
        mock_session_repository: AsyncMock,
        mock_agent: AsyncMock
    ) -> None:
        """Test that conversation history is passed to agent"""
        session = Session(id="test-session")
        session = session.with_message(Message(role=MessageRole.USER, content="Previous message"))
        session = session.with_message(Message(role=MessageRole.ASSISTANT, content="Previous response"))
        mock_session_repository.get_or_create.return_value = session
        mock_agent.invoke.return_value = "New response"

        service = ChatService(mock_session_repository, mock_agent)
        await service.send_message("test-session", "New message")

        # Verify agent was invoked with history
        mock_agent.invoke.assert_called_once()

    async def test_get_history_returns_session_messages(
        self,
        mock_session_repository: AsyncMock,
        mock_agent: AsyncMock
    ) -> None:
        """Test getting conversation history"""
        session = Session(id="test-session")
        session = session.with_message(Message(role=MessageRole.USER, content="Hello"))
        session = session.with_message(Message(role=MessageRole.ASSISTANT, content="Hi!"))
        mock_session_repository.get.return_value = session

        service = ChatService(mock_session_repository, mock_agent)
        history = await service.get_history("test-session")

        assert history is not None
        assert len(history) == 2
        assert history[0].content == "Hello"
        assert history[1].content == "Hi!"

    async def test_get_history_returns_none_for_nonexistent_session(
        self,
        mock_session_repository: AsyncMock,
        mock_agent: AsyncMock
    ) -> None:
        """Test getting history for non-existent session"""
        mock_session_repository.get.return_value = None

        service = ChatService(mock_session_repository, mock_agent)
        history = await service.get_history("nonexistent")

        assert history is None

    async def test_delete_session(
        self,
        mock_session_repository: AsyncMock,
        mock_agent: AsyncMock
    ) -> None:
        """Test deleting a session"""
        mock_session_repository.delete.return_value = True

        service = ChatService(mock_session_repository, mock_agent)
        result = await service.delete_session("test-session")

        assert result is True
        mock_session_repository.delete.assert_called_once_with("test-session")

    async def test_delete_nonexistent_session(
        self,
        mock_session_repository: AsyncMock,
        mock_agent: AsyncMock
    ) -> None:
        """Test deleting a non-existent session"""
        mock_session_repository.delete.return_value = False

        service = ChatService(mock_session_repository, mock_agent)
        result = await service.delete_session("nonexistent")

        assert result is False
