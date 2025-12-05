"""
Validation utilities for the core domain.

These validators enforce business rules that apply across multiple services.
"""

import re

# Semantic Kernel requires plugin/tool names to match this pattern
# Only letters, numbers, and underscores - no hyphens or special characters
PLUGIN_NAME_PATTERN = re.compile(r'^[0-9A-Za-z_]+$')


def validate_plugin_name(name: str) -> bool:
    """
    Validate that a name is acceptable for Semantic Kernel plugins.

    Semantic Kernel requires plugin names to contain only letters,
    numbers, and underscores. Hyphens and other special characters
    will cause cryptic Pydantic validation errors.

    Args:
        name: The plugin/tool name to validate

    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False
    return bool(PLUGIN_NAME_PATTERN.match(name))


class InvalidPluginNameError(ValueError):
    """Raised when a plugin/tool name doesn't meet Semantic Kernel requirements"""

    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"Invalid name '{name}': must contain only letters, numbers, and underscores"
        )
