"""
Tests for AgentPluginManager - handles wiring OpenAPI tools to the agent.

This separates the concern of managing agent plugins from CRUD operations on tools.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.models import Tool, ToolStatus
from app.core.services.agent_plugin_manager import AgentPluginManager
from app.core.validation import validate_plugin_name


class TestAgentPluginManager:
    """Tests for AgentPluginManager"""

    @pytest.fixture
    def mock_agent(self) -> MagicMock:
        """Create a mock agent"""
        agent = MagicMock()
        agent.add_plugin = MagicMock()
        agent.remove_plugin = MagicMock()
        agent.get_plugins = MagicMock(return_value=[])
        return agent

    @pytest.fixture
    def mock_http_client(self) -> AsyncMock:
        """Create a mock HTTP client"""
        client = AsyncMock()
        return client

    @pytest.fixture
    def manager(self, mock_agent: MagicMock, mock_http_client: AsyncMock) -> AgentPluginManager:
        """Create AgentPluginManager with mocks"""
        return AgentPluginManager(mock_agent, mock_http_client)

    @pytest.mark.asyncio
    async def test_load_plugin_fetches_spec_and_registers(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test that loading a plugin fetches the spec and registers with agent"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/items": {
                    "get": {"operationId": "listItems", "summary": "List items"}
                }
            }
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = spec
        mock_http_client.get.return_value = mock_response

        tool = Tool(name="test_api", openapi_url="https://example.com/spec.json")

        result = await manager.load_plugin(tool)

        assert result.success is True
        mock_http_client.get.assert_called_once_with("https://example.com/spec.json")
        mock_agent.add_plugin.assert_called_once()
        # Verify plugin was added with correct name
        call_args = mock_agent.add_plugin.call_args
        assert call_args[1]["plugin_name"] == "test_api"

    @pytest.mark.asyncio
    async def test_load_plugin_returns_error_on_http_failure(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test that loading returns error when HTTP request fails"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_http_client.get.return_value = mock_response

        tool = Tool(name="test_api", openapi_url="https://example.com/not-found.json")

        result = await manager.load_plugin(tool)

        assert result.success is False
        assert result.error_message is not None
        assert "404" in result.error_message
        mock_agent.add_plugin.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_plugin_returns_error_on_invalid_spec(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test that loading returns error for invalid OpenAPI spec"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = "not a dict"
        mock_http_client.get.return_value = mock_response

        tool = Tool(name="test_api", openapi_url="https://example.com/invalid.json")

        result = await manager.load_plugin(tool)

        assert result.success is False
        assert result.error_message is not None
        assert "invalid" in result.error_message.lower()
        mock_agent.add_plugin.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_plugin_returns_error_on_network_exception(
        self,
        manager: AgentPluginManager,
        mock_http_client: AsyncMock
    ) -> None:
        """Test that loading returns error when network fails"""
        mock_http_client.get.side_effect = Exception("Connection refused")

        tool = Tool(name="test_api", openapi_url="https://example.com/spec.json")

        result = await manager.load_plugin(tool)

        assert result.success is False
        assert result.error_message is not None
        assert "Connection refused" in result.error_message

    def test_unload_plugin_removes_from_agent(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock
    ) -> None:
        """Test that unloading removes the plugin from agent"""
        manager.unload_plugin("test_api")

        mock_agent.remove_plugin.assert_called_once_with("test_api")

    def test_get_loaded_plugins_returns_agent_plugins(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock
    ) -> None:
        """Test that get_loaded_plugins returns list from agent"""
        mock_agent.get_plugins.return_value = ["api1", "api2"]

        plugins = manager.get_loaded_plugins()

        assert plugins == ["api1", "api2"]
        mock_agent.get_plugins.assert_called_once()

    @pytest.mark.asyncio
    async def test_reload_plugin_unloads_then_loads(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test that reloading unloads first, then loads again"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = spec
        mock_http_client.get.return_value = mock_response

        tool = Tool(name="test_api", openapi_url="https://example.com/spec.json")

        result = await manager.reload_plugin(tool)

        assert result.success is True
        mock_agent.remove_plugin.assert_called_once_with("test_api")
        mock_agent.add_plugin.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_plugin_rejects_invalid_name_with_hyphen(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test that plugin names with hyphens are rejected early"""
        tool = Tool(name="test-api", openapi_url="https://example.com/spec.json")

        result = await manager.load_plugin(tool)

        assert result.success is False
        assert result.error_message is not None
        assert "Invalid plugin name" in result.error_message
        assert "letters, numbers, and underscores" in result.error_message
        # Should fail before making HTTP request
        mock_http_client.get.assert_not_called()
        mock_agent.add_plugin.assert_not_called()


class TestPluginNameValidation:
    """Tests for plugin name validation"""

    def test_valid_names(self) -> None:
        """Test that valid plugin names pass validation"""
        valid_names = ["petstore", "pet_store", "PetStore", "api1", "API_v2", "test123"]
        for name in valid_names:
            assert validate_plugin_name(name) is True, f"{name} should be valid"

    def test_invalid_names_with_hyphens(self) -> None:
        """Test that names with hyphens fail validation"""
        invalid_names = ["pet-store", "my-api", "test-api-v2"]
        for name in invalid_names:
            assert validate_plugin_name(name) is False, f"{name} should be invalid"

    def test_invalid_names_with_special_chars(self) -> None:
        """Test that names with special characters fail validation"""
        invalid_names = ["pet.store", "my api", "test@api", "api/v2"]
        for name in invalid_names:
            assert validate_plugin_name(name) is False, f"{name} should be invalid"

    def test_empty_name_is_invalid(self) -> None:
        """Test that empty name fails validation"""
        assert validate_plugin_name("") is False
