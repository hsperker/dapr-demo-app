"""
Tool service for CRUD operations on OpenAPI tools.

This service handles persistence of tool metadata only.
For loading tools into the agent, use AgentPluginManager.
"""

from typing import List, Optional

from app.core.models import Tool, ToolStatus
from app.core.protocols import ToolRepositoryProtocol
from app.core.validation import validate_plugin_name, InvalidPluginNameError


# Re-export for backwards compatibility with existing imports
InvalidToolNameError = InvalidPluginNameError


class ToolService:
    """
    Service for CRUD operations on OpenAPI tools.

    This is a pure persistence layer - it does not interact with the agent.
    Use AgentPluginManager to load/unload plugins into the agent.
    """

    def __init__(self, tool_repository: ToolRepositoryProtocol):
        self.tool_repository = tool_repository

    async def register_tool(
        self,
        name: str,
        openapi_url: str,
        description: Optional[str] = None
    ) -> Tool:
        """
        Register a new tool with pending status.

        Args:
            name: Tool name (must contain only letters, numbers, and underscores)
            openapi_url: URL to the OpenAPI specification
            description: Optional description

        Returns:
            The created Tool

        Raises:
            InvalidToolNameError: If name contains invalid characters
        """
        if not validate_plugin_name(name):
            raise InvalidToolNameError(name)

        tool = Tool(
            name=name,
            openapi_url=openapi_url,
            description=description,
            status=ToolStatus.PENDING
        )
        return await self.tool_repository.create(tool)

    async def get_tool(self, tool_id: str) -> Optional[Tool]:
        """Get a tool by ID"""
        return await self.tool_repository.get(tool_id)

    async def get_all_tools(self) -> List[Tool]:
        """Get all registered tools"""
        return await self.tool_repository.get_all()

    async def get_active_tools(self) -> List[Tool]:
        """Get only active tools"""
        return await self.tool_repository.get_active()

    async def delete_tool(self, tool_id: str) -> bool:
        """Delete a tool"""
        tool = await self.tool_repository.get(tool_id)
        if tool is None:
            return False
        return await self.tool_repository.delete(tool_id)

    async def update_status(
        self,
        tool_id: str,
        status: ToolStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """Update tool status"""
        tool = await self.tool_repository.get(tool_id)
        if tool is None:
            return False
        await self.tool_repository.update_status(tool_id, status, error_message)
        return True
