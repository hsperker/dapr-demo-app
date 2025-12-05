"""
Semantic Kernel Agent implementation.

This module provides the concrete implementation of the Agent protocol
using Semantic Kernel's ChatCompletionAgent with OpenAI.
"""

import os
from typing import Any, Dict, List, Optional, Union, cast

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent

from app.core.models import MessageRole, Session


class SemanticKernelAgent:
    """
    Wrapper around Semantic Kernel ChatCompletionAgent.

    Implements the Agent protocol defined in app.core.protocols.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        instructions: str = "You are a helpful AI assistant."
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")

        self.model = model
        self.instructions = instructions
        self._kernel: Optional[Kernel] = None
        self._agent: Optional[ChatCompletionAgent] = None
        self._plugins: Dict[str, Any] = {}

    def _ensure_initialized(self) -> None:
        """Lazily initialize the kernel and agent"""
        if self._kernel is None:
            self._kernel = Kernel()
            service = OpenAIChatCompletion(
                ai_model_id=self.model,
                api_key=self.api_key
            )
            self._kernel.add_service(service)

        if self._agent is None:
            self._agent = ChatCompletionAgent(
                kernel=self._kernel,
                name="ChatAgent",
                instructions=self.instructions
            )

    async def invoke(self, session: Session, message: str) -> str:
        """
        Invoke the agent with conversation history and a new message.

        Args:
            session: The session containing conversation history
            message: The new user message

        Returns:
            The agent's response as a string
        """
        self._ensure_initialized()
        assert self._agent is not None

        # Map MessageRole to SK's AuthorRole
        role_map = {
            MessageRole.USER: AuthorRole.USER,
            MessageRole.ASSISTANT: AuthorRole.ASSISTANT,
            MessageRole.SYSTEM: AuthorRole.SYSTEM,
        }

        # Build messages list from session history
        messages_list: List[ChatMessageContent] = [
            ChatMessageContent(
                role=role_map.get(msg.role, AuthorRole.USER),
                content=msg.content
            )
            for msg in session.messages
        ]

        # Add the new user message
        messages_list.append(ChatMessageContent(role=AuthorRole.USER, content=message))

        # Get response from agent
        response = await self._agent.get_response(
            messages=cast(List[Union[str, ChatMessageContent]], messages_list)
        )

        # Extract content from response
        if hasattr(response, 'content'):
            return str(response.content)
        return str(response)

    def add_plugin(self, plugin: Any, plugin_name: str) -> None:
        """Add a plugin to extend agent capabilities"""
        self._ensure_initialized()
        assert self._kernel is not None
        self._kernel.add_plugin(plugin, plugin_name)
        self._plugins[plugin_name] = plugin

    def add_plugin_from_openapi(
        self,
        plugin_name: str,
        openapi_url: str
    ) -> None:
        """
        Add a plugin from an OpenAPI specification URL.

        Uses Semantic Kernel's built-in OpenAPI support which handles:
        - Fetching and parsing the OpenAPI spec
        - Creating callable functions for each operation
        - Parameter mapping and payload construction
        - HTTP request execution

        Args:
            plugin_name: Name for the plugin
            openapi_url: URL to the OpenAPI specification
        """
        self._ensure_initialized()
        assert self._kernel is not None

        self._kernel.add_plugin_from_openapi(
            plugin_name=plugin_name,
            openapi_document_path=openapi_url
        )
        self._plugins[plugin_name] = True  # Track that plugin is loaded

    def remove_plugin(self, plugin_name: str) -> None:
        """Remove a plugin from the agent"""
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
            # Also remove from the kernel's plugin registry
            if self._kernel is not None and plugin_name in self._kernel.plugins:
                del self._kernel.plugins[plugin_name]

    def get_plugins(self) -> List[str]:
        """Get list of registered plugin names"""
        return list(self._plugins.keys())
