#!/usr/bin/env python3
"""Audita cobertura do registry de validação de desenho (Fase B/C)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONTENT = _REPO_ROOT / "app" / "content" / "pt-BR" / "assistant"

# Regras cobertas por testes de serviço dedicados (fora drawing_validation_rule_regression_cases).
_SERVICE_ONLY_RULES = frozenset(
    {
        "product_code_cross_check",
        "guide_structure",
        "multipage_coverage",
        "intermediate_presence",
        "intermediate_length",
        "total_length",
        "decapes_ed",
        "dimension_note",
    }
)


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


def _audit_rule_coverage(rules_bundle: dict) -> tuple[list[str], list[str]]:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

    from tests.fixtures.drawing_validation_rule_regression_cases import rule_ids_with_cases

    catalog = rules_bundle.get("rules")

    if not isinstance(catalog, dict):
        return [], []

    catalog_ids = {str(key) for key in catalog}
    covered = rule_ids_with_cases() | _SERVICE_ONLY_RULES
    missing = sorted(catalog_ids - covered)
    extra = sorted(covered - catalog_ids)

    return missing, extra


def audit(*, check: bool, check_rules: bool) -> int:
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

    exit_code = 0

    if check and (missing or extra):
        exit_code = 1

    if check_rules:
        rule_missing, rule_extra = _audit_rule_coverage(rules_bundle)

        if rule_missing:
            print("Regras do catalog sem caso de regressão:")

            for rule_id in rule_missing:
                print(f"  - {rule_id}")

        if rule_extra:
            print("Casos de regressão referenciam regras inexistentes no catalog:")

            for rule_id in rule_extra:
                print(f"  - {rule_id}")

        if not rule_missing and not rule_extra:
            print(
                f"OK: {len(rules_bundle.get('rules') or {})} regras com cobertura "
                f"({len(_SERVICE_ONLY_RULES)} via testes de serviço)."
            )

        if check and (rule_missing or rule_extra):
            exit_code = 1

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Retorna código 1 se houver template ou regra sem cobertura.",
    )
    parser.add_argument(
        "--check-rules",
        action="store_true",
        help="Valida cobertura de regras (implícito com --check).",
    )
    args = parser.parse_args()
    check_rules = args.check_rules or args.check

    return audit(check=args.check, check_rules=check_rules)


if __name__ == "__main__":
    sys.exit(main())
