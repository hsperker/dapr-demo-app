import pytest
from typing import Generator
from unittest.mock import AsyncMock, MagicMock
from fastapi import Request
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_tool_service, get_plugin_manager
from app.core.models import Tool, ToolStatus, PluginLoadResult


@pytest.fixture
def mock_tool_service() -> AsyncMock:
    """Create a mock tool service"""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_plugin_manager() -> MagicMock:
    """Create a mock plugin manager"""
    manager = MagicMock()
    manager.load_plugin = MagicMock()
    manager.unload_plugin = MagicMock()
    return manager


@pytest.fixture
def client(mock_tool_service: AsyncMock, mock_plugin_manager: MagicMock) -> Generator[TestClient, None, None]:
    """Create a test client with mocked dependencies"""
    def override_tool_service(request: Request) -> AsyncMock:
        return mock_tool_service

    def override_plugin_manager(request: Request) -> MagicMock:
        return mock_plugin_manager

    app.dependency_overrides[get_tool_service] = override_tool_service
    app.dependency_overrides[get_plugin_manager] = override_plugin_manager
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestToolsRouter:
    """Test suite for tools API endpoints"""

    def test_register_tool(self, client: TestClient, mock_tool_service: AsyncMock) -> None:
        """Test registering a new tool"""
        tool = Tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json",
            description="Pet Store API"
        )
        mock_tool_service.register_tool.return_value = tool

        response = client.post(
            "/tools",
            json={
                "name": "petstore",
                "openapi_url": "https://petstore.swagger.io/v2/swagger.json",
                "description": "Pet Store API"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "petstore"
        assert data["status"] == "pending"

    def test_activate_tool(
        self,
        client: TestClient,
        mock_tool_service: AsyncMock,
        mock_plugin_manager: MagicMock
    ) -> None:
        """Test activating a tool"""
        tool = Tool(name="petstore", openapi_url="https://example.com/spec.json")
        mock_tool_service.get_tool.return_value = tool
        mock_plugin_manager.load_plugin.return_value = PluginLoadResult.ok()

        response = client.post(f"/tools/{tool.id}/activate")

        assert response.status_code == 200
        mock_plugin_manager.load_plugin.assert_called_once()

    def test_activate_tool_failure(
        self,
        client: TestClient,
        mock_tool_service: AsyncMock,
        mock_plugin_manager: MagicMock
    ) -> None:
        """Test activating a tool that fails"""
        tool = Tool(name="petstore", openapi_url="https://example.com/spec.json")
        mock_tool_service.get_tool.return_value = tool
        mock_plugin_manager.load_plugin.return_value = PluginLoadResult.error("Failed to fetch")

        response = client.post(f"/tools/{tool.id}/activate")

        assert response.status_code == 400
        mock_tool_service.update_status.assert_called()

    def test_activate_tool_not_found(
        self,
        client: TestClient,
        mock_tool_service: AsyncMock,
        mock_plugin_manager: MagicMock
    ) -> None:
        """Test activating a non-existent tool"""
        mock_tool_service.get_tool.return_value = None

        response = client.post("/tools/nonexistent/activate")

        assert response.status_code == 404

    def test_get_tools(self, client: TestClient, mock_tool_service: AsyncMock) -> None:
        """Test getting all tools"""
        tools = [
            Tool(name="api1", openapi_url="https://example.com/spec1.json"),
            Tool(name="api2", openapi_url="https://example.com/spec2.json")
        ]
        mock_tool_service.get_all_tools.return_value = tools

        response = client.get("/tools")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_tool(self, client: TestClient, mock_tool_service: AsyncMock) -> None:
        """Test getting a specific tool"""
        tool = Tool(
            name="petstore",
            openapi_url="https://petstore.swagger.io/v2/swagger.json"
        )
        mock_tool_service.get_tool.return_value = tool

        response = client.get(f"/tools/{tool.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "petstore"

    def test_get_tool_not_found(self, client: TestClient, mock_tool_service: AsyncMock) -> None:
        """Test getting a non-existent tool"""
        mock_tool_service.get_tool.return_value = None

        response = client.get("/tools/nonexistent")

        assert response.status_code == 404

    def test_delete_tool(
        self,
        client: TestClient,
        mock_tool_service: AsyncMock,
        mock_plugin_manager: MagicMock
    ) -> None:
        """Test deleting a tool"""
        tool = Tool(name="petstore", openapi_url="https://example.com/spec.json")
        mock_tool_service.get_tool.return_value = tool
        mock_tool_service.delete_tool.return_value = True

        response = client.delete(f"/tools/{tool.id}")

        assert response.status_code == 204

    def test_delete_active_tool_unloads_plugin(
        self,
        client: TestClient,
        mock_tool_service: AsyncMock,
        mock_plugin_manager: MagicMock
    ) -> None:
        """Test deleting an active tool unloads the plugin"""
        tool = Tool(
            name="petstore",
            openapi_url="https://example.com/spec.json",
            status=ToolStatus.ACTIVE
        )
        mock_tool_service.get_tool.return_value = tool
        mock_tool_service.delete_tool.return_value = True

        response = client.delete(f"/tools/{tool.id}")

        assert response.status_code == 204
        mock_plugin_manager.unload_plugin.assert_called_once_with("petstore")

    def test_delete_tool_not_found(
        self,
        client: TestClient,
        mock_tool_service: AsyncMock,
        mock_plugin_manager: MagicMock
    ) -> None:
        """Test deleting a non-existent tool"""
        mock_tool_service.get_tool.return_value = None

        response = client.delete("/tools/nonexistent")

        assert response.status_code == 404
