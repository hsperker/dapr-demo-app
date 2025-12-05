"""
Tests for SemanticKernelAgent.

These tests verify the agent wrapper works correctly with mocked Semantic Kernel.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSemanticKernelAgent:
    """Tests for the SemanticKernelAgent wrapper"""

    def test_requires_api_key(self) -> None:
        """Test that agent requires an API key"""
        from app.core.services.agent import SemanticKernelAgent

        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                SemanticKernelAgent(api_key=None)

    def test_accepts_explicit_api_key(self) -> None:
        """Test that agent accepts explicit API key"""
        from app.core.services.agent import SemanticKernelAgent

        # Should not raise
        agent = SemanticKernelAgent(api_key="test-key")
        assert agent.api_key == "test-key"

    def test_uses_env_api_key(self) -> None:
        """Test that agent uses OPENAI_API_KEY from environment"""
        from app.core.services.agent import SemanticKernelAgent

        with patch.dict('os.environ', {'OPENAI_API_KEY': 'env-key'}):
            agent = SemanticKernelAgent()
            assert agent.api_key == "env-key"

    def test_add_plugin_tracks_plugin(self) -> None:
        """Test that add_plugin registers the plugin in internal tracking"""
        from app.core.services.agent import SemanticKernelAgent
        from app.core.services.openapi_plugin import OpenApiPlugin

        agent = SemanticKernelAgent(api_key="test-key")

        # Use a real OpenApiPlugin since SK validates plugin structure
        spec = {"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}, "paths": {}}
        plugin = OpenApiPlugin("test_plugin", spec)
        agent.add_plugin(plugin, "test_plugin")

        assert "test_plugin" in agent.get_plugins()

    def test_remove_plugin_untracks_plugin(self) -> None:
        """Test that remove_plugin removes from tracking"""
        from app.core.services.agent import SemanticKernelAgent
        from app.core.services.openapi_plugin import OpenApiPlugin

        agent = SemanticKernelAgent(api_key="test-key")

        spec = {"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}, "paths": {}}
        plugin = OpenApiPlugin("test_plugin", spec)
        agent.add_plugin(plugin, "test_plugin")
        assert "test_plugin" in agent.get_plugins()

        agent.remove_plugin("test_plugin")
        assert "test_plugin" not in agent.get_plugins()

    def test_get_plugins_returns_empty_initially(self) -> None:
        """Test that get_plugins returns empty list initially"""
        from app.core.services.agent import SemanticKernelAgent

        agent = SemanticKernelAgent(api_key="test-key")
        assert agent.get_plugins() == []

    @pytest.mark.asyncio
    async def test_invoke_returns_string(self) -> None:
        """Test that invoke always returns a string"""
        from app.core.services.agent import SemanticKernelAgent

        agent = SemanticKernelAgent(api_key="test-key")

        # Mock the internal agent
        mock_response = MagicMock()
        mock_response.content = "Hello, world!"

        mock_sk_agent = AsyncMock()
        mock_sk_agent.get_response.return_value = mock_response

        agent._agent = mock_sk_agent
        agent._kernel = MagicMock()

        result = await agent.invoke([], "Hi")

        assert isinstance(result, str)
        assert result == "Hello, world!"

    @pytest.mark.asyncio
    async def test_invoke_passes_history(self) -> None:
        """Test that invoke passes conversation history to agent"""
        from app.core.services.agent import SemanticKernelAgent

        agent = SemanticKernelAgent(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = "Response"

        mock_sk_agent = AsyncMock()
        mock_sk_agent.get_response.return_value = mock_response

        agent._agent = mock_sk_agent
        agent._kernel = MagicMock()

        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        await agent.invoke(history, "How are you?")

        # Verify get_response was called
        mock_sk_agent.get_response.assert_called_once()

        # The ChatHistory should contain all messages
        call_args = mock_sk_agent.get_response.call_args
        chat_history = call_args[0][0]
        # History should have: 2 from history + 1 new message = 3 messages
        assert len(chat_history.messages) == 3


class TestAgentPluginIntegration:
    """Tests verifying plugins actually work with the agent"""

    def test_plugin_added_to_kernel_plugins(self) -> None:
        """Test that plugins are actually added to the kernel's plugin registry"""
        from app.core.services.agent import SemanticKernelAgent
        from app.core.services.openapi_plugin import OpenApiPlugin

        agent = SemanticKernelAgent(api_key="test-key")

        spec = {"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}, "paths": {}}
        plugin = OpenApiPlugin("test_plugin", spec)
        agent.add_plugin(plugin, "test_plugin")

        # Verify the kernel actually has the plugin
        assert agent._kernel is not None
        assert "test_plugin" in agent._kernel.plugins

    def test_plugin_removed_from_kernel_plugins(self) -> None:
        """Test that remove_plugin actually removes from the kernel, not just tracking"""
        from app.core.services.agent import SemanticKernelAgent
        from app.core.services.openapi_plugin import OpenApiPlugin

        agent = SemanticKernelAgent(api_key="test-key")

        spec = {"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}, "paths": {}}
        plugin = OpenApiPlugin("test_plugin", spec)
        agent.add_plugin(plugin, "test_plugin")

        # Verify plugin is in kernel
        assert "test_plugin" in agent._kernel.plugins

        # Remove it
        agent.remove_plugin("test_plugin")

        # Must be removed from KERNEL too, not just internal tracking
        assert "test_plugin" not in agent._kernel.plugins
