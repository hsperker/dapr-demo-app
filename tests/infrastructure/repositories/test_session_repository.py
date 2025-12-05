import pytest
from typing import AsyncGenerator

from app.core.models import Message, MessageRole, Session
from app.infrastructure.repositories import SessionRepository


@pytest.fixture
async def repository() -> AsyncGenerator[SessionRepository, None]:
    """Create a session repository with in-memory SQLite for testing"""
    repo = SessionRepository(":memory:")
    await repo.initialize()
    yield repo
    await repo.close()


class TestSessionRepository:
    """Test suite for SessionRepository"""

    async def test_create_session(self, repository: SessionRepository) -> None:
        """Test creating a new session"""
        session = await repository.create("test-session-123")
        assert session.id == "test-session-123"
        assert session.messages == ()  # tuple since Session is immutable

    async def test_get_session(self, repository: SessionRepository) -> None:
        """Test retrieving an existing session"""
        await repository.create("test-session")
        session = await repository.get("test-session")
        assert session is not None
        assert session.id == "test-session"

    async def test_get_nonexistent_session(self, repository: SessionRepository) -> None:
        """Test retrieving a non-existent session returns None"""
        session = await repository.get("nonexistent")
        assert session is None

    async def test_add_message_to_session(self, repository: SessionRepository) -> None:
        """Test adding a message to a session"""
        await repository.create("test-session")
        message = Message(role=MessageRole.USER, content="Hello!")

        await repository.add_message("test-session", message)

        session = await repository.get("test-session")
        assert session is not None
        assert len(session.messages) == 1
        assert session.messages[0].content == "Hello!"
        assert session.messages[0].role == MessageRole.USER

    async def test_add_multiple_messages(self, repository: SessionRepository) -> None:
        """Test adding multiple messages preserves order"""
        await repository.create("test-session")

        msg1 = Message(role=MessageRole.USER, content="Hello")
        msg2 = Message(role=MessageRole.ASSISTANT, content="Hi there!")
        msg3 = Message(role=MessageRole.USER, content="How are you?")

        await repository.add_message("test-session", msg1)
        await repository.add_message("test-session", msg2)
        await repository.add_message("test-session", msg3)

        session = await repository.get("test-session")
        assert session is not None
        assert len(session.messages) == 3
        assert session.messages[0].content == "Hello"
        assert session.messages[1].content == "Hi there!"
        assert session.messages[2].content == "How are you?"

    async def test_delete_session(self, repository: SessionRepository) -> None:
        """Test deleting a session"""
        await repository.create("test-session")
        await repository.add_message(
            "test-session",
            Message(role=MessageRole.USER, content="Hello")
        )

        result = await repository.delete("test-session")
        assert result is True

        session = await repository.get("test-session")
        assert session is None

    async def test_delete_nonexistent_session(self, repository: SessionRepository) -> None:
        """Test deleting a non-existent session returns False"""
        result = await repository.delete("nonexistent")
        assert result is False

    async def test_session_persists_message_metadata(self, repository: SessionRepository) -> None:
        """Test that message metadata (id, created_at) is persisted"""
        await repository.create("test-session")
        message = Message(role=MessageRole.USER, content="Hello")
        original_id = message.id
        original_created = message.created_at

        await repository.add_message("test-session", message)

        session = await repository.get("test-session")
        assert session is not None
        assert session.messages[0].id == original_id
        assert session.messages[0].created_at == original_created

    async def test_get_or_create_new_session(self, repository: SessionRepository) -> None:
        """Test get_or_create creates a new session if it doesn't exist"""
        session = await repository.get_or_create("new-session")
        assert session.id == "new-session"
        assert session.messages == ()  # tuple since Session is immutable

    async def test_get_or_create_existing_session(self, repository: SessionRepository) -> None:
        """Test get_or_create returns existing session"""
        await repository.create("existing-session")
        await repository.add_message(
            "existing-session",
            Message(role=MessageRole.USER, content="Hello")
        )

        session = await repository.get_or_create("existing-session")
        assert session.id == "existing-session"
        assert len(session.messages) == 1
