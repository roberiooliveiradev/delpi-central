#!/usr/bin/env python3
"""Gate: CSS do TV Dashboard deve ficar escopado em .dashboard-tv-dashboard.

Uso:
  python3 scripts/ci/check_tv_dashboard_css_scope.py
  python3 scripts/ci/check_tv_dashboard_css_scope.py --check

Exit 0 = OK; exit 1 = violações (com --check) ou arquivo ausente.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSS = ROOT / "plugins" / "tv-dashboard" / "src" / "index.css"

SCOPE_CLASS = ".dashboard-tv-dashboard"
COMPONENT_CLASS_RE = re.compile(r"(^|[^\w-])\.(td-|tdp-|delpi-)")
BARE_BODY_RE = re.compile(r"(^|[,\{]\s*)body\s*\{", re.MULTILINE)
# :root { sem data-theme — permite :root[data-theme=...]
BARE_ROOT_RE = re.compile(r"(^|[,\{]\s*):root\s*\{", re.MULTILINE)
AT_RULE_NAME_RE = re.compile(r"^@([a-zA-Z\-]+)")


@dataclass(frozen=True)
class Violation:
    line: int
    kind: str
    detail: str


def _strip_comments(css: str) -> str:
    """Remove /* ... */ preservando quebras de linha para números estáveis."""
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


def split_selector_list(selector: str) -> list[str]:
    """Divide lista de seletores por vírgula fora de parênteses/colchetes."""
    parts: list[str] = []
    buf: list[str] = []
    depth_paren = 0
    depth_bracket = 0
    for ch in selector:
        if ch == "(":
            depth_paren += 1
        elif ch == ")":
            depth_paren = max(0, depth_paren - 1)
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]":
            depth_bracket = max(0, depth_bracket - 1)
        if ch == "," and depth_paren == 0 and depth_bracket == 0:
            parts.append("".join(buf).strip())
            buf = []
            continue
        buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def selector_targets_component(selector: str) -> bool:
    return bool(COMPONENT_CLASS_RE.search(selector))


def selector_is_scoped(selector: str) -> bool:
    """True se o seletor está sob .dashboard-tv-dashboard ou #root:has(...)."""
    s = selector.strip()
    if not s:
        return True
    if SCOPE_CLASS in s:
        return True
    if s.startswith("#root:has") and "dashboard-tv-dashboard" in s:
        return True
    return False


def iter_top_level_rules(css: str) -> list[tuple[int, str, str]]:
    """Retorna (line_no, prelude, kind) para regras em profundidade relevante.

    kind: 'style' | 'at-keyframes' | 'at-other'
    Ignora conteúdo interno de @keyframes (percentuais / from / to).
    Inclui regras dentro de @media / @supports.
    """
    text = _strip_comments(css)
    rules: list[tuple[int, str, str]] = []
    i = 0
    n = len(text)
    # stack of at-rule names currently open (only those that wrap style rules)
    at_stack: list[str] = []

    def line_at(pos: int) -> int:
        return text.count("\n", 0, pos) + 1

    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break

        # find next { or ;
        start = i
        brace = text.find("{", i)
        semi = text.find(";", i)
        if brace < 0 and semi < 0:
            break
        if semi >= 0 and (brace < 0 or semi < brace):
            # at-rule without block (e.g. @import) or stray
            i = semi + 1
            continue
        assert brace >= 0
        prelude = text[start:brace].strip()
        # find matching close
        depth = 1
        j = brace + 1
        while j < n and depth:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        block_end = j
        at_m = AT_RULE_NAME_RE.match(prelude)
        if at_m:
            name = at_m.group(1).lower()
            if name == "keyframes" or name.endswith("keyframes"):
                rules.append((line_at(start), prelude, "at-keyframes"))
                i = block_end
                continue
            # @media / @supports / etc.: recurse into block as nested stylesheet
            rules.append((line_at(start), prelude, "at-other"))
            inner = text[brace + 1 : block_end - 1]
            # offset line numbers for nested: re-scan with line offset
            nested = iter_top_level_rules(inner)
            base_line = line_at(brace + 1) - 1
            for ln, pre, kind in nested:
                # ln is 1-based within inner; adjust by counting newlines before brace+1
                # Actually iter uses its own text — line numbers are relative to inner.
                # Recompute absolute: find prelude in inner is hard; use approximate.
                rules.append((base_line + ln, pre, kind))
            i = block_end
            continue

        # style rule
        if at_stack and at_stack[-1] in {"keyframes"}:
            i = block_end
            continue
        rules.append((line_at(start), prelude, "style"))
        i = block_end

    return rules


def check_css(css: str, path: Path | None = None) -> list[Violation]:
    violations: list[Violation] = []
    label = str(path) if path else "<css>"

    if BARE_BODY_RE.search(css):
        m = BARE_BODY_RE.search(css)
        line = css.count("\n", 0, m.start()) + 1 if m else 1
        violations.append(
            Violation(line, "bare-body", f"{label}: seletor `body {{` proibido (vaza no host)")
        )

    if BARE_ROOT_RE.search(css):
        m = BARE_ROOT_RE.search(css)
        line = css.count("\n", 0, m.start()) + 1 if m else 1
        violations.append(
            Violation(
                line,
                "bare-root",
                f"{label}: `:root {{` sem data-theme proibido (use .dashboard-tv-dashboard ou :root[data-theme])",
            )
        )

    for line, prelude, kind in iter_top_level_rules(css):
        if kind != "style":
            continue
        for part in split_selector_list(prelude):
            if not selector_targets_component(part):
                continue
            if selector_is_scoped(part):
                continue
            violations.append(
                Violation(
                    line,
                    "unscoped-component",
                    f"{label}:{line}: seletor sem escopo `{part}`",
                )
            )
    return violations


def format_report(violations: list[Violation]) -> str:
    if not violations:
        return "OK: TV Dashboard CSS está escopado em .dashboard-tv-dashboard."
    lines = [f"FAIL: {len(violations)} violação(ões) de escopo CSS no TV Dashboard:"]
    for v in violations[:50]:
        lines.append(f"  [{v.kind}] L{v.line}: {v.detail}")
    if len(violations) > 50:
        lines.append(f"  ... e mais {len(violations) - 50}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 se houver violações (modo CI).",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_CSS,
        help="Caminho do index.css (default: plugins/tv-dashboard/src/index.css).",
    )
    args = parser.parse_args(argv)

    css_path: Path = args.file
    if not css_path.is_file():
        print(f"FAIL: arquivo não encontrado: {css_path}", file=sys.stderr)
        return 1

    css = css_path.read_text(encoding="utf-8")
    violations = check_css(css, css_path)
    report = format_report(violations)
    print(report)
    if violations and args.check:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
