import pytest
from datetime import datetime
from pydantic import ValidationError

from app.core.models.chat import Message, MessageRole, Session


class TestMessage:
    """Test suite for the Message model"""

    def test_create_user_message(self) -> None:
        """Test creating a user message"""
        message = Message(
            role=MessageRole.USER,
            content="Hello, how are you?"
        )
        assert message.role == MessageRole.USER
        assert message.content == "Hello, how are you?"
        assert message.id is not None
        assert message.created_at is not None

    def test_create_assistant_message(self) -> None:
        """Test creating an assistant message"""
        message = Message(
            role=MessageRole.ASSISTANT,
            content="I'm doing well, thank you!"
        )
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "I'm doing well, thank you!"

    def test_create_system_message(self) -> None:
        """Test creating a system message"""
        message = Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant."
        )
        assert message.role == MessageRole.SYSTEM

    def test_message_requires_content(self) -> None:
        """Test that message requires content"""
        with pytest.raises(ValidationError):
            Message(role=MessageRole.USER, content="")

    def test_message_auto_generates_id(self) -> None:
        """Test that message auto-generates unique IDs"""
        msg1 = Message(role=MessageRole.USER, content="Hello")
        msg2 = Message(role=MessageRole.USER, content="World")
        assert msg1.id != msg2.id


class TestSession:
    """Test suite for the Session model"""

    def test_create_session(self) -> None:
        """Test creating a new session"""
        session = Session(id="test-session-123")
        assert session.id == "test-session-123"
        assert session.messages == ()
        assert session.created_at is not None

    def test_session_with_messages(self) -> None:
        """Test session with messages"""
        messages = (
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there!")
        )
        session = Session(id="test-session", messages=messages)
        assert len(session.messages) == 2
        assert session.messages[0].role == MessageRole.USER
        assert session.messages[1].role == MessageRole.ASSISTANT

    def test_session_is_immutable(self) -> None:
        """Test that session cannot be mutated directly"""
        session = Session(id="test-session")
        with pytest.raises(Exception):  # ValidationError for frozen model
            session.id = "new-id"

    def test_with_message_returns_new_session(self) -> None:
        """Test that with_message returns a new session with the message"""
        session = Session(id="test-session")
        message = Message(role=MessageRole.USER, content="Hello")

        new_session = session.with_message(message)

        # Original unchanged
        assert len(session.messages) == 0
        # New session has message
        assert len(new_session.messages) == 1
        assert new_session.messages[0] == message
        # Same ID
        assert new_session.id == session.id

    def test_with_message_updates_timestamp(self) -> None:
        """Test that with_message updates the updated_at timestamp"""
        session = Session(id="test-session")
        original_updated = session.updated_at
        message = Message(role=MessageRole.USER, content="Hello")

        new_session = session.with_message(message)

        assert new_session.updated_at >= original_updated

    def test_get_conversation_history(self) -> None:
        """Test getting conversation history in format for LLM"""
        session = Session(id="test-session")
        session = session.with_message(Message(role=MessageRole.USER, content="Hello"))
        session = session.with_message(Message(role=MessageRole.ASSISTANT, content="Hi!"))

        history = session.get_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi!"

    def test_message_is_immutable(self) -> None:
        """Test that message cannot be mutated"""
        message = Message(role=MessageRole.USER, content="Hello")
        with pytest.raises(Exception):  # ValidationError for frozen model
            message.content = "World"
