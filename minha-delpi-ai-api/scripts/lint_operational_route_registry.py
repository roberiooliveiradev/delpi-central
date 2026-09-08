#!/usr/bin/env python3
"""Lint de integridade para acoplamentos operacionais ainda detectáveis pelo CI.

Este script não define arquitetura de routing. A orientação canônica para qualquer
violação é OpenAPI + Action Catalog + retrieval/planner/validator genéricos.
"""

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


_OPENAPI_FIRST_GUIDANCE = (
    "path/provider específico hardcoded no motor genérico — use OpenAPI importado + "
    "Action Catalog/index + retrieval/planner/validator; não crie catálogo técnico por endpoint"
)


def _normalize_architecture_guidance(message: str) -> str:
    """Impede que diagnostics internos antigos recomendem uma arquitetura não canônica."""
    text = str(message)
    if "path api-delpi hardcoded" in text:
        prefix = text.split("path api-delpi hardcoded", 1)[0]
        return f"{prefix}{_OPENAPI_FIRST_GUIDANCE}"
    return text


def _normalize_report_guidance(report: object) -> None:
    errors = getattr(report, "errors", None)
    warnings = getattr(report, "warnings", None)
    if isinstance(errors, list):
        errors[:] = [_normalize_architecture_guidance(item) for item in errors]
    if isinstance(warnings, list):
        warnings[:] = [_normalize_architecture_guidance(item) for item in warnings]


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
    _normalize_report_guidance(report)

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
