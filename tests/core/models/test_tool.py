import pytest
from pydantic import ValidationError

from app.core.models.tool import Tool, ToolStatus


class TestTool:
    """Test suite for the Tool model"""

    def test_create_tool(self) -> None:
        """Test creating a tool from OpenAPI spec URL"""
        tool = Tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json",
            description="Pet Store API"
        )
        assert tool.name == "petstore"
        assert tool.openapi_url == "https://petstore.swagger.io/v2/swagger.json"
        assert tool.description == "Pet Store API"
        assert tool.id is not None
        assert tool.status == ToolStatus.PENDING

    def test_tool_requires_name(self) -> None:
        """Test that tool requires a name"""
        with pytest.raises(ValidationError):
            Tool(
                name="",
                openapi_url="https://example.com/spec.json"
            )

    def test_tool_requires_valid_url(self) -> None:
        """Test that tool requires a valid URL"""
        with pytest.raises(ValidationError):
            Tool(
                name="test",
                openapi_url="not-a-valid-url"
            )

    def test_tool_auto_generates_id(self) -> None:
        """Test that tool auto-generates unique IDs"""
        tool1 = Tool(name="api1", openapi_url="https://example.com/spec1.json")
        tool2 = Tool(name="api2", openapi_url="https://example.com/spec2.json")
        assert tool1.id != tool2.id

    def test_tool_status_transitions(self) -> None:
        """Test tool status transitions"""
        tool = Tool(name="test", openapi_url="https://example.com/spec.json")
        assert tool.status == ToolStatus.PENDING

        tool.status = ToolStatus.ACTIVE
        assert tool.status == ToolStatus.ACTIVE

        tool.status = ToolStatus.ERROR
        assert tool.status == ToolStatus.ERROR

    def test_tool_with_optional_description(self) -> None:
        """Test tool without description"""
        tool = Tool(
            name="test",
            openapi_url="https://example.com/spec.json"
        )
        assert tool.description is None

    def test_tool_stores_error_message(self) -> None:
        """Test that tool can store error messages"""
        tool = Tool(
            name="test",
            openapi_url="https://example.com/spec.json",
            status=ToolStatus.ERROR,
            error_message="Failed to fetch OpenAPI spec"
        )
        assert tool.error_message == "Failed to fetch OpenAPI spec"
