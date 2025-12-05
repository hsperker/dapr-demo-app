"""
Tests for core validation utilities.
"""

import pytest

from app.core.validation import validate_plugin_name, InvalidPluginNameError


class TestValidatePluginName:
    """Tests for plugin name validation"""

    def test_valid_lowercase_name(self) -> None:
        """Test that lowercase names are valid"""
        assert validate_plugin_name("petstore") is True

    def test_valid_uppercase_name(self) -> None:
        """Test that uppercase names are valid"""
        assert validate_plugin_name("PETSTORE") is True

    def test_valid_mixed_case_name(self) -> None:
        """Test that mixed case names are valid"""
        assert validate_plugin_name("PetStore") is True

    def test_valid_name_with_underscore(self) -> None:
        """Test that underscores are valid"""
        assert validate_plugin_name("pet_store") is True

    def test_valid_name_with_numbers(self) -> None:
        """Test that numbers are valid"""
        assert validate_plugin_name("api1") is True
        assert validate_plugin_name("v2_api") is True

    def test_invalid_name_with_hyphen(self) -> None:
        """Test that hyphens are invalid (SK requirement)"""
        assert validate_plugin_name("pet-store") is False

    def test_invalid_name_with_space(self) -> None:
        """Test that spaces are invalid"""
        assert validate_plugin_name("pet store") is False

    def test_invalid_name_with_dot(self) -> None:
        """Test that dots are invalid"""
        assert validate_plugin_name("pet.store") is False

    def test_invalid_name_with_special_chars(self) -> None:
        """Test that special characters are invalid"""
        assert validate_plugin_name("pet@store") is False
        assert validate_plugin_name("pet/store") is False
        assert validate_plugin_name("pet:store") is False

    def test_empty_name_is_invalid(self) -> None:
        """Test that empty string is invalid"""
        assert validate_plugin_name("") is False


class TestInvalidPluginNameError:
    """Tests for InvalidPluginNameError exception"""

    def test_error_contains_name(self) -> None:
        """Test that error message contains the invalid name"""
        error = InvalidPluginNameError("bad-name")
        assert "bad-name" in str(error)

    def test_error_contains_guidance(self) -> None:
        """Test that error message explains the rules"""
        error = InvalidPluginNameError("bad-name")
        assert "letters" in str(error)
        assert "numbers" in str(error)
        assert "underscores" in str(error)

    def test_error_stores_name(self) -> None:
        """Test that error stores the invalid name"""
        error = InvalidPluginNameError("bad-name")
        assert error.name == "bad-name"

    def test_error_is_value_error(self) -> None:
        """Test that error is a ValueError subclass"""
        error = InvalidPluginNameError("bad-name")
        assert isinstance(error, ValueError)
