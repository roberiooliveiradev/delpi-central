from __future__ import annotations

from typing import Any

from app.domain.entities.kaizen.kaizen import KaizenDetail
from app.shared.utils.spreadsheet_date import parse_spreadsheet_date


def normalize_sheet_status(value: str | None) -> str:
    if not value:
        return "recebido"
    normalized = (
        str(value)
        .strip()
        .lower()
        .replace("í", "i")
        .replace("ú", "u")
        .replace("ã", "a")
        .replace("ç", "c")
        .replace(" ", "_")
    )
    allowed = {"recebido", "aprovado", "implantado", "descontinuado", "cancelado"}
    if normalized in allowed:
        return normalized
    if normalized in {"em_andamento", "emandamento"}:
        return "recebido"
    if normalized == "implantada":
        return "implantado"
    if normalized in {"aprovada", "aprovacao"}:
        return "aprovado"
    return "recebido"


def sheet_detail_to_record_fields(detail: KaizenDetail) -> dict[str, Any]:
    branch_code = (detail.branch or "").strip()
    fields: dict[str, Any] = {
        "branch_code": branch_code,
        "title": detail.title.strip(),
        "accountable": detail.accountable,
        "sector": detail.sector,
        "investment": detail.investment,
        "seconds_per_occurrence": detail.seconds_per_occurrence,
        "occurrences_per_day": detail.occurrences_per_day,
        "hourly_cost": detail.hourly_cost,
        "status": normalize_sheet_status(detail.status),
    }

    parsed_date = parse_spreadsheet_date(detail.date_implemented)
    if parsed_date is not None:
        fields["date_implemented"] = parsed_date.isoformat()

    return fields
