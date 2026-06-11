"""Gate R17 — presenters não montam colunas via caminho legado `fixed_table_columns`."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRESENTERS_DIR = ROOT / "app" / "domain" / "services" / "external_actions" / "presenters"
HOST_PRESENTER = (
    ROOT / "app" / "domain" / "services" / "external_actions" / "external_action_result_presenter.py"
)

_LEGACY_MARKERS = (
    "fixed_table_columns(",
    "_fixed_columns(",
)


def _legacy_usages_in_file(path: Path) -> list[str]:
    if not path.is_file():
        return []

    issues: list[str] = []

    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if "def _fixed_columns" in line or "def fixed_table_columns" in line:
            continue

        for marker in _LEGACY_MARKERS:
            if marker in line:
                rel = path.relative_to(ROOT)
                issues.append(f"{rel}:{line_no}: {marker.rstrip('(')}")

    return issues


def validate_no_legacy_table_columns_in_presenters() -> dict[str, object]:
    violations: list[str] = []

    if PRESENTERS_DIR.is_dir():
        for path in sorted(PRESENTERS_DIR.rglob("*.py")):
            violations.extend(_legacy_usages_in_file(path))

    violations.extend(_legacy_usages_in_file(HOST_PRESENTER))

    return {
        "ok": not violations,
        "violations": violations,
    }
