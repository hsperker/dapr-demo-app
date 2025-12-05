import pytest
from typing import AsyncGenerator

from app.core.models import Tool, ToolStatus
from app.infrastructure.repositories.tool_repository import ToolRepository


@pytest.fixture
async def repository() -> AsyncGenerator[ToolRepository, None]:
    """Create a tool repository with in-memory SQLite for testing"""
    repo = ToolRepository(":memory:")
    await repo.initialize()
    yield repo
    await repo.close()


class TestToolRepository:
    """Test suite for ToolRepository"""

    async def test_create_tool(self, repository: ToolRepository) -> None:
        """Test creating a new tool"""
        tool = Tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json",
            description="Pet Store API"
        )
        saved_tool = await repository.create(tool)
        assert saved_tool.id == tool.id
        assert saved_tool.name == "petstore"
        assert saved_tool.openapi_url == "https://petstore.swagger.io/v2/swagger.json"

    async def test_get_tool(self, repository: ToolRepository) -> None:
        """Test retrieving a tool by ID"""
        tool = Tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json"
        )
        await repository.create(tool)

        retrieved = await repository.get(tool.id)
        assert retrieved is not None
        assert retrieved.id == tool.id
        assert retrieved.name == "petstore"

    async def test_get_nonexistent_tool(self, repository: ToolRepository) -> None:
        """Test retrieving a non-existent tool returns None"""
        tool = await repository.get("nonexistent")
        assert tool is None

    async def test_get_all_tools(self, repository: ToolRepository) -> None:
        """Test retrieving all tools"""
        tool1 = Tool(name="api1", openapi_url="https://example.com/spec1.json")
        tool2 = Tool(name="api2", openapi_url="https://example.com/spec2.json")

        await repository.create(tool1)
        await repository.create(tool2)

        tools = await repository.get_all()
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert names == {"api1", "api2"}

    async def test_get_active_tools(self, repository: ToolRepository) -> None:
        """Test retrieving only active tools"""
        tool1 = Tool(name="active1", openapi_url="https://example.com/spec1.json")
        tool2 = Tool(name="pending", openapi_url="https://example.com/spec2.json")
        tool3 = Tool(name="active2", openapi_url="https://example.com/spec3.json")

        await repository.create(tool1)
        await repository.create(tool2)
        await repository.create(tool3)

        # Update status
        await repository.update_status(tool1.id, ToolStatus.ACTIVE)
        await repository.update_status(tool3.id, ToolStatus.ACTIVE)

        active_tools = await repository.get_active()
        assert len(active_tools) == 2
        names = {t.name for t in active_tools}
        assert names == {"active1", "active2"}

    async def test_update_status(self, repository: ToolRepository) -> None:
        """Test updating a tool's status"""
        tool = Tool(name="test", openapi_url="https://example.com/spec.json")
        await repository.create(tool)

        await repository.update_status(tool.id, ToolStatus.ACTIVE)
        retrieved = await repository.get(tool.id)
        assert retrieved is not None
        assert retrieved.status == ToolStatus.ACTIVE

    async def test_update_status_with_error(self, repository: ToolRepository) -> None:
        """Test updating a tool's status with error message"""
        tool = Tool(name="test", openapi_url="https://example.com/spec.json")
        await repository.create(tool)

        await repository.update_status(
            tool.id,
            ToolStatus.ERROR,
            error_message="Failed to fetch spec"
        )

        retrieved = await repository.get(tool.id)
        assert retrieved is not None
        assert retrieved.status == ToolStatus.ERROR
        assert retrieved.error_message == "Failed to fetch spec"

    async def test_delete_tool(self, repository: ToolRepository) -> None:
        """Test deleting a tool"""
        tool = Tool(name="test", openapi_url="https://example.com/spec.json")
        await repository.create(tool)

        result = await repository.delete(tool.id)
        assert result is True

        retrieved = await repository.get(tool.id)
        assert retrieved is None

    async def test_delete_nonexistent_tool(self, repository: ToolRepository) -> None:
        """Test deleting a non-existent tool returns False"""
        result = await repository.delete("nonexistent")
        assert result is False

    async def test_tool_persists_all_fields(self, repository: ToolRepository) -> None:
        """Test that all tool fields are persisted"""
        tool = Tool(
            name="full-test",
            openapi_url="https://example.com/spec.json",
            description="A test tool",
            status=ToolStatus.ACTIVE,
            error_message=None
        )
        await repository.create(tool)

        retrieved = await repository.get(tool.id)
        assert retrieved is not None
        assert retrieved.name == tool.name
        assert retrieved.openapi_url == tool.openapi_url
        assert retrieved.description == tool.description
        assert retrieved.status == tool.status
        assert retrieved.created_at is not None
