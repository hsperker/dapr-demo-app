"""
Tests that verify OpenApiPlugin actually integrates with Semantic Kernel.

These tests ensure the plugin's functions are discoverable and callable by SK.
This was missing from the original test suite - we tested HTTP calls work,
but not that SK can actually use the plugin!
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from semantic_kernel import Kernel

from app.core.services.openapi_plugin import OpenApiPlugin, create_openapi_plugin


class TestOpenApiPluginSemanticKernelDiscovery:
    """Tests that SK can discover and use plugin functions"""

    def test_plugin_functions_are_discoverable_by_kernel(self) -> None:
        """Test that when added to kernel, functions are discoverable"""
        kernel = Kernel()

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Pet Store", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/pets": {
                    "get": {
                        "operationId": "listPets",
                        "summary": "List all pets",
                        "description": "Returns all pets from the store"
                    }
                },
                "/pets/{petId}": {
                    "get": {
                        "operationId": "getPet",
                        "summary": "Get a pet by ID"
                    }
                }
            }
        }

        plugin = create_openapi_plugin("petstore", spec)
        kernel.add_plugin(plugin, "petstore")

        # SK should see the plugin
        assert "petstore" in kernel.plugins

        # SK should see the functions
        plugin_functions = kernel.plugins["petstore"].functions
        assert len(plugin_functions) == 2, f"Expected 2 functions, got {len(plugin_functions)}: {list(plugin_functions.keys())}"
        assert "listPets" in plugin_functions
        assert "getPet" in plugin_functions

    def test_plugin_function_has_description(self) -> None:
        """Test that function descriptions are passed to SK"""
        kernel = Kernel()

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Pet Store", "version": "1.0.0"},
            "paths": {
                "/pets": {
                    "get": {
                        "operationId": "listPets",
                        "summary": "List all pets",
                        "description": "Returns all pets from the store"
                    }
                }
            }
        }

        plugin = create_openapi_plugin("petstore", spec)
        kernel.add_plugin(plugin, "petstore")

        list_pets_fn = kernel.plugins["petstore"].functions["listPets"]
        assert list_pets_fn.description is not None
        assert "pets" in list_pets_fn.description.lower()


class TestOpenApiPluginSemanticKernelInvocation:
    """Tests that SK can actually invoke plugin functions"""

    @pytest.mark.asyncio
    async def test_kernel_can_invoke_plugin_function(self) -> None:
        """Test that SK can invoke plugin functions and get results"""
        kernel = Kernel()

        # Create mock HTTP client that returns pets
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "name": "Fluffy"}]
        mock_client.get.return_value = mock_response

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Pet Store", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/pets": {
                    "get": {
                        "operationId": "listPets",
                        "summary": "List all pets",
                        "responses": {"200": {"description": "List of pets"}}
                    }
                }
            }
        }

        plugin = create_openapi_plugin("petstore", spec, http_client=mock_client)
        kernel.add_plugin(plugin, "petstore")

        # Use SK's invoke method to call the function
        result = await kernel.invoke(
            plugin_name="petstore",
            function_name="listPets"
        )

        # Verify the HTTP call was made and result returned
        mock_client.get.assert_called_once()
        assert result is not None
        assert result.value == [{"id": 1, "name": "Fluffy"}]

    @pytest.mark.asyncio
    async def test_kernel_can_invoke_post_function(self) -> None:
        """Test that SK can invoke POST operations through plugin"""
        kernel = Kernel()

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 42, "name": "New Pet"}
        mock_client.post.return_value = mock_response

        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Pet Store", "version": "1.0.0"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {
                "/pets": {
                    "post": {
                        "operationId": "createPet",
                        "summary": "Create a new pet",
                        "responses": {"201": {"description": "Pet created"}}
                    }
                }
            }
        }

        plugin = create_openapi_plugin("petstore", spec, http_client=mock_client)
        kernel.add_plugin(plugin, "petstore")

        result = await kernel.invoke(
            plugin_name="petstore",
            function_name="createPet"
        )

        mock_client.post.assert_called_once()
        assert result is not None
        assert result.value["id"] == 42
