#!/usr/bin/env python3
"""Inventário e gate da dívida de seletores `.delpi-ui-*` nos MFEs.

CSS canônico dos componentes fica só em `plugins/plugin-ui/src/styles/**`.
MFE pode mapear tokens `--delpi-ui-*` e layout de página — nunca seletores
que reestilizem o chrome do kit.

Dois usos:

  python3 scripts/ci/audit_mfe_plugin_ui_css.py
      Inventário. Exit 0. `FULL_TREE_DEBT = OPEN` enquanto houver ocorrência.
      Não declara o monorepo conforme.

  python3 scripts/ci/audit_mfe_plugin_ui_css.py --check
      Mesmo inventário e exit 1 se a dívida for maior que zero.
      Programa de quitação. Não é o gate de um release sem CSS novo.

O gate que bloqueia override novo no diff é `MFE_PLUGIN_UI_OVERRIDE`
em `audit_platform_guardrails.py`.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGINS_DIR = ROOT / "plugins"

# Pacote canônico do kit — único lugar permitido para `.delpi-ui-*` em CSS.
EXCLUDED_PLUGINS = frozenset({"plugin-ui"})

# `.delpi-ui-` em seletor CSS (não em comentários — strip antes).
DELPI_UI_CLASS_RE = re.compile(r"\.delpi-ui-[\w-]*")
FAMILY_RE = re.compile(r"\.delpi-ui-([A-Za-z0-9_-]+)")


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


def finding_key(item: Finding) -> tuple[str, str]:
    return (item.rel_path, item.snippet)


def family_of(snippet: str) -> str:
    match = FAMILY_RE.search(snippet)
    if not match:
        return "unclassified"
    return match.group(1).split("--", 1)[0]


def debt_label(total: int) -> str:
    if total > 0:
        return "OPEN"
    return "CLEAR"


def render_report(
    findings: list[Finding],
    *,
    added: list[Finding] | None = None,
    removed: list[Finding] | None = None,
) -> str:
    total = len(findings)
    by_plugin = Counter(item.plugin for item in findings)
    by_family = Counter(family_of(item.snippet) for item in findings)
    lines = [
        f"FULL_TREE_DEBT = {debt_label(total)}",
        f"TOTAL = {total}",
        "BY_PLUGIN:",
    ]
    for plugin, count in by_plugin.most_common():
        lines.append(f"  {plugin} {count}")
    lines.append("BY_FAMILY:")
    for family, count in by_family.most_common():
        lines.append(f"  {family} {count}")
    if added is not None and removed is not None:
        lines.append(f"NEW = {len(added)}")
        lines.append(f"REMOVED = {len(removed)}")
        for item in added:
            lines.append(f"  + {item.rel_path}:{item.line}: {item.snippet}")
        for item in removed:
            lines.append(f"  - {item.rel_path}:{item.line}: {item.snippet}")
    lines.append(f"OWNERS = {len(by_plugin)}")
    if total:
        lines.append(
            "A dívida histórica permanece aberta. O gate de regressão é "
            "MFE_PLUGIN_UI_OVERRIDE; --check deste inventário só falha o programa de quitação."
        )
    return "\n".join(lines)


def git_show(rev: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        cwd=ROOT,
        text=True,
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def findings_at_revision(rev: str) -> list[Finding]:
    listing = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", rev, "plugins"],
        cwd=ROOT,
        text=True,
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if listing.returncode != 0:
        return []
    findings: list[Finding] = []
    for rel in listing.stdout.splitlines():
        normalized = rel.replace("\\", "/")
        parts = normalized.split("/")
        if len(parts) < 3 or parts[0] != "plugins" or not normalized.endswith(".css"):
            continue
        plugin = parts[1]
        if plugin in EXCLUDED_PLUGINS:
            continue
        text = git_show(rev, normalized)
        if text is None:
            continue
        stripped = _strip_css_comments(text)
        for line_no, line in enumerate(stripped.splitlines(), start=1):
            if DELPI_UI_CLASS_RE.search(line):
                findings.append(
                    Finding(plugin, normalized, line_no, line.strip()[:160])
                )
    return findings


def diff_findings(
    base_findings: list[Finding],
    head_findings: list[Finding],
) -> tuple[list[Finding], list[Finding]]:
    base_keys = {finding_key(item) for item in base_findings}
    head_keys = {finding_key(item) for item in head_findings}
    added = [item for item in head_findings if finding_key(item) not in base_keys]
    removed = [item for item in base_findings if finding_key(item) not in head_keys]
    return added, removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 se a dívida full-tree for maior que zero",
    )
    parser.add_argument(
        "--base",
        default=None,
        help="Revisão git para calcular violações novas e removidas",
    )
    args = parser.parse_args()

    all_findings: list[Finding] = []
    for plugin in plugin_dirs():
        all_findings.extend(scan_plugin(plugin))

    added: list[Finding] | None = None
    removed: list[Finding] | None = None
    if args.base:
        added, removed = diff_findings(findings_at_revision(args.base), all_findings)

    print(render_report(all_findings, added=added, removed=removed))

    if args.check and all_findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
