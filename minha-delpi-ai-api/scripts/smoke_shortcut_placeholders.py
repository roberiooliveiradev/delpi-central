#!/usr/bin/env python3
"""Smoke — templates de atalhos usam {{placeholders}}, não código fixo na query.

Valida JSON do assistente + serviço de follow-up (sem HTTP).

Uso:
  PYTHONPATH=/app python scripts/smoke_shortcut_placeholders.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from app.application.services.chat_follow_up_suggestion_service import (
    ChatFollowUpSuggestionService,
)

_CONTENT_DIR = (
    Path(__file__).resolve().parent.parent / "app" / "content" / "pt-BR" / "assistant"
)

_PLACEHOLDER = re.compile(r"\{\{[a-zA-Z][a-zA-Z0-9]*\}\}")
_HARDCODED_SMOKE_CODE = re.compile(r"\b10080001\b")


def _load_json(name: str) -> dict[str, Any]:
    path = _CONTENT_DIR / name
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _check_query(label: str, query: str) -> str | None:
    text = query.strip()

    if not text:
        return None

    if _HARDCODED_SMOKE_CODE.search(text) and "{{productCode}}" not in text:
        return f"{label}: código fixo 10080001 na query"

    return None


def _iter_suggestion_queries(node: Any) -> list[tuple[str, str]]:
    """(label, query)"""
    found: list[tuple[str, str]] = []

    if isinstance(node, dict):
        suggestion = node.get("suggestion")

        if isinstance(suggestion, dict):
            label = str(suggestion.get("label") or "suggestion")
            query = str(suggestion.get("query") or "")
            found.append((label, query))

        for value in node.values():
            found.extend(_iter_suggestion_queries(value))
    elif isinstance(node, list):
        for item in node:
            if isinstance(item, dict) and "query" in item and "label" in item:
                label = str(item.get("label") or "chip")
                query = str(item.get("query") or "")
                found.append((label, query))

            found.extend(_iter_suggestion_queries(item))

    return found


def _queries_from_playbook_follow_ups(playbook: dict[str, Any]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    follow_up = playbook.get("followUpChips")

    if not isinstance(follow_up, dict):
        return rows

    for section_name, section in follow_up.items():
        if not isinstance(section, dict):
            continue

        for chip_label, query in section.items():
            if not isinstance(query, str) or not query.strip():
                continue

            rows.append((f"followUpChips.{section_name}.{chip_label}", query.strip()))

    return rows


def _check_content_queries() -> list[str]:
    errors: list[str] = []

    onboarding = _load_json("onboarding.json")

    for starter in onboarding.get("starterCards") or []:
        if not isinstance(starter, dict):
            continue

        label = f"onboarding.{starter.get('id') or starter.get('label')}"
        query = str(starter.get("query") or "")
        problem = _check_query(label, query)

        if problem:
            errors.append(problem)

    capabilities = _load_json("capabilities.json")

    for label, query in _iter_suggestion_queries(capabilities.get("interactive")):
        problem = _check_query(f"capabilities.interactive.{label}", query)

        if problem:
            errors.append(problem)

    for label, query in _iter_suggestion_queries(capabilities.get("guidedFlows")):
        problem = _check_query(f"capabilities.guidedFlows.{label}", query)

        if problem:
            errors.append(problem)

    playbook = _load_json("personality_playbook.json")

    for label, query in _queries_from_playbook_follow_ups(playbook):
        problem = _check_query(label, query)

        if problem:
            errors.append(problem)

    return errors


def _check_follow_up_service() -> list[str]:
    errors: list[str] = []

    suggestions = ChatFollowUpSuggestionService.build(
        message="me fale do produto 10080001",
        answer="Cadastro do produto 10080001",
        tool_calls=[{"path": "/products/10080001/analyser"}],
    )

    for item in suggestions:
        label = str(item.get("label") or "")
        query = str(item.get("query") or "")

        if label in {"Ver estoque", "Ver fornecedores", "Ver estrutura", "Onde é usado?"}:
            if "{{productCode}}" not in query:
                errors.append(f"follow-up service: {label} sem {{{{productCode}}}}")

            if _HARDCODED_SMOKE_CODE.search(query) and "{{productCode}}" not in query:
                errors.append(f"follow-up service: código fixo em {label}")

    return errors


def main() -> int:
    errors = _check_content_queries() + _check_follow_up_service()

    if errors:
        for message in errors:
            print(f"FAIL {message}", file=sys.stderr)
        return 1

    print("OK conteúdo onboarding/capabilities/playbook — queries sem código fixo")
    print("OK ChatFollowUpSuggestionService — chips com {{productCode}}")
    print("Smoke shortcut placeholders: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
