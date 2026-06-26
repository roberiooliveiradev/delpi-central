#!/usr/bin/env python3
"""Copia utilitários de competência do dashboard-commercial para os demais dashboards."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugins/dashboard-commercial/src"

TARGET_PLUGINS = [
    "plugins/dashboard-hr",
    "plugins/dashboard-production",
    "plugins/dashboard-financial",
    "plugins/dashboard-supplies",
    "plugins/dashboard-engineering",
    "plugins/dashboard-quality",
    "plugins/dashboard-lmps",
]

FILES = [
    ("utils/competenceFilters.ts", "utils/competenceFilters.ts"),
    ("hooks/useCompetenceLinkedDates.ts", "hooks/useCompetenceLinkedDates.ts"),
]


def main() -> None:
    for rel_src, rel_dst in FILES:
        content = (SOURCE / rel_src).read_text(encoding="utf-8")
        for plugin in TARGET_PLUGINS:
            target = ROOT / plugin / "src" / rel_dst
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"OK {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
