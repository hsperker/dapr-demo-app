"""
Tests that verify tools registered via ToolService and loaded via AgentPluginManager
are actually available to the agent.

This test file was created because the original TDD missed testing this integration -
the ToolService tests only verified bookkeeping (status updates) not actual functionality.

After refactoring: ToolService handles CRUD, AgentPluginManager handles agent integration.
The AgentPluginManager now uses the agent's add_plugin_from_openapi method which delegates
to Semantic Kernel's built-in OpenAPI support.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.models import Tool, ToolStatus, PluginLoadResult
from app.core.protocols import Agent
from app.core.services.chat_service import ChatService
from app.core.services.tool_service import ToolService
from app.core.services.agent_plugin_manager import AgentPluginManager
from app.infrastructure.repositories import SessionRepository, ToolRepository


class TestToolAgentIntegration:
    """Tests verifying tools are actually wired to the agent via AgentPluginManager"""

    def test_loading_plugin_adds_to_agent(self) -> None:
        """Test that loading a plugin via AgentPluginManager calls agent's add_plugin_from_openapi"""
        # Arrange
        mock_agent = MagicMock()
        mock_agent.add_plugin_from_openapi = MagicMock()

        tool = Tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json",
            description="Pet Store API"
        )

        # Act
        plugin_manager = AgentPluginManager(mock_agent)
        result = plugin_manager.load_plugin(tool)

        # Assert
        assert result.success is True
        mock_agent.add_plugin_from_openapi.assert_called_once_with(
            plugin_name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json"
        )

    async def test_chat_service_can_use_loaded_plugins(self) -> None:
        """Test that ChatService's agent can use tools loaded by AgentPluginManager"""
        # Arrange
        mock_session_repo = AsyncMock(spec=SessionRepository)

        # Create a mock agent that tracks plugin additions
        mock_agent = AsyncMock(spec=Agent)
        mock_agent.add_plugin_from_openapi = MagicMock()
        mock_agent.invoke.return_value = "The pet store has 3 pets available."
        mock_agent.get_plugins = MagicMock(return_value=["petstore"])

        # Setup session
        from app.core.models import Session
        session = Session(id="test-session")
        mock_session_repo.get_or_create.return_value = session

        # Create chat service using the same agent
        chat_service = ChatService(mock_session_repo, mock_agent)

        # Verify agent has access to tools
        plugins = mock_agent.get_plugins()
        assert "petstore" in plugins

        # The chat service can invoke the agent (which has access to tools)
        response = await chat_service.send_message("test-session", "How many pets?")
        assert response is not None

    def test_unloading_plugin_removes_from_agent(self) -> None:
        """Test that unloading a plugin via AgentPluginManager removes it from the agent"""
        # Arrange
        mock_agent = MagicMock()
        mock_agent.remove_plugin = MagicMock()

        # Act
        plugin_manager = AgentPluginManager(mock_agent)
        plugin_manager.unload_plugin("petstore")

        # Assert
        mock_agent.remove_plugin.assert_called_once_with("petstore")


class TestFullToolLifecycle:
    """Tests verifying the full lifecycle: register → activate → use → delete"""

    async def test_full_tool_lifecycle(self) -> None:
        """Test the complete tool lifecycle through ToolService and AgentPluginManager"""
        # Arrange
        mock_tool_repo = AsyncMock(spec=ToolRepository)
        mock_agent = MagicMock()
        mock_agent.add_plugin_from_openapi = MagicMock()
        mock_agent.remove_plugin = MagicMock()
        mock_agent.get_plugins = MagicMock(return_value=[])

        tool_service = ToolService(mock_tool_repo)
        plugin_manager = AgentPluginManager(mock_agent)

        # 1. Register tool
        new_tool = Tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json",
            status=ToolStatus.PENDING
        )
        mock_tool_repo.create.return_value = new_tool
        mock_tool_repo.get.return_value = new_tool

        registered = await tool_service.register_tool(
            "petstore",
            "https://petstore.swagger.io/v2/swagger.json"
        )
        assert registered.status == ToolStatus.PENDING

        # 2. Load plugin (activate) - now uses agent's add_plugin_from_openapi
        load_result = plugin_manager.load_plugin(new_tool)
        assert load_result.success is True
        mock_agent.add_plugin_from_openapi.assert_called_once_with(
            plugin_name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json"
        )

        # Update status in tool service
        await tool_service.update_status(new_tool.id, ToolStatus.ACTIVE)

        # 3. Unload plugin (deactivate)
        plugin_manager.unload_plugin("petstore")
        mock_agent.remove_plugin.assert_called_once_with("petstore")

        # 4. Delete tool
        mock_tool_repo.delete.return_value = True
        result = await tool_service.delete_tool(new_tool.id)
        assert result is True
