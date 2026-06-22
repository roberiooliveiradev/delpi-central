"""Defaults declarativos de query por rota operacional — registry + override canônico."""

from __future__ import annotations

from typing import Any


class OperationalRouteQueryDefaultsService:
    @classmethod
    def apply(
        cls,
        action: dict,
        parameters: dict[str, Any] | None,
        *,
        route: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        spec = (route or {}).get("parameters")

        if not isinstance(spec, dict):
            return dict(parameters or {})

        defaults = spec.get("queryDefaults")

        if not isinstance(defaults, dict) or not defaults:
            return dict(parameters or {})

        merged = dict(parameters or {})
        existing = {str(key).strip().lower() for key in merged}
        override_keys = cls._normalized_keys(spec.get("overrideKeys"))
        schema_by_lower = cls._schema_names_by_lower(action)

        for key, value in defaults.items():
            lowered = str(key or "").strip().lower()

            if not lowered:
                continue

            schema_name = schema_by_lower.get(lowered)

            if schema_name is None:
                continue

            if lowered in existing and lowered not in override_keys:
                continue

            merged[schema_name] = value

        return merged

    @classmethod
    def _schema_names_by_lower(cls, action: dict) -> dict[str, str]:
        return {
            str(parameter.get("name") or "").strip().lower(): str(parameter.get("name") or "").strip()
            for parameter in (action.get("parametersSchema") or [])
            if str(parameter.get("name") or "").strip()
        }

    @classmethod
    def _normalized_keys(cls, raw: Any) -> set[str]:
        if not isinstance(raw, list):
            return set()

        return {
            str(item or "").strip().lower()
            for item in raw
            if str(item or "").strip()
        }
