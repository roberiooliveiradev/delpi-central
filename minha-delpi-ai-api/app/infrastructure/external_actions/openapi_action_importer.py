import re

from app.domain.services.openapi_delpi_extension_service import (
    OpenApiDelpiExtensionService,
)


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


class OpenApiActionImporter:
    def import_actions(self, provider_key: str, schema: dict) -> list[dict]:
        paths = schema.get("paths") or {}

        if not isinstance(paths, dict):
            raise ValueError("OpenAPI schema must contain paths object")

        actions = []

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if method.lower() not in HTTP_METHODS:
                    continue

                if not isinstance(operation, dict):
                    continue

                actions.append(
                    self._operation_to_action(
                        provider_key=provider_key,
                        path=path,
                        method=method.upper(),
                        operation=operation,
                    )
                )

        return actions

    def _operation_to_action(
        self,
        provider_key: str,
        path: str,
        method: str,
        operation: dict,
    ) -> dict:
        operation_id = operation.get("operationId") or self._operation_id_from_path(method, path)
        tags = operation.get("tags") or []
        primary_tag = self._normalize_token(tags[0]) if tags else "default"
        provider_token = self._normalize_token(provider_key)

        action_id = f"{provider_token}.{primary_tag}.{self._normalize_token(operation_id)}"

        delpi_metadata = OpenApiDelpiExtensionService.extract_from_operation(operation)

        payload = {
            "action_id": action_id,
            "operation_id": operation_id,
            "method": method,
            "path": path,
            "summary": operation.get("summary"),
            "description": operation.get("description"),
            "tags": tags,
            "parameters_schema": operation.get("parameters") or [],
            "request_body_schema": operation.get("requestBody"),
            "response_schema": operation.get("responses"),
            "sensitivity": self._classify_sensitivity(method, path),
            "deprecated": bool(operation.get("deprecated")),
            "enabled": True,
        }

        if delpi_metadata:
            payload["delpi_metadata"] = delpi_metadata

        return payload

    def _operation_id_from_path(self, method: str, path: str) -> str:
        clean = re.sub(r"[{}]", "", path.strip("/"))
        clean = re.sub(r"[^a-zA-Z0-9]+", "_", clean).strip("_")
        return f"{method.lower()}_{clean or 'root'}"

    def _normalize_token(self, value: str) -> str:
        token = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower()).strip("_")
        return token or "unknown"

    def _classify_sensitivity(self, method: str, path: str) -> str:
        lower_path = path.lower()

        if "/data/sql" in lower_path or "sql" in lower_path:
            return "sql"

        if "export" in lower_path or "download" in lower_path or "excel" in lower_path:
            return "export"

        if "/admin" in lower_path:
            return "admin"

        if method == "GET":
            return "read"

        if method == "DELETE":
            return "destructive"

        return "write"
