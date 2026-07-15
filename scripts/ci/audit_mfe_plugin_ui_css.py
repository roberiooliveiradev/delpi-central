#!/usr/bin/env python3
"""Gate: MFEs não podem estilizar classes `.delpi-ui-*` do kit (Fase 7).

CSS canônico dos componentes fica só em `plugins/plugin-ui/src/styles/**`.
MFE pode mapear tokens `--delpi-ui-*` e layout de página — nunca seletores
que reestilizem o chrome do kit.

Uso:
  python3 scripts/ci/audit_mfe_plugin_ui_css.py
  python3 scripts/ci/audit_mfe_plugin_ui_css.py --check

Exit 0 = OK; exit 1 = violações (com --check).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS_DIR = ROOT / "plugins"

# Pacote canônico do kit — único lugar permitido para `.delpi-ui-*` em CSS.
EXCLUDED_PLUGINS = frozenset({"plugin-ui"})

# `.delpi-ui-` em seletor CSS (não em comentários — strip antes).
DELPI_UI_CLASS_RE = re.compile(r"\.delpi-ui-[\w-]*")


@dataclass(frozen=True)
class Finding:
    plugin: str
    rel_path: str
    line: int
    snippet: str


def _strip_css_comments(css: str) -> str:
    out: list[str] = []
    i = 0
    n = len(css)
    while i < n:
        if css.startswith("/*", i):
            end = css.find("*/", i + 2)
            if end < 0:
                chunk = css[i:]
                out.append("\n" * chunk.count("\n"))
                break
            chunk = css[i : end + 2]
            out.append("\n" * chunk.count("\n"))
            i = end + 2
            continue
        out.append(css[i])
        i += 1
    return "".join(out)


def plugin_dirs() -> list[Path]:
    dirs: list[Path] = []
    for path in sorted(PLUGINS_DIR.iterdir()):
        if not path.is_dir() or path.name in EXCLUDED_PLUGINS:
            continue
        if (path / "package.json").is_file():
            dirs.append(path)
    return dirs


def scan_plugin(plugin_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    src = plugin_dir / "src"
    if not src.is_dir():
        return findings
    for css_path in sorted(src.rglob("*.css")):
        raw = css_path.read_text(encoding="utf-8", errors="ignore")
        text = _strip_css_comments(raw)
        rel = css_path.relative_to(ROOT).as_posix()
        for line_no, line in enumerate(text.splitlines(), start=1):
            if DELPI_UI_CLASS_RE.search(line):
                findings.append(
                    Finding(
                        plugin=plugin_dir.name,
                        rel_path=rel,
                        line=line_no,
                        snippet=line.strip()[:160],
                    )
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 se houver seletores .delpi-ui-* em CSS de MFE",
    )
    args = parser.parse_args()

    all_findings: list[Finding] = []
    for plugin in plugin_dirs():
        all_findings.extend(scan_plugin(plugin))

    if not all_findings:
        print("[OK] Nenhum seletor .delpi-ui-* em CSS de MFEs (fora de plugin-ui).")
        return 0

    print(
        f"[FAIL] {len(all_findings)} ocorrência(s) de seletor .delpi-ui-* em CSS de MFE:"
    )
    for item in all_findings:
        print(f"  - {item.rel_path}:{item.line}: {item.snippet}")

    print(
        "\nCorrija no kit (plugins/plugin-ui/src/styles/) ou use tokens --delpi-ui-* / "
        "layout de página. Ver plugins-reusable-components.mdc § CSS do kit."
    )

    if args.check:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
