"""
Tests for AgentPluginManager - handles wiring OpenAPI tools to the agent.

This separates the concern of managing agent plugins from CRUD operations on tools.
"""

import pytest
from unittest.mock import MagicMock

from app.core.models import Tool
from app.core.services.agent_plugin_manager import AgentPluginManager
from app.core.validation import validate_plugin_name


class TestAgentPluginManager:
    """Tests for AgentPluginManager"""

    @pytest.fixture
    def mock_agent(self) -> MagicMock:
        """Create a mock agent"""
        agent = MagicMock()
        agent.add_plugin_from_openapi = MagicMock()
        agent.remove_plugin = MagicMock()
        agent.get_plugins = MagicMock(return_value=[])
        return agent

    @pytest.fixture
    def manager(self, mock_agent: MagicMock) -> AgentPluginManager:
        """Create AgentPluginManager with mock agent"""
        return AgentPluginManager(mock_agent)

    def test_load_plugin_calls_agent_add_plugin_from_openapi(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock
    ) -> None:
        """Test that loading a plugin calls agent's add_plugin_from_openapi"""
        tool = Tool(name="test_api", openapi_url="https://example.com/spec.json")

        result = manager.load_plugin(tool)

        assert result.success is True
        mock_agent.add_plugin_from_openapi.assert_called_once_with(
            plugin_name="test_api",
            openapi_url="https://example.com/spec.json"
        )

    def test_load_plugin_returns_error_on_exception(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock
    ) -> None:
        """Test that loading returns error when agent raises exception"""
        mock_agent.add_plugin_from_openapi.side_effect = Exception("Failed to load spec")

        tool = Tool(name="test_api", openapi_url="https://example.com/spec.json")

        result = manager.load_plugin(tool)

        assert result.success is False
        assert result.error_message is not None
        assert "Failed to load spec" in result.error_message

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

    def test_reload_plugin_unloads_then_loads(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock
    ) -> None:
        """Test that reloading unloads first, then loads again"""
        tool = Tool(name="test_api", openapi_url="https://example.com/spec.json")

        result = manager.reload_plugin(tool)

        assert result.success is True
        mock_agent.remove_plugin.assert_called_once_with("test_api")
        mock_agent.add_plugin_from_openapi.assert_called_once_with(
            plugin_name="test_api",
            openapi_url="https://example.com/spec.json"
        )

    def test_load_plugin_rejects_invalid_name_with_hyphen(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock
    ) -> None:
        """Test that plugin names with hyphens are rejected early"""
        tool = Tool(name="test-api", openapi_url="https://example.com/spec.json")

        result = manager.load_plugin(tool)

        assert result.success is False
        assert result.error_message is not None
        assert "Invalid plugin name" in result.error_message
        assert "letters, numbers, and underscores" in result.error_message
        # Should fail before calling agent
        mock_agent.add_plugin_from_openapi.assert_not_called()

    def test_load_plugin_rejects_invalid_name_with_spaces(
        self,
        manager: AgentPluginManager,
        mock_agent: MagicMock
    ) -> None:
        """Test that plugin names with spaces are rejected early"""
        tool = Tool(name="test api", openapi_url="https://example.com/spec.json")

        result = manager.load_plugin(tool)

        assert result.success is False
        assert "Invalid plugin name" in result.error_message  # type: ignore[operator]
        mock_agent.add_plugin_from_openapi.assert_not_called()


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
