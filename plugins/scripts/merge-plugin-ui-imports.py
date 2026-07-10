#!/usr/bin/env python3
"""Mescla imports duplicados de @delpi/plugin-ui/index no mesmo arquivo (rollup MF)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

IMPORT_RE = re.compile(
    r"^import\s+(type\s+)?(\{[^}]+\}|\*\s+as\s+\w+)\s+from\s+['\"]@delpi/plugin-ui/index['\"];\s*\n",
    re.MULTILINE,
)
EXPORT_TYPE_RE = re.compile(
    r"^export\s+type\s+\{([^}]+)\}\s+from\s+['\"]@delpi/plugin-ui/index['\"];\s*\n",
    re.MULTILINE,
)
EXPORT_VALUE_RE = re.compile(
    r"^export\s+\{([^}]+)\}\s+from\s+['\"]@delpi/plugin-ui/index['\"];\s*\n",
    re.MULTILINE,
)


def parse_specifiers(block: str) -> tuple[list[str], list[str]]:
    """Retorna (value_specs, type_specs)."""
    values: list[str] = []
    types: list[str] = []
    for part in block.strip("{} \n").split(","):
        item = part.strip()
        if not item:
            continue
        if item.startswith("type "):
            types.append(item.removeprefix("type ").strip())
        else:
            values.append(item)
    return values, types


def merge_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    value_specs: list[str] = []
    type_specs: list[str] = []

    for match in IMPORT_RE.finditer(text):
        is_type_only = bool(match.group(1))
        block = match.group(2)
        vals, types = parse_specifiers(block)
        if is_type_only:
            type_specs.extend(vals or types)
        else:
            value_specs.extend(vals)
            type_specs.extend(types)

    for match in EXPORT_TYPE_RE.finditer(text):
        _, types = parse_specifiers("{" + match.group(1) + "}")
        type_specs.extend(types)

    for match in EXPORT_VALUE_RE.finditer(text):
        vals, types = parse_specifiers("{" + match.group(1) + "}")
        value_specs.extend(vals)
        type_specs.extend(types)

    imports = list(IMPORT_RE.finditer(text))
    exports = list(EXPORT_TYPE_RE.finditer(text)) + list(EXPORT_VALUE_RE.finditer(text))
    if len(imports) + len(exports) <= 1:
        return False

    # Remove all plugin-ui import/export lines
    cleaned = IMPORT_RE.sub("", text)
    cleaned = EXPORT_TYPE_RE.sub("", cleaned)
    cleaned = EXPORT_VALUE_RE.sub("", cleaned)

    def uniq(items: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in items:
            key = item.split(" as ")[0].strip()
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    value_specs = uniq(value_specs)
    type_specs = uniq(type_specs)

    lines: list[str] = []
    if value_specs or type_specs:
        merged_types = [f"type {t}" for t in type_specs]
        all_specs = value_specs + merged_types
        lines.append(f'import {{ {", ".join(all_specs)} }} from "@delpi/plugin-ui/index";\n')

    # Re-inject merged import at top of file (after optional leading comments/shebang)
    body = cleaned.lstrip("\n")
    leading = cleaned[: len(cleaned) - len(body)]
    new_text = leading + "".join(lines) + body
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main(argv: list[str]) -> int:
    roots = [Path(p) for p in argv[1:]] if len(argv) > 1 else [Path(__file__).resolve().parents[1]]
    changed = 0
    for root in roots:
        base = root if root.is_dir() else root.parent
        for path in base.rglob("*"):
            if path.suffix not in {".ts", ".tsx"}:
                continue
            if merge_file(path):
                print(f"merged {path.relative_to(base)}")
                changed += 1
    print(f"[OK] {changed} arquivo(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
