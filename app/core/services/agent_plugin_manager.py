"""
Agent Plugin Manager - handles wiring OpenAPI tools to the Semantic Kernel agent.

This separates the concern of managing agent plugins from CRUD operations on tools.
"""

from typing import List

from app.core.models import Tool, PluginLoadResult
from app.core.protocols import Agent, HttpClient
from app.core.services.openapi_plugin import create_openapi_plugin
from app.core.validation import validate_plugin_name


class AgentPluginManager:
    """
    Manages loading and unloading OpenAPI plugins into the agent.

    This is responsible only for the agent integration, not for
    persisting tool metadata (that's ToolService's job).
    """

    def __init__(self, agent: Agent, http_client: HttpClient):
        self._agent = agent
        self._http_client = http_client

    async def load_plugin(self, tool: Tool) -> PluginLoadResult:
        """
        Load an OpenAPI plugin into the agent.

        Fetches the OpenAPI spec and registers it as a plugin with the agent.

        Args:
            tool: The tool containing the OpenAPI URL

        Returns:
            PluginLoadResult indicating success or failure
        """
        # Validate plugin name before attempting to load
        if not validate_plugin_name(tool.name):
            return PluginLoadResult.error(
                f"Invalid plugin name '{tool.name}': must contain only letters, numbers, and underscores"
            )

        try:
            response = await self._http_client.get(tool.openapi_url)

            if response.status_code != 200:
                return PluginLoadResult.error(
                    f"Failed to fetch OpenAPI spec: HTTP {response.status_code}"
                )

            spec = response.json()

            if not isinstance(spec, dict):
                return PluginLoadResult.error(
                    "Invalid OpenAPI spec: expected a JSON object"
                )

            plugin = create_openapi_plugin(tool.name, spec, self._http_client)
            self._agent.add_plugin(plugin, plugin_name=tool.name)

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

    async def reload_plugin(self, tool: Tool) -> PluginLoadResult:
        """
        Reload a plugin by unloading then loading it again.

        Useful when the OpenAPI spec has changed.

        Args:
            tool: The tool to reload

        Returns:
            PluginLoadResult indicating success or failure
        """
        self.unload_plugin(tool.name)
        return await self.load_plugin(tool)
