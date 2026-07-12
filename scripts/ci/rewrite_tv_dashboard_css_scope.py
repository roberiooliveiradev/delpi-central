#!/usr/bin/env python3
"""One-shot: escopa seletores .td-/.tdp-/.delpi- em plugins/tv-dashboard/src/index.css.

Também:
  - padroniza breakpoints 720→768 e 820/900→1100
  - expande dark mode com tokens --td-*
  - troca superfícies hardcoded da shape library por var(--td-surface)/var(--td-text)

Uso:
  python3 scripts/ci/rewrite_tv_dashboard_css_scope.py
  python3 scripts/ci/rewrite_tv_dashboard_css_scope.py --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSS = ROOT / "plugins" / "tv-dashboard" / "src" / "index.css"

SCOPE = ".dashboard-tv-dashboard"
COMPONENT_RE = re.compile(r"(^|[^\w-])\.(td-|tdp-|delpi-)")
ROOT_DARK_PREFIX_RE = re.compile(
    r'^(:root\[data-theme=(["\'])dark\2\])\s+(.+)$',
    re.DOTALL,
)
AT_RULE_RE = re.compile(r"^@([a-zA-Z\-]+)")


def split_selector_list(selector: str) -> list[str]:
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


def scope_one_selector(sel: str) -> str:
    s = sel.strip()
    if not s:
        return s
    if SCOPE in s:
        return s
    if s.startswith("#root:has") and "dashboard-tv-dashboard" in s:
        return s

    dark = ROOT_DARK_PREFIX_RE.match(s)
    if dark:
        rest = dark.group(3).strip()
        if SCOPE in rest:
            return s
        if COMPONENT_RE.search(rest) or rest.startswith(SCOPE.lstrip(".")):
            return f"{dark.group(1)} {SCOPE} {rest}"
        return s

    if COMPONENT_RE.search(s):
        return f"{SCOPE} {s}"
    return s


def scope_selector_list(prelude: str) -> str:
    parts = split_selector_list(prelude)
    if not parts:
        return prelude
    scoped = [scope_one_selector(p) for p in parts]
    # Preserve multi-line formatting lightly: join with comma+space
    if "\n" in prelude:
        # keep each on own line if original was multi-line
        indent = ""
        m = re.match(r"^(\s*)", prelude)
        if m:
            # use indent of continuation lines if any
            pass
        lines = prelude.split("\n")
        cont_indent = "  "
        for line in lines[1:]:
            if line.strip():
                cont_indent = re.match(r"^(\s*)", line).group(1)  # type: ignore[union-attr]
                break
        if len(scoped) == len([p for p in parts]):
            out_lines = [scoped[0]]
            for p in scoped[1:]:
                out_lines.append(f"{cont_indent}{p}")
            # reconstruct with commas
            result = ",\n".join(out_lines)
            return result
    return ", ".join(scoped)


def rewrite_stylesheet(css: str) -> str:
    """Reescreve prelúdios de regras de estilo; preserva @keyframes e comentários."""
    out: list[str] = []
    i = 0
    n = len(css)

    while i < n:
        if css.startswith("/*", i):
            end = css.find("*/", i + 2)
            if end < 0:
                out.append(css[i:])
                break
            out.append(css[i : end + 2])
            i = end + 2
            continue

        # copy whitespace
        if css[i].isspace():
            j = i
            while j < n and css[j].isspace():
                j += 1
            out.append(css[i:j])
            i = j
            continue

        brace = css.find("{", i)
        semi = css.find(";", i)
        if brace < 0:
            out.append(css[i:])
            break
        # declaration-like without block before next brace? treat as at-rule ;
        if semi >= 0 and semi < brace:
            out.append(css[i : semi + 1])
            i = semi + 1
            continue

        prelude_raw = css[i:brace]
        prelude = prelude_raw.strip()
        # find matching }
        depth = 1
        j = brace + 1
        while j < n and depth:
            # skip strings roughly? CSS urls rarely have braces
            if css.startswith("/*", j):
                end = css.find("*/", j + 2)
                j = n if end < 0 else end + 2
                continue
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
            j += 1
        block_inner = css[brace + 1 : j - 1]
        close = "}"

        at_m = AT_RULE_RE.match(prelude)
        if at_m:
            name = at_m.group(1).lower()
            # keep @keyframes body untouched
            if name == "keyframes" or name.endswith("keyframes"):
                out.append(prelude_raw)
                out.append("{")
                out.append(block_inner)
                out.append(close)
                i = j
                continue
            # @media / @supports: rewrite nested stylesheet
            out.append(prelude_raw)
            out.append("{")
            out.append(rewrite_stylesheet(block_inner))
            out.append(close)
            i = j
            continue

        # style rule — scope prelude; leave declarations as-is
        leading_ws = prelude_raw[: len(prelude_raw) - len(prelude_raw.lstrip())]
        trailing_ws = prelude_raw[len(prelude_raw.rstrip()) :]
        new_prelude = scope_selector_list(prelude)
        out.append(leading_ws)
        out.append(new_prelude)
        out.append(trailing_ws)
        out.append("{")
        out.append(block_inner)
        out.append(close)
        i = j

    return "".join(out)


DARK_BLOCK = '''
:root[data-theme="dark"] .dashboard-tv-dashboard {
  --td-surface: color-mix(in srgb, var(--surface-2, #1b2030) 82%, black);
  --td-text: rgba(255, 255, 255, 0.88);
  --td-border: rgba(255, 255, 255, 0.1);
  --td-muted: rgba(255, 255, 255, 0.72);
  --td-stage-chrome: color-mix(in srgb, var(--td-text) 10%, var(--td-surface));
  --td-stage-preview: color-mix(in srgb, var(--td-text) 88%, var(--td-surface));
  --delpi-ui-surface: var(--td-surface);
  --delpi-ui-text: var(--td-text);
  --delpi-ui-border: var(--td-border);
  --delpi-ui-muted: var(--td-muted);
  --tdp-data-bg: var(--td-surface);
  --tdp-data-surface: color-mix(in srgb, var(--td-accent) 12%, var(--td-surface));
  --tdp-data-source-bg: color-mix(in srgb, var(--td-accent) 10%, var(--td-surface));
  --tdp-data-text: var(--td-text);
  --tdp-data-text-strong: var(--td-text);
  --tdp-data-muted: var(--td-muted);
  --tdp-data-border: var(--td-border);
}
'''.lstrip()

FILMSTRIP_DARK_RE = re.compile(
    r':root\[data-theme="dark"\]\s+\.dashboard-tv-dashboard\s+\.td-deck-filmstrip\s*\{[^}]*\}'
    r"|:root\[data-theme=\"dark\"\]\s+\.td-deck-filmstrip\s*\{[^}]*\}",
    re.MULTILINE,
)


def standardize_breakpoints(css: str) -> str:
    """Alinha breakpoints odd → 768 / 1100 (design system)."""
    # max-width media queries
    css = re.sub(
        r"@media\s*\(\s*max-width:\s*720px\s*\)",
        "@media (max-width: 768px)",
        css,
    )
    css = re.sub(
        r"@media\s*\(\s*max-width:\s*820px\s*\)",
        "@media (max-width: 1100px)",
        css,
    )
    css = re.sub(
        r"@media\s*\(\s*max-width:\s*900px\s*\)",
        "@media (max-width: 1100px)",
        css,
    )
    return css


def apply_token_surfaces(css: str) -> str:
    """Troca hardcoded óbvios da shape library / bordas por tokens."""
    replacements = [
        (
            r"(\.dashboard-tv-dashboard\s+\.td-shape-library\s*\{[^}]*?)background:\s*#ffffff\s*;",
            r"\1background: var(--td-surface);",
        ),
        (
            r"(\.dashboard-tv-dashboard\s+\.td-shape-library\s*\{[^}]*?)color:\s*#111111\s*;",
            r"\1color: var(--td-text);",
        ),
        (
            r"(\.dashboard-tv-dashboard\s+\.td-shape-library__section\s*\+\s*\.td-shape-library__section\s*\{[^}]*?)border-top:\s*1px\s+solid\s+#e5e7eb\s*;",
            r"\1border-top: 1px solid var(--td-border);",
        ),
        (
            r"(\.dashboard-tv-dashboard\s+\.td-shape-library__title\s*\{[^}]*?)color:\s*#111827\s*;",
            r"\1color: var(--td-text);",
        ),
        # thumb stage: canvas do slide é tipicamente claro — usar surface token
        (
            r"(\.dashboard-tv-dashboard\s+\.td-slide-thumb__stage\s*\{[^}]*?)background:\s*#ffffff\s*;",
            r"\1background: var(--td-surface);",
        ),
    ]
    for pat, repl in replacements:
        css = re.sub(pat, repl, css, count=1, flags=re.DOTALL)
    return css


def expand_dark_mode(css: str) -> str:
    css = FILMSTRIP_DARK_RE.sub("", css)
    # Avoid duplicating if already present
    marker = ':root[data-theme="dark"] .dashboard-tv-dashboard {'
    if marker in css and "--td-surface: color-mix" in css:
        return css
    # Insert after the opening token block (first .dashboard-tv-dashboard { ... })
    # Prefer right after first closing of root token block.
    m = re.search(
        r"\.dashboard-tv-dashboard\s*\{[^{}]*--td-accent:[^{}]*\}",
        css,
        re.DOTALL,
    )
    if m:
        insert_at = m.end()
        return css[:insert_at] + "\n\n" + DARK_BLOCK + css[insert_at:]
    return DARK_BLOCK + "\n" + css


def transform(css: str) -> str:
    css = rewrite_stylesheet(css)
    css = standardize_breakpoints(css)
    css = expand_dark_mode(css)
    css = apply_token_surfaces(css)
    # tidy double blank lines from filmstrip removal
    css = re.sub(r"\n{3,}", "\n\n", css)
    return css


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_CSS)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    original = args.file.read_text(encoding="utf-8")
    updated = transform(original)
    if args.dry_run:
        print(f"dry-run: {len(original)} → {len(updated)} bytes")
        return 0
    args.file.write_text(updated, encoding="utf-8")
    print(f"Wrote {args.file} ({len(original)} → {len(updated)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
