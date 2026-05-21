from __future__ import annotations

CONSOLIDATED_BRANCH_KEY = "consolidated"


def is_consolidated_sheet_row(filial: object) -> bool:
    if filial is None:
        return True
    return str(filial).strip() == ""


def normalize_sheet_branch(filial: object) -> str | None:
    if is_consolidated_sheet_row(filial):
        return None
    return str(filial).strip()
