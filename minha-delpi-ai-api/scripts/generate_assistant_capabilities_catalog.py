#!/usr/bin/env python3
"""Sincroniza features_catalog.json com actions/skills registrados (autoajuda Fase 3)."""

from __future__ import annotations

import argparse
import sys

from app.application.services.assistant_capabilities_catalog_generator import (
    AssistantCapabilitiesCatalogGenerator,
)
from app.application.services.assistant_capabilities_catalog_validator import (
    AssistantCapabilitiesCatalogValidator,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Falha se o catálogo em disco divergir do gerado (campos sincronizados).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Grava features_catalog.json após validação.",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Não consulta actions no banco (só skills + regras de path).",
    )
    args = parser.parse_args()

    if not args.check and not args.write:
        parser.print_help()
        return 2

    actions: list[dict] = []

    if not args.no_db:
        try:
            actions = AssistantCapabilitiesCatalogGenerator.load_actions_from_database()
        except Exception as exc:
            print(f"WARN actions DB indisponível: {exc}", file=sys.stderr)

    on_disk = AssistantCapabilitiesCatalogGenerator.load_catalog()
    generated = AssistantCapabilitiesCatalogGenerator.generate(actions=actions)

    if args.check:
        drift = AssistantCapabilitiesCatalogGenerator.drift_report(
            on_disk=on_disk,
            generated=generated,
        )

        if drift:
            for line in drift:
                print(f"FAIL {line}", file=sys.stderr)

            unmapped = (generated.get("generation") or {}).get("unmappedActionPaths") or []

            if unmapped:
                print(
                    f"INFO paths sem regra ({len(unmapped)}): {', '.join(unmapped[:8])}",
                    file=sys.stderr,
                )

            return 1

        print("OK catálogo sincronizado com actions/skills.")
        return 0

    path = AssistantCapabilitiesCatalogGenerator.write_catalog(generated)
    errors = AssistantCapabilitiesCatalogValidator.validate()

    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)

        return 1

    print(f"OK catálogo gravado em {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
