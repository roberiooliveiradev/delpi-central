"""Ephemeral OpenAPI providers for E8-C / metamorphic evals (self-contained)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def load_catalog_actions(filename: str) -> tuple[str, list[dict[str, Any]]]:
    payload = json.loads((_FIXTURES / filename).read_text(encoding="utf-8"))
    provider_key = str(payload.get("providerKey") or "").strip()
    actions = []
    for item in payload.get("actions") or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("providerKey", provider_key)
        row.setdefault("enabled", True)
        actions.append(row)
    return provider_key, actions


def load_nebula_factory() -> tuple[str, list[dict[str, Any]]]:
    return load_catalog_actions("nebula_factory_openapi_actions.json")


def load_nebula_metamorphic() -> tuple[str, list[dict[str, Any]]]:
    return load_catalog_actions("nebula_factory_openapi_actions_metamorphic.json")


def load_orion_manufacturing() -> tuple[str, list[dict[str, Any]]]:
    return load_catalog_actions("orion_manufacturing_openapi_actions.json")


def bind_ephemeral_allowed_ids(*catalogs: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for catalog in catalogs:
        for item in catalog:
            action_id = str(item.get("actionId") or "").strip()
            if action_id:
                ids.append(action_id)
    return ids
