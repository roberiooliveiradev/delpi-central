"""Carrega cenários e marcadores de validação de assistant/smoke_e2e_scenarios.json."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


@dataclass(frozen=True)
class SmokeScenario:
    id: str
    domain: str
    message: str
    path_fragment: str
    checks: str | None = None


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ContentService.load_json("assistant/smoke_e2e_scenarios")


def validation_markers(*path: str) -> tuple[str, ...]:
    node: Any = _content().get("validation") or {}

    for key in path:
        if not isinstance(node, dict):
            return ()

        node = node.get(key)

    if not isinstance(node, list):
        return ()

    return tuple(str(item) for item in node if str(item).strip())


def load_suite(suite_name: str) -> tuple[SmokeScenario, ...]:
    suites = _content().get("suites") or {}
    suite = suites.get(suite_name) if isinstance(suites, dict) else None

    if not isinstance(suite, dict):
        raise KeyError(f"Suite de smoke não encontrada: {suite_name!r}")

    items = suite.get("scenarios") or []
    scenarios: list[SmokeScenario] = []

    for entry in items:
        if not isinstance(entry, dict):
            continue

        scenario_id = str(entry.get("id") or "").strip()
        message = str(entry.get("message") or "").strip()
        path_fragment = str(entry.get("pathFragment") or "").strip()

        if not scenario_id or not message or not path_fragment:
            continue

        scenarios.append(
            SmokeScenario(
                id=scenario_id,
                domain=str(entry.get("domain") or "").strip(),
                message=message,
                path_fragment=path_fragment,
                checks=str(entry.get("checks") or "").strip() or None,
            )
        )

    if not scenarios:
        raise ValueError(f"Suite {suite_name!r} sem cenários válidos")

    return tuple(scenarios)


def suite_forbids_product_path(suite_name: str) -> bool:
    suites = _content().get("suites") or {}
    suite = suites.get(suite_name) if isinstance(suites, dict) else None

    if not isinstance(suite, dict):
        return False

    return bool(suite.get("forbidProductPath"))
