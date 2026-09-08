#!/usr/bin/env python3
"""Gate CI: motor OpenAPI-first não ganha if de rota / pathMarkers novos."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"

# Arquivos do motor novo — proibidos padrões de acoplamento por path.
NEW_CORE = [
    APP / "application" / "services" / "retrieve_action_candidates_service.py",
    APP / "application" / "services" / "plan_external_actions_service.py",
    APP / "application" / "services" / "validate_action_arguments_service.py",
    APP / "application" / "services" / "openapi_first_selection_bridge_service.py",
    APP / "domain" / "services" / "openapi_planner_mode_service.py",
]

FORBIDDEN = [
    (re.compile(r'if\s+["\']\/products\/'), "if path /products/"),
    (re.compile(r'if\s+["\']\/stock'), "if path /stock"),
    (re.compile(r"pathMarkers"), "pathMarkers"),
    (re.compile(r"_INTENT_PATH_HINTS"), "_INTENT_PATH_HINTS"),
    (re.compile(r"parameterStrategy\s*[:=]\s*[\"']shipment"), "shipment parameterStrategy"),
]


def check_new_core() -> list[str]:
    errors: list[str] = []
    for path in NEW_CORE:
        if not path.exists():
            errors.append(f"missing new-core file: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, label in FORBIDDEN:
            if pattern.search(text):
                errors.append(f"{path.relative_to(ROOT)}: forbidden {label}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail on forbidden patterns")
    args = parser.parse_args(argv)
    errors = check_new_core()
    if not args.check:
        for item in errors:
            print(item)
        return 0
    if errors:
        print("audit_openapi_first_routing --check FAILED:")
        for item in errors:
            print(f"  - {item}")
        return 1
    print("audit_openapi_first_routing --check OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
