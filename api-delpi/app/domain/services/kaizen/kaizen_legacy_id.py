from __future__ import annotations

from datetime import date


def build_legacy_sheet_id(
    *,
    branch: str | None,
    date_implemented: date | None,
    title: str | None,
) -> str:
    """Id composto legado da planilha: filial-data-título (ex.: 01-16/01/2026-App resina)."""
    branch_part = (branch or "").strip()
    title_part = (title or "").strip()
    date_part = date_implemented.strftime("%d/%m/%Y") if date_implemented else ""
    return f"{branch_part}-{date_part}-{title_part}".strip("-")
