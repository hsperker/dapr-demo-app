"""
Semantic Kernel Agent implementation.

This module provides the concrete implementation of the Agent protocol
using Semantic Kernel's ChatCompletionAgent with OpenAI.
"""

import os
from typing import List, Dict, Any, Optional, Sequence

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatMessageContent, AuthorRole


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

    async def invoke(self, history: List[Dict[str, Any]], message: str) -> str:
        """
        Invoke the agent with conversation history and a new message.

        Args:
            history: List of previous messages as dicts with 'role' and 'content'
            message: The new user message

        Returns:
            The agent's response as a string (always a string, never wrapped)
        """
        self._ensure_initialized()
        assert self._agent is not None

        # Build messages list from conversation history
        messages_list: List[ChatMessageContent] = []

        # Map role strings to AuthorRole enum
        role_map = {
            "user": AuthorRole.USER,
            "assistant": AuthorRole.ASSISTANT,
            "system": AuthorRole.SYSTEM,
        }

        # Add previous messages
        for msg in history:
            role_str = msg.get("role", "user")
            content = msg.get("content", "")
            role = role_map.get(role_str, AuthorRole.USER)
            messages_list.append(ChatMessageContent(role=role, content=content))

        # Add the new user message
        messages_list.append(ChatMessageContent(role=AuthorRole.USER, content=message))

        # Get response from agent
        response = await self._agent.get_response(messages=list(messages_list))

        # Extract content from response - normalize to string
        if hasattr(response, 'content'):
            return str(response.content)
        return str(response)

    def add_plugin(self, plugin: Any, plugin_name: str) -> None:
        """Add a plugin to extend agent capabilities"""
        self._ensure_initialized()
        assert self._kernel is not None
        self._kernel.add_plugin(plugin, plugin_name)
        self._plugins[plugin_name] = plugin

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
