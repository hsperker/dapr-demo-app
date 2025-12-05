"""
Protocol definitions for the application.

These protocols define the contracts between layers, enabling:
1. Clean dependency injection
2. Easy mocking in tests
3. Swappable implementations (e.g., different databases)
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from app.core.models import Message, Session, Tool, ToolStatus


# =============================================================================
# Agent Protocol
# =============================================================================

@runtime_checkable
class Agent(Protocol):
    """Protocol for LLM agent implementations"""

    async def invoke(self, history: List[Dict[str, Any]], message: str) -> str:
        """
        Invoke the agent with conversation history and a new message.

        Args:
            history: List of previous messages as dicts with 'role' and 'content'
            message: The new user message

        Returns:
            The agent's response as a string
        """
        ...

    def add_plugin(self, plugin: Any, plugin_name: str) -> None:
        """Add a plugin to extend agent capabilities"""
        ...

    def remove_plugin(self, plugin_name: str) -> None:
        """Remove a plugin from the agent"""
        ...

    def get_plugins(self) -> List[str]:
        """Get list of registered plugin names"""
        ...


# =============================================================================
# Repository Protocols
# =============================================================================

@runtime_checkable
class SessionRepositoryProtocol(Protocol):
    """Protocol for session repository implementations"""

    async def initialize(self) -> None:
        """Initialize the repository (create tables, etc.)"""
        ...

    async def close(self) -> None:
        """Close any connections"""
        ...

    async def create(self, session_id: str) -> Session:
        """Create a new session"""
        ...

    async def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        ...

    async def get_or_create(self, session_id: str) -> Session:
        """Get an existing session or create a new one"""
        ...

    async def add_message(self, session_id: str, message: Message) -> None:
        """Add a message to a session"""
        ...

    async def delete(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        ...


@runtime_checkable
class ToolRepositoryProtocol(Protocol):
    """Protocol for tool repository implementations"""

    async def initialize(self) -> None:
        """Initialize the repository"""
        ...

    async def close(self) -> None:
        """Close any connections"""
        ...

    async def create(self, tool: Tool) -> Tool:
        """Create a new tool"""
        ...

    async def get(self, tool_id: str) -> Optional[Tool]:
        """Get a tool by ID"""
        ...

    async def get_all(self) -> List[Tool]:
        """Get all tools"""
        ...

    async def get_active(self) -> List[Tool]:
        """Get all active tools"""
        ...

    async def update_status(
        self,
        tool_id: str,
        status: ToolStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update a tool's status"""
        ...

    async def delete(self, tool_id: str) -> bool:
        """Delete a tool"""
        ...


# =============================================================================
# HTTP Client Protocol
# =============================================================================

@runtime_checkable
class HttpResponse(Protocol):
    """Protocol for HTTP response objects"""

    @property
    def status_code(self) -> int:
        """HTTP status code"""
        ...

    def json(self) -> Any:
        """Parse response body as JSON"""
        ...

    @property
    def text(self) -> str:
        """Response body as text"""
        ...


@runtime_checkable
class HttpClient(Protocol):
    """
    Protocol for HTTP client implementations.

    All methods return an HttpResponse object that provides
    status_code, json(), and text properties.

    Note: Uses Any for url to be compatible with httpx.AsyncClient
    which accepts both str and URL objects.
    """

    async def get(self, url: Any, **kwargs: Any) -> Any:
        """Make a GET request"""
        ...

    async def post(self, url: Any, **kwargs: Any) -> Any:
        """Make a POST request"""
        ...

    async def put(self, url: Any, **kwargs: Any) -> Any:
        """Make a PUT request"""
        ...

    async def patch(self, url: Any, **kwargs: Any) -> Any:
        """Make a PATCH request"""
        ...

    async def delete(self, url: Any, **kwargs: Any) -> Any:
        """Make a DELETE request"""
        ...
