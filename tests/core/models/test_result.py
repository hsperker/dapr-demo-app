"""
Tests for Result types.

These tests verify the Result and PluginLoadResult types work correctly.
"""

import pytest

from app.core.models.result import Result, PluginLoadResult


class TestResult:
    """Tests for the generic Result type"""

    def test_ok_creates_successful_result(self) -> None:
        """Test Result.ok() creates a successful result"""
        result = Result.ok("value")

        assert result.success is True
        assert result.value == "value"
        assert result.error_message is None

    def test_ok_without_value(self) -> None:
        """Test Result.ok() without a value"""
        result: Result[None] = Result.ok()

        assert result.success is True
        assert result.value is None
        assert result.error_message is None

    def test_error_creates_failed_result(self) -> None:
        """Test Result.error() creates a failed result"""
        result: Result[str] = Result.error("Something went wrong")

        assert result.success is False
        assert result.value is None
        assert result.error_message == "Something went wrong"

    def test_result_is_immutable(self) -> None:
        """Test that Result is immutable (frozen dataclass)"""
        result = Result.ok("value")

        with pytest.raises(Exception):  # FrozenInstanceError
            result.success = False  # type: ignore[misc]


class TestPluginLoadResult:
    """Tests for PluginLoadResult"""

    def test_ok_creates_successful_result(self) -> None:
        """Test PluginLoadResult.ok() creates a successful result"""
        result = PluginLoadResult.ok()

        assert result.success is True
        assert result.error_message is None

    def test_error_creates_failed_result(self) -> None:
        """Test PluginLoadResult.error() creates a failed result"""
        result = PluginLoadResult.error("Failed to load plugin")

        assert result.success is False
        assert result.error_message == "Failed to load plugin"

    def test_plugin_load_result_is_immutable(self) -> None:
        """Test that PluginLoadResult is immutable"""
        result = PluginLoadResult.ok()

        with pytest.raises(Exception):  # FrozenInstanceError
            result.success = False  # type: ignore[misc]

    def test_error_message_preserved(self) -> None:
        """Test that error messages are preserved through the chain"""
        # Simulate what happens in AgentPluginManager
        error_msg = "HTTP 404: Not Found"
        result = PluginLoadResult.error(error_msg)

        assert result.error_message is not None
        assert error_msg in result.error_message
