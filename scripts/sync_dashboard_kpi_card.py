#!/usr/bin/env python3
"""Replica KpiCard do dashboard-commercial para os demais dashboards (com prefixo CSS)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugins/dashboard-commercial/src/components/KpiCard.tsx"

TARGET_PLUGINS = {
    "plugins/dashboard-hr": "dh",
    "plugins/dashboard-production": "dp",
    "plugins/dashboard-financial": "ds",
    "plugins/dashboard-supplies": "ds",
    "plugins/dashboard-engineering": "ds",
    "plugins/dashboard-quality": "dq",
    "plugins/dashboard-lmps": "dl",
}

PREFIX_REPLACEMENTS = ("dc-", "PREFIX-")


def main() -> None:
    template = SOURCE.read_text(encoding="utf-8")
    for plugin, prefix in TARGET_PLUGINS.items():
        content = template.replace("dc-", f"{prefix}-")
        target = ROOT / plugin / "src/components/KpiCard.tsx"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"OK {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
