#!/usr/bin/env python3
"""Audita cobertura do registry de validação de desenho (Fase B/C)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTENT = _REPO_ROOT / "app" / "content" / "pt-BR" / "assistant"


def _load_json(name: str) -> dict:
    path = _CONTENT / name

    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)

    return payload if isinstance(payload, dict) else {}


def _collect_template_keys(validation: dict) -> set[str]:
    templates = validation.get("itemTemplates")

    if not isinstance(templates, dict):
        return set()

    return {str(key) for key in templates}


def _collect_registry_template_keys(rules_bundle: dict) -> set[str]:
    mapped: set[str] = set()
    core = rules_bundle.get("coreTemplateKeys")

    if isinstance(core, list):
        mapped.update(str(item) for item in core if str(item).strip())

    catalog = rules_bundle.get("rules")

    if isinstance(catalog, dict):
        for node in catalog.values():
            if not isinstance(node, dict):
                continue

            for key in node.get("templateKeys") or []:
                normalized = str(key).strip()

                if normalized:
                    mapped.add(normalized)

    return mapped


def audit(*, check: bool) -> int:
    validation = _load_json("drawing_validation.json")
    rules_bundle = _load_json("drawing_validation_rules.json")
    all_templates = _collect_template_keys(validation)
    mapped = _collect_registry_template_keys(rules_bundle)
    missing = sorted(all_templates - mapped)
    extra = sorted(mapped - all_templates)

    if missing:
        print("Templates sem rule_id/core no registry:")

        for key in missing:
            print(f"  - {key}")

    if extra:
        print("Chaves no registry inexistentes em itemTemplates:")

        for key in extra:
            print(f"  - {key}")

    if not missing and not extra:
        print(
            f"OK: {len(all_templates)} templateKeys cobertos "
            f"({len(mapped)} entradas no registry)."
        )

    if check and (missing or extra):
        return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Retorna código 1 se houver template sem mapeamento.",
    )
    args = parser.parse_args()

    return audit(check=args.check)


if __name__ == "__main__":
    sys.exit(main())
