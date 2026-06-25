#!/usr/bin/env python3
"""Gate: pathEntityFallbacks não duplica entityPathHints (Fase 13)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)

configure_domain_infrastructure_ports()


def _is_product_example_hint(hint: str) -> bool:
    lowered = str(hint or "").lower().rstrip("/")
    marker = "/products/"

    if marker not in lowered:
        return False

    suffix = lowered.split(marker, 1)[1]
    code = suffix.split("/", 1)[0]

    return code.isdigit() or code in {"{code}", "0"}


def redundant_fallbacks() -> list[dict[str, str]]:
    hints = ChatPresentationProfileService.entity_path_hints()
    violations: list[dict[str, str]] = []

    for fragment, entity in ChatPresentationProfileService.path_entity_fallbacks():
        hint = str(hints.get(entity) or "").lower().rstrip("/")
        frag = str(fragment or "").lower()

        if not hint or not frag:
            continue

        if _is_product_example_hint(hint):
            continue

        if frag in hint:
            violations.append(
                {
                    "contains": fragment,
                    "entity": entity,
                    "entityPathHint": hints.get(entity) or "",
                }
            )

    return violations


def validate() -> dict:
    violations = redundant_fallbacks()
    remaining = ChatPresentationProfileService.path_entity_fallbacks()

    return {
        "ok": not violations and not remaining,
        "redundantFallbackCount": len(violations),
        "redundantFallbacks": violations,
        "remainingFallbackCount": len(remaining),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 quando houver redundâncias.")
    parser.add_argument("--json", action="store_true", help="Imprime relatório JSON.")
    args = parser.parse_args()

    report = validate()

    if args.json or not args.check:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.check and not report["ok"]:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
