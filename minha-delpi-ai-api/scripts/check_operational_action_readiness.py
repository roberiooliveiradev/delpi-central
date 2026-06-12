#!/usr/bin/env python3
"""Verifica actions críticas Playbook 15/16 no catálogo api-delpi.

Uso (container minha-delpi-ai-api):

  PYTHONPATH=/app python scripts/check_operational_action_readiness.py
  PYTHONPATH=/app python scripts/check_operational_action_readiness.py --json

Exit 0 = todas presentes; 1 = faltando; 2 = erro fatal.
"""

from __future__ import annotations

import argparse
import json
import sys

DEFAULT_PROVIDER_KEY = "api-delpi"

CRITICAL_ACTIONS: tuple[dict[str, str], ...] = (
    {
        "operationId": "get_production_schedule_today",
        "path": "/production/schedule/today",
        "label": "Programação de hoje",
    },
    {
        "operationId": "get_production_orders_open",
        "path": "/production/orders/open",
        "label": "Ordens abertas",
    },
    {
        "operationId": "get_production_consumption_top_items",
        "path": "/production/consumption/top-items",
        "label": "Top consumo",
    },
    {
        "operationId": "get_purchases_top_products",
        "path": "/purchases/top-products",
        "label": "Top compras",
    },
)


def _action_matches(spec: dict[str, str], action: dict) -> bool:
    operation_id = str(action.get("operationId") or "").strip()
    path = str(action.get("path") or "").strip()

    if operation_id == spec["operationId"]:
        return True

    return path.rstrip("/") == spec["path"].rstrip("/")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider-key",
        default=DEFAULT_PROVIDER_KEY,
        help="Provider OpenAPI (default: api-delpi).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Saída JSON em vez de texto.",
    )
    args = parser.parse_args()

    from app.composition.root_composer import create_application
    from app.infrastructure.persistence.postgres_external_action_repository import (
        PostgresExternalActionRepository,
    )

    app = create_application()

    with app.app_context():
        repository = PostgresExternalActionRepository()
        actions = repository.list_actions(provider_key=args.provider_key)

        missing: list[dict[str, str]] = []
        present: list[dict[str, str]] = []

        for spec in CRITICAL_ACTIONS:
            if any(_action_matches(spec, action) for action in actions):
                present.append(spec)
            else:
                missing.append(spec)

        report = {
            "providerKey": args.provider_key,
            "totalActions": len(actions),
            "criticalExpected": len(CRITICAL_ACTIONS),
            "criticalPresent": len(present),
            "missing": missing,
            "present": [
                {
                    "operationId": item["operationId"],
                    "path": item["path"],
                    "label": item["label"],
                }
                for item in present
            ],
        }

        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        elif missing:
            print(
                f"Faltam {len(missing)} action(s) crítica(s) em {args.provider_key}:",
                file=sys.stderr,
            )
            for item in missing:
                print(
                    f"  - {item['label']}: {item['operationId']} ({item['path']})",
                    file=sys.stderr,
                )
        else:
            print(
                f"OK: {len(present)}/{len(CRITICAL_ACTIONS)} actions críticas em "
                f"{args.provider_key} ({len(actions)} no catálogo)."
            )

        return 1 if missing else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
