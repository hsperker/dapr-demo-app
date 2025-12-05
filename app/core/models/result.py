"""
Result types for operation outcomes.

These replace bool/None returns with explicit success/failure types
that carry error information.
"""

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    """
    Result of an operation that can succeed or fail.

    Use this instead of returning bool or Optional values when
    you need to communicate error details.
    """
    success: bool
    value: Optional[T] = None
    error_message: Optional[str] = None

    @classmethod
    def ok(cls, value: Optional[T] = None) -> "Result[T]":
        """Create a successful result"""
        return cls(success=True, value=value)

    @classmethod
    def error(cls, message: str) -> "Result[T]":
        """Create a failed result"""
        return cls(success=False, error_message=message)


@dataclass(frozen=True)
class PluginLoadResult:
    """Result of loading an OpenAPI plugin"""
    success: bool
    error_message: Optional[str] = None

    @classmethod
    def ok(cls) -> "PluginLoadResult":
        """Create a successful result"""
        return cls(success=True)

    @classmethod
    def error(cls, message: str) -> "PluginLoadResult":
        """Create a failed result"""
        return cls(success=False, error_message=message)
