"""E11.S3 — parameter strategy is not path/operationId authority.

Legacy callers may still ask for a strategy label for telemetry/shadow compare.
Always returns ``schema``: OpenAPI parametersSchema + SchemaDrivenArgumentBinder /
PlanExternalActionsService._bind_arguments are the authority.
"""

from __future__ import annotations

from typing import Any

_SCHEMA_AUTHORITY = "schema"


class ParameterStrategyInferenceService:
    """Deprecated label helper — does not infer from path or operationId."""

    @classmethod
    def infer_from_action(
        cls,
        action: dict[str, Any] | None,
        *,
        route: dict[str, Any] | None = None,
    ) -> str:
        _ = (action, route)
        return _SCHEMA_AUTHORITY

    @classmethod
    def infer_from_path(cls, path: str, *, operation_id: str = "") -> str:
        _ = (path, operation_id)
        return _SCHEMA_AUTHORITY
