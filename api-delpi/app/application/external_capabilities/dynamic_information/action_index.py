"""In-process technical action index for DAVI dynamic READ."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
    build_technical_actions_from_openapi,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_external_read_allowlist,
)

_ACTIONS: list[TechnicalAction] | None = None
_BY_ID: dict[str, TechnicalAction] | None = None
_CONTENT_ROOT = Path(__file__).resolve().parents[3] / "content"


def reset_action_index_for_tests() -> None:
    global _ACTIONS, _BY_ID
    _ACTIONS = None
    _BY_ID = None


def _load_baseline() -> dict[str, Any]:
    path = _CONTENT_ROOT / "openapi_baseline.json"
    return json.loads(path.read_text(encoding="utf-8"))


def seed_actions_from_openapi(openapi: dict[str, Any]) -> list[TechnicalAction]:
    """Composition/bootstrap may refresh the index from live OpenAPI."""
    allowlist = load_external_read_allowlist()
    actions = build_technical_actions_from_openapi(openapi, allowlist=allowlist)
    set_actions_for_tests(actions)
    return actions


def get_technical_actions(*, force_reload: bool = False) -> list[TechnicalAction]:
    global _ACTIONS, _BY_ID
    if _ACTIONS is not None and not force_reload:
        return _ACTIONS
    allowlist = load_external_read_allowlist()
    actions = build_technical_actions_from_baseline(_load_baseline(), allowlist=allowlist)
    _ACTIONS = actions
    _BY_ID = {a.action_id: a for a in actions}
    return actions


def get_action_by_id(action_id: str) -> TechnicalAction | None:
    get_technical_actions()
    assert _BY_ID is not None
    return _BY_ID.get(action_id)


def set_actions_for_tests(actions: list[TechnicalAction]) -> None:
    global _ACTIONS, _BY_ID
    _ACTIONS = list(actions)
    _BY_ID = {a.action_id: a for a in _ACTIONS}
