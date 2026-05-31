#!/usr/bin/env python3
"""CI/local — valida features_catalog.json e assistant_release_notes.json."""

from __future__ import annotations

import sys

from app.application.services.assistant_capabilities_catalog_validator import (
    AssistantCapabilitiesCatalogValidator,
)


def main() -> int:
    errors = AssistantCapabilitiesCatalogValidator.validate()

    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)

        return 1

    print("OK assistant capabilities catalog validado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
