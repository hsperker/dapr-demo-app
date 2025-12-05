"""
Agent Plugin Manager - handles wiring OpenAPI tools to the Semantic Kernel agent.

This separates the concern of managing agent plugins from CRUD operations on tools.
"""

from typing import List

from app.core.models import Tool, PluginLoadResult
from app.core.protocols import Agent
from app.core.validation import validate_plugin_name


class AgentPluginManager:
    """
    Manages loading and unloading OpenAPI plugins into the agent.

    This is responsible only for the agent integration, not for
    persisting tool metadata (that's ToolService's job).

    Uses Semantic Kernel's built-in OpenAPI support for plugin creation.
    """

    def __init__(self, agent: Agent):
        self._agent = agent

    def load_plugin(self, tool: Tool) -> PluginLoadResult:
        """
        Load an OpenAPI plugin into the agent.

        Uses SK's add_plugin_from_openapi which handles fetching the spec,
        parsing operations, and creating callable functions.

        Args:
            tool: The tool containing the OpenAPI URL

        Returns:
            PluginLoadResult indicating success or failure
        """
        if not validate_plugin_name(tool.name):
            return PluginLoadResult.error(
                f"Invalid plugin name '{tool.name}': must contain only letters, numbers, and underscores"
            )

        try:
            self._agent.add_plugin_from_openapi(
                plugin_name=tool.name,
                openapi_url=tool.openapi_url
            )
            return PluginLoadResult.ok()

        except Exception as e:
            return PluginLoadResult.error(str(e))

    def unload_plugin(self, plugin_name: str) -> None:
        """
        Remove a plugin from the agent.

        Args:
            plugin_name: The name of the plugin to remove
        """
        self._agent.remove_plugin(plugin_name)

    def get_loaded_plugins(self) -> List[str]:
        """
        Get list of currently loaded plugin names.

        Returns:
            List of plugin names currently registered with the agent
        """
        return self._agent.get_plugins()

    def reload_plugin(self, tool: Tool) -> PluginLoadResult:
        """
        Reload a plugin by unloading then loading it again.

        Useful when the OpenAPI spec has changed.

        Args:
            tool: The tool to reload

        Returns:
            PluginLoadResult indicating success or failure
        """
        self.unload_plugin(tool.name)
        return self.load_plugin(tool)
