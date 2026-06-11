"""Gate R22 — chamadas KV nos presenters devem repassar `path=` para discovery R16."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRESENTERS_DIR = ROOT / "app" / "domain" / "services" / "external_actions" / "presenters"

_KV_CALL_MARKERS = (
    "summary_kv_rows(",
    "kv_rows_from_mapping(",
    "build_kv_profile_rows(",
)


def _extract_balanced_call(source: str, open_paren_index: int) -> str:
    depth = 0

    for index in range(open_paren_index, len(source)):
        char = source[index]

        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1

            if depth == 0:
                return source[open_paren_index : index + 1]

    return source[open_paren_index:]


def _kv_call_issues_in_file(path: Path) -> list[str]:
    if not path.is_file():
        return []

    source = path.read_text(encoding="utf-8")
    issues: list[str] = []

    for marker in _KV_CALL_MARKERS:
        search_from = 0

        while True:
            marker_index = source.find(marker, search_from)

            if marker_index < 0:
                break

            open_paren_index = source.find("(", marker_index)
            call_text = _extract_balanced_call(source, open_paren_index)

            if "path=" not in call_text:
                line_no = source[:marker_index].count("\n") + 1
                rel = path.relative_to(ROOT)
                issues.append(f"{rel}:{line_no}: {marker.rstrip('(')} sem path=")

            search_from = open_paren_index + len(call_text)

    return issues


def validate_kv_label_context_in_presenters() -> dict[str, object]:
    violations: list[str] = []

    if PRESENTERS_DIR.is_dir():
        for path in sorted(PRESENTERS_DIR.rglob("*.py")):
            violations.extend(_kv_call_issues_in_file(path))

    return {
        "ok": not violations,
        "violations": violations,
    }
