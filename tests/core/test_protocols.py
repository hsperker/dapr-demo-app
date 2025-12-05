"""
Tests for protocol definitions.

These tests verify that:
1. Protocols are properly defined
2. Expected implementations satisfy the protocols
3. Protocol contracts are complete
"""

import pytest

from app.core.protocols import (
    Agent,
    SessionRepositoryProtocol,
    ToolRepositoryProtocol,
)


class TestAgentProtocol:
    """Tests for Agent protocol"""

    def test_protocol_requires_invoke(self) -> None:
        """Test that Agent protocol requires invoke method"""
        assert hasattr(Agent, "invoke")

    def test_protocol_requires_plugin_methods(self) -> None:
        """Test that Agent protocol requires plugin management methods"""
        assert hasattr(Agent, "add_plugin")
        assert hasattr(Agent, "add_plugin_from_openapi")
        assert hasattr(Agent, "remove_plugin")
        assert hasattr(Agent, "get_plugins")

    def test_semantic_kernel_agent_satisfies_protocol(self) -> None:
        """Test that our SemanticKernelAgent satisfies Agent protocol"""
        from app.core.services.agent import SemanticKernelAgent

        # Check required methods exist
        assert hasattr(SemanticKernelAgent, "invoke")
        assert hasattr(SemanticKernelAgent, "add_plugin")
        assert hasattr(SemanticKernelAgent, "add_plugin_from_openapi")
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
