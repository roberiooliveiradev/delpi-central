#!/usr/bin/env python3
"""Adiciona COPY plugin-ui nos Dockerfiles de MFEs federados (tsconfig paths no build)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS = ROOT / "plugins"

SNIPPET = "# Source plugin-ui — tsconfig paths no build; runtime = remote MF.\nCOPY plugin-ui ./plugin-ui\n"
MARKER = "COPY plugin-ui ./plugin-ui"


def patch_dockerfile(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return False
    if "Module Federation" not in text and "remote MF" not in text:
        return False
    if "COPY vite ./vite" not in text:
        return False
    updated = text.replace("COPY vite ./vite", SNIPPET + "COPY vite ./vite", 1)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    changed = 0
    for dockerfile in sorted(PLUGINS.glob("*/Dockerfile")):
        if dockerfile.parent.name == "plugin-ui":
            continue
        if patch_dockerfile(dockerfile):
            print(f"patched {dockerfile.relative_to(PLUGINS)}")
            changed += 1
    print(f"[OK] {changed} Dockerfile(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
