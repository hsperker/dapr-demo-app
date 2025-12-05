import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator

from app.core.models import Tool, ToolStatus
from app.core.services.tool_service import ToolService, InvalidToolNameError
from app.infrastructure.repositories import ToolRepository


@pytest.fixture
def mock_tool_repository() -> AsyncMock:
    """Create a mock tool repository"""
    repo = AsyncMock(spec=ToolRepository)
    return repo


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """Create a mock HTTP client"""
    client = AsyncMock()
    return client


class TestToolService:
    """Test suite for ToolService - CRUD operations only"""

    async def test_register_tool_creates_pending_tool(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test that registering a tool creates it with pending status"""
        mock_tool_repository.create.return_value = Tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json",
            description="Pet Store API"
        )

        service = ToolService(mock_tool_repository, mock_http_client)
        tool = await service.register_tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json",
            description="Pet Store API"
        )

        assert tool.name == "petstore"
        assert tool.status == ToolStatus.PENDING
        mock_tool_repository.create.assert_called_once()

    async def test_update_status(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test updating tool status"""
        tool = Tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json"
        )
        mock_tool_repository.get.return_value = tool

        service = ToolService(mock_tool_repository, mock_http_client)
        result = await service.update_status(tool.id, ToolStatus.ACTIVE)

        assert result is True
        mock_tool_repository.update_status.assert_called_once_with(
            tool.id, ToolStatus.ACTIVE, None
        )

    async def test_update_status_with_error_message(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test updating tool status with error message"""
        tool = Tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json"
        )
        mock_tool_repository.get.return_value = tool

        service = ToolService(mock_tool_repository, mock_http_client)
        result = await service.update_status(tool.id, ToolStatus.ERROR, "Failed to fetch")

        assert result is True
        mock_tool_repository.update_status.assert_called_once_with(
            tool.id, ToolStatus.ERROR, "Failed to fetch"
        )

    async def test_update_status_nonexistent_tool(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test updating status of non-existent tool"""
        mock_tool_repository.get.return_value = None

        service = ToolService(mock_tool_repository, mock_http_client)
        result = await service.update_status("nonexistent", ToolStatus.ACTIVE)

        assert result is False

    async def test_get_tool(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test getting a tool by ID"""
        tool = Tool(name="test", openapi_url="https://example.com/spec.json")
        mock_tool_repository.get.return_value = tool

        service = ToolService(mock_tool_repository, mock_http_client)
        result = await service.get_tool(tool.id)

        assert result == tool

    async def test_get_all_tools(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test getting all tools"""
        tools = [
            Tool(name="api1", openapi_url="https://example.com/spec1.json"),
            Tool(name="api2", openapi_url="https://example.com/spec2.json")
        ]
        mock_tool_repository.get_all.return_value = tools

        service = ToolService(mock_tool_repository, mock_http_client)
        result = await service.get_all_tools()

        assert len(result) == 2

    async def test_get_active_tools(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test getting only active tools"""
        tools = [
            Tool(name="active", openapi_url="https://example.com/spec.json", status=ToolStatus.ACTIVE)
        ]
        mock_tool_repository.get_active.return_value = tools

        service = ToolService(mock_tool_repository, mock_http_client)
        result = await service.get_active_tools()

        assert len(result) == 1
        assert result[0].status == ToolStatus.ACTIVE

    async def test_delete_tool(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test deleting a tool"""
        tool = Tool(name="test", openapi_url="https://example.com/spec.json")
        mock_tool_repository.get.return_value = tool
        mock_tool_repository.delete.return_value = True

        service = ToolService(mock_tool_repository, mock_http_client)
        result = await service.delete_tool(tool.id)

        assert result is True
        mock_tool_repository.delete.assert_called_once_with(tool.id)

    async def test_delete_nonexistent_tool(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test deleting a non-existent tool"""
        mock_tool_repository.get.return_value = None

        service = ToolService(mock_tool_repository, mock_http_client)
        result = await service.delete_tool("nonexistent")

        assert result is False
        mock_tool_repository.delete.assert_not_called()

    async def test_get_openapi_spec(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test fetching OpenAPI spec for a tool"""
        tool = Tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json",
            status=ToolStatus.ACTIVE
        )
        mock_tool_repository.get.return_value = tool

        spec = {"openapi": "3.0.0", "info": {"title": "Pet Store"}}
        # Use MagicMock for response since json() is sync in httpx
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = spec
        mock_http_client.get.return_value = mock_response

        service = ToolService(mock_tool_repository, mock_http_client)
        result = await service.get_openapi_spec(tool.id)

        assert result == spec


class TestToolNameValidation:
    """Tests for validating tool names at registration time"""

    async def test_register_rejects_name_with_hyphens(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test that names with hyphens are rejected at registration"""
        service = ToolService(mock_tool_repository, mock_http_client)

        with pytest.raises(InvalidToolNameError) as exc_info:
            await service.register_tool(
                name="pet-store",
                openapi_url="https://example.com/spec.json"
            )

        assert "pet-store" in str(exc_info.value)
        assert "letters, numbers, and underscores" in str(exc_info.value)
        mock_tool_repository.create.assert_not_called()

    async def test_register_rejects_name_with_spaces(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test that names with spaces are rejected at registration"""
        service = ToolService(mock_tool_repository, mock_http_client)

        with pytest.raises(InvalidToolNameError):
            await service.register_tool(
                name="pet store",
                openapi_url="https://example.com/spec.json"
            )

        mock_tool_repository.create.assert_not_called()

    async def test_register_accepts_valid_names(
        self,
        mock_tool_repository: AsyncMock,
        mock_http_client: AsyncMock
    ) -> None:
        """Test that valid names are accepted"""
        mock_tool_repository.create.return_value = Tool(
            name="pet_store",
            openapi_url="https://example.com/spec.json"
        )

        service = ToolService(mock_tool_repository, mock_http_client)

        # These should all work
        valid_names = ["petstore", "pet_store", "PetStore", "api1", "API_v2"]
        for name in valid_names:
            mock_tool_repository.create.reset_mock()
            mock_tool_repository.create.return_value = Tool(
                name=name,
                openapi_url="https://example.com/spec.json"
            )
            await service.register_tool(name=name, openapi_url="https://example.com/spec.json")
            mock_tool_repository.create.assert_called_once()
