"""
Tests for protocol definitions.

These tests verify that:
1. Protocols are properly defined
2. Expected implementations satisfy the protocols
3. Protocol contracts are complete
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

import httpx

from app.core.protocols import (
    Agent,
    SessionRepositoryProtocol,
    ToolRepositoryProtocol,
    HttpClient,
    HttpResponse,
)


class TestHttpResponseProtocol:
    """Tests for HttpResponse protocol"""

    def test_httpx_response_satisfies_protocol(self) -> None:
        """Test that httpx.Response satisfies HttpResponse protocol"""
        # Create a real httpx Response
        response = httpx.Response(
            status_code=200,
            content=b'{"key": "value"}',
            headers={"content-type": "application/json"}
        )

        # Verify it has the required attributes
        assert hasattr(response, "status_code")
        assert hasattr(response, "json")
        assert hasattr(response, "text")

        # Verify they work
        assert response.status_code == 200
        assert response.json() == {"key": "value"}
        assert isinstance(response.text, str)

    def test_mock_response_can_satisfy_protocol(self) -> None:
        """Test that a mock can satisfy HttpResponse protocol"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.text = "raw text"

        # Verify mock works like a response
        assert mock_response.status_code == 200
        assert mock_response.json() == {"data": "test"}
        assert mock_response.text == "raw text"


class TestHttpClientProtocol:
    """Tests for HttpClient protocol"""

    def test_protocol_requires_all_http_methods(self) -> None:
        """Test that HttpClient protocol defines all standard HTTP methods"""
        # Check that protocol has all required methods
        required_methods = ["get", "post", "put", "patch", "delete"]

        for method in required_methods:
            assert hasattr(HttpClient, method), f"HttpClient missing {method} method"

    def test_httpx_client_has_required_methods(self) -> None:
        """Test that httpx.AsyncClient has all required methods"""
        required_methods = ["get", "post", "put", "patch", "delete"]

        for method in required_methods:
            assert hasattr(httpx.AsyncClient, method), f"httpx.AsyncClient missing {method}"

    def test_mock_client_can_satisfy_protocol(self) -> None:
        """Test that a properly configured mock satisfies HttpClient"""
        mock_client = AsyncMock()

        # Should be able to call all methods
        assert callable(mock_client.get)
        assert callable(mock_client.post)
        assert callable(mock_client.put)
        assert callable(mock_client.patch)
        assert callable(mock_client.delete)


class TestAgentProtocol:
    """Tests for Agent protocol"""

    def test_protocol_requires_invoke(self) -> None:
        """Test that Agent protocol requires invoke method"""
        assert hasattr(Agent, "invoke")

    def test_protocol_requires_plugin_methods(self) -> None:
        """Test that Agent protocol requires plugin management methods"""
        assert hasattr(Agent, "add_plugin")
        assert hasattr(Agent, "remove_plugin")
        assert hasattr(Agent, "get_plugins")

    def test_semantic_kernel_agent_satisfies_protocol(self) -> None:
        """Test that our SemanticKernelAgent satisfies Agent protocol"""
        from app.core.services.agent import SemanticKernelAgent

        # Check required methods exist
        assert hasattr(SemanticKernelAgent, "invoke")
        assert hasattr(SemanticKernelAgent, "add_plugin")
        assert hasattr(SemanticKernelAgent, "remove_plugin")
        assert hasattr(SemanticKernelAgent, "get_plugins")


class TestRepositoryProtocols:
    """Tests for repository protocols"""

    def test_session_repository_satisfies_protocol(self) -> None:
        """Test that SessionRepository satisfies SessionRepositoryProtocol"""
        from app.infrastructure.repositories import SessionRepository

        required_methods = [
            "initialize", "close", "create", "get",
            "get_or_create", "add_message", "delete"
        ]

        for method in required_methods:
            assert hasattr(SessionRepository, method), f"Missing {method}"

    def test_tool_repository_satisfies_protocol(self) -> None:
        """Test that ToolRepository satisfies ToolRepositoryProtocol"""
        from app.infrastructure.repositories import ToolRepository

        required_methods = [
            "initialize", "close", "create", "get",
            "get_all", "get_active", "update_status", "delete"
        ]

        for method in required_methods:
            assert hasattr(ToolRepository, method), f"Missing {method}"
