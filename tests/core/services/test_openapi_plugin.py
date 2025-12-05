"""
Tests for OpenAPI plugin functionality.

These tests verify that OpenAPI plugins can actually make HTTP calls,
not just parse specs. This was missing from the original test suite.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.services.openapi_plugin import OpenApiPlugin, create_openapi_plugin


class TestOpenApiPlugin:
    """Tests for OpenAPI plugin"""

    def test_creates_plugin_from_spec(self) -> None:
        """Test that a plugin can be created from an OpenAPI spec"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/pets": {
                    "get": {
                        "operationId": "listPets",
                        "summary": "List all pets",
                        "responses": {"200": {"description": "A list of pets"}}
                    }
                }
            }
        }

        plugin = create_openapi_plugin("petstore", spec)

        assert plugin.name == "petstore"
        assert plugin.base_url == "https://api.example.com"
        assert "listPets" in plugin.operations

    def test_extracts_operations_from_paths(self) -> None:
        """Test that operations are extracted correctly"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/pets": {
                    "get": {"operationId": "listPets", "summary": "List pets"},
                    "post": {"operationId": "createPet", "summary": "Create pet"}
                },
                "/pets/{id}": {
                    "get": {"operationId": "getPet", "summary": "Get pet"},
                    "delete": {"operationId": "deletePet", "summary": "Delete pet"}
                }
            }
        }

        plugin = create_openapi_plugin("petstore", spec)

        assert len(plugin.operations) == 4
        assert "listPets" in plugin.operations
        assert "createPet" in plugin.operations
        assert "getPet" in plugin.operations
        assert "deletePet" in plugin.operations

    def test_plugin_has_callable_functions(self) -> None:
        """Test that plugin operations are callable as functions"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/pets": {
                    "get": {
                        "operationId": "listPets",
                        "summary": "List all pets",
                        "responses": {"200": {"description": "A list of pets"}}
                    }
                }
            }
        }

        plugin = create_openapi_plugin("petstore", spec)

        # Plugin should have callable methods for each operation
        assert hasattr(plugin, "listPets") or hasattr(plugin, "call_operation")
        # The function should be async callable
        func = getattr(plugin, "listPets", None) or plugin.call_operation
        assert callable(func)


class TestOpenApiPluginHttpCalls:
    """Tests verifying the plugin actually makes HTTP calls"""

    @pytest.mark.asyncio
    async def test_get_operation_makes_http_request(self) -> None:
        """Test that calling a GET operation makes an HTTP request"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Pet Store", "version": "1.0.0"},
            "servers": [{"url": "https://petstore.example.com"}],
            "paths": {
                "/pets": {
                    "get": {
                        "operationId": "listPets",
                        "summary": "List all pets",
                        "responses": {"200": {"description": "A list of pets"}}
                    }
                }
            }
        }

        # Create mock HTTP client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "name": "Fluffy"}]
        mock_client.get.return_value = mock_response

        plugin = create_openapi_plugin("petstore", spec, http_client=mock_client)

        result = await plugin.call_operation("listPets")

        mock_client.get.assert_called_once_with("https://petstore.example.com/pets", params=None)
        assert result == [{"id": 1, "name": "Fluffy"}]

    @pytest.mark.asyncio
    async def test_post_operation_sends_body(self) -> None:
        """Test that calling a POST operation sends request body"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Pet Store", "version": "1.0.0"},
            "servers": [{"url": "https://petstore.example.com"}],
            "paths": {
                "/pets": {
                    "post": {
                        "operationId": "createPet",
                        "summary": "Create a pet",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        },
                        "responses": {"201": {"description": "Pet created"}}
                    }
                }
            }
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "name": "Buddy"}
        mock_client.post.return_value = mock_response

        plugin = create_openapi_plugin("petstore", spec, http_client=mock_client)

        result = await plugin.call_operation("createPet", body={"name": "Buddy"})

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://petstore.example.com/pets"
        assert call_args[1]["json"] == {"name": "Buddy"}

    @pytest.mark.asyncio
    async def test_operation_with_path_parameters(self) -> None:
        """Test that path parameters are substituted correctly"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Pet Store", "version": "1.0.0"},
            "servers": [{"url": "https://petstore.example.com"}],
            "paths": {
                "/pets/{petId}": {
                    "get": {
                        "operationId": "getPet",
                        "summary": "Get a pet by ID",
                        "parameters": [
                            {"name": "petId", "in": "path", "required": True}
                        ],
                        "responses": {"200": {"description": "Pet details"}}
                    }
                }
            }
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 42, "name": "Fluffy"}
        mock_client.get.return_value = mock_response

        plugin = create_openapi_plugin("petstore", spec, http_client=mock_client)

        result = await plugin.call_operation("getPet", path_params={"petId": "42"})

        mock_client.get.assert_called_once_with("https://petstore.example.com/pets/42", params=None)


class TestOpenApiPluginSemanticKernelIntegration:
    """Tests verifying the plugin works with Semantic Kernel"""

    def test_plugin_has_callable_operation_methods(self) -> None:
        """Test that plugin has callable methods for each operation"""
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Pet Store", "version": "1.0.0"},
            "servers": [{"url": "https://petstore.example.com"}],
            "paths": {
                "/pets": {
                    "get": {
                        "operationId": "listPets",
                        "summary": "List all pets",
                        "description": "Returns all pets from the store",
                        "responses": {"200": {"description": "A list of pets"}}
                    }
                }
            }
        }

        plugin = create_openapi_plugin("petstore", spec)

        # Plugin should have a listPets method
        assert hasattr(plugin, "listPets")
        assert callable(getattr(plugin, "listPets"))
