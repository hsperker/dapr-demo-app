"""
Tools API router.

Provides endpoints for managing OpenAPI tools that extend agent capabilities.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.models import Tool, ToolStatus
from app.core.services import ToolService, AgentPluginManager
from app.dependencies import get_tool_service, get_plugin_manager


router = APIRouter(
    prefix="/tools",
    tags=["tools"]
)


class ToolCreateRequest(BaseModel):
    """Request model for creating a tool"""
    name: str
    openapi_url: str
    description: Optional[str] = None


class ToolResponse(BaseModel):
    """Response model for a tool"""
    id: str
    name: str
    openapi_url: str
    description: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: str

    @classmethod
    def from_tool(cls, tool: Tool) -> "ToolResponse":
        return cls(
            id=tool.id,
            name=tool.name,
            openapi_url=tool.openapi_url,
            description=tool.description,
            status=tool.status.value,
            error_message=tool.error_message,
            created_at=tool.created_at.isoformat()
        )


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def register_tool(
    request: ToolCreateRequest,
    tool_service: ToolService = Depends(get_tool_service)
) -> ToolResponse:
    """Register a new OpenAPI tool"""
    tool = await tool_service.register_tool(
        name=request.name,
        openapi_url=request.openapi_url,
        description=request.description
    )
    return ToolResponse.from_tool(tool)


@router.post("/{tool_id}/activate")
async def activate_tool(
    tool_id: str,
    tool_service: ToolService = Depends(get_tool_service),
    plugin_manager: AgentPluginManager = Depends(get_plugin_manager)
) -> dict:
    """Activate a tool by fetching and validating its OpenAPI spec"""
    tool = await tool_service.get_tool(tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found"
        )

    # Load plugin into agent
    result = plugin_manager.load_plugin(tool)

    if not result.success:
        await tool_service.update_status(tool_id, ToolStatus.ERROR, result.error_message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error_message or f"Failed to activate tool {tool_id}"
        )

    await tool_service.update_status(tool_id, ToolStatus.ACTIVE)
    return {"status": "activated"}


@router.get("", response_model=List[ToolResponse])
async def get_tools(
    tool_service: ToolService = Depends(get_tool_service)
) -> List[ToolResponse]:
    """Get all registered tools"""
    tools = await tool_service.get_all_tools()
    return [ToolResponse.from_tool(tool) for tool in tools]


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: str,
    tool_service: ToolService = Depends(get_tool_service)
) -> ToolResponse:
    """Get a specific tool by ID"""
    tool = await tool_service.get_tool(tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found"
        )
    return ToolResponse.from_tool(tool)


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_id: str,
    tool_service: ToolService = Depends(get_tool_service),
    plugin_manager: AgentPluginManager = Depends(get_plugin_manager)
) -> None:
    """Delete a tool and unload from agent if active"""
    tool = await tool_service.get_tool(tool_id)
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found"
        )

    # Unload plugin if it was active
    if tool.status == ToolStatus.ACTIVE:
        plugin_manager.unload_plugin(tool.name)

    result = await tool_service.delete_tool(tool_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool {tool_id} not found"
        )
