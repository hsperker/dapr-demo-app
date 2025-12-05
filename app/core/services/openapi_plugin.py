"""
OpenAPI Plugin Factory.

Creates Semantic Kernel plugins from OpenAPI specifications that can
actually make HTTP calls to external APIs.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING

from semantic_kernel.functions import kernel_function

if TYPE_CHECKING:
    from app.core.protocols import HttpClient


class OpenApiPlugin:
    """
    A plugin created from an OpenAPI specification.

    This plugin can make actual HTTP calls to the API defined in the spec.
    Methods decorated with @kernel_function are discoverable by Semantic Kernel.
    """

    def __init__(
        self,
        name: str,
        spec: Dict[str, Any],
        http_client: Optional["HttpClient"] = None
    ):
        self.name = name
        self.spec = spec
        self._http_client = http_client
        self.base_url = self._extract_base_url(spec)
        self.operations = self._extract_operations(spec)
        self._create_kernel_functions()

    def _extract_base_url(self, spec: Dict[str, Any]) -> str:
        """Extract base URL from OpenAPI spec"""
        # OpenAPI 3.x
        if "servers" in spec and spec["servers"]:
            url: str = spec["servers"][0].get("url", "")
            return url.rstrip("/")
        # OpenAPI 2.x (Swagger)
        if "host" in spec:
            scheme = spec.get("schemes", ["https"])[0]
            base_path = spec.get("basePath", "")
            return f"{scheme}://{spec['host']}{base_path}".rstrip("/")
        return ""

    def _extract_operations(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract operations from OpenAPI spec paths"""
        operations = {}
        paths = spec.get("paths", {})

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue

            for method, details in methods.items():
                if method not in ("get", "post", "put", "delete", "patch"):
                    continue
                if not isinstance(details, dict):
                    continue

                operation_id = details.get("operationId", f"{method}_{path.replace('/', '_')}")
                operations[operation_id] = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description", details.get("summary", "")),
                    "parameters": details.get("parameters", []),
                    "request_body": details.get("requestBody"),
                }

        return operations

    def _create_kernel_functions(self) -> None:
        """
        Dynamically create kernel functions for each operation.

        This creates methods on the class instance that are decorated with
        @kernel_function so Semantic Kernel can discover and invoke them.
        """
        for op_id, op_details in self.operations.items():
            description = op_details.get("description") or op_details.get("summary") or f"Call {op_id}"

            # Create an async method that calls the operation
            # We need to capture op_id in the closure properly
            async def make_caller(operation_id: str = op_id) -> Any:
                """Dynamically generated function to call the API"""
                return await self.call_operation(operation_id)

            # Apply the kernel_function decorator
            decorated_func = kernel_function(name=op_id, description=description)(make_caller)

            # Attach as a method on this instance
            setattr(self, op_id, decorated_func)

    async def call_operation(
        self,
        operation_id: str,
        path_params: Optional[Dict[str, str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Call an API operation by its operation ID.

        Args:
            operation_id: The operationId from the OpenAPI spec
            path_params: Parameters to substitute in the URL path
            query_params: Query string parameters
            body: Request body for POST/PUT/PATCH requests

        Returns:
            The JSON response from the API
        """
        if operation_id not in self.operations:
            raise ValueError(f"Unknown operation: {operation_id}")

        operation = self.operations[operation_id]
        method = operation["method"]
        path = operation["path"]

        # Substitute path parameters
        if path_params:
            for param_name, param_value in path_params.items():
                path = path.replace(f"{{{param_name}}}", str(param_value))

        url = f"{self.base_url}{path}"

        # Make the HTTP request
        if self._http_client is None:
            raise RuntimeError("HTTP client not configured")

        if method == "GET":
            response = await self._http_client.get(url, params=query_params)
        elif method == "POST":
            response = await self._http_client.post(url, params=query_params, json=body)
        elif method == "PUT":
            response = await self._http_client.put(url, params=query_params, json=body)
        elif method == "PATCH":
            response = await self._http_client.patch(url, params=query_params, json=body)
        elif method == "DELETE":
            response = await self._http_client.delete(url, params=query_params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Return JSON response
        if response.status_code >= 200 and response.status_code < 300:
            try:
                return response.json()
            except Exception:
                return response.text
        else:
            raise RuntimeError(f"API call failed: {response.status_code} {response.text}")

    def get_description(self) -> str:
        """Get a description of this plugin for the agent"""
        info = self.spec.get("info", {})
        title = info.get("title", self.name)
        description = info.get("description", "")

        ops_summary = ", ".join(list(self.operations.keys())[:5])
        if len(self.operations) > 5:
            ops_summary += f", ... ({len(self.operations)} total operations)"

        return f"{title}: {description}\nOperations: {ops_summary}"


def create_openapi_plugin(
    name: str,
    spec: Dict[str, Any],
    http_client: Optional["HttpClient"] = None
) -> OpenApiPlugin:
    """
    Create a plugin from an OpenAPI specification.

    Args:
        name: Name for the plugin
        spec: The OpenAPI specification as a dictionary
        http_client: Optional HTTP client for making requests

    Returns:
        An OpenApiPlugin instance that can be added to the agent
    """
    return OpenApiPlugin(name, spec, http_client)
