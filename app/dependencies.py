"""
Dependency injection for the application using FastAPI's state pattern.

Dependencies are stored in app.state during lifespan and accessed via Request.
This avoids global singletons and makes testing easier.
"""

from typing import TYPE_CHECKING

from fastapi import Request

if TYPE_CHECKING:
    from app.core.services import ChatService, ToolService, AgentPluginManager
    from app.core.protocols import Agent


def get_chat_service(request: Request) -> "ChatService":
    """Get ChatService from app state"""
    return request.app.state.chat_service


def get_tool_service(request: Request) -> "ToolService":
    """Get ToolService from app state"""
    return request.app.state.tool_service


def get_plugin_manager(request: Request) -> "AgentPluginManager":
    """Get AgentPluginManager from app state"""
    return request.app.state.plugin_manager


def get_agent(request: Request) -> "Agent":
    """Get Agent from app state"""
    return request.app.state.agent
