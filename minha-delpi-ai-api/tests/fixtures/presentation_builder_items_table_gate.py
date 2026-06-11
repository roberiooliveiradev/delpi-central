"""Gate R23 — builder genérico repassa path/entity ao montar tabelas."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = (
    ROOT
    / "app"
    / "domain"
    / "services"
    / "external_actions"
    / "presenters"
    / "presentation_builder_presenter.py"
)


def validate_presentation_builder_items_table_context() -> dict[str, object]:
    if not BUILDER.is_file():
        return {"ok": True, "violations": []}

    source = BUILDER.read_text(encoding="utf-8")
    violations: list[str] = []

    for line_no, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()

        if "self._host._build_items_table(" not in stripped:
            continue

        if "_build_items_table_for_path" in stripped:
            continue

        rel = BUILDER.relative_to(ROOT)
        violations.append(
            f"{rel}:{line_no}: usar _build_items_table_for_path em vez de _host._build_items_table"
        )

    return {
        "ok": not violations,
        "violations": violations,
    }
