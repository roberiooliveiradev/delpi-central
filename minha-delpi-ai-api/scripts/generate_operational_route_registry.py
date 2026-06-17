#!/usr/bin/env python3
"""Gera entradas autoTierCRoutes a partir do OpenAPI baseline — DOCIE Fase 20."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_coverage_service import (
    ChatPresentationCoverageService,
)
from app.domain.services.operational_route_registry_generator_service import (
    OperationalRouteRegistryGeneratorService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=ChatPresentationCoverageService.default_openapi_baseline_path(),
        help="Caminho para openapi_baseline.json",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=OperationalRouteRegistryGeneratorService.default_registry_path(),
        help="Caminho para operational_route_registry.json",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Grava autoTierCRoutes no registry",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Falha se autoTierCRoutes divergir do gerador ou tier C descoberto",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Imprime relatório JSON",
    )
    args = parser.parse_args()

    configure_domain_infrastructure_ports()

    generated = OperationalRouteRegistryGeneratorService.generate_routes(
        openapi_baseline_path=args.baseline,
    )
    coverage = OperationalRouteRegistryGeneratorService.validate_tier_c_coverage(
        openapi_baseline_path=args.baseline,
    )
    get_coverage = OperationalRouteRegistryGeneratorService.validate_get_auto_coverage(
        openapi_baseline_path=args.baseline,
    )
    stored = OperationalRouteRegistryService.auto_tier_c_routes()
    synced, drift_errors = OperationalRouteRegistryGeneratorService.compare_generated_to_stored(
        stored,
        generated,
    )

    report = {
        "generatedCount": len(generated),
        "storedCount": len(stored),
        "coverageOk": coverage.ok,
        "coverageGaps": list(coverage.gaps),
        "getCoverageOk": get_coverage.ok,
        "getCoverageGaps": list(get_coverage.gaps),
        "syncedWithGenerator": synced,
        "driftErrors": drift_errors,
    }

    if args.write:
        coverage = OperationalRouteRegistryGeneratorService.write_auto_tier_c_section(
            registry_path=args.registry,
            openapi_baseline_path=args.baseline,
        )
        get_coverage = OperationalRouteRegistryGeneratorService.validate_get_auto_coverage(
            openapi_baseline_path=args.baseline,
        )
        stored = OperationalRouteRegistryService.auto_tier_c_routes()
        synced = True
        drift_errors = []
        report["storedCount"] = len(stored)
        report["coverageOk"] = coverage.ok
        report["coverageGaps"] = list(coverage.gaps)
        report["getCoverageOk"] = get_coverage.ok
        report["getCoverageGaps"] = list(get_coverage.gaps)
        report["syncedWithGenerator"] = True
        report["driftErrors"] = []

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            "DOCIE Fase 20 — autoTierCRoutes\n"
            f"  geradas: {report['generatedCount']}\n"
            f"  no registry: {report['storedCount']}\n"
            f"  cobertura tier C: {'OK' if report['coverageOk'] else 'FALHA'}\n"
            f"  cobertura GET auto: {'OK' if report.get('getCoverageOk') else 'FALHA'}\n"
            f"  sync gerador: {'OK' if report['syncedWithGenerator'] else 'FALHA'}"
        )

        for item in report.get("getCoverageGaps") or report["coverageGaps"][:10]:
            print(f"  - gap: {item}")

        for item in report["driftErrors"][:10]:
            print(f"  - drift: {item}")

    if args.check and (not get_coverage.ok or not synced):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
