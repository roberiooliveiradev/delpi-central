#!/usr/bin/env python3
"""Lint CI DOCIE — termos só em JSON + integridade do operational_route_registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.operational_route_registry_lint_service import (
    OperationalRouteRegistryLintService,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Retorna código 1 se houver violações",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime relatório JSON",
    )
    args = parser.parse_args()

    configure_domain_infrastructure_ports()
    report = OperationalRouteRegistryLintService.run(package_root=ROOT)

    if args.json:
        print(
            json.dumps(
                {
                    "ok": report.ok,
                    "errors": report.errors,
                    "warnings": report.warnings,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(OperationalRouteRegistryLintService.format_report(report))

    if args.check and not report.ok:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
