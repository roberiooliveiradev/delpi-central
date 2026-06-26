#!/usr/bin/env python3
"""Replica operationalUnitLabels.ts do commercial para os demais dashboards."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugins/dashboard-commercial/src/utils/operationalUnitLabels.ts"

TARGET_PLUGINS = [
    "plugins/dashboard-hr",
    "plugins/dashboard-production",
    "plugins/dashboard-financial",
    "plugins/dashboard-supplies",
    "plugins/dashboard-engineering",
    "plugins/dashboard-quality",
    "plugins/dashboard-lmps",
]


def main() -> None:
    content = SOURCE.read_text(encoding="utf-8")
    for plugin in TARGET_PLUGINS:
        target = ROOT / plugin / "src/utils/operationalUnitLabels.ts"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"OK {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
