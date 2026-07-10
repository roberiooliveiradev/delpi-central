#!/usr/bin/env python3
"""Ajusta Dockerfiles federados: vite build no Docker (sem tsc/plugin-ui COPY)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS = ROOT / "plugins"

PLUGIN_UI_COPY_BLOCK = re.compile(
    r"\n# Source plugin-ui — tsconfig paths no build; runtime = remote MF\.\nCOPY plugin-ui \./plugin-ui\n",
    re.MULTILINE,
)


def patch_dockerfile(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "Module Federation" not in text and "remote MF" not in text:
        return False

    original = text
    text = PLUGIN_UI_COPY_BLOCK.sub("\n", text)
    text = text.replace(
        "RUN npm run build",
        "# tsc roda no CI/local; Docker só bundla (MF externaliza @delpi/plugin-ui).\nRUN npx vite build",
        1,
    )
    if text == original:
        return False
    path.write_text(text, encoding="utf-8")
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
