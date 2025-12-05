import pytest
from typing import Generator
from unittest.mock import AsyncMock
from fastapi import Request
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_chat_service
from app.core.models import Message, MessageRole


@pytest.fixture
def mock_chat_service() -> AsyncMock:
    """Create a mock chat service"""
    service = AsyncMock()
    return service


@pytest.fixture
def client(mock_chat_service: AsyncMock) -> Generator[TestClient, None, None]:
    """Create a test client with mocked dependencies"""
    def override_chat_service(request: Request) -> AsyncMock:
        return mock_chat_service

    app.dependency_overrides[get_chat_service] = override_chat_service
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestChatRouter:
    """Test suite for chat API endpoints"""

    def test_send_message(self, client: TestClient, mock_chat_service: AsyncMock) -> None:
        """Test sending a message"""
        response_message = Message(
            role=MessageRole.ASSISTANT,
            content="Hello! How can I help you?"
        )
        mock_chat_service.send_message.return_value = response_message

        response = client.post(
            "/chat/test-session",
            json={"content": "Hello!"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello! How can I help you?"
        assert data["role"] == "assistant"

    def test_get_history(self, client: TestClient, mock_chat_service: AsyncMock) -> None:
        """Test getting conversation history"""
        messages = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there!")
        ]
        mock_chat_service.get_history.return_value = messages

        response = client.get("/chat/test-session/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["content"] == "Hello"
        assert data[1]["content"] == "Hi there!"

    def test_get_history_not_found(self, client: TestClient, mock_chat_service: AsyncMock) -> None:
        """Test getting history for non-existent session"""
        mock_chat_service.get_history.return_value = None

        response = client.get("/chat/nonexistent/history")

        assert response.status_code == 404

    def test_delete_session(self, client: TestClient, mock_chat_service: AsyncMock) -> None:
        """Test deleting a session"""
        mock_chat_service.delete_session.return_value = True

        response = client.delete("/chat/test-session")

        assert response.status_code == 204

    def test_delete_session_not_found(self, client: TestClient, mock_chat_service: AsyncMock) -> None:
        """Test deleting a non-existent session"""
        mock_chat_service.delete_session.return_value = False

        response = client.delete("/chat/nonexistent")

        assert response.status_code == 404
