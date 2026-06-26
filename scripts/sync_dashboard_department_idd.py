#!/usr/bin/env python3
"""Replica módulos de IDD departamental do dashboard-commercial para os demais dashboards."""

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
    ("api/departmentIddApi.ts", "api/departmentIddApi.ts"),
    ("hooks/useDepartmentIdd.ts", "hooks/useDepartmentIdd.ts"),
    ("components/DepartmentIddBadge.tsx", "components/DepartmentIddBadge.tsx"),
    ("utils/departmentIddFilters.ts", "utils/departmentIddFilters.ts"),
]


def main() -> None:
    for rel_src, rel_dst in FILES:
        content = (SOURCE / rel_src).read_text(encoding="utf-8")
        for plugin in TARGET_PLUGINS:
            target = ROOT / plugin / "src" / rel_dst
            target.parent.mkdir(parents=True, exist_ok=True)
            if plugin == "plugins/dashboard-lmps" and rel_dst == "api/departmentIddApi.ts":
                content = content.replace(
                    'from "../types/api"',
                    'from "../types/lmp"',
                )
            target.write_text(content, encoding="utf-8")
            print(f"OK {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
