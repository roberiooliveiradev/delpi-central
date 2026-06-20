#!/usr/bin/env python3
"""Audita acoplamento template×LLM — gates canônicos e anti-padrões."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_APP = ROOT / "app"
MFE_SRC = ROOT.parent / "plugins" / "minha-delpi-chat" / "src"

CANONICAL_GATE = "ChatPresentationProseDeliveryService"
DECOUPLE_SERVICE = "ChatPresentationLlmProseDecouplingService"
NARRATIVE_GATE = "ChatOperationalNarrativeSynthesisService"

REQUIRED_CALLSITES = {
    API_APP / "application/services/chat_turn/chat_turn_preparation_post_tool_resolution_service.py": CANONICAL_GATE,
}

ANTI_PATTERNS = [
    (
        "product_overview_template_fallback",
        re.compile(r"should_force_llm_synthesis[\s\S]{0,120}authorized_tool_answer"),
        set(),
    ),
]

ALLOWLIST_FILES = frozenset(
    {
        "chat_tool_context_presentation_service.py",
        "chat_tool_context_service.py",
        "chat_response_mode_synthesis_quality_service.py",
        "chat_turn_preparation_post_tool_resolution_service.py",
        "chat_rich_presentation_text_service.py",
    }
)

MFE_DECOUPLE_MARKERS = [
    "isLlmProseDecoupledFromToolCalls",
    "isLlmProseDecoupledMetadata",
    "resolveLeadMarkdownSource",
]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def audit_required_callsites() -> list[str]:
    issues: list[str] = []

    for path, symbol in REQUIRED_CALLSITES.items():
        body = _read(path)

        if symbol not in body:
            issues.append(f"callsite ausente: {path.relative_to(ROOT)} não referencia {symbol}")

    return issues


def audit_canonical_modules_exist() -> list[str]:
    issues: list[str] = []
    modules = [
        API_APP / "domain/services/chat_presentation_prose_delivery_service.py",
        API_APP / "domain/services/chat_presentation_llm_prose_decoupling_service.py",
        API_APP / "content/pt-BR/assistant/presentation_prose_delivery.json",
    ]

    for path in modules:
        if not path.is_file():
            issues.append(f"módulo canônico ausente: {path.relative_to(ROOT)}")

    return issues


def audit_mfe_decouple_helpers() -> list[str]:
    issues: list[str] = []
    normalization = MFE_SRC / "ui/components/presentation/presentationMarkdownNormalization.ts"
    body = _read(normalization)

    for marker in MFE_DECOUPLE_MARKERS:
        if marker not in body:
            issues.append(f"MFE sem helper canônico `{marker}` em presentationMarkdownNormalization.ts")

    return issues


def audit_anti_patterns() -> list[str]:
    issues: list[str] = []

    for py_file in API_APP.rglob("*.py"):
        body = _read(py_file)
        rel = str(py_file.relative_to(ROOT))

        for name, pattern, allowed in ANTI_PATTERNS:
            if not pattern.search(body):
                continue

            if py_file.name in ALLOWLIST_FILES:
                continue

            if any(token in rel or token in body for token in allowed):
                continue

            if name == "product_overview_template_fallback" and "post_tool" not in rel:
                continue

            issues.append(f"anti-padrão `{name}` em {rel}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 se houver issues")
    args = parser.parse_args()

    issues = [
        *audit_canonical_modules_exist(),
        *audit_required_callsites(),
        *audit_mfe_decouple_helpers(),
        *audit_anti_patterns(),
    ]

    if not issues:
        print("audit_presentation_prose_delivery: OK")
        return 0

    print("audit_presentation_prose_delivery: issues encontradas\n")

    for item in issues:
        print(f"  - {item}")

    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
