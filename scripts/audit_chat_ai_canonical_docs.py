#!/usr/bin/env python3
"""Audit canonical Minha DELPI AI guidance consumed by Cursor.

The goal is intentionally narrow: canonical architecture/eval documents and Cursor
rules must not reintroduce superseded routing/evaluation guidance. Historical
records outside this allowlist are not treated as implementation instructions.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_FILES = (
    ".cursor/rules/development-standards-index.mdc",
    ".cursor/rules/centralized-rules-first.mdc",
    ".cursor/rules/chat-intelligence-base.mdc",
    ".cursor/rules/openapi-first-universal-tool-routing.mdc",
    ".cursor/rules/operational-api-routing.mdc",
    ".cursor/rules/new-api-route-checklist.mdc",
    ".cursor/rules/assistant-content-json.mdc",
    ".cursor/rules/clean-architecture-chat-api.mdc",
    ".cursor/rules/ai-intelligence-evaluation.mdc",
    ".cursor/rules/test-and-commit.mdc",
    "minha-delpi-ai-api/docs/README.md",
    "minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md",
    "minha-delpi-ai-api/docs/architecture/new-api-route-checklist.md",
    "minha-delpi-ai-api/docs/architecture/assistant-content-catalog.md",
    "minha-delpi-ai-api/docs/api/04-actions-openapi.md",
    "minha-delpi-ai-api/docs/development/guia-desenvolvimento.md",
    "minha-delpi-ai-api/docs/testing/README.md",
    "minha-delpi-ai-api/docs/testing/chat-ai-flow-families.md",
    "minha-delpi-ai-api/docs/flows/README.md",
    "minha-delpi-ai-api/docs/flows/03-tools-rag-agentic.md",
    "minha-delpi-ai-api/docs/flows/04-operacional-e-apresentacao.md",
    "minha-delpi-ai-api/docs/roadmap/README.md",
    "minha-delpi-ai-api/docs/roadmap/openapi-first-universal-tool-routing.md",
)

REMOVED_DOCS = (
    "minha-delpi-ai-api/docs/roadmap/prompt-refatoracao-motor-selecao-actions-openapi-first-set2026.md",
    "minha-delpi-ai-api/docs/roadmap/docie-desacoplamento-selecao-rotas-openapi.md",
    "minha-delpi-ai-api/docs/roadmap/audit-chat-base-familias-fluxos-set2026.md",
    "minha-delpi-ai-api/docs/architecture/chat-refactor-status-jun2026.md",
)

# These strings are forbidden specifically in the canonical implementation/eval
# sources. They either name superseded docs or teach the previous routing/eval model.
FORBIDDEN = (
    "R1–R8",
    "R1-R8",
    "operational_route_registry.json",
    "docie-desacoplamento-selecao-rotas-openapi.md",
    "prompt-refatoracao-motor-selecao-actions-openapi-first-set2026.md",
    "audit-chat-base-familias-fluxos-set2026.md",
    "chat-refactor-status-jun2026.md",
    "use operational_route_registry.json",
)

R11_REQUIRED = (
    ".cursor/rules/development-standards-index.mdc",
    ".cursor/rules/ai-intelligence-evaluation.mdc",
    ".cursor/rules/test-and-commit.mdc",
    "minha-delpi-ai-api/docs/README.md",
    "minha-delpi-ai-api/docs/testing/README.md",
    "minha-delpi-ai-api/docs/testing/chat-ai-flow-families.md",
    "minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md",
    "minha-delpi-ai-api/docs/development/guia-desenvolvimento.md",
)

OPENAPI_FIRST_REQUIRED = (
    ".cursor/rules/development-standards-index.mdc",
    ".cursor/rules/openapi-first-universal-tool-routing.mdc",
    ".cursor/rules/operational-api-routing.mdc",
    ".cursor/rules/new-api-route-checklist.mdc",
    "minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md",
    "minha-delpi-ai-api/docs/architecture/new-api-route-checklist.md",
    "minha-delpi-ai-api/docs/api/04-actions-openapi.md",
    "minha-delpi-ai-api/docs/roadmap/openapi-first-universal-tool-routing.md",
)


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    for relative in CANONICAL_FILES:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"canonical file missing: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN:
            if forbidden in text:
                errors.append(
                    f"{relative}: forbidden superseded guidance/reference: {forbidden!r}"
                )

    for relative in REMOVED_DOCS:
        if (ROOT / relative).exists():
            errors.append(f"superseded document must stay removed: {relative}")

    for relative in R11_REQUIRED:
        path = ROOT / relative
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            if "R1–R11" not in text and "R1-R11" not in text:
                errors.append(f"{relative}: canonical eval protocol R1–R11 not referenced")

    for relative in OPENAPI_FIRST_REQUIRED:
        path = ROOT / relative
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            if "OpenAPI" not in text or "Action Catalog" not in text:
                errors.append(
                    f"{relative}: canonical OpenAPI + Action Catalog guidance missing"
                )

    if errors:
        print("Chat AI canonical documentation audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "Chat AI canonical documentation audit: PASS "
        f"({len(CANONICAL_FILES)} canonical files, {len(REMOVED_DOCS)} removed docs enforced)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
