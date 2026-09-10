import re

from app.domain.services.openapi_delpi_extension_service import (
    OpenApiDelpiExtensionService,
)


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


class OpenApiActionImporter:
    def import_actions(self, provider_key: str, schema: dict) -> list[dict]:
        from app.infrastructure.openapi.openapi_ref_resolver import OpenApiRefResolver

        if not isinstance(schema, dict):
            raise ValueError("OpenAPI schema must contain paths object")

        materialized = OpenApiRefResolver.resolve_document(schema)
        paths = materialized.get("paths") or {}

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
        locale_texts = OpenApiDelpiExtensionService.preferred_locale_texts(
            operation,
            lang="pt-BR",
        )

        payload = {
            "action_id": action_id,
            "operation_id": operation_id,
            "method": method,
            "path": path,
            "summary": locale_texts.get("summary") or operation.get("summary"),
            "description": locale_texts.get("description") or operation.get("description"),
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

        if locale_texts.get("whenToUse"):
            when_to = str(locale_texts["whenToUse"]).strip()
            payload["when_to_use"] = when_to
            base_description = str(payload.get("description") or "").strip()
            if when_to.lower() not in base_description.lower():
                payload["description"] = (
                    f"{when_to} {base_description}".strip() if base_description else when_to
                )
            metadata = dict(payload.get("delpi_metadata") or {})
            metadata["whenToUse"] = when_to
            payload["delpi_metadata"] = metadata

        when_not = str(locale_texts.get("whenNotToUse") or "").strip()
        if when_not:
            # Persist negative guidance without a dedicated column: fold into description.
            base_description = str(payload.get("description") or "").strip()
            if when_not.lower() not in base_description.lower():
                payload["description"] = (
                    f"{base_description} {when_not}".strip() if base_description else when_not
                )
            payload["when_not_to_use"] = when_not
            metadata = dict(payload.get("delpi_metadata") or {})
            metadata["whenNotToUse"] = when_not
            payload["delpi_metadata"] = metadata

        from app.domain.services.capability_ux_classifier_service import (
            CapabilityUxClassifierService,
        )

        CapabilityUxClassifierService.attach_to_action(payload)

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
