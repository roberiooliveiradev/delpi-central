from __future__ import annotations

from app.application.dto.commercial.list_commercial_proposals_request import (
    ListCommercialProposalsRequest,
)
from app.application.models.page import Page
from app.domain.entities.commercial.commercial_proposal import CommercialProposal
from app.domain.ports.commercial.commercial_proposals_repository_port import (
    CommercialProposalsRepositoryPort,
)
from app.domain.services.commercial_proposal_status import (
    WON_STATUS_CODE,
    resolve_proposal_status_category,
    resolve_proposal_status_label,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.shared.utils.spreadsheet_date import parse_spreadsheet_date


class CommercialProposalsRepository(BaseRepository, CommercialProposalsRepositoryPort):
    _MAX_PAGE_SIZE = 200

    def list_proposals(
        self,
        request: ListCommercialProposalsRequest,
    ) -> Page[CommercialProposal]:
        page = max(request.page or 1, 1)
        page_size = min(max(request.page_size or 50, 1), self._MAX_PAGE_SIZE)
        offset = (page - 1) * page_size

        qb = QueryBuilder()
        qb.raw("AD1.D_E_L_E_T_ = ''")

        if request.branch:
            qb.eq("AD1.AD1_FILIAL", request.branch)

        qb.date_range("AD1.AD1_DATA", request.start_date, request.end_date)

        status_filter = (request.status or "").strip().lower()
        if status_filter == "won":
            qb.eq("AD1.AD1_STATUS", WON_STATUS_CODE)
            qb.raw("AD1.AD1_DTFIM IS NOT NULL")
            qb.raw("RTRIM(CAST(AD1.AD1_DTFIM AS VARCHAR(20))) <> ''")
            qb.date_range("AD1.AD1_DTFIM", request.start_date, request.end_date)
        elif status_filter == "open":
            qb.raw(f"AD1.AD1_STATUS <> '{WON_STATUS_CODE}'")

        where_clause, where_params = qb.build()

        base_cte = f"""
            WITH ovs_base AS (
                SELECT DISTINCT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA,
                    AD1.AD1_DESCRI,
                    AD1.AD1_DATA,
                    AD1.AD1_DTFIM,
                    AD1.AD1_STATUS,
                    AD1.AD1_CODCLI,
                    AD1.AD1_STAGE
                FROM AD1010 AD1
                WHERE {where_clause}
            ),
            ovs_latest AS (
                SELECT
                    AD1_FILIAL,
                    AD1_NROPOR,
                    AD1_REVISA,
                    AD1_DESCRI,
                    AD1_DATA,
                    AD1_DTFIM,
                    AD1_STATUS,
                    AD1_CODCLI,
                    AD1_STAGE,
                    ROW_NUMBER() OVER (
                        PARTITION BY AD1_FILIAL, AD1_NROPOR
                        ORDER BY AD1_REVISA DESC
                    ) AS rn
                FROM ovs_base
            )
        """

        count_sql = f"""
            {base_cte}
            SELECT COUNT(1) AS total
            FROM ovs_latest
            WHERE rn = 1
        """

        list_sql = f"""
            {base_cte}
            SELECT
                AD1_FILIAL AS branch,
                AD1_NROPOR AS proposal_number,
                AD1_REVISA AS revision,
                AD1_DESCRI AS description,
                AD1_DATA AS proposal_date,
                AD1_DTFIM AS end_date,
                AD1_STATUS AS status_code,
                AD1_CODCLI AS customer_code,
                AD1_STAGE AS stage
            FROM ovs_latest
            WHERE rn = 1
            ORDER BY AD1_DATA DESC, AD1_NROPOR DESC, AD1_REVISA DESC
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
        """

        list_params = list(where_params) + [offset, page_size]

        with self:
            total_row = self.execute_one(count_sql, where_params)
            rows = self.execute_query(list_sql, list_params)

        total = int((total_row or {}).get("total") or 0)
        items = [_row_to_entity(row) for row in rows]

        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )


def _row_to_entity(row: dict) -> CommercialProposal:
    status_code = (row.get("status_code") or "").strip() or None
    return CommercialProposal(
        branch=(row.get("branch") or "").strip(),
        proposal_number=(row.get("proposal_number") or "").strip(),
        revision=(row.get("revision") or "").strip(),
        description=(row.get("description") or "").strip() or None,
        proposal_date=_format_api_date(row.get("proposal_date")),
        end_date=_format_api_date(row.get("end_date")),
        status_code=status_code,
        status_label=resolve_proposal_status_label(status_code),
        status_category=resolve_proposal_status_category(status_code),
        customer_code=(row.get("customer_code") or "").strip() or None,
        stage=(row.get("stage") or "").strip() or None,
    )


def _format_api_date(value: object) -> str | None:
    parsed = parse_spreadsheet_date(value)
    if parsed is None:
        return None
    return parsed.strftime("%Y-%m-%d")
