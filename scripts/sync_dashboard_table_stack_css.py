#!/usr/bin/env python3
"""Reaplica o CSS da stack de tabelas (padrão dashboard-commercial) nos plugins departamentais."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMERCIAL_CSS = ROOT / "plugins/dashboard-commercial/src/index.css"

# Trechos canônicos do commercial (1-based, inclusive).
COMMERCIAL_LINE_RANGES: list[tuple[int, int]] = [
    (179, 182),
    (194, 215),
    (217, 224),
    (398, 400),
    (407, 424),
    (508, 603),
    (1490, 1620),
    (1912, 2040),
    (2534, 2540),
    (2681, 2693),
]

RESPONSIVE_LINE_RANGES: list[tuple[int, int]] = [(2251, 2258)]

PLUGINS: list[tuple[str, str, str]] = [
    ("plugins/dashboard-hr/src/index.css", "dashboard-hr", "dh"),
    ("plugins/dashboard-production/src/index.css", "dashboard-production", "dp"),
    ("plugins/dashboard-financial/src/index.css", "dashboard-financial", "ds"),
    ("plugins/dashboard-supplies/src/index.css", "dashboard-supplies", "ds"),
    ("plugins/dashboard-engineering/src/index.css", "dashboard-engineering", "ds"),
    ("plugins/dashboard-quality/src/index.css", "dashboard-quality", "dq"),
]

MARKER = "/* Table stack (padrão commercial"


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def slice_lines(lines: list[str], start: int, end: int) -> str:
    return "".join(lines[start - 1 : end])


def transform_css(css: str, dashboard_class: str, prefix: str) -> str:
    css = css.replace(".dashboard-commercial", f".{dashboard_class}")
    css = css.replace(".dc-", f".{prefix}-")
    css = css.replace("--dc-", f"--{prefix}-")
    return css


def extract_commercial_stack() -> str:
    commercial_lines = read_lines(COMMERCIAL_CSS)
    chunks: list[str] = []
    for start, end in COMMERCIAL_LINE_RANGES:
        chunks.append(slice_lines(commercial_lines, start, end))
    responsive = "".join(
        slice_lines(commercial_lines, start, end) for start, end in RESPONSIVE_LINE_RANGES
    )
    chunks.append(
        "@media (max-width: 768px) {\n"
        + responsive
        + "}\n"
    )
    return "".join(chunks)


def strip_corrupted_append(content: str) -> str:
    idx = content.find(MARKER)
    if idx == -1:
        return content
    return content[:idx].rstrip() + "\n"


def remove_legacy_pagination(content: str, dashboard_class: str, prefix: str) -> str:
    """Remove paginação legada (layout horizontal com __actions) que conflita com o commercial."""
    patterns = [
        rf"\.{re.escape(dashboard_class)} \.{prefix}-pagination \{{[^}}]*\}}\n?",
        rf"\.{re.escape(dashboard_class)} \.{prefix}-pagination__info \{{[^}}]*\}}\n?",
        rf"\.{re.escape(dashboard_class)} \.{prefix}-pagination__actions \{{[^}}]*\}}\n?",
    ]
    for pattern in patterns:
        content = re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)
    return content


def build_stack_block(dashboard_class: str, prefix: str, body: str) -> str:
    transformed = transform_css(body, dashboard_class, prefix)
    return (
        f"\n{MARKER} — {prefix}) */\n"
        f"{transformed}\n"
    )


def sync_plugin(rel_path: str, dashboard_class: str, prefix: str, stack_body: str) -> None:
    path = ROOT / rel_path
    content = path.read_text(encoding="utf-8")
    content = strip_corrupted_append(content)
    content = remove_legacy_pagination(content, dashboard_class, prefix)
    content = content.rstrip() + build_stack_block(dashboard_class, prefix, stack_body)
    path.write_text(content + "\n", encoding="utf-8")
    print(f"OK {rel_path}")


def main() -> None:
    stack_body = extract_commercial_stack()
    for rel_path, dashboard_class, prefix in PLUGINS:
        sync_plugin(rel_path, dashboard_class, prefix, stack_body)
    print("Concluído.")


if __name__ == "__main__":
    main()
