"""Leitura analítica de auditorias 5S a partir do PostgreSQL (substitui Google Sheets)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from app.application.dto.auditoria_5s.audit_5s_summary_response import (
    Audit5SSummaryResponse,
)
from app.domain.entities.audit_5s.audit_5s import Audit5S
from app.domain.ports.audit_5s.audit_5s_query_port import Audit5SQueryRepositoryPort
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_AUDIT_SUMMARY_SELECT = """
    SELECT a.id,
           a.branch_code,
           a.audit_code,
           a.audit_date,
           a.area_responsible,
           a.shift,
           a.status,
           a.overall_score_pct,
           ar.name AS area_name,
           (
               SELECT string_agg(aud.display_name, ', ' ORDER BY aud.display_name)
                 FROM quality.audit_5s_auditors aud
                WHERE aud.audit_id = a.id
           ) AS auditor_names
      FROM quality.audit_5s_audits a
      JOIN quality.audit_5s_areas ar ON ar.id = a.area_id
     WHERE a.status != 'draft'
       AND a.overall_score_pct IS NOT NULL
"""


class PostgresAudit5SQueryRepository(PluginBaseRepository, Audit5SQueryRepositoryPort):
    """Summary KPI / lista para dashboard-quality e SI — fonte Postgres."""

    def __init__(self, utils: Utils | None = None, connection=None) -> None:
        super().__init__(connection=connection)
        self._utils = utils or Utils()

    def get_audit_summary(
        self,
        request: Audit5SSummaryRequest,
    ) -> Audit5SSummaryResponse:
        range_start, range_end = self._parse_request_dates(request)
        where_sql, params = self._filter_clause(
            branch=request.branch,
            range_start=range_start,
            range_end=range_end,
        )
        rows = self.fetch_all(
            f"""
            {_AUDIT_SUMMARY_SELECT}
              AND {where_sql}
            ORDER BY a.audit_date DESC, a.created_at DESC
            """,
            tuple(params),
        )

        audits = [self._row_to_audit(row) for row in rows]
        scores = [
            audit.average_line_score
            for audit in audits
            if audit.average_line_score is not None
        ]
        average_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        return Audit5SSummaryResponse(
            start_date=request.start_date,
            end_date=request.end_date,
            average_score=average_score,
            list_audits=audits,
        )

    def _parse_request_dates(
        self,
        request: Audit5SSummaryRequest,
    ) -> tuple[date | None, date | None]:
        self._utils.validate_date_range(
            start_date_str=request.start_date,
            end_date_str=request.end_date,
        )
        start = (
            self._utils.parse_date(request.start_date) if request.start_date else None
        )
        end = self._utils.parse_date(request.end_date) if request.end_date else None
        return start, end

    @staticmethod
    def _filter_clause(
        *,
        branch: str | None,
        range_start: date | None,
        range_end: date | None,
    ) -> tuple[str, list[Any]]:
        conditions: list[str] = ["TRUE"]
        params: list[Any] = []

        if branch and branch.strip():
            conditions.append("a.branch_code = %s")
            params.append(branch.strip())

        if range_start is not None:
            conditions.append("a.audit_date >= %s")
            params.append(range_start.isoformat())

        if range_end is not None:
            conditions.append("a.audit_date <= %s")
            params.append(range_end.isoformat())

        return " AND ".join(conditions), params

    @classmethod
    def _row_to_audit(cls, row: dict[str, Any]) -> Audit5S:
        return Audit5S(
            id=cls._as_id(row.get("id")),
            date=cls._as_iso_date(row.get("audit_date")),
            average_line_score=cls._as_float(row.get("overall_score_pct")),
            evaluated_area=cls._as_optional_str(row.get("area_name")),
            auditor=cls._as_optional_str(row.get("auditor_names")),
            audited=cls._as_optional_str(row.get("area_responsible")),
            inspection_number=cls._as_optional_str(row.get("audit_code")),
            shift=cls._as_optional_str(row.get("shift")),
            branch=cls._as_optional_str(row.get("branch_code")),
        )

    @staticmethod
    def _as_id(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, UUID):
            return str(value)
        return str(value)

    @staticmethod
    def _as_iso_date(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        text = str(value).strip()
        return text[:10] if text else None

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_optional_str(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None
