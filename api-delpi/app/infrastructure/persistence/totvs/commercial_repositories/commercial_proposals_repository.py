from __future__ import annotations

from app.application.dto.commercial.get_commercial_proposal_request import (
    GetCommercialProposalRequest,
)
from app.application.dto.commercial.list_commercial_proposals_request import (
    ListCommercialProposalsRequest,
)
from app.application.dto.commercial.summarize_commercial_proposals_by_collaborator_request import (
    SummarizeCommercialProposalsByCollaboratorRequest,
)
from app.application.models.page import Page
from app.domain.entities.commercial.commercial_proposal import CommercialProposal
from app.domain.entities.commercial.commercial_proposal_detail import (
    CommercialProposalDetail,
)
from app.domain.ports.commercial.commercial_proposals_repository_port import (
    CommercialProposalsRepositoryPort,
)
from app.domain.services.commercial_proposal_list_search_service import (
    CommercialProposalListSearchService,
)
from app.domain.services.commercial_proposal_status import (
    LOST_STATUS_CODES,
    WON_STATUS_CODE,
    resolve_proposal_status_category,
    resolve_proposal_status_label,
)
from app.domain.services.commercial_proposal_acceptance_date_service import (
    CommercialProposalAcceptanceDateService,
)
from app.domain.services.commercial_customer_segment_service import (
    CommercialCustomerSegmentService,
)
from app.domain.services.commercial_customer_codes_filter_service import (
    CommercialCustomerCodesFilterService,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.shared.utils.spreadsheet_date import parse_spreadsheet_date


class CommercialProposalsRepository(BaseRepository, CommercialProposalsRepositoryPort):
    _MAX_PAGE_SIZE = 200

    @staticmethod
    def _list_order_clause(request: ListCommercialProposalsRequest) -> str:
        sort_columns = {
            "branch": "branch",
            "proposal": "proposal_number",
            "proposal_number": "proposal_number",
            "revision": "revision",
            "description": "description",
            "proposal_date": "proposal_date",
            "end_date": "end_date",
            "status": "status_code",
            "status_code": "status_code",
            "customer": "customer_code",
            "customer_code": "customer_code",
            "customer_store": "customer_store",
            "stage": "stage",
        }
        sort_key = (request.sort_by or "").strip().lower()
        sort_column = sort_columns.get(sort_key)
        if sort_column:
            direction = (
                "DESC" if str(request.sort_dir or "asc").lower() == "desc" else "ASC"
            )
            tie_columns = [
                column
                for column in ("branch", "proposal_number", "revision")
                if column != sort_column
            ]
            tie_sql = ", ".join(f"{column} ASC" for column in tie_columns)
            return f"""
                ORDER BY {sort_column} {direction}, {tie_sql}
            """

        return """
            ORDER BY proposal_date DESC, proposal_number DESC, revision DESC
        """

    @staticmethod
    def _apply_product_filters(
        qb: QueryBuilder,
        request: ListCommercialProposalsRequest,
    ) -> None:
        product_code = (request.product_code or "").strip()
        product_group = (request.product_group or "").strip()
        if not product_code and not product_group:
            return

        conditions: list[str] = [
            "ADJ.D_E_L_E_T_ = ''",
            "ADJ.ADJ_FILIAL = AD1.AD1_FILIAL",
            "ADJ.ADJ_NROPOR = AD1.AD1_NROPOR",
            "ADJ.ADJ_REVISA = AD1.AD1_REVISA",
        ]
        params: list[str] = []

        if product_code:
            conditions.append("RTRIM(LTRIM(ADJ.ADJ_PROD)) = ?")
            params.append(product_code)

        join_sb1 = ""
        if product_group:
            join_sb1 = """
                INNER JOIN SB1010 SB1
                    ON SB1.D_E_L_E_T_ = ''
                   AND SB1.B1_COD = ADJ.ADJ_PROD
            """
            conditions.append("RTRIM(LTRIM(SB1.B1_GRUPO)) = ?")
            params.append(product_group)

        exists_sql = f"""
            EXISTS (
                SELECT 1
                FROM ADJ010 ADJ
                {join_sb1}
                WHERE {' AND '.join(conditions)}
            )
        """
        qb.raw(exists_sql, *params)

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

        status_filter = (request.status or "").strip().lower()
        acceptance_expr = CommercialProposalAcceptanceDateService.sql_acceptance_date_for_alias(
            "AD1"
        )

        if status_filter == "won":
            qb.eq("AD1.AD1_STATUS", WON_STATUS_CODE)
            qb.raw(f"({acceptance_expr}) IS NOT NULL")
            qb.raw(f"RTRIM(CAST(({acceptance_expr}) AS VARCHAR(20))) <> ''")
            qb.date_range(f"({acceptance_expr})", request.start_date, request.end_date)
        else:
            qb.date_range("AD1.AD1_DATA", request.start_date, request.end_date)
            if status_filter == "open":
                qb.raw(f"AD1.AD1_STATUS <> '{WON_STATUS_CODE}'")

        CommercialCustomerSegmentService.apply_segment_to_query_builder(
            qb,
            "AD1.AD1_CODCLI",
            request.customer_segment,
        )
        CommercialCustomerCodesFilterService.apply_to_query_builder(
            qb,
            "AD1.AD1_CODCLI",
            request.customer_codes,
        )
        self._apply_product_filters(qb, request)

        where_clause, where_params = qb.build()
        search_clause, search_params = CommercialProposalListSearchService.clause_for_latest_row(
            request.search
        )

        base_cte = f"""
            WITH ovs_base AS (
                SELECT DISTINCT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA,
                    AD1.AD1_DESCRI,
                    AD1.AD1_DATA,
                    AD1.AD1_DTASSI,
                    AD1.AD1_DTFIM,
                    {acceptance_expr} AS proposal_acceptance_date,
                    AD1.AD1_STATUS,
                    AD1.AD1_CODCLI,
                    AD1.AD1_LOJCLI,
                    AD1.AD1_STAGE,
                    AD1.AD1_VEND
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
                    AD1_DTASSI,
                    AD1_DTFIM,
                    proposal_acceptance_date,
                    AD1_STATUS,
                    AD1_CODCLI,
                    AD1_LOJCLI,
                    AD1_STAGE,
                    AD1_VEND,
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
            {search_clause}
        """

        list_sql = f"""
            {base_cte}
            SELECT
                AD1_FILIAL AS branch,
                AD1_NROPOR AS proposal_number,
                AD1_REVISA AS revision,
                AD1_DESCRI AS description,
                AD1_DATA AS proposal_date,
                proposal_acceptance_date AS end_date,
                AD1_STATUS AS status_code,
                AD1_CODCLI AS customer_code,
                AD1_LOJCLI AS customer_store,
                AD1_STAGE AS stage,
                AD1_VEND AS seller_code
            FROM ovs_latest
            WHERE rn = 1
            {search_clause}
            {self._list_order_clause(request)}
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
        """

        count_params = list(where_params) + search_params
        list_params = count_params + [offset, page_size]

        with self:
            total_row = self.execute_one(count_sql, count_params)
            rows = self.execute_query(list_sql, list_params)

        total = int((total_row or {}).get("total") or 0)
        items = [_row_to_entity(row) for row in rows]

        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )



    def summarize_by_collaborator(
        self,
        request: SummarizeCommercialProposalsByCollaboratorRequest,
    ) -> dict:
        """Global period summary by seller (same status semantics as the proposals list).

        - open/lost: opening date (AD1_DATA) in period
        - won: acceptance date in period (AD1_DTASSI / AD1_DTFIM fallback)
        Independent of the list Status dropdown; no page cap.
        """
        qb = QueryBuilder()
        qb.raw("AD1.D_E_L_E_T_ = ''")
        if request.branch:
            qb.eq("AD1.AD1_FILIAL", request.branch)
        CommercialCustomerSegmentService.apply_segment_to_query_builder(
            qb,
            "AD1.AD1_CODCLI",
            request.customer_segment,
        )
        CommercialCustomerCodesFilterService.apply_to_query_builder(
            qb,
            "AD1.AD1_CODCLI",
            request.customer_codes,
        )
        list_like = type(
            "ListLike",
            (),
            {
                "product_code": request.product_code,
                "product_group": request.product_group,
            },
        )()
        self._apply_product_filters(qb, list_like)

        where_clause, where_params = qb.build()
        acceptance_expr = CommercialProposalAcceptanceDateService.sql_acceptance_date_for_alias(
            "AD1"
        )
        start_p = qb.convert_date_to_protheus(request.start_date)
        end_p = qb.convert_date_to_protheus(request.end_date)
        lost_sql = ", ".join(f"'{code}'" for code in sorted(LOST_STATUS_CODES))
        open_sql = "'1', '2', '3', '4', '5', '6', '7'"

        period_params: list[object] = []
        open_lost_date_sql = "1 = 1"
        won_date_sql = "1 = 1"
        if start_p is not None and end_p is not None:
            open_lost_date_sql = "AD1.AD1_DATA BETWEEN ? AND ?"
            won_date_sql = f"({acceptance_expr}) BETWEEN ? AND ?"
            period_params = [start_p, end_p, start_p, end_p]
        elif start_p is not None:
            open_lost_date_sql = "AD1.AD1_DATA >= ?"
            won_date_sql = f"({acceptance_expr}) >= ?"
            period_params = [start_p, start_p]
        elif end_p is not None:
            open_lost_date_sql = "AD1.AD1_DATA <= ?"
            won_date_sql = f"({acceptance_expr}) <= ?"
            period_params = [end_p, end_p]

        sql = f"""
            WITH ovs_base AS (
                SELECT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA,
                    AD1.AD1_DATA,
                    AD1.AD1_STATUS,
                    AD1.AD1_VEND,
                    {acceptance_expr} AS proposal_acceptance_date,
                    ROW_NUMBER() OVER (
                        PARTITION BY AD1.AD1_FILIAL, AD1.AD1_NROPOR
                        ORDER BY AD1.AD1_REVISA DESC
                    ) AS rn
                FROM AD1010 AD1
                WHERE {where_clause}
                  AND (
                        (
                            {open_lost_date_sql}
                            AND LTRIM(RTRIM(ISNULL(AD1.AD1_STATUS, ''))) IN ({open_sql}, {lost_sql})
                        )
                     OR (
                            LTRIM(RTRIM(ISNULL(AD1.AD1_STATUS, ''))) = '{WON_STATUS_CODE}'
                            AND ({acceptance_expr}) IS NOT NULL
                            AND RTRIM(CAST(({acceptance_expr}) AS VARCHAR(20))) <> ''
                            AND {won_date_sql}
                        )
                  )
            ),
            ovs_latest AS (
                SELECT
                    AD1_DATA,
                    LTRIM(RTRIM(ISNULL(AD1_STATUS, ''))) AS status_code,
                    LTRIM(RTRIM(ISNULL(AD1_VEND, ''))) AS seller_code,
                    proposal_acceptance_date
                FROM ovs_base
                WHERE rn = 1
            )
            SELECT
                L.seller_code AS seller_code,
                MAX(LTRIM(RTRIM(ISNULL(SA3.A3_NOME, '')))) AS seller_name,
                SUM(
                    CASE
                        WHEN L.status_code = '{WON_STATUS_CODE}' THEN 1
                        ELSE 0
                    END
                ) AS won_count,
                SUM(
                    CASE
                        WHEN L.status_code IN ({lost_sql}) THEN 1
                        ELSE 0
                    END
                ) AS lost_count,
                SUM(
                    CASE
                        WHEN L.status_code IN ({open_sql}) THEN 1
                        ELSE 0
                    END
                ) AS open_count,
                COUNT(1) AS total_count,
                AVG(
                    CAST(
                        DATEDIFF(DAY, L.AD1_DATA, CAST(GETDATE() AS DATE))
                        AS FLOAT
                    )
                ) AS age_days_avg
            FROM ovs_latest L
            LEFT JOIN SA3010 SA3
                ON SA3.D_E_L_E_T_ = ''
               AND LTRIM(RTRIM(SA3.A3_COD)) = L.seller_code
            GROUP BY L.seller_code
            ORDER BY total_count DESC, seller_code ASC
        """

        query_params = list(where_params) + period_params
        with self:
            rows = self.execute_query(sql, tuple(query_params))

        items: list[dict] = []
        source_count = 0
        for row in rows or []:
            total = int(row.get("total_count") or 0)
            source_count += total
            age = row.get("age_days_avg")
            items.append(
                {
                    "seller_code": (row.get("seller_code") or "").strip(),
                    "seller_name": (row.get("seller_name") or "").strip() or None,
                    "open_count": int(row.get("open_count") or 0),
                    "won_count": int(row.get("won_count") or 0),
                    "lost_count": int(row.get("lost_count") or 0),
                    "total_count": total,
                    "age_days_avg": round(float(age), 1) if age is not None else None,
                }
            )
        return {
            "items": items,
            "source_count": source_count,
            "truncated": False,
        }


    def get_proposal(
        self,
        request: GetCommercialProposalRequest,
    ) -> CommercialProposalDetail | None:
        qb = QueryBuilder()
        qb.raw("AD1.D_E_L_E_T_ = ''")
        qb.eq("AD1.AD1_FILIAL", request.branch.strip())
        qb.eq("AD1.AD1_NROPOR", request.proposal_number.strip())

        revision = (request.revision or "").strip()
        if revision:
            qb.eq("AD1.AD1_REVISA", revision)

        where_clause, where_params = qb.build()
        revision_order = "" if revision else "ORDER BY AD1.AD1_REVISA DESC"
        acceptance_expr = CommercialProposalAcceptanceDateService.sql_acceptance_date_for_alias(
            "AD1"
        )

        sql = f"""
            SELECT TOP 1
                AD1.AD1_FILIAL AS branch,
                AD1.AD1_NROPOR AS proposal_number,
                AD1.AD1_REVISA AS revision,
                AD1.AD1_DESCRI AS description,
                AD1.AD1_DATA AS proposal_date,
                {acceptance_expr} AS end_date,
                AD1.AD1_STATUS AS status_code,
                AD1.AD1_CODCLI AS customer_code,
                AD1.AD1_LOJCLI AS customer_store,
                AD1.AD1_STAGE AS stage,
                AD1.AD1_PROVEN AS process_code,
                AD1.AD1_VEND AS seller_code,
                LTRIM(RTRIM(SA1.A1_NOME)) AS customer_name,
                LTRIM(RTRIM(SA3.A3_NOME)) AS seller_name,
                LTRIM(RTRIM(STG.stage_label)) AS stage_label,
                LTRIM(RTRIM(PRC.process_label)) AS process_label
            FROM AD1010 AD1
            LEFT JOIN SA1010 SA1
                ON SA1.D_E_L_E_T_ = ''
               AND SA1.A1_COD = AD1.AD1_CODCLI
               AND SA1.A1_LOJA = AD1.AD1_LOJCLI
            LEFT JOIN SA3010 SA3
                ON SA3.D_E_L_E_T_ = ''
               AND SA3.A3_COD = AD1.AD1_VEND
            OUTER APPLY (
                SELECT TOP 1 LTRIM(RTRIM(AC2.AC2_DESCRI)) AS stage_label
                FROM AC2010 AC2
                WHERE AC2.D_E_L_E_T_ = ''
                  AND AC2.AC2_PROVEN = AD1.AD1_PROVEN
                  AND AC2.AC2_STAGE = AD1.AD1_STAGE
                  AND (
                        RTRIM(ISNULL(AC2.AC2_FILIAL, '')) = ''
                     OR AC2.AC2_FILIAL = AD1.AD1_FILIAL
                  )
                ORDER BY
                    CASE
                        WHEN AC2.AC2_FILIAL = AD1.AD1_FILIAL THEN 0
                        ELSE 1
                    END
            ) STG
            OUTER APPLY (
                SELECT TOP 1 LTRIM(RTRIM(AC1.AC1_DESCRI)) AS process_label
                FROM AC1010 AC1
                WHERE AC1.D_E_L_E_T_ = ''
                  AND AC1.AC1_PROVEN = AD1.AD1_PROVEN
                  AND (
                        RTRIM(ISNULL(AC1.AC1_FILIAL, '')) = ''
                     OR AC1.AC1_FILIAL = AD1.AD1_FILIAL
                  )
                ORDER BY
                    CASE
                        WHEN AC1.AC1_FILIAL = AD1.AD1_FILIAL THEN 0
                        ELSE 1
                    END
            ) PRC
            WHERE {where_clause}
            {revision_order}
        """

        with self:
            row = self.execute_one(sql, where_params)

        if not row:
            return None

        return _row_to_detail(row)


def _row_to_detail(row: dict) -> CommercialProposalDetail:
    base = _row_to_entity(row)
    return CommercialProposalDetail(
        branch=base.branch,
        proposal_number=base.proposal_number,
        revision=base.revision,
        description=base.description,
        proposal_date=base.proposal_date,
        end_date=base.end_date,
        status_code=base.status_code,
        status_label=base.status_label,
        status_category=base.status_category,
        customer_code=base.customer_code,
        customer_store=base.customer_store,
        stage=base.stage,
        customer_name=(row.get("customer_name") or "").strip() or None,
        seller_code=(row.get("seller_code") or "").strip() or None,
        seller_name=(row.get("seller_name") or "").strip() or None,
        process_code=(row.get("process_code") or "").strip() or None,
        process_label=(row.get("process_label") or "").strip() or None,
        stage_label=(row.get("stage_label") or "").strip() or None,
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
        customer_store=(row.get("customer_store") or "").strip() or None,
        stage=(row.get("stage") or "").strip() or None,
        seller_code=(row.get("seller_code") or "").strip() or None,
        seller_name=(row.get("seller_name") or "").strip() or None,
    )


def _format_api_date(value: object) -> str | None:
    parsed = parse_spreadsheet_date(value)
    if parsed is None:
        return None
    return parsed.strftime("%Y-%m-%d")
