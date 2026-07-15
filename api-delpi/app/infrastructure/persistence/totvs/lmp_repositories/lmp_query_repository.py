from typing import List, Tuple

from app.application.dto.lmp.get_lmp_history_request import GetLmpHistoryRequest
from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.application.dto.lmp.list_lmp_request import (
    LISTING_KIND_LMP,
    LISTING_KIND_OTHER,
    LISTING_KIND_SAMPLE,
    ListLMPRequest,
    resolve_listing_type_filter,
)
from app.application.models.page import Page
from app.application.services.lmp.lmp_dashboard_cache import (
    get_cached_lmp_dashboard_summary_rows,
    lmp_dashboard_summary_rows_cache_key,
    set_cached_lmp_dashboard_summary_rows,
)
from app.domain.entities.lmp.lmp import LMP
from app.domain.entities.lmp.lmp_history_event import LMPHistoryEvent
from app.domain.entities.lmp.lmp_product import LMPProduct
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort
from app.domain.services.lmp_period_inclusion_semantics_service import (
    HOMOLOG_IN_PERIOD,
    LmpPeriodInclusionSemanticsService,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.lmp_repositories.lmp_query_settings import (
    LMPQuerySettings,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class LMPQueryRepository(BaseRepository, LMPQueryRepositoryPort):

    def __init__(self, settings: LMPQuerySettings | None = None):
        super().__init__()
        self.settings = settings or LMPQuerySettings()

    # =========================
    # HELPERS
    # =========================

    def _build_filter_sql(self, callback) -> Tuple[str, tuple]:
        qb = QueryBuilder()
        callback(qb)
        return qb.build()

    @staticmethod
    def _totvs_from(table: str, alias: str) -> str:
        """Leitura analítica — alias antes do hint (T-SQL: FROM Tbl X WITH (NOLOCK))."""
        return f"{table} {alias} WITH (NOLOCK)"

    def _active_filter(self, qb: QueryBuilder, field: str):
        qb.eq(field, self.settings.active_delete_flag)

    def _resolve_branches(self, requested_branch: str | None = None) -> list[str]:
        if requested_branch:
            return [requested_branch]
        return self.settings.branches

    def _branch_filter(
        self,
        qb: QueryBuilder,
        field: str,
        requested_branch: str | None = None,
    ):
        qb.in_list(field, self._resolve_branches(requested_branch))

    def _root_product_type_filter(self, qb: QueryBuilder, field: str):
        qb.in_list(field, self.settings.root_product_types)

    def _pi_product_type_filter(self, qb: QueryBuilder, field: str):
        qb.in_list(field, self.settings.pi_product_types)

    def _engineering_status_in_progress_label(self) -> str:
        return self.settings.engineering_status_labels["in_progress"]

    def _engineering_status_finished_label(self) -> str:
        return self.settings.engineering_status_labels["finished"]

    def _engineering_status_partial_label(self) -> str:
        return self.settings.engineering_status_labels["partial"]

    def _engineering_status_returned_label(self) -> str:
        return self.settings.engineering_status_labels["returned"]

    def _min_engineering_residence_minutes(self) -> int:
        return self.settings.min_engineering_residence_minutes

    def _sql_ad1_current_revision_match(
        self,
        aij_alias: str,
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        where_ad1, params_ad1 = self._sql_filter_ad1_active_branch("AD1", requested_branch)
        sql = f"""
            EXISTS (
                SELECT 1
                FROM AD1010 AD1
                WHERE AD1.AD1_FILIAL = {aij_alias}.AIJ_FILIAL
                  AND AD1.AD1_NROPOR = {aij_alias}.AIJ_NROPOR
                  AND AD1.AD1_REVISA = {aij_alias}.AIJ_REVISA
                  AND {where_ad1}
            )
        """
        return sql, params_ad1

    def _engineering_residence_filter_sql(self) -> str:
        """Tempo mínimo em engenharia aplica somente a LMP; Amostra e Outro listam sempre."""
        minutes = self._min_engineering_residence_minutes()
        if self.settings.strict_residence_after_homolog:
            return f"""
            WHERE
                C.LISTING_KIND IN ('{LISTING_KIND_SAMPLE}', '{LISTING_KIND_OTHER}')
                OR (
                    C.LISTING_KIND = '{LISTING_KIND_LMP}'
                    AND ISNULL(H.TEMPO_TOTAL_MINUTOS_ENG, 0) >= {minutes}
                )
        """
        return f"""
            WHERE
                C.LISTING_KIND IN ('{LISTING_KIND_SAMPLE}', '{LISTING_KIND_OTHER}')
                OR (
                    C.LISTING_KIND = '{LISTING_KIND_LMP}'
                    AND (
                        ISNULL(H.TEMPO_TOTAL_MINUTOS_ENG, 0) >= ?
                        OR C.HAS_SAMPLE_ANCHOR = 1
                    )
                )
        """

    def _effective_listing_kind_expr(
        self,
        *,
        listing_kind_field: str = "C.LISTING_KIND",
        has_sample_field: str = "C.HAS_SAMPLE_ANCHOR",
        has_lmp_finalized_field: str = "C.HAS_LMP_FINALIZED",
    ) -> str:
        minutes = self._min_engineering_residence_minutes()
        strict_after_homolog = ""
        if self.settings.strict_residence_after_homolog:
            strict_after_homolog = f"""
                WHEN {listing_kind_field} = '{LISTING_KIND_LMP}'
                 AND {has_lmp_finalized_field} = 1
                 AND ISNULL(H.TEMPO_TOTAL_MINUTOS_ENG, 0) < {minutes}
                THEN '{LISTING_KIND_OTHER}'
            """
        return f"""
            CASE
                {strict_after_homolog}
                WHEN {listing_kind_field} = '{LISTING_KIND_LMP}'
                 AND {has_sample_field} = 1
                 AND ISNULL(H.TEMPO_MINUTOS_AMOSTRA_ENG, 0) > 0
                 AND {has_lmp_finalized_field} = 0
                THEN '{LISTING_KIND_SAMPLE}'
                WHEN {listing_kind_field} = '{LISTING_KIND_LMP}'
                 AND {has_sample_field} = 1
                 AND ISNULL(H.TEMPO_TOTAL_MINUTOS_ENG, 0) < ?
                 AND {has_lmp_finalized_field} = 0
                THEN '{LISTING_KIND_OTHER}'
                ELSE {listing_kind_field}
            END
        """

    def _staged_residence_final_params(
        self,
        *,
        listing_kind_reclass_count: int = 1,
        residence_filter_count: int = 1,
    ) -> tuple:
        minutes = self._min_engineering_residence_minutes()
        if self.settings.strict_residence_after_homolog:
            return tuple([minutes] * listing_kind_reclass_count)
        params: list[int] = []
        params.extend([minutes] * residence_filter_count)
        params.extend([minutes] * listing_kind_reclass_count)
        return tuple(params)

    def _period_inclusion_policy(self) -> str:
        return LmpPeriodInclusionSemanticsService.normalize_policy(
            self.settings.period_inclusion_policy,
        )

    def _uses_homolog_cycle_listing(self) -> bool:
        return LmpPeriodInclusionSemanticsService.uses_homolog_cycle_listing(
            self._period_inclusion_policy(),
        )

    def _uses_per_revision_candidate_listing(self) -> bool:
        return LmpPeriodInclusionSemanticsService.uses_per_revision_candidate_listing(
            self._period_inclusion_policy(),
        )

    def _uses_work_month_lmp_listing(self) -> bool:
        return LmpPeriodInclusionSemanticsService.uses_work_month_lmp_listing(
            self._period_inclusion_policy(),
        )

    def _staged_eng_resumo_join_revision_sql(self) -> str:
        if self._uses_per_revision_candidate_listing():
            return "AND H.MEASUREMENT_REVISION = C.AD1_REVISA"
        return ""

    def _staged_cycle_index_expr(self) -> str:
        if self._uses_per_revision_candidate_listing():
            return "ISNULL(C.CYCLE_INDEX, 1) AS cycle_index"
        return "1 AS cycle_index"

    def _staged_cycle_index_group_by(self) -> str:
        if self._uses_per_revision_candidate_listing():
            return ",\n                    C.CYCLE_INDEX"
        return ""

    def _uses_period_revision_measurement(
        self,
        *,
        scope_cte_name: str | None,
        date_start: str | None,
        date_end: str | None,
    ) -> bool:
        return bool(scope_cte_name and date_start and date_end)

    def _has_listing_period_filter(
        self,
        date_start: str | None,
        date_end: str | None,
    ) -> bool:
        return bool(date_start and date_end)

    def _listing_anchor_period_dates(
        self,
        date_start: str | None,
        date_end: str | None,
    ) -> Tuple[str | None, str | None]:
        """Com período informado, âncoras usam revisão atual; filtro fica nos candidatos."""
        if self._has_listing_period_filter(date_start, date_end):
            return None, None
        return date_start, date_end

    def _sql_candidate_period_where_clause(
        self,
        request: ListLMPRequest,
        *,
        anchor_date_sql: str,
        first_eng_date_sql: str = "F.FIRST_ENG_DATE",
        homolog_date_sql: str = "LF.ANCHOR_START_DATE",
    ) -> Tuple[str, tuple]:
        qb_anchor = QueryBuilder()
        qb_anchor.date_range(
            field=anchor_date_sql,
            start=request.date_start,
            end=request.date_end,
        )
        where_anchor, params_anchor = qb_anchor.build()

        if not self._has_listing_period_filter(
            request.date_start,
            request.date_end,
        ):
            return where_anchor, params_anchor

        qb_homolog = QueryBuilder()
        qb_homolog.date_range(
            field=homolog_date_sql,
            start=request.date_start,
            end=request.date_end,
        )
        where_homolog, params_homolog = qb_homolog.build()

        if self._period_inclusion_policy() == HOMOLOG_IN_PERIOD:
            if not where_homolog:
                return "1=0", ()
            return where_homolog, params_homolog

        qb_first = QueryBuilder()
        qb_first.date_range(
            field=first_eng_date_sql,
            start=request.date_start,
            end=request.date_end,
        )
        where_first, params_first = qb_first.build()

        sql = LmpPeriodInclusionSemanticsService.build_candidate_period_predicate(
            policy=self._period_inclusion_policy(),
            anchor_date_sql=anchor_date_sql,
            first_eng_date_sql=first_eng_date_sql,
            homolog_date_sql=homolog_date_sql,
            where_anchor=where_anchor,
            where_first_eng=where_first,
            where_homolog=where_homolog,
        )
        if sql == where_first:
            return where_first, params_first
        if sql == where_anchor:
            return where_anchor, params_anchor
        return sql, (*params_anchor, *params_first)

    def _sql_ov_first_engineering_arrival_cte(
        self,
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        where_aij_base, params_aij_base = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", requested_branch),
            )
        )
        where_eng_support, params_eng_support = (
            self._sql_engineering_support_process_stage_condition(
                "A.AIJ_PROVEN",
                "A.AIJ_STAGE",
            )
        )
        where_ad1, params_ad1 = self._sql_filter_ad1_active_branch(
            "AD1",
            requested_branch,
        )

        sql = f"""
            OvFirstEngineeringArrival AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    MIN(A.AIJ_DTINIC) AS FIRST_ENG_DATE
                FROM AIJ010 A
                INNER JOIN AD1010 AD1
                    ON AD1.AD1_FILIAL = A.AIJ_FILIAL
                   AND AD1.AD1_NROPOR = A.AIJ_NROPOR
                WHERE {where_ad1}
                  AND {where_aij_base}
                  AND {where_eng_support}
                  AND ISNULL(A.AIJ_DTINIC, '') <> ''
                GROUP BY
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR
            )
        """
        return sql, (*params_ad1, *params_aij_base, *params_eng_support)

    def _sql_event_engineering_minutes_expr(self, alias: str) -> str:
        return f"""
            CASE
                WHEN ISNULL({alias}.AIJ_DTINIC, '') <> ''
                 AND ISNULL({alias}.AIJ_HRINIC, '') <> ''
                THEN DATEDIFF(
                    MINUTE,
                    CAST(
                        CONCAT(
                            SUBSTRING({alias}.AIJ_DTINIC, 1, 4), '-',
                            SUBSTRING({alias}.AIJ_DTINIC, 5, 2), '-',
                            SUBSTRING({alias}.AIJ_DTINIC, 7, 2), ' ',
                            {alias}.AIJ_HRINIC, ':00'
                        ) AS DATETIME
                    ),
                    CASE
                        WHEN ISNULL({alias}.AIJ_DTENCE, '') <> ''
                         AND ISNULL({alias}.AIJ_HRENCE, '') <> ''
                        THEN CAST(
                            CONCAT(
                                SUBSTRING({alias}.AIJ_DTENCE, 1, 4), '-',
                                SUBSTRING({alias}.AIJ_DTENCE, 5, 2), '-',
                                SUBSTRING({alias}.AIJ_DTENCE, 7, 2), ' ',
                                {alias}.AIJ_HRENCE, ':00'
                            ) AS DATETIME
                        )
                        WHEN ISNULL({alias}.PROXIMO_DTINIC_GLOBAL, '') <> ''
                         AND ISNULL({alias}.PROXIMO_HRINIC_GLOBAL, '') <> ''
                        THEN CAST(
                            CONCAT(
                                SUBSTRING({alias}.PROXIMO_DTINIC_GLOBAL, 1, 4), '-',
                                SUBSTRING({alias}.PROXIMO_DTINIC_GLOBAL, 5, 2), '-',
                                SUBSTRING({alias}.PROXIMO_DTINIC_GLOBAL, 7, 2), ' ',
                                {alias}.PROXIMO_HRINIC_GLOBAL, ':00'
                            ) AS DATETIME
                        )
                        ELSE GETDATE()
                    END
                )
                ELSE 0
            END
        """

    def _sql_period_revision_measurement_ctes(
        self,
        *,
        use_period_revision: bool,
        per_candidate_revision: bool,
        scope_cte_name: str | None,
        where_period_eng: str,
        where_period_eng_e2: str,
        where_lmp_anchor_rank_e: str,
        where_lmp_anchor_rank_m: str,
        eng_minutes_expr: str,
    ) -> str:
        eng_minutes_per_rev_expr = self._sql_event_engineering_minutes_expr("M")
        if per_candidate_revision and scope_cte_name:
            return f"""
            UltimaRevisaoMedicaoEngenharia AS (
                SELECT
                    S.AD1_FILIAL AS AIJ_FILIAL,
                    S.AD1_NROPOR AS AIJ_NROPOR,
                    S.AD1_REVISA AS ULTIMA_REVISA_MEDICAO
                FROM {scope_cte_name} S
            ),
            """
        if use_period_revision:
            return f"""
            EngenhariaMinutosPorRevisao AS (
                SELECT
                    M.AIJ_FILIAL,
                    M.AIJ_NROPOR,
                    M.AIJ_REVISA,
                    SUM({eng_minutes_per_rev_expr}) AS MINUTOS_REVISAO,
                    MAX(
                        CASE
                            WHEN {where_lmp_anchor_rank_m} THEN 1
                            ELSE 0
                        END
                    ) AS TEM_ANCORA_LMP
                FROM EngenhariaEventos M
                GROUP BY
                    M.AIJ_FILIAL,
                    M.AIJ_NROPOR,
                    M.AIJ_REVISA
            ),

            RevisoesElegiveisMedicao AS (
                SELECT DISTINCT
                    E.AIJ_FILIAL,
                    E.AIJ_NROPOR,
                    E.AIJ_REVISA
                FROM EngenhariaEventos E
                WHERE 1=1
                  {where_period_eng}

                UNION

                SELECT
                    S.AD1_FILIAL,
                    S.AD1_NROPOR,
                    S.AD1_REVISA
                FROM {scope_cte_name} S
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM EngenhariaEventos E2
                    WHERE E2.AIJ_FILIAL = S.AD1_FILIAL
                      AND E2.AIJ_NROPOR = S.AD1_NROPOR
                      {where_period_eng_e2}
                )
            ),

            UltimaRevisaoMedicaoEngenharia AS (
                SELECT
                    T.AIJ_FILIAL,
                    T.AIJ_NROPOR,
                    T.AIJ_REVISA AS ULTIMA_REVISA_MEDICAO
                FROM (
                    SELECT
                        M.AIJ_FILIAL,
                        M.AIJ_NROPOR,
                        M.AIJ_REVISA,
                        ROW_NUMBER() OVER (
                            PARTITION BY M.AIJ_FILIAL, M.AIJ_NROPOR
                            ORDER BY
                                M.MINUTOS_REVISAO DESC,
                                M.TEM_ANCORA_LMP DESC,
                                M.AIJ_REVISA DESC
                        ) AS RN
                    FROM EngenhariaMinutosPorRevisao M
                    INNER JOIN RevisoesElegiveisMedicao R
                        ON R.AIJ_FILIAL = M.AIJ_FILIAL
                       AND R.AIJ_NROPOR = M.AIJ_NROPOR
                       AND R.AIJ_REVISA = M.AIJ_REVISA
                ) T
                WHERE T.RN = 1
            ),
            """

        return f"""
            UltimaRevisaoMedicaoEngenharia AS (
                SELECT
                    T.AIJ_FILIAL,
                    T.AIJ_NROPOR,
                    T.AIJ_REVISA AS ULTIMA_REVISA_MEDICAO
                FROM (
                    SELECT
                        R.AIJ_FILIAL,
                        R.AIJ_NROPOR,
                        R.AIJ_REVISA,
                        ROW_NUMBER() OVER (
                            PARTITION BY R.AIJ_FILIAL, R.AIJ_NROPOR
                            ORDER BY
                                CASE
                                    WHEN {where_lmp_anchor_rank_e} THEN 2
                                    ELSE 1
                                END DESC,
                                R.AIJ_REVISA DESC
                        ) AS RN
                    FROM EngenhariaEventos R
                    GROUP BY
                        R.AIJ_FILIAL,
                        R.AIJ_NROPOR,
                        R.AIJ_REVISA,
                        R.AIJ_PROVEN,
                        R.AIJ_STAGE
                ) T
                WHERE T.RN = 1
            ),
            """

    def _get_request_branch(self, request) -> str | None:
        return getattr(request, "branch", None)

    def _sql_process_stage_condition(
        self,
        process_field: str,
        stage_field: str,
        process_stages: dict[str, list[str]],
    ) -> Tuple[str, tuple]:
        clauses = []
        params: list[str] = []

        for process_code, stages in process_stages.items():
            if not stages:
                continue

            placeholders = ",".join("?" for _ in stages)
            clauses.append(f"({process_field} = ? AND {stage_field} IN ({placeholders}))")
            params.append(process_code)
            params.extend(stages)

        if not clauses:
            return "1=0", ()

        return "(" + " OR ".join(clauses) + ")", tuple(params)

    def _sql_lmp_anchor_process_stage_condition(
        self,
        process_field: str,
        stage_field: str,
    ) -> Tuple[str, tuple]:
        return self._sql_process_stage_condition(
            process_field=process_field,
            stage_field=stage_field,
            process_stages=self.settings.lmp_anchor_process_stages,
        )

    def _sql_lmp_followup_process_stage_condition(
        self,
        process_field: str,
        stage_field: str,
    ) -> Tuple[str, tuple]:
        return self._sql_process_stage_condition(
            process_field=process_field,
            stage_field=stage_field,
            process_stages=self.settings.lmp_followup_process_stages,
        )

    def _sql_engineering_support_process_stage_condition(
        self,
        process_field: str,
        stage_field: str,
    ) -> Tuple[str, tuple]:
        return self._sql_process_stage_condition(
            process_field=process_field,
            stage_field=stage_field,
            process_stages=self.settings.engineering_support_process_stages,
        )

    def _sql_sample_anchor_process_stage_condition(
        self,
        process_field: str,
        stage_field: str,
    ) -> Tuple[str, tuple]:
        return self._sql_process_stage_condition(
            process_field=process_field,
            stage_field=stage_field,
            process_stages=self.settings.sample_anchor_process_stages,
        )

    def _sql_lmp_finalized_process_stage_condition(
        self,
        process_field: str,
        stage_field: str,
    ) -> Tuple[str, tuple]:
        return self._sql_process_stage_condition(
            process_field=process_field,
            stage_field=stage_field,
            process_stages=self.settings.lmp_finalized_process_stages,
        )

    def _resolve_listing_type_filter(
        self,
        request: ListLMPRequest,
        *,
        lmp_only: bool = False,
    ) -> str | None:
        return resolve_listing_type_filter(
            request.listing_type,
            lmp_only=lmp_only,
        )

    def _resolve_include_qtd_pi(self, request: ListLMPRequest) -> bool:
        if request.include_qtd_pi is None:
            return False
        return bool(request.include_qtd_pi)

    def _sql_aij_period_filter_clause(
        self,
        field: str,
        date_start: str | None,
        date_end: str | None,
    ) -> Tuple[str, tuple]:
        qb_period = QueryBuilder()
        qb_period.date_range(
            field=field,
            start=date_start,
            end=date_end,
        )
        where_period, params_period = qb_period.build()
        if not where_period:
            return "", ()
        return f"AND {where_period}", params_period

    # =========================
    # SQL FILTER BLOCKS
    # =========================

    def _sql_filter_ad1_active_branch(
        self,
        alias: str = "AD1",
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        return self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, f"{alias}.D_E_L_E_T_"),
                self._branch_filter(qb, f"{alias}.AD1_FILIAL", requested_branch),
            )
        )

    def _sql_filter_adj_active_branch(
        self,
        alias: str = "ADJ",
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        return self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, f"{alias}.D_E_L_E_T_"),
                self._branch_filter(qb, f"{alias}.ADJ_FILIAL", requested_branch),
            )
        )

    def _sql_filter_sb1_active(self, alias: str = "SB1") -> Tuple[str, tuple]:
        return self._build_filter_sql(
            lambda qb: self._active_filter(qb, f"{alias}.D_E_L_E_T_")
        )

    def _sql_lmp_resolved_product_sb1_apply(
        self,
        *,
        adj_alias: str = "P",
        sb_alias: str = "SB1",
    ) -> Tuple[str, tuple]:
        """
        Resolve produto da OV para exibição: prioriza PA DELPI (9026…) cujo
        B1_CODANT aponta para o código ainda ligado no ADJ010 (800…).
        """
        where_sb, params_sb = self._sql_filter_sb1_active(sb_alias)
        sql = f"""
            OUTER APPLY (
                SELECT TOP 1
                    {sb_alias}.B1_GRUPO,
                    {sb_alias}.B1_COD,
                    {sb_alias}.B1_DESC,
                    {sb_alias}.B1_TIPO
                FROM SB1010 {sb_alias}
                WHERE {where_sb}
                  AND (
                      {sb_alias}.B1_COD = {adj_alias}.ADJ_PROD
                      OR (
                          {sb_alias}.B1_CODANT = {adj_alias}.ADJ_PROD
                          AND {sb_alias}.B1_COD LIKE '9026%'
                          AND {sb_alias}.B1_TIPO = 'PA'
                      )
                  )
                ORDER BY
                    CASE
                        WHEN {sb_alias}.B1_COD LIKE '9026%' THEN 0
                        ELSE 1
                    END,
                    {sb_alias}.B1_COD
            ) {sb_alias}
        """
        return sql, params_sb

    def _sql_filter_sb_root_types(self, alias: str = "SB") -> Tuple[str, tuple]:
        return self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, f"{alias}.D_E_L_E_T_"),
                self._root_product_type_filter(qb, f"{alias}.B1_TIPO"),
            )
        )

    def _sql_filter_sb_pi_types(self, alias: str = "SB") -> Tuple[str, tuple]:
        return self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, f"{alias}.D_E_L_E_T_"),
                self._pi_product_type_filter(qb, f"{alias}.B1_TIPO"),
            )
        )

    def _sql_filter_sg_active(self, alias: str = "G") -> Tuple[str, tuple]:
        return self._build_filter_sql(
            lambda qb: self._active_filter(qb, f"{alias}.D_E_L_E_T_")
        )

    def _sql_filter_sa1_active(self, alias: str = "SA1") -> Tuple[str, tuple]:
        return self._build_filter_sql(
            lambda qb: self._active_filter(qb, f"{alias}.D_E_L_E_T_")
        )

    def _sql_filter_sa3_active(self, alias: str = "SA3") -> Tuple[str, tuple]:
        return self._build_filter_sql(
            lambda qb: self._active_filter(qb, f"{alias}.D_E_L_E_T_")
        )

    # =========================
    # SQL BLOCKS
    # =========================

    def _sql_lmp_base_dataset_ctes(
        self,
        request: ListLMPRequest,
        *,
        include_qtd_pi: bool,
        lmp_only: bool = False,
    ) -> Tuple[str, tuple]:
        cte_candidates, params_candidates = self._sql_candidate_lmps_cte(
            request,
            lmp_only=lmp_only,
        )
        cte_hist, params_hist = self._sql_historico_ov_cte(
            scope_cte_name="CandidateLMPs",
            requested_branch=request.branch,
            date_start=request.date_start,
            date_end=request.date_end,
        )

        ctes = [
            cte_candidates,
            cte_hist,
        ]
        params: list = [
            *params_candidates,
            *params_hist,
        ]

        if include_qtd_pi:
            cte_prod, params_prod = self._sql_produtos_lmp_cte(
                scope_cte_name="CandidateLMPs",
                requested_branch=request.branch,
            )
            cte_pi_total, params_pi_total = self._sql_pi_total_by_ov_ctes_from_produtos_lmp()

            ctes.extend([cte_prod, cte_pi_total])
            params.extend([*params_prod, *params_pi_total])

        sql = ",\n".join(ctes)
        return sql, tuple(params)

    def _sql_lmp_base_rows_dataset_query(
        self,
        request: ListLMPRequest,
        *,
        include_qtd_pi: bool,
        order_by: bool,
        lmp_only: bool = False,
    ) -> Tuple[str, tuple]:
        ctes_sql, ctes_params = self._sql_lmp_base_dataset_ctes(
            request,
            include_qtd_pi=include_qtd_pi,
            lmp_only=lmp_only,
        )

        qtd_pi_select = "ISNULL(PI.QTD_PI, 0) AS qtd_pi" if include_qtd_pi else "0 AS qtd_pi"
        qtd_pi_join = """
            LEFT JOIN PI_COUNT_BY_OV PI
                ON PI.ADJ_FILIAL = C.AD1_FILIAL
               AND PI.ADJ_NROPOR = C.AD1_NROPOR
               AND PI.ADJ_REVISA = C.AD1_REVISA
        """ if include_qtd_pi else ""

        qtd_pi_group_by = ",\n                PI.QTD_PI" if include_qtd_pi else ""
        order_clause = """
            ORDER BY
                C.LMP_START_DATE DESC,
                C.AD1_NROPOR DESC
        """ if order_by else ""

        sql = f"""
            WITH
            {ctes_sql}
            SELECT
                C.AD1_FILIAL AS branch,
                C.AD1_NROPOR AS sale_number,
                C.AD1_DESCRI AS sale_description,
                C.LISTING_KIND AS listing_kind,
                C.LMP_START_DATE AS start_date,
                C.LMP_END_DATE AS end_date,
                H.ENGINEERING_STATUS AS engineering_status,
                H.QTD_PASSAGENS_ENG AS qtd_engineering_entries,
                H.QTD_PASSAGENS_ENCERRADAS AS qtd_engineering_closed,
                H.QTD_AVANCOU_ENG AS qtd_advanced_from_engineering,
                H.QTD_RETORNOU_ENG AS qtd_returned_from_engineering,
                H.TEMPO_TOTAL_MINUTOS_ENG AS engineering_total_minutes,
                {qtd_pi_select}
            FROM CandidateLMPs C
            LEFT JOIN EngenhariaResumoUltimaRevisao H
                ON H.AIJ_FILIAL = C.AD1_FILIAL
               AND H.AIJ_NROPOR = C.AD1_NROPOR
            {qtd_pi_join}
            GROUP BY
                C.AD1_FILIAL,
                C.AD1_NROPOR,
                C.AD1_DESCRI,
                C.LISTING_KIND,
                C.LMP_START_DATE,
                C.LMP_END_DATE,
                H.ENGINEERING_STATUS,
                H.QTD_PASSAGENS_ENG,
                H.QTD_PASSAGENS_ENCERRADAS,
                H.QTD_AVANCOU_ENG,
                H.QTD_RETORNOU_ENG,
                H.TEMPO_TOTAL_MINUTOS_ENG
                {qtd_pi_group_by}
            {order_clause}
        """

        return sql, ctes_params

    def _sql_lmp_base_rows_query(
        self,
        request: ListLMPRequest,
        *,
        include_qtd_pi: bool,
    ) -> Tuple[str, tuple]:
        return self._sql_lmp_base_rows_dataset_query(
            request,
            include_qtd_pi=include_qtd_pi,
            order_by=True,
        )

    def _sql_lmp_base_rows_count_query(
        self,
        request: ListLMPRequest,
        *,
        include_qtd_pi: bool,
    ) -> Tuple[str, tuple]:
        ctes_sql, ctes_params = self._sql_lmp_base_dataset_ctes(
            request,
            include_qtd_pi=include_qtd_pi,
        )

        qtd_pi_join = """
            LEFT JOIN PI_COUNT_BY_OV PI
                ON PI.ADJ_FILIAL = C.AD1_FILIAL
               AND PI.ADJ_NROPOR = C.AD1_NROPOR
               AND PI.ADJ_REVISA = C.AD1_REVISA
        """ if include_qtd_pi else ""

        qtd_pi_group_by = ",\n                    PI.QTD_PI" if include_qtd_pi else ""

        sql = f"""
            WITH
            {ctes_sql}
            SELECT COUNT(*) AS total
            FROM (
                SELECT
                    C.AD1_FILIAL,
                    C.AD1_NROPOR
                FROM CandidateLMPs C
                LEFT JOIN EngenhariaResumoUltimaRevisao H
                    ON H.AIJ_FILIAL = C.AD1_FILIAL
                   AND H.AIJ_NROPOR = C.AD1_NROPOR
                {qtd_pi_join}
                GROUP BY
                    C.AD1_FILIAL,
                    C.AD1_NROPOR,
                    C.AD1_DESCRI,
                    C.LISTING_KIND,
                    C.LMP_START_DATE,
                    C.LMP_END_DATE,
                    H.ENGINEERING_STATUS,
                    H.QTD_PASSAGENS_ENG,
                    H.QTD_PASSAGENS_ENCERRADAS,
                    H.QTD_AVANCOU_ENG,
                    H.QTD_RETORNOU_ENG,
                    H.TEMPO_TOTAL_MINUTOS_ENG
                    {qtd_pi_group_by}
            ) BASE_ROWS
        """
        return sql, ctes_params

    def _sql_lmp_base_rows_paged_query(
        self,
        request: ListLMPRequest,
        *,
        include_qtd_pi: bool,
    ) -> Tuple[str, tuple]:
        base_sql, base_params = self._sql_lmp_base_rows_dataset_query(
            request,
            include_qtd_pi=include_qtd_pi,
            order_by=True,
        )

        page = request.page or 1
        page_size = request.page_size or 0
        offset = (page - 1) * page_size

        sql = f"""
            {base_sql}
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
        """
        params = (*base_params, offset, page_size)
        return sql, params

    def _sql_lmp_summary_rows_query(
        self,
        request: ListLMPRequest,
        *,
        include_qtd_pi: bool,
        lmp_only: bool = True,
    ) -> Tuple[str, tuple]:
        ctes_sql, ctes_params = self._sql_lmp_base_dataset_ctes(
            request,
            include_qtd_pi=include_qtd_pi,
            lmp_only=lmp_only,
        )

        qtd_pi_select = "ISNULL(PI.QTD_PI, 0) AS qtd_pi" if include_qtd_pi else "0 AS qtd_pi"
        qtd_pi_join = """
            LEFT JOIN PI_COUNT_BY_OV PI
                ON PI.ADJ_FILIAL = C.AD1_FILIAL
               AND PI.ADJ_NROPOR = C.AD1_NROPOR
               AND PI.ADJ_REVISA = C.AD1_REVISA
        """ if include_qtd_pi else ""

        qtd_pi_group_by = ",\n                PI.QTD_PI" if include_qtd_pi else ""

        sql = f"""
            WITH
            {ctes_sql}
            SELECT
                C.AD1_FILIAL AS branch,
                C.AD1_NROPOR AS sale_number,
                C.AD1_DESCRI AS sale_description,
                C.LISTING_KIND AS listing_kind,
                C.LMP_START_DATE AS start_date,
                C.LMP_END_DATE AS end_date,
                H.ENGINEERING_STATUS AS engineering_status,
                H.TEMPO_TOTAL_MINUTOS_ENG AS engineering_total_minutes,
                {qtd_pi_select}
            FROM CandidateLMPs C
            LEFT JOIN EngenhariaResumoUltimaRevisao H
                ON H.AIJ_FILIAL = C.AD1_FILIAL
               AND H.AIJ_NROPOR = C.AD1_NROPOR
            {qtd_pi_join}
            GROUP BY
                C.AD1_FILIAL,
                C.AD1_NROPOR,
                C.AD1_DESCRI,
                C.LISTING_KIND,
                C.LMP_START_DATE,
                C.LMP_END_DATE,
                H.ENGINEERING_STATUS,
                H.TEMPO_TOTAL_MINUTOS_ENG
                {qtd_pi_group_by}
            ORDER BY
                C.LMP_START_DATE DESC,
                C.AD1_NROPOR DESC
        """

        return sql, ctes_params

    def _sql_eng_support_ov_reference_cte(
        self,
        requested_branch: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
    ) -> Tuple[str, tuple]:
        where_aij_base, params_aij_base = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", requested_branch),
            )
        )
        where_eng_support, params_eng_support = (
            self._sql_engineering_support_process_stage_condition(
                "A.AIJ_PROVEN",
                "A.AIJ_STAGE",
            )
        )
        where_period, params_period = self._sql_aij_period_filter_clause(
            "A.AIJ_DTINIC",
            date_start,
            date_end,
        )
        where_ad1, params_ad1 = self._sql_filter_ad1_active_branch("AD1", requested_branch)

        sql = f"""
            EngSupportOvRef AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA,
                    MIN(A.AIJ_DTINIC) AS ANCHOR_START_DATE,
                    MAX(
                        COALESCE(NULLIF(A.AIJ_DTENCE, ''), A.AIJ_DTINIC)
                    ) AS ANCHOR_END_DATE
                FROM AIJ010 A
                INNER JOIN AD1010 AD1
                    ON AD1.AD1_FILIAL = A.AIJ_FILIAL
                   AND AD1.AD1_NROPOR = A.AIJ_NROPOR
                   AND AD1.AD1_REVISA = A.AIJ_REVISA
                WHERE {where_ad1}
                  AND {where_aij_base}
                  AND {where_eng_support}
                  {where_period}
                GROUP BY
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA
            )
        """
        return sql, (*params_ad1, *params_aij_base, *params_eng_support, *params_period)

    def _apply_effective_listing_type_filter_to_select(
        self,
        request: ListLMPRequest,
        select_sql: str,
        select_params: tuple,
    ) -> Tuple[str, tuple]:
        """Filtra pelo tipo exibido após reclassificação Amostra/Outro."""
        listing_filter = self._resolve_listing_type_filter(request, lmp_only=False)
        if not listing_filter:
            return select_sql, select_params

        inner_sql = select_sql
        order_clause = ""
        order_marker = "\n            ORDER BY"
        order_index = select_sql.rfind(order_marker)
        if order_index != -1:
            inner_sql = select_sql[:order_index]
            order_clause = (
                select_sql[order_index:]
                .replace("C.LMP_START_DATE", "start_date")
                .replace("C.AD1_NROPOR", "sale_number")
            )

        return (
            f"""
            SELECT *
            FROM (
                {inner_sql}
            ) EFFECTIVE_LISTING_ROWS
            WHERE EFFECTIVE_LISTING_ROWS.listing_kind = ?
            {order_clause}
            """,
            (*select_params, listing_filter),
        )

    def _candidate_scope_lmp_only(self, request: ListLMPRequest) -> bool:
        """Quando o filtro efetivo é só LMP, pula OVs «Outro» sem âncora de listagem."""
        return self._resolve_listing_type_filter(request, lmp_only=False) == LISTING_KIND_LMP

    def _sql_work_month_lmp_candidates_cte(
        self,
        request: ListLMPRequest,
        *,
        lmp_only: bool = False,
    ) -> Tuple[str, tuple]:
        """
        Revisões com trabalho LMP no mês (first_eng ou âncora na revisão) + fallback âncora OV.
        """
        del lmp_only
        where_aij_base, params_aij_base = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", request.branch),
            )
        )
        where_lmp_finalized, params_lmp_finalized = (
            self._sql_lmp_finalized_process_stage_condition(
                "A.AIJ_PROVEN",
                "A.AIJ_STAGE",
            )
        )
        where_lmp_anchor_a, params_lmp_anchor_a = self._sql_lmp_anchor_process_stage_condition(
            "A.AIJ_PROVEN",
            "A.AIJ_STAGE",
        )
        where_eng_support_a, params_eng_support_a = (
            self._sql_engineering_support_process_stage_condition(
                "A.AIJ_PROVEN",
                "A.AIJ_STAGE",
            )
        )
        where_sample_anchor, params_sample_anchor = (
            self._sql_sample_anchor_process_stage_condition(
                "A.AIJ_PROVEN",
                "A.AIJ_STAGE",
            )
        )

        qb_rev_first = QueryBuilder()
        qb_rev_first.date_range(
            field="R.REV_FIRST_ENG",
            start=request.date_start,
            end=request.date_end,
        )
        where_rev_first, params_rev_first = qb_rev_first.build()

        qb_rev_anchor = QueryBuilder()
        qb_rev_anchor.date_range(
            field="R.ANCHOR_DATE",
            start=request.date_start,
            end=request.date_end,
        )
        where_rev_anchor, params_rev_anchor = qb_rev_anchor.build()

        if where_rev_first and where_rev_anchor:
            where_work_month = f"(({where_rev_first}) OR ({where_rev_anchor}))"
            params_work_month = (*params_rev_first, *params_rev_anchor)
        elif where_rev_first:
            where_work_month = where_rev_first
            params_work_month = params_rev_first
        elif where_rev_anchor:
            where_work_month = where_rev_anchor
            params_work_month = params_rev_anchor
        else:
            where_work_month = "1=1"
            params_work_month = ()

        where_ad1, params_ad1 = self._sql_filter_ad1_active_branch("AD1", request.branch)

        where_period_touch, params_period_touch = self._sql_aij_period_filter_clause(
            "A.AIJ_DTINIC",
            request.date_start,
            request.date_end,
        )
        cte_marker, params_marker = self._sql_listing_anchor_marker_cte(
            request.branch,
            request.date_start,
            request.date_end,
        )
        where_period_anchor, params_period_anchor = self._sql_candidate_period_where_clause(
            request,
            anchor_date_sql="L.ANCHOR_START_DATE",
            homolog_date_sql="LF.ANCHOR_START_DATE",
        )

        work_month_rows_sql = f"""
                SELECT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    W.AIJ_REVISA AS AD1_REVISA,
                    AD1.AD1_DESCRI,
                    ? AS LISTING_KIND,
                    CASE
                        WHEN SA.AIJ_NROPOR IS NOT NULL THEN 1
                        ELSE 0
                    END AS HAS_SAMPLE_ANCHOR,
                    1 AS HAS_LMP_FINALIZED,
                    W.WORK_START_DATE AS LMP_START_DATE,
                    W.HOMOLOG_END_DATE AS LMP_END_DATE,
                    W.CYCLE_INDEX AS CYCLE_INDEX
                FROM WorkMonthRevisionsInPeriod W
                INNER JOIN {self._totvs_from("AD1010", "AD1")}
                    ON AD1.AD1_FILIAL = W.AIJ_FILIAL
                   AND AD1.AD1_NROPOR = W.AIJ_NROPOR
                   AND AD1.AD1_REVISA = W.AIJ_REVISA
                LEFT JOIN SampleOnRevision SA
                    ON SA.AIJ_FILIAL = W.AIJ_FILIAL
                   AND SA.AIJ_NROPOR = W.AIJ_NROPOR
                   AND SA.AIJ_REVISA = W.AIJ_REVISA
                WHERE {where_ad1}
        """

        anchor_supplement_sql = f"""
                SELECT DISTINCT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA,
                    AD1.AD1_DESCRI,
                    L.LISTING_KIND,
                    CASE
                        WHEN SA.AIJ_NROPOR IS NOT NULL THEN 1
                        ELSE 0
                    END AS HAS_SAMPLE_ANCHOR,
                    CASE
                        WHEN LF.AIJ_NROPOR IS NOT NULL THEN 1
                        ELSE 0
                    END AS HAS_LMP_FINALIZED,
                    L.ANCHOR_START_DATE AS LMP_START_DATE,
                    L.ANCHOR_END_DATE AS LMP_END_DATE,
                    1 AS CYCLE_INDEX
                FROM {self._totvs_from("AD1010", "AD1")}
                INNER JOIN ListingAnchorEventos L
                    ON L.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND L.AIJ_NROPOR = AD1.AD1_NROPOR
                   AND L.AIJ_REVISA = AD1.AD1_REVISA
                LEFT JOIN SampleAnchorOvKeys SA
                    ON SA.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND SA.AIJ_NROPOR = AD1.AD1_NROPOR
                   AND SA.AIJ_REVISA = AD1.AD1_REVISA
                LEFT JOIN LmpFinalizedAnchorChosen LF
                    ON LF.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND LF.AIJ_NROPOR = AD1.AD1_NROPOR
                   AND LF.AIJ_REVISA = AD1.AD1_REVISA
                WHERE {where_ad1}
                  AND {where_period_anchor}
                  AND NOT EXISTS (
                      SELECT 1
                      FROM WorkMonthRevisionKeys WK
                      WHERE WK.AIJ_FILIAL = AD1.AD1_FILIAL
                        AND WK.AIJ_NROPOR = AD1.AD1_NROPOR
                        AND WK.AIJ_REVISA = AD1.AD1_REVISA
                  )
        """

        sql = f"""
            OvRevisionTouchedInPeriod AS (
                SELECT DISTINCT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA
                FROM {self._totvs_from("AIJ010", "A")}
                WHERE {where_aij_base}
                  {where_period_touch}
                  AND (
                      ({where_eng_support_a})
                      OR ({where_lmp_anchor_a})
                      OR ({where_lmp_finalized})
                      OR ({where_sample_anchor})
                  )
            ),

            RevCycleFacts AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA,
                    MIN(
                        CASE
                            WHEN ({where_lmp_finalized}) THEN A.AIJ_DTINIC
                        END
                    ) AS HOMOLOG_DATE,
                    MAX(
                        CASE
                            WHEN ({where_lmp_finalized}) THEN
                                CASE
                                    WHEN ISNULL(A.AIJ_DTENCE, '') <> '' THEN A.AIJ_DTENCE
                                    ELSE A.AIJ_DTINIC
                                END
                        END
                    ) AS HOMOLOG_END_DATE,
                    MIN(
                        CASE
                            WHEN ({where_eng_support_a}) THEN A.AIJ_DTINIC
                        END
                    ) AS REV_FIRST_ENG,
                    MIN(
                        CASE
                            WHEN ({where_lmp_anchor_a}) THEN A.AIJ_DTINIC
                        END
                    ) AS ANCHOR_DATE,
                    MAX(
                        CASE
                            WHEN ({where_sample_anchor}) THEN 1
                            ELSE 0
                        END
                    ) AS HAS_SAMPLE
                FROM {self._totvs_from("AIJ010", "A")}
                INNER JOIN OvRevisionTouchedInPeriod K
                    ON K.AIJ_FILIAL = A.AIJ_FILIAL
                   AND K.AIJ_NROPOR = A.AIJ_NROPOR
                   AND K.AIJ_REVISA = A.AIJ_REVISA
                WHERE {where_aij_base}
                GROUP BY
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA
            ),

            RevCycleRows AS (
                SELECT
                    F.AIJ_FILIAL,
                    F.AIJ_NROPOR,
                    F.AIJ_REVISA,
                    F.HOMOLOG_DATE,
                    F.HOMOLOG_END_DATE,
                    F.REV_FIRST_ENG,
                    F.ANCHOR_DATE
                FROM RevCycleFacts F
                WHERE F.HOMOLOG_DATE IS NOT NULL
            ),

            WorkMonthRevisionsInPeriod AS (
                SELECT
                    R.AIJ_FILIAL,
                    R.AIJ_NROPOR,
                    R.AIJ_REVISA,
                    R.HOMOLOG_END_DATE,
                    COALESCE(R.REV_FIRST_ENG, R.ANCHOR_DATE, R.HOMOLOG_DATE) AS WORK_START_DATE,
                    ROW_NUMBER() OVER (
                        PARTITION BY R.AIJ_FILIAL, R.AIJ_NROPOR
                        ORDER BY
                            COALESCE(R.REV_FIRST_ENG, R.ANCHOR_DATE, R.HOMOLOG_DATE),
                            R.AIJ_REVISA
                    ) AS CYCLE_INDEX
                FROM RevCycleRows R
                WHERE {where_work_month}
            ),

            WorkMonthRevisionKeys AS (
                SELECT
                    W.AIJ_FILIAL,
                    W.AIJ_NROPOR,
                    W.AIJ_REVISA
                FROM WorkMonthRevisionsInPeriod W
            ),

            SampleOnRevision AS (
                SELECT
                    F.AIJ_FILIAL,
                    F.AIJ_NROPOR,
                    F.AIJ_REVISA
                FROM RevCycleFacts F
                WHERE F.HAS_SAMPLE = 1
            ),

            {cte_marker},

            CandidateLMPs AS (
                {work_month_rows_sql}

                UNION

                {anchor_supplement_sql}
            )
        """

        params: list = [
            *params_aij_base,
            *params_period_touch,
            *params_eng_support_a,
            *params_lmp_anchor_a,
            *params_lmp_finalized,
            *params_sample_anchor,
            *params_aij_base,
            *params_lmp_finalized,
            *params_lmp_finalized,
            *params_eng_support_a,
            *params_lmp_anchor_a,
            *params_sample_anchor,
            *params_work_month,
            *params_marker,
            LISTING_KIND_LMP,
            *params_ad1,
            *params_ad1,
            *params_period_anchor,
        ]
        return sql, tuple(params)

    def _sql_homolog_cycle_candidates_cte(
        self,
        request: ListLMPRequest,
        *,
        lmp_only: bool = False,
    ) -> Tuple[str, tuple]:
        """
        Uma linha por ciclo de homologação LMP (000012) no período — reaberturas e revisões.

        O histórico AIJ010 é a fonte; pastas RQ-060 são referência de auditoria, não filtro SQL.
        """
        where_aij_base, params_aij_base = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", request.branch),
            )
        )
        where_lmp_finalized, params_lmp_finalized = (
            self._sql_lmp_finalized_process_stage_condition(
                "A.AIJ_PROVEN",
                "A.AIJ_STAGE",
            )
        )
        where_sample_anchor, params_sample_anchor = (
            self._sql_sample_anchor_process_stage_condition(
                "A.AIJ_PROVEN",
                "A.AIJ_STAGE",
            )
        )
        qb_period_homolog = QueryBuilder()
        qb_period_homolog.date_range(
            field="H.HOMOLOG_DATE",
            start=request.date_start,
            end=request.date_end,
        )
        where_period_homolog, params_period_homolog = qb_period_homolog.build()
        if not where_period_homolog:
            where_period_homolog = "1=1"
        where_ad1, params_ad1 = self._sql_filter_ad1_active_branch("AD1", request.branch)

        candidate_body = f"""
                SELECT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    H.AIJ_REVISA AS AD1_REVISA,
                    AD1.AD1_DESCRI,
                    ? AS LISTING_KIND,
                    CASE
                        WHEN SA.AIJ_NROPOR IS NOT NULL THEN 1
                        ELSE 0
                    END AS HAS_SAMPLE_ANCHOR,
                    1 AS HAS_LMP_FINALIZED,
                    H.HOMOLOG_DATE AS LMP_START_DATE,
                    H.HOMOLOG_END_DATE AS LMP_END_DATE,
                    H.CYCLE_INDEX AS CYCLE_INDEX
                FROM HomologCyclesInPeriod H
                INNER JOIN AD1010 AD1
                    ON AD1.AD1_FILIAL = H.AIJ_FILIAL
                   AND AD1.AD1_NROPOR = H.AIJ_NROPOR
                   AND AD1.AD1_REVISA = H.AIJ_REVISA
                LEFT JOIN SampleOnRevision SA
                    ON SA.AIJ_FILIAL = H.AIJ_FILIAL
                   AND SA.AIJ_NROPOR = H.AIJ_NROPOR
                   AND SA.AIJ_REVISA = H.AIJ_REVISA
                WHERE {where_ad1}
        """

        sql = f"""
            HomologByRevisionRaw AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA,
                    MIN(A.AIJ_DTINIC) AS HOMOLOG_DATE,
                    MAX(
                        CASE
                            WHEN ISNULL(A.AIJ_DTENCE, '') <> '' THEN A.AIJ_DTENCE
                            ELSE A.AIJ_DTINIC
                        END
                    ) AS HOMOLOG_END_DATE
                FROM AIJ010 A
                WHERE {where_aij_base}
                  AND {where_lmp_finalized}
                GROUP BY
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA
            ),

            HomologCyclesInPeriod AS (
                SELECT
                    H.AIJ_FILIAL,
                    H.AIJ_NROPOR,
                    H.AIJ_REVISA,
                    H.HOMOLOG_DATE,
                    H.HOMOLOG_END_DATE,
                    ROW_NUMBER() OVER (
                        PARTITION BY H.AIJ_FILIAL, H.AIJ_NROPOR
                        ORDER BY H.HOMOLOG_DATE, H.AIJ_REVISA
                    ) AS CYCLE_INDEX
                FROM HomologByRevisionRaw H
                WHERE {where_period_homolog}
            ),

            SampleOnRevision AS (
                SELECT DISTINCT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA
                FROM AIJ010 A
                WHERE {where_aij_base}
                  AND {where_sample_anchor}
            ),

            CandidateLMPs AS (
                {candidate_body}
            )
        """

        params: list = [
            *params_aij_base,
            *params_lmp_finalized,
            *params_period_homolog,
            *params_aij_base,
            *params_sample_anchor,
            LISTING_KIND_LMP,
            *params_ad1,
        ]
        return sql, tuple(params)

    def _sql_candidate_lmps_cte(
        self,
        request: ListLMPRequest,
        *,
        lmp_only: bool = False,
    ) -> Tuple[str, tuple]:
        if (
            self._uses_work_month_lmp_listing()
            and self._has_listing_period_filter(
                request.date_start,
                request.date_end,
            )
        ):
            return self._sql_work_month_lmp_candidates_cte(request, lmp_only=lmp_only)

        if (
            self._uses_homolog_cycle_listing()
            and self._has_listing_period_filter(
                request.date_start,
                request.date_end,
            )
        ):
            return self._sql_homolog_cycle_candidates_cte(request, lmp_only=lmp_only)

        anchor_period_start, anchor_period_end = self._listing_anchor_period_dates(
            request.date_start,
            request.date_end,
        )
        cte_marker, params_marker = self._sql_listing_anchor_marker_cte(
            request.branch,
            anchor_period_start,
            anchor_period_end,
        )
        where_ad1, params_ad1 = self._sql_filter_ad1_active_branch("AD1", request.branch)

        where_period_anchor, params_period_anchor = self._sql_candidate_period_where_clause(
            request,
            anchor_date_sql="L.ANCHOR_START_DATE",
            homolog_date_sql="LF.ANCHOR_START_DATE",
        )
        where_period_other, params_period_other = self._sql_candidate_period_where_clause(
            request,
            anchor_date_sql="R.ANCHOR_START_DATE",
            homolog_date_sql="R.ANCHOR_START_DATE",
        )

        has_period = self._has_listing_period_filter(
            request.date_start,
            request.date_end,
        )
        first_eng_cte = ""
        first_eng_params: tuple = ()
        first_eng_join = ""
        anchor_start_expr = "L.ANCHOR_START_DATE"
        other_start_expr = "R.ANCHOR_START_DATE"
        if has_period and LmpPeriodInclusionSemanticsService.requires_first_eng_join(
            self._period_inclusion_policy(),
        ):
            first_eng_cte, first_eng_params = self._sql_ov_first_engineering_arrival_cte(
                request.branch,
            )
            first_eng_join = """
                LEFT JOIN OvFirstEngineeringArrival F
                    ON F.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND F.AIJ_NROPOR = AD1.AD1_NROPOR
            """

        anchor_candidates_sql = f"""
                SELECT DISTINCT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA,
                    AD1.AD1_DESCRI,
                    L.LISTING_KIND,
                    CASE
                        WHEN SA.AIJ_NROPOR IS NOT NULL THEN 1
                        ELSE 0
                    END AS HAS_SAMPLE_ANCHOR,
                    CASE
                        WHEN LF.AIJ_NROPOR IS NOT NULL THEN 1
                        ELSE 0
                    END AS HAS_LMP_FINALIZED,
                    {anchor_start_expr} AS LMP_START_DATE,
                    L.ANCHOR_END_DATE AS LMP_END_DATE,
                    1 AS CYCLE_INDEX
                FROM AD1010 AD1
                INNER JOIN ListingAnchorEventos L
                    ON L.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND L.AIJ_NROPOR = AD1.AD1_NROPOR
                   AND L.AIJ_REVISA = AD1.AD1_REVISA
                LEFT JOIN SampleAnchorOvKeys SA
                    ON SA.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND SA.AIJ_NROPOR = AD1.AD1_NROPOR
                   AND SA.AIJ_REVISA = AD1.AD1_REVISA
                LEFT JOIN LmpFinalizedAnchorChosen LF
                    ON LF.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND LF.AIJ_NROPOR = AD1.AD1_NROPOR
                   AND LF.AIJ_REVISA = AD1.AD1_REVISA
                {first_eng_join}
                WHERE {where_ad1}
                  AND {where_period_anchor}
        """

        other_candidates_sql = f"""
                SELECT DISTINCT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA,
                    AD1.AD1_DESCRI,
                    ? AS LISTING_KIND,
                    0 AS HAS_SAMPLE_ANCHOR,
                    0 AS HAS_LMP_FINALIZED,
                    {other_start_expr} AS LMP_START_DATE,
                    R.ANCHOR_END_DATE AS LMP_END_DATE,
                    1 AS CYCLE_INDEX
                FROM AD1010 AD1
                INNER JOIN EngSupportOvRef R
                    ON R.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND R.AIJ_NROPOR = AD1.AD1_NROPOR
                   AND R.AIJ_REVISA = AD1.AD1_REVISA
                {first_eng_join}
                WHERE {where_ad1}
                  AND {where_period_other}
                  AND NOT EXISTS (
                      SELECT 1
                      FROM ListingAnchorEventos L2
                      WHERE L2.AIJ_FILIAL = AD1.AD1_FILIAL
                        AND L2.AIJ_NROPOR = AD1.AD1_NROPOR
                        AND L2.AIJ_REVISA = AD1.AD1_REVISA
                  )
        """

        candidate_body = anchor_candidates_sql
        cte_prefix = cte_marker
        if first_eng_cte:
            cte_prefix = f"{cte_marker},\n            {first_eng_cte}"

        if lmp_only:
            sql = f"""
                {cte_prefix},

                CandidateLMPs AS (
                    {candidate_body}
                )
            """
            params: list = [
                *params_marker,
                *first_eng_params,
                *params_ad1,
                *params_period_anchor,
            ]
            return sql, tuple(params)

        cte_eng_ref, params_eng_ref = self._sql_eng_support_ov_reference_cte(
            request.branch,
            anchor_period_start,
            anchor_period_end,
        )

        candidate_body = f"""
                {anchor_candidates_sql}

                UNION

                {other_candidates_sql}
            """

        sql = f"""
            {cte_prefix},
            {cte_eng_ref},

            CandidateLMPs AS (
                {candidate_body}
            )
        """

        params = [*params_marker, *first_eng_params, *params_eng_ref]
        params.extend(
            [
                *params_ad1,
                *params_period_anchor,
                LISTING_KIND_OTHER,
                *params_ad1,
                *params_period_other,
            ]
        )

        return sql, tuple(params)

    def _sql_engenharia_resumo_ultima_revisao_select(
        self,
        *,
        eng_minutes_expr: str,
        where_sample_eng_e: str,
        lite: bool,
    ) -> str:
        """Colunas de EngenhariaResumoUltimaRevisao; lite omite passagens/datas extras."""
        tempo_cols = f"""
                    SUM({eng_minutes_expr}) AS TEMPO_TOTAL_MINUTOS_ENG,
                    SUM(
                        CASE
                            WHEN {where_sample_eng_e}
                            THEN {eng_minutes_expr}
                            ELSE 0
                        END
                    ) AS TEMPO_MINUTOS_AMOSTRA_ENG,
                    S.ENGINEERING_STATUS AS ENGINEERING_STATUS"""
        if lite:
            return f"""
                    E.AIJ_FILIAL,
                    E.AIJ_NROPOR,
                    MAX(M.ULTIMA_REVISA_MEDICAO) AS MEASUREMENT_REVISION,
                    {tempo_cols}"""

        return f"""
                    E.AIJ_FILIAL,
                    E.AIJ_NROPOR,
                    MAX(M.ULTIMA_REVISA_MEDICAO) AS MEASUREMENT_REVISION,
                    MIN(E.AIJ_DTINIC) AS START_DATE,
                    MAX(
                        CASE
                            WHEN ISNULL(E.AIJ_DTENCE, '') <> '' THEN E.AIJ_DTENCE
                            WHEN ISNULL(E.PROXIMO_DTINIC_GLOBAL, '') <> '' THEN E.PROXIMO_DTINIC_GLOBAL
                            ELSE NULL
                        END
                    ) AS END_DATE,
                    COUNT(*) AS QTD_PASSAGENS_ENG,
                    SUM(
                        CASE
                            WHEN ISNULL(E.AIJ_DTENCE, '') <> ''
                              OR ISNULL(E.PROXIMO_DTINIC_GLOBAL, '') <> ''
                            THEN 1
                            ELSE 0
                        END
                    ) AS QTD_PASSAGENS_ENCERRADAS,
                    {tempo_cols},
                    SUM(
                        CASE
                            WHEN (
                                ISNULL(E.AIJ_DTENCE, '') <> ''
                                OR ISNULL(E.PROXIMO_DTINIC_GLOBAL, '') <> ''
                            )
                            AND E.PROXIMO_STAGE_GLOBAL IS NOT NULL
                            AND ISNULL(E.PROXIMO_EH_ENG_GLOBAL, 0) = 0
                            AND E.PROXIMA_REVISA_GLOBAL = E.AIJ_REVISA
                            AND E.PROXIMO_STAGE_GLOBAL > E.AIJ_STAGE
                            THEN 1
                            ELSE 0
                        END
                    ) AS QTD_AVANCOU_ENG,
                    SUM(
                        CASE
                            WHEN (
                                ISNULL(E.AIJ_DTENCE, '') <> ''
                                OR ISNULL(E.PROXIMO_DTINIC_GLOBAL, '') <> ''
                            )
                            AND E.PROXIMO_STAGE_GLOBAL IS NOT NULL
                            AND ISNULL(E.PROXIMO_EH_ENG_GLOBAL, 0) = 0
                            AND (
                                E.PROXIMA_REVISA_GLOBAL > E.AIJ_REVISA
                                OR E.PROXIMO_STAGE_GLOBAL < E.AIJ_STAGE
                            )
                            THEN 1
                            ELSE 0
                        END
                    ) AS QTD_RETORNOU_ENG"""

    def _sql_historico_ov_cte(
        self,
        scope_cte_name: str | None = None,
        requested_branch: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        *,
        eng_resumo_lite: bool = False,
        per_candidate_revision: bool = False,
    ) -> Tuple[str, tuple]:
        where_aij_base_a, params_aij_base_a = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", requested_branch),
            )
        )

        where_eng_support_e, params_eng_support_e = self._sql_engineering_support_process_stage_condition(
            "E.AIJ_PROVEN",
            "E.AIJ_STAGE",
        )

        where_eng_support_next, params_eng_support_next = self._sql_engineering_support_process_stage_condition(
            "E.NEXT_PROVEN",
            "E.NEXT_STAGE",
        )

        where_lmp_anchor_rank_e, params_lmp_anchor_rank_e = self._sql_lmp_anchor_process_stage_condition(
            "R.AIJ_PROVEN",
            "R.AIJ_STAGE",
        )

        where_lmp_anchor_rank_m, params_lmp_anchor_rank_m = self._sql_lmp_anchor_process_stage_condition(
            "M.AIJ_PROVEN",
            "M.AIJ_STAGE",
        )

        use_period_revision = self._uses_period_revision_measurement(
            scope_cte_name=scope_cte_name,
            date_start=date_start,
            date_end=date_end,
        )
        where_period_eng, params_period_eng = self._sql_aij_period_filter_clause(
            "E.AIJ_DTINIC",
            date_start,
            date_end,
        )
        where_period_eng_e2, _params_period_eng_e2 = self._sql_aij_period_filter_clause(
            "E2.AIJ_DTINIC",
            date_start,
            date_end,
        )
        eng_minutes_expr = self._sql_event_engineering_minutes_expr("E")
        where_sample_eng_e, params_sample_eng_e = (
            self._sql_sample_anchor_process_stage_condition(
                "E.AIJ_PROVEN",
                "E.AIJ_STAGE",
            )
        )

        scope_join_a = ""
        if scope_cte_name:
            revision_match = ""
            if per_candidate_revision or not use_period_revision:
                revision_match = "AND SCOPE_A.AD1_REVISA = A.AIJ_REVISA"
            scope_join_a = f"""
                INNER JOIN {scope_cte_name} SCOPE_A
                    ON SCOPE_A.AD1_FILIAL = A.AIJ_FILIAL
                   AND SCOPE_A.AD1_NROPOR = A.AIJ_NROPOR
                   {revision_match}
            """

        status_group_by = "E.AIJ_FILIAL, E.AIJ_NROPOR"
        eng_resumo_group_by = "E.AIJ_FILIAL, E.AIJ_NROPOR, S.ENGINEERING_STATUS"
        if per_candidate_revision:
            status_group_by = "E.AIJ_FILIAL, E.AIJ_NROPOR, E.AIJ_REVISA"
            eng_resumo_group_by = (
                "E.AIJ_FILIAL, E.AIJ_NROPOR, E.AIJ_REVISA, S.ENGINEERING_STATUS"
            )
            status_revision_select = "E.AIJ_REVISA,"
            status_revision_join = "AND S.AIJ_REVISA = E.AIJ_REVISA"
        else:
            status_revision_select = ""
            status_revision_join = ""

        win = """PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
                        ORDER BY
                            A.AIJ_REVISA,
                            A.AIJ_DTINIC,
                            A.AIJ_HRINIC,
                            A.AIJ_STAGE,
                            A.R_E_C_N_O_"""

        period_revision_measurement_ctes = self._sql_period_revision_measurement_ctes(
            use_period_revision=use_period_revision,
            per_candidate_revision=per_candidate_revision,
            scope_cte_name=scope_cte_name,
            where_period_eng=where_period_eng,
            where_period_eng_e2=where_period_eng_e2,
            where_lmp_anchor_rank_e=where_lmp_anchor_rank_e,
            where_lmp_anchor_rank_m=where_lmp_anchor_rank_m,
            eng_minutes_expr=eng_minutes_expr,
        )

        sql = f"""
            TodosEventosOV AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA,
                    A.AIJ_PROVEN,
                    A.AIJ_STAGE,
                    A.AIJ_DTINIC,
                    A.AIJ_HRINIC,
                    A.AIJ_DTLIMI,
                    A.AIJ_HRLIMI,
                    A.AIJ_DTENCE,
                    A.AIJ_HRENCE,
                    A.AIJ_HISTOR,
                    A.AIJ_STATUS,
                    A.R_E_C_N_O_,
                    LEAD(A.AIJ_REVISA) OVER ({win}) AS NEXT_REVISA,
                    LEAD(A.AIJ_PROVEN) OVER ({win}) AS NEXT_PROVEN,
                    LEAD(A.AIJ_STAGE)  OVER ({win}) AS NEXT_STAGE,
                    LEAD(A.AIJ_DTINIC) OVER ({win}) AS NEXT_DTINIC,
                    LEAD(A.AIJ_HRINIC) OVER ({win}) AS NEXT_HRINIC,
                    LEAD(A.AIJ_DTENCE) OVER ({win}) AS NEXT_DTENCE,
                    LEAD(A.AIJ_HRENCE) OVER ({win}) AS NEXT_HRENCE
                FROM {self._totvs_from("AIJ010", "A")}
                {scope_join_a}
                WHERE {where_aij_base_a}
            ),

            EngenhariaEventos AS (
                SELECT
                    E.AIJ_FILIAL,
                    E.AIJ_NROPOR,
                    E.AIJ_REVISA,
                    E.AIJ_PROVEN,
                    E.AIJ_STAGE,
                    E.AIJ_DTINIC,
                    E.AIJ_HRINIC,
                    E.AIJ_DTLIMI,
                    E.AIJ_HRLIMI,
                    E.AIJ_DTENCE,
                    E.AIJ_HRENCE,
                    E.AIJ_HISTOR,
                    E.AIJ_STATUS,
                    E.R_E_C_N_O_,
                    E.NEXT_REVISA  AS PROXIMA_REVISA_GLOBAL,
                    E.NEXT_PROVEN  AS PROXIMO_PROVEN_GLOBAL,
                    E.NEXT_STAGE   AS PROXIMO_STAGE_GLOBAL,
                    E.NEXT_DTINIC  AS PROXIMO_DTINIC_GLOBAL,
                    E.NEXT_HRINIC  AS PROXIMO_HRINIC_GLOBAL,
                    E.NEXT_DTENCE  AS PROXIMO_DTENCE_GLOBAL,
                    E.NEXT_HRENCE  AS PROXIMO_HRENCE_GLOBAL,
                    CASE
                        WHEN {where_eng_support_next} THEN 1
                        ELSE 0
                    END AS PROXIMO_EH_ENG_GLOBAL
                FROM TodosEventosOV E
                WHERE {where_eng_support_e}
            ),

            {period_revision_measurement_ctes}
            StatusUltimaRevisaoEngenharia AS (
                SELECT
                    E.AIJ_FILIAL,
                    E.AIJ_NROPOR,
                    {status_revision_select}
                    CASE
                        WHEN SUM(
                            CASE
                                WHEN ISNULL(E.AIJ_DTENCE, '') = ''
                                 AND E.PROXIMO_STAGE_GLOBAL IS NOT NULL
                                 AND ISNULL(E.PROXIMO_EH_ENG_GLOBAL, 0) = 0
                                 AND (
                                     E.PROXIMA_REVISA_GLOBAL > E.AIJ_REVISA
                                     OR E.PROXIMO_STAGE_GLOBAL < E.AIJ_STAGE
                                 )
                                THEN 1 ELSE 0
                            END
                        ) > 0 THEN ?

                        WHEN SUM(
                            CASE
                                WHEN ISNULL(E.AIJ_DTENCE, '') = ''
                                 AND E.PROXIMO_STAGE_GLOBAL IS NULL
                                THEN 1 ELSE 0
                            END
                        ) > 0 THEN ?

                        WHEN COUNT(*) = SUM(
                            CASE
                                WHEN ISNULL(E.AIJ_DTENCE, '') <> ''
                                  OR ISNULL(E.PROXIMO_DTINIC_GLOBAL, '') <> ''
                                THEN 1 ELSE 0
                            END
                        ) THEN ?

                        ELSE ?
                    END AS ENGINEERING_STATUS
                FROM EngenhariaEventos E
                INNER JOIN UltimaRevisaoMedicaoEngenharia M
                    ON M.AIJ_FILIAL = E.AIJ_FILIAL
                   AND M.AIJ_NROPOR = E.AIJ_NROPOR
                   AND M.ULTIMA_REVISA_MEDICAO = E.AIJ_REVISA
                GROUP BY
                    {status_group_by}
            ),

            EngenhariaResumoUltimaRevisao AS (
                SELECT
                    {self._sql_engenharia_resumo_ultima_revisao_select(
                        eng_minutes_expr=eng_minutes_expr,
                        where_sample_eng_e=where_sample_eng_e,
                        lite=eng_resumo_lite,
                    )}
                FROM EngenhariaEventos E
                INNER JOIN UltimaRevisaoMedicaoEngenharia M
                    ON M.AIJ_FILIAL = E.AIJ_FILIAL
                   AND M.AIJ_NROPOR = E.AIJ_NROPOR
                   AND M.ULTIMA_REVISA_MEDICAO = E.AIJ_REVISA
                INNER JOIN StatusUltimaRevisaoEngenharia S
                    ON S.AIJ_FILIAL = E.AIJ_FILIAL
                   AND S.AIJ_NROPOR = E.AIJ_NROPOR
                   {status_revision_join}
                GROUP BY
                    {eng_resumo_group_by}
            )
        """

        params: list = [
            *params_aij_base_a,
            *params_eng_support_next,
            *params_eng_support_e,
        ]
        if per_candidate_revision:
            pass
        elif use_period_revision:
            params.extend([
                *params_lmp_anchor_rank_m,
                *params_period_eng,
                *params_period_eng,
            ])
        else:
            params.extend([*params_lmp_anchor_rank_e])

        params.extend([
            self._engineering_status_returned_label(),
            self._engineering_status_in_progress_label(),
            self._engineering_status_finished_label(),
            self._engineering_status_partial_label(),
            *params_sample_eng_e,
        ])
        return sql, tuple(params)

    def _sql_listing_anchor_marker_cte(
        self,
        requested_branch: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
    ) -> Tuple[str, tuple]:
        """
        Resolve uma única âncora por OV na revisão atual do AD1010.

        Se a OV já teve lançamento/homologação LMP (estágio 000012), permanece LMP
        com âncora na passagem 000012 mais recente — histórico de amostra não reclassifica.

        Caso contrário: entre LMP e amostra na mesma revisão, LMP prevalece sobre amostra.
        """
        where_aij_base, params_aij_base = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", requested_branch),
            )
        )
        where_aij_base_x, params_aij_base_x = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "X.D_E_L_E_T_"),
                self._branch_filter(qb, "X.AIJ_FILIAL", requested_branch),
            )
        )

        where_lmp_anchor, params_lmp_anchor = self._sql_lmp_anchor_process_stage_condition(
            "A.AIJ_PROVEN",
            "A.AIJ_STAGE",
        )
        where_sample_anchor, params_sample_anchor = (
            self._sql_sample_anchor_process_stage_condition(
                "A.AIJ_PROVEN",
                "A.AIJ_STAGE",
            )
        )
        where_lmp_finalized, params_lmp_finalized = (
            self._sql_lmp_finalized_process_stage_condition(
                "A.AIJ_PROVEN",
                "A.AIJ_STAGE",
            )
        )
        where_period, params_period = self._sql_aij_period_filter_clause(
            "A.AIJ_DTINIC",
            date_start,
            date_end,
        )
        where_ad1_rev, params_ad1_rev = self._sql_ad1_current_revision_match(
            "A",
            requested_branch,
        )

        sql = f"""
            AllListingAnchorRaw AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA,
                    A.AIJ_PROVEN,
                    A.AIJ_STAGE,
                    A.AIJ_DTINIC,
                    A.AIJ_HRINIC,
                    A.AIJ_DTENCE,
                    A.AIJ_HRENCE,
                    A.R_E_C_N_O_,
                    ? AS LISTING_KIND
                FROM AIJ010 A
                WHERE {where_aij_base}
                  AND {where_lmp_anchor}
                  AND {where_ad1_rev}
                  {where_period}

                UNION ALL

                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA,
                    A.AIJ_PROVEN,
                    A.AIJ_STAGE,
                    A.AIJ_DTINIC,
                    A.AIJ_HRINIC,
                    A.AIJ_DTENCE,
                    A.AIJ_HRENCE,
                    A.R_E_C_N_O_,
                    ? AS LISTING_KIND
                FROM AIJ010 A
                WHERE {where_aij_base}
                  AND {where_sample_anchor}
                  AND {where_ad1_rev}
                  {where_period}
            ),

            ListingAnchorOvKeys AS (
                SELECT DISTINCT
                    R.AIJ_FILIAL,
                    R.AIJ_NROPOR
                FROM AllListingAnchorRaw R
            ),

            Aij010ListingOvScoped AS (
                SELECT
                    X.AIJ_FILIAL,
                    X.AIJ_NROPOR,
                    X.AIJ_REVISA,
                    X.AIJ_DTINIC,
                    X.AIJ_HRINIC,
                    X.AIJ_DTENCE,
                    X.R_E_C_N_O_,
                    LEAD(
                        COALESCE(NULLIF(X.AIJ_DTENCE, ''), NULLIF(X.AIJ_DTINIC, ''))
                    ) OVER (
                        PARTITION BY X.AIJ_FILIAL, X.AIJ_NROPOR
                        ORDER BY X.AIJ_DTINIC, X.AIJ_HRINIC, X.AIJ_REVISA, X.R_E_C_N_O_
                    ) AS NEXT_EVENT_DATE
                FROM AIJ010 X
                INNER JOIN ListingAnchorOvKeys K
                    ON K.AIJ_FILIAL = X.AIJ_FILIAL
                   AND K.AIJ_NROPOR = X.AIJ_NROPOR
                WHERE {where_aij_base_x}
            ),

            AllListingAnchorRanked AS (
                SELECT
                    R.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY R.AIJ_FILIAL, R.AIJ_NROPOR
                        ORDER BY
                            CASE
                                WHEN R.LISTING_KIND = ? THEN 2
                                WHEN R.LISTING_KIND = ? THEN 1
                                ELSE 0
                            END DESC,
                            R.AIJ_DTINIC DESC,
                            R.AIJ_HRINIC DESC,
                            R.R_E_C_N_O_ DESC
                    ) AS RN_DESC
                FROM AllListingAnchorRaw R
            ),

            ListingAnchorChosen AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA,
                    A.AIJ_PROVEN,
                    A.AIJ_STAGE,
                    A.AIJ_DTINIC,
                    A.AIJ_HRINIC,
                    A.LISTING_KIND,
                    A.AIJ_DTINIC AS ANCHOR_START_DATE,
                    COALESCE(
                        NULLIF(A.AIJ_DTENCE, ''),
                        S.NEXT_EVENT_DATE
                    ) AS ANCHOR_END_DATE,
                    A.RN_DESC
                FROM AllListingAnchorRanked A
                LEFT JOIN Aij010ListingOvScoped S
                    ON S.AIJ_FILIAL  = A.AIJ_FILIAL
                   AND S.AIJ_NROPOR  = A.AIJ_NROPOR
                   AND S.R_E_C_N_O_  = A.R_E_C_N_O_
                WHERE A.RN_DESC = 1
            ),

            LmpFinalizedAnchorRaw AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA,
                    A.AIJ_PROVEN,
                    A.AIJ_STAGE,
                    A.AIJ_DTINIC,
                    A.AIJ_HRINIC,
                    A.AIJ_DTENCE,
                    A.AIJ_HRENCE,
                    A.R_E_C_N_O_,
                    ? AS LISTING_KIND
                FROM AIJ010 A
                WHERE {where_aij_base}
                  AND {where_lmp_finalized}
                  AND {where_ad1_rev}
                  {where_period}
            ),

            LmpFinalizedOvKeys AS (
                SELECT DISTINCT
                    R.AIJ_FILIAL,
                    R.AIJ_NROPOR
                FROM LmpFinalizedAnchorRaw R
            ),

            Aij010FinalizedOvScoped AS (
                SELECT
                    X.AIJ_FILIAL,
                    X.AIJ_NROPOR,
                    X.AIJ_REVISA,
                    X.AIJ_DTINIC,
                    X.AIJ_HRINIC,
                    X.AIJ_DTENCE,
                    X.R_E_C_N_O_,
                    LEAD(
                        COALESCE(NULLIF(X.AIJ_DTENCE, ''), NULLIF(X.AIJ_DTINIC, ''))
                    ) OVER (
                        PARTITION BY X.AIJ_FILIAL, X.AIJ_NROPOR
                        ORDER BY X.AIJ_DTINIC, X.AIJ_HRINIC, X.AIJ_REVISA, X.R_E_C_N_O_
                    ) AS NEXT_EVENT_DATE
                FROM AIJ010 X
                INNER JOIN LmpFinalizedOvKeys K
                    ON K.AIJ_FILIAL = X.AIJ_FILIAL
                   AND K.AIJ_NROPOR = X.AIJ_NROPOR
                WHERE {where_aij_base_x}
            ),

            LmpFinalizedAnchorRanked AS (
                SELECT
                    R.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY R.AIJ_FILIAL, R.AIJ_NROPOR
                        ORDER BY
                            R.AIJ_DTINIC DESC,
                            R.AIJ_HRINIC DESC,
                            R.R_E_C_N_O_ DESC
                    ) AS RN_DESC
                FROM LmpFinalizedAnchorRaw R
            ),

            LmpFinalizedAnchorChosen AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA,
                    A.AIJ_PROVEN,
                    A.AIJ_STAGE,
                    A.AIJ_DTINIC,
                    A.AIJ_HRINIC,
                    A.LISTING_KIND,
                    A.AIJ_DTINIC AS ANCHOR_START_DATE,
                    COALESCE(
                        NULLIF(A.AIJ_DTENCE, ''),
                        S.NEXT_EVENT_DATE
                    ) AS ANCHOR_END_DATE,
                    A.RN_DESC
                FROM LmpFinalizedAnchorRanked A
                LEFT JOIN Aij010FinalizedOvScoped S
                    ON S.AIJ_FILIAL  = A.AIJ_FILIAL
                   AND S.AIJ_NROPOR  = A.AIJ_NROPOR
                   AND S.R_E_C_N_O_  = A.R_E_C_N_O_
                WHERE A.RN_DESC = 1
            ),

            SampleAnchorOvKeys AS (
                SELECT DISTINCT
                    R.AIJ_FILIAL,
                    R.AIJ_NROPOR,
                    R.AIJ_REVISA
                FROM AllListingAnchorRaw R
                WHERE R.LISTING_KIND = '{LISTING_KIND_SAMPLE}'
            ),

            ListingAnchorEventos AS (
                SELECT
                    F.AIJ_FILIAL,
                    F.AIJ_NROPOR,
                    F.AIJ_REVISA,
                    F.LISTING_KIND,
                    F.ANCHOR_START_DATE,
                    F.ANCHOR_END_DATE
                FROM LmpFinalizedAnchorChosen F

                UNION ALL

                SELECT
                    C.AIJ_FILIAL,
                    C.AIJ_NROPOR,
                    C.AIJ_REVISA,
                    C.LISTING_KIND,
                    C.ANCHOR_START_DATE,
                    C.ANCHOR_END_DATE
                FROM ListingAnchorChosen C
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM LmpFinalizedAnchorChosen F
                    WHERE F.AIJ_FILIAL = C.AIJ_FILIAL
                      AND F.AIJ_NROPOR = C.AIJ_NROPOR
                )
            )
        """

        params = (
            LISTING_KIND_LMP,
            *params_aij_base,
            *params_lmp_anchor,
            *params_ad1_rev,
            *params_period,
            LISTING_KIND_SAMPLE,
            *params_aij_base,
            *params_sample_anchor,
            *params_ad1_rev,
            *params_period,
            *params_aij_base_x,
            LISTING_KIND_LMP,
            LISTING_KIND_SAMPLE,
            LISTING_KIND_LMP,
            *params_aij_base,
            *params_lmp_finalized,
            *params_ad1_rev,
            *params_period,
            *params_aij_base_x,
        )
        return sql, params

    def _sql_produtos_lmp_cte(
        self,
        scope_cte_name: str | None = None,
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        where_adj, params_adj = self._sql_filter_adj_active_branch("ADJ", requested_branch)

        if scope_cte_name:
            sql = f"""
                ProdutosLMP AS (
                    SELECT DISTINCT
                        ADJ.ADJ_FILIAL,
                        ADJ.ADJ_NROPOR,
                        ADJ.ADJ_REVISA,
                        ADJ.ADJ_PROD
                    FROM ADJ010 ADJ
                    INNER JOIN {scope_cte_name} SCOPE_P
                        ON SCOPE_P.AD1_FILIAL = ADJ.ADJ_FILIAL
                       AND SCOPE_P.AD1_NROPOR = ADJ.ADJ_NROPOR
                       AND SCOPE_P.AD1_REVISA = ADJ.ADJ_REVISA
                    WHERE {where_adj}
                )
            """
            return sql, params_adj

        where_ad1, params_ad1 = self._sql_filter_ad1_active_branch("AD1", requested_branch)

        sql = f"""
            ProdutosLMP AS (
                SELECT DISTINCT
                    ADJ.ADJ_FILIAL,
                    ADJ.ADJ_NROPOR,
                    ADJ.ADJ_REVISA,
                    ADJ.ADJ_PROD
                FROM ADJ010 ADJ
                INNER JOIN AD1010 AD1
                    ON AD1.AD1_FILIAL = ADJ.ADJ_FILIAL
                   AND AD1.AD1_NROPOR = ADJ.ADJ_NROPOR
                   AND AD1.AD1_REVISA = ADJ.ADJ_REVISA
                WHERE {where_adj}
                  AND {where_ad1}
            )
        """
        return sql, (*params_adj, *params_ad1)

    def _sql_pi_total_by_ov_ctes_from_produtos_lmp(self) -> Tuple[str, tuple]:
        where_sb1, params_sb1 = self._sql_filter_sb1_active("SB1")
        where_sb_root, params_sb_root = self._sql_filter_sb_root_types("SB")
        where_sg, params_sg = self._sql_filter_sg_active("G")
        where_sb_pi, params_sb_pi = self._sql_filter_sb_pi_types("SB")

        sql = f"""
            ProdutosLMPRef AS (
                SELECT
                    P.ADJ_FILIAL,
                    P.ADJ_NROPOR,
                    P.ADJ_REVISA,
                    P.ADJ_PROD,
                    SB1.B1_REFEREN
                FROM ProdutosLMP P
                INNER JOIN SB1010 SB1
                    ON SB1.B1_COD = P.ADJ_PROD
                WHERE {where_sb1}
                  AND SB1.B1_REFEREN <> ''
            ),

            ProdutosBase AS (
                SELECT DISTINCT
                    R.ADJ_FILIAL,
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD,
                    SB.B1_COD AS ROOT_PRODUCT
                FROM ProdutosLMPRef R
                INNER JOIN SB1010 SB
                    ON SB.B1_REFEREN = R.B1_REFEREN
                WHERE {where_sb_root}
            ),

            Recursive_BOM AS (
                SELECT
                    B.ADJ_FILIAL,
                    B.ADJ_NROPOR,
                    B.ADJ_REVISA,
                    B.ADJ_PROD,
                    G.G1_COMP AS COMPONENT,
                    1 AS LEVEL
                FROM ProdutosBase B
                INNER JOIN SG1010 G
                    ON G.G1_COD = B.ROOT_PRODUCT
                WHERE {where_sg}
                  AND G.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

                UNION ALL

                SELECT
                    R.ADJ_FILIAL,
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD,
                    G.G1_COMP,
                    R.LEVEL + 1
                FROM SG1010 G
                INNER JOIN Recursive_BOM R
                    ON R.COMPONENT = G.G1_COD
                WHERE {where_sg}
                  AND G.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
                  AND R.LEVEL < {int(self.settings.max_bom_level)}
            ),

            PI_COUNT_BY_OV AS (
                SELECT
                    X.ADJ_FILIAL,
                    X.ADJ_NROPOR,
                    X.ADJ_REVISA,
                    SUM(X.QTD_PI_PRODUTO) AS QTD_PI
                FROM (
                    SELECT
                        R.ADJ_FILIAL,
                        R.ADJ_NROPOR,
                        R.ADJ_REVISA,
                        R.ADJ_PROD,
                        COUNT(DISTINCT SB.B1_COD) AS QTD_PI_PRODUTO
                    FROM Recursive_BOM R
                    INNER JOIN SB1010 SB
                        ON SB.B1_COD = R.COMPONENT
                    WHERE {where_sb_pi}
                    GROUP BY
                        R.ADJ_FILIAL,
                        R.ADJ_NROPOR,
                        R.ADJ_REVISA,
                        R.ADJ_PROD
                ) X
                GROUP BY
                    X.ADJ_FILIAL,
                    X.ADJ_NROPOR,
                    X.ADJ_REVISA
            )
        """

        params = (
            *params_sb1,
            *params_sb_root,
            *params_sg,
            *params_sg,
            *params_sb_pi,
        )
        return sql, params

    def _sql_pi_por_referencia_ctes_from_produtos_lmp(self) -> Tuple[str, tuple]:
        where_sb1, params_sb1 = self._sql_filter_sb1_active("SB1")
        where_sb_root, params_sb_root = self._sql_filter_sb_root_types("SB")
        where_sg, params_sg = self._sql_filter_sg_active("G")
        where_sb_pi, params_sb_pi = self._sql_filter_sb_pi_types("SB")

        sql = f"""
            ProdutosLMPRef AS (
                SELECT
                    P.ADJ_FILIAL,
                    P.ADJ_NROPOR,
                    P.ADJ_REVISA,
                    P.ADJ_PROD,
                    SB1.B1_REFEREN
                FROM ProdutosLMP P
                INNER JOIN SB1010 SB1
                    ON SB1.B1_COD = P.ADJ_PROD
                WHERE {where_sb1}
                  AND SB1.B1_REFEREN <> ''
            ),

            ProdutosBase AS (
                SELECT DISTINCT
                    R.ADJ_FILIAL,
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD,
                    SB.B1_COD AS ROOT_PRODUCT,
                    SB.B1_REFEREN
                FROM ProdutosLMPRef R
                INNER JOIN SB1010 SB
                    ON SB.B1_REFEREN = R.B1_REFEREN
                WHERE {where_sb_root}
            ),

            Recursive_BOM AS (
                SELECT
                    B.ADJ_FILIAL,
                    B.ADJ_NROPOR,
                    B.ADJ_REVISA,
                    B.ADJ_PROD,
                    B.ROOT_PRODUCT,
                    G.G1_COMP AS COMPONENT,
                    1 AS LEVEL
                FROM ProdutosBase B
                INNER JOIN SG1010 G
                    ON G.G1_COD = B.ROOT_PRODUCT
                WHERE {where_sg}
                  AND G.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

                UNION ALL

                SELECT
                    R.ADJ_FILIAL,
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD,
                    R.ROOT_PRODUCT,
                    G.G1_COMP,
                    R.LEVEL + 1
                FROM SG1010 G
                INNER JOIN Recursive_BOM R
                    ON R.COMPONENT = G.G1_COD
                WHERE {where_sg}
                  AND G.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
                  AND R.LEVEL < {int(self.settings.max_bom_level)}
            ),

            PI_COUNT_BY_PRODUCT AS (
                SELECT
                    R.ADJ_FILIAL,
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD,
                    COUNT(DISTINCT SB.B1_COD) AS QTD_PI
                FROM Recursive_BOM R
                INNER JOIN SB1010 SB
                    ON SB.B1_COD = R.COMPONENT
                WHERE {where_sb_pi}
                GROUP BY
                    R.ADJ_FILIAL,
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD
            ),

            PI_COUNT_BY_OV AS (
                SELECT
                    P.ADJ_FILIAL,
                    P.ADJ_NROPOR,
                    P.ADJ_REVISA,
                    SUM(P.QTD_PI) AS QTD_PI
                FROM PI_COUNT_BY_PRODUCT P
                GROUP BY
                    P.ADJ_FILIAL,
                    P.ADJ_NROPOR,
                    P.ADJ_REVISA
            )
        """

        params = (
            *params_sb1,
            *params_sb_root,
            *params_sg,
            *params_sg,
            *params_sb_pi,
        )
        return sql, params

    def _sql_get_lmp_candidate_scope_cte(self, *, where_ad1: str) -> str:
        return f"""
            GetLmpCandidateScope AS (
                SELECT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA,
                    COALESCE(L.LISTING_KIND, ?) AS LISTING_KIND,
                    CASE
                        WHEN SA.AIJ_NROPOR IS NOT NULL THEN 1
                        ELSE 0
                    END AS HAS_SAMPLE_ANCHOR,
                    CASE
                        WHEN LF.AIJ_NROPOR IS NOT NULL THEN 1
                        ELSE 0
                    END AS HAS_LMP_FINALIZED
                FROM AD1010 AD1
                LEFT JOIN ListingAnchorEventos L
                    ON L.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND L.AIJ_NROPOR = AD1.AD1_NROPOR
                   AND L.AIJ_REVISA = AD1.AD1_REVISA
                LEFT JOIN SampleAnchorOvKeys SA
                    ON SA.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND SA.AIJ_NROPOR = AD1.AD1_NROPOR
                   AND SA.AIJ_REVISA = AD1.AD1_REVISA
                LEFT JOIN LmpFinalizedAnchorChosen LF
                    ON LF.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND LF.AIJ_NROPOR = AD1.AD1_NROPOR
                   AND LF.AIJ_REVISA = AD1.AD1_REVISA
                WHERE {where_ad1}
                  AND AD1.AD1_NROPOR = ?
            ),
        """

    def _sql_header_lmp(self, request: GetLMPRequest) -> Tuple[str, tuple]:
        requested_branch = self._get_request_branch(request)
        use_period = self._uses_period_revision_measurement(
            scope_cte_name="GetLmpCandidateScope",
            date_start=request.date_start,
            date_end=request.date_end,
        )

        first_eng_cte = ""
        first_eng_params: tuple = ()
        first_eng_join = ""
        start_date_expr = "COALESCE(L.ANCHOR_START_DATE, R.ANCHOR_START_DATE)"

        if use_period:
            anchor_period_start, anchor_period_end = self._listing_anchor_period_dates(
                request.date_start,
                request.date_end,
            )
            cte_marker, params_marker = self._sql_listing_anchor_marker_cte(
                requested_branch,
                anchor_period_start,
                anchor_period_end,
            )
            cte_eng_ref, params_eng_ref = self._sql_eng_support_ov_reference_cte(
                requested_branch,
                anchor_period_start,
                anchor_period_end,
            )
        else:
            cte_marker, params_marker = self._sql_listing_anchor_marker_cte(
                requested_branch,
            )
            cte_eng_ref, params_eng_ref = self._sql_eng_support_ov_reference_cte(
                requested_branch,
            )

        where_ad1, params_ad1 = self._sql_filter_ad1_active_branch("AD1", requested_branch)
        where_sa1, params_sa1 = self._sql_filter_sa1_active("SA1")
        where_sa3, params_sa3 = self._sql_filter_sa3_active("SA3")

        scope_cte = ""
        params_scope: tuple = ()
        if use_period:
            scope_cte = self._sql_get_lmp_candidate_scope_cte(where_ad1=where_ad1)
            params_scope = (LISTING_KIND_OTHER, *params_ad1, request.sale_number)
            cte_hist, params_hist = self._sql_historico_ov_cte(
                scope_cte_name="GetLmpCandidateScope",
                requested_branch=requested_branch,
                date_start=request.date_start,
                date_end=request.date_end,
            )
        else:
            cte_hist, params_hist = self._sql_historico_ov_cte(
                requested_branch=requested_branch,
            )

        listing_kind_select = (
            f"{self._effective_listing_kind_expr()} AS listing_kind"
            if use_period
            else f"""
                CASE
                    WHEN L.AIJ_NROPOR IS NOT NULL THEN L.LISTING_KIND
                    ELSE ?
                END AS listing_kind
            """
        )
        candidate_join = """
            INNER JOIN GetLmpCandidateScope C
                ON C.AD1_FILIAL = AD1.AD1_FILIAL
               AND C.AD1_NROPOR = AD1.AD1_NROPOR
               AND C.AD1_REVISA = AD1.AD1_REVISA
        """ if use_period else ""

        sale_filter = "" if use_period else "AND AD1.AD1_NROPOR = ?"
        listing_presence_filter = (
            ""
            if use_period
            else "AND (L.AIJ_NROPOR IS NOT NULL OR R.AIJ_NROPOR IS NOT NULL)"
        )

        first_eng_cte_block = f",\n            {first_eng_cte}" if first_eng_cte else ""

        sql = f"""
            WITH
            {cte_marker},
            {cte_eng_ref}{first_eng_cte_block},
            {scope_cte}
            {cte_hist}
            SELECT TOP 1
                AD1.AD1_FILIAL AS branch,
                AD1.AD1_NROPOR AS sale_number,
                AD1.AD1_DESCRI AS sale_description,
                AD1.AD1_REVISA AS reference_revision,
                MREV.ULTIMA_REVISA_MEDICAO AS measurement_revision,
                {listing_kind_select},
                {start_date_expr} AS start_date,
                COALESCE(L.ANCHOR_END_DATE, R.ANCHOR_END_DATE) AS end_date,
                H.ENGINEERING_STATUS AS engineering_status,
                H.QTD_PASSAGENS_ENG AS qtd_engineering_entries,
                H.QTD_PASSAGENS_ENCERRADAS AS qtd_engineering_closed,
                H.QTD_AVANCOU_ENG AS qtd_advanced_from_engineering,
                H.QTD_RETORNOU_ENG AS qtd_returned_from_engineering,
                H.TEMPO_TOTAL_MINUTOS_ENG AS engineering_total_minutes,
                AD1.AD1_CODCLI AS costumer_code,
                AD1.AD1_LOJCLI AS costumer_store,
                SA1.A1_NOME AS costumer_name,
                AD1.AD1_VEND AS seller_code,
                SA3.A3_NOME AS seller_name
            FROM AD1010 AD1
            {candidate_join}
            LEFT JOIN ListingAnchorEventos L
                ON L.AIJ_FILIAL = AD1.AD1_FILIAL
               AND L.AIJ_NROPOR = AD1.AD1_NROPOR
               AND L.AIJ_REVISA = AD1.AD1_REVISA
            LEFT JOIN EngSupportOvRef R
                ON R.AIJ_FILIAL = AD1.AD1_FILIAL
               AND R.AIJ_NROPOR = AD1.AD1_NROPOR
               AND R.AIJ_REVISA = AD1.AD1_REVISA
            {first_eng_join}
            LEFT JOIN EngenhariaResumoUltimaRevisao H
                ON H.AIJ_FILIAL = AD1.AD1_FILIAL
               AND H.AIJ_NROPOR = AD1.AD1_NROPOR
            LEFT JOIN UltimaRevisaoMedicaoEngenharia MREV
                ON MREV.AIJ_FILIAL = AD1.AD1_FILIAL
               AND MREV.AIJ_NROPOR = AD1.AD1_NROPOR
            LEFT JOIN SA1010 SA1
                ON SA1.A1_COD = AD1.AD1_CODCLI
               AND SA1.A1_LOJA = AD1.AD1_LOJCLI
               AND {where_sa1}
            LEFT JOIN SA3010 SA3
                ON SA3.A3_COD = AD1.AD1_VEND
               AND {where_sa3}
            WHERE {where_ad1}
              {sale_filter}
              {listing_presence_filter}
            ORDER BY AD1.AD1_REVISA DESC
        """

        params: list = [
            *params_marker,
            *params_eng_ref,
            *first_eng_params,
            *params_scope,
            *params_hist,
        ]
        if use_period:
            params.append(self._min_engineering_residence_minutes())
        else:
            params.append(LISTING_KIND_OTHER)

        params.extend([
            *params_sa1,
            *params_sa3,
            *params_ad1,
        ])
        if not use_period:
            params.append(request.sale_number)

        return sql, tuple(params)

    def _sql_products_lmp(
        self,
        requested_branch: str | None = None,
        *,
        sale_number: str | None = None,
    ) -> Tuple[str, tuple]:
        cte_prod, params_prod = self._sql_produtos_lmp_cte(requested_branch=requested_branch)
        cte_pi, params_pi = self._sql_pi_por_referencia_ctes_from_produtos_lmp()
        resolved_sb1_apply, params_resolved_sb1 = self._sql_lmp_resolved_product_sb1_apply(
            adj_alias="P",
            sb_alias="SB1",
        )
        where_sb_adj, params_sb_adj = self._sql_filter_sb1_active("SB0")
        sale_filter = "AND P.ADJ_NROPOR = ?" if sale_number is not None else ""

        sql = f"""
            WITH
            {cte_prod},
            {cte_pi},
            ResolvedProducts AS (
                SELECT
                    P.ADJ_FILIAL,
                    P.ADJ_NROPOR,
                    P.ADJ_REVISA,
                    P.ADJ_PROD,
                    SB1.B1_GRUPO AS group_code,
                    SB1.B1_COD AS code,
                    SB1.B1_DESC AS description,
                    SB1.B1_TIPO AS type
                FROM ProdutosLMP P
                {resolved_sb1_apply}
                WHERE SB1.B1_COD IS NOT NULL
                  {sale_filter}
            ),
            ProductsForDisplay AS (
                SELECT
                    R.group_code,
                    R.code,
                    R.description,
                    R.type,
                    R.ADJ_FILIAL,
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD
                FROM ResolvedProducts R

                UNION ALL

                SELECT
                    SB0.B1_GRUPO,
                    SB0.B1_COD,
                    SB0.B1_DESC,
                    SB0.B1_TIPO,
                    R.ADJ_FILIAL,
                    R.ADJ_NROPOR,
                    R.ADJ_REVISA,
                    R.ADJ_PROD
                FROM ResolvedProducts R
                INNER JOIN SB1010 SB0
                    ON SB0.B1_COD = R.ADJ_PROD
                   AND {where_sb_adj}
                WHERE R.code LIKE '9026%'
                  AND RTRIM(LTRIM(SB0.B1_COD)) <> RTRIM(LTRIM(R.code))
            )
            SELECT
                PU.group_code,
                PU.code,
                PU.description,
                PU.type,
                ISNULL(SUM(PI.QTD_PI), 0) AS qtd_pi
            FROM ProductsForDisplay PU
            LEFT JOIN PI_COUNT_BY_PRODUCT PI
                ON PI.ADJ_FILIAL = PU.ADJ_FILIAL
               AND PI.ADJ_NROPOR = PU.ADJ_NROPOR
               AND PI.ADJ_REVISA = PU.ADJ_REVISA
               AND PI.ADJ_PROD = PU.ADJ_PROD
            GROUP BY
                PU.group_code,
                PU.code,
                PU.description,
                PU.type
            ORDER BY
                CASE
                    WHEN PU.code LIKE '9026%' THEN 0
                    ELSE 1
                END,
                PU.code
        """

        params: tuple = (*params_prod, *params_pi, *params_resolved_sb1)
        if sale_number is not None:
            params = (*params, sale_number)
        params = (*params, *params_sb_adj)
        return sql, params

    def _sql_qtd_pi_lmp_total(
        self,
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        cte_prod, params_prod = self._sql_produtos_lmp_cte(requested_branch=requested_branch)
        cte_pi, params_pi = self._sql_pi_por_referencia_ctes_from_produtos_lmp()

        sql = f"""
            WITH
            {cte_prod},
            {cte_pi}
            SELECT ISNULL(SUM(PI.QTD_PI), 0) AS qtd_pi
            FROM (
                SELECT DISTINCT
                    ADJ_FILIAL,
                    ADJ_NROPOR,
                    ADJ_REVISA,
                    QTD_PI
                FROM PI_COUNT_BY_OV
            ) PI
            WHERE PI.ADJ_NROPOR = ?
        """
        return sql, (*params_prod, *params_pi)

    def _sql_history_events_lmp_lite(
        self,
        requested_branch: str | None = None,
        revision: str | None = None,
    ) -> Tuple[str, tuple]:
        where_aij, params_aij = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", requested_branch),
            )
        )
        where_eng, params_eng = self._sql_engineering_support_process_stage_condition(
            "A.AIJ_PROVEN",
            "A.AIJ_STAGE",
        )
        revision_filter = ""
        revision_params: tuple = ()
        normalized_revision = str(revision or "").strip()
        if normalized_revision:
            revision_filter = "AND A.AIJ_REVISA = ?"
            revision_params = (normalized_revision,)

        sql = f"""
            SELECT
                A.AIJ_REVISA AS revision,
                A.AIJ_PROVEN AS process_code,
                A.AIJ_STAGE AS stage_code,
                A.AIJ_DTINIC AS start_date,
                A.AIJ_HRINIC AS start_time,
                A.AIJ_DTLIMI AS limit_date,
                A.AIJ_HRLIMI AS limit_time,
                A.AIJ_DTENCE AS end_date,
                A.AIJ_HRENCE AS end_time,
                CASE
                    WHEN ISNULL(A.AIJ_DTINIC, '') <> ''
                     AND ISNULL(A.AIJ_HRINIC, '') <> ''
                     AND ISNULL(A.AIJ_DTENCE, '') <> ''
                     AND ISNULL(A.AIJ_HRENCE, '') <> ''
                    THEN DATEDIFF(
                        MINUTE,
                        CAST(
                            CONCAT(
                                SUBSTRING(A.AIJ_DTINIC, 1, 4), '-',
                                SUBSTRING(A.AIJ_DTINIC, 5, 2), '-',
                                SUBSTRING(A.AIJ_DTINIC, 7, 2), ' ',
                                A.AIJ_HRINIC, ':00'
                            ) AS DATETIME
                        ),
                        CAST(
                            CONCAT(
                                SUBSTRING(A.AIJ_DTENCE, 1, 4), '-',
                                SUBSTRING(A.AIJ_DTENCE, 5, 2), '-',
                                SUBSTRING(A.AIJ_DTENCE, 7, 2), ' ',
                                A.AIJ_HRENCE, ':00'
                            ) AS DATETIME
                        )
                    )
                    ELSE NULL
                END AS duration_minutes,
                A.AIJ_STATUS AS status,
                A.AIJ_HISTOR AS history_flag,
                CASE WHEN {where_eng} THEN 1 ELSE 0 END AS is_engineering
            FROM AIJ010 A
            WHERE {where_aij}
              AND A.AIJ_NROPOR = ?
              {revision_filter}
            ORDER BY
                A.AIJ_REVISA,
                A.AIJ_DTINIC,
                A.AIJ_HRINIC,
                A.AIJ_STAGE,
                A.R_E_C_N_O_
        """

        return sql, params_eng, params_aij, revision_params

    def _sql_history_flow_lmp(
        self,
        requested_branch: str | None = None,
        revision: str | None = None,
    ) -> Tuple[str, tuple]:
        where_aij, params_aij = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", requested_branch),
            )
        )
        where_eng, params_eng = self._sql_engineering_support_process_stage_condition(
            "E.AIJ_PROVEN",
            "E.AIJ_STAGE",
        )
        where_eng_next, params_eng_next = self._sql_engineering_support_process_stage_condition(
            "E.PROXIMO_PROVEN_GLOBAL",
            "E.PROXIMO_STAGE_GLOBAL",
        )
        revision_filter = ""
        revision_params: tuple = ()
        normalized_revision = str(revision or "").strip()
        if normalized_revision:
            revision_filter = "AND A.AIJ_REVISA = ?"
            revision_params = (normalized_revision,)

        win = """PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
                        ORDER BY
                            A.AIJ_REVISA,
                            A.AIJ_DTINIC,
                            A.AIJ_HRINIC,
                            A.AIJ_STAGE,
                            A.R_E_C_N_O_"""

        sql = f"""
            WITH EventosOV AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_REVISA,
                    A.AIJ_PROVEN,
                    A.AIJ_STAGE,
                    A.AIJ_DTINIC,
                    A.AIJ_HRINIC,
                    A.AIJ_DTENCE,
                    A.AIJ_HRENCE,
                    LEAD(A.AIJ_REVISA) OVER ({win}) AS PROXIMA_REVISA_GLOBAL,
                    LEAD(A.AIJ_PROVEN) OVER ({win}) AS PROXIMO_PROVEN_GLOBAL,
                    LEAD(A.AIJ_STAGE) OVER ({win}) AS PROXIMO_STAGE_GLOBAL,
                    LEAD(A.AIJ_DTINIC) OVER ({win}) AS PROXIMO_DTINIC_GLOBAL,
                    LAG(A.AIJ_REVISA) OVER ({win}) AS REVISA_ANTERIOR,
                    LAG(A.AIJ_PROVEN) OVER ({win}) AS PROVEN_ANTERIOR,
                    LAG(A.AIJ_STAGE) OVER ({win}) AS STAGE_ANTERIOR
                FROM AIJ010 A
                WHERE {where_aij}
                  AND A.AIJ_NROPOR = ?
                  {revision_filter}
            )
            SELECT
                E.AIJ_REVISA AS revision,
                E.AIJ_PROVEN AS process_code,
                E.AIJ_STAGE AS stage_code,
                E.AIJ_DTINIC AS start_date,
                E.AIJ_HRINIC AS start_time,
                E.AIJ_DTENCE AS end_date,
                E.AIJ_HRENCE AS end_time,
                E.PROXIMA_REVISA_GLOBAL AS next_revision,
                E.PROXIMO_PROVEN_GLOBAL AS next_process_code,
                E.PROXIMO_STAGE_GLOBAL AS next_stage_code,
                E.PROXIMO_DTINIC_GLOBAL AS next_start_date,
                E.REVISA_ANTERIOR AS previous_revision,
                E.PROVEN_ANTERIOR AS previous_process_code,
                E.STAGE_ANTERIOR AS previous_stage_code,
                CASE WHEN {where_eng} THEN 1 ELSE 0 END AS is_engineering,
                CASE WHEN {where_eng_next} THEN 1 ELSE 0 END AS next_is_engineering
            FROM EventosOV E
            WHERE {where_eng}
            ORDER BY
                E.AIJ_REVISA,
                E.AIJ_DTINIC,
                E.AIJ_HRINIC,
                E.AIJ_STAGE
        """

        return sql, params_aij, revision_params, params_eng, params_eng_next

    def _sql_history_stage_labels_lmp(
        self,
        *,
        requested_branch: str | None = None,
        process_code: str,
        stage_code: str,
    ) -> Tuple[str, tuple]:
        where_ac1, params_ac1 = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "AC1.D_E_L_E_T_"),
            )
        )
        branch_clause = ""
        branch_params: tuple = ()
        if requested_branch:
            branch_clause = "AND (RTRIM(ISNULL(AC2.AC2_FILIAL, '')) = '' OR AC2.AC2_FILIAL = ?)"
            branch_params = (requested_branch,)

        sql = f"""
            SELECT TOP 1
                LTRIM(RTRIM(AC1.AC1_DESCRI)) AS process_description,
                LTRIM(RTRIM(AC2.AC2_DESCRI)) AS stage_description
            FROM AC2010 AC2
            LEFT JOIN AC1010 AC1
                ON AC1.D_E_L_E_T_ = '{self.settings.active_delete_flag}'
               AND AC1.AC1_PROVEN = AC2.AC2_PROVEN
               AND (
                   RTRIM(ISNULL(AC1.AC1_FILIAL, '')) = ''
                   OR AC1.AC1_FILIAL = AC2.AC2_FILIAL
               )
            WHERE AC2.D_E_L_E_T_ = '{self.settings.active_delete_flag}'
              AND AC2.AC2_PROVEN = ?
              AND AC2.AC2_STAGE = ?
              {branch_clause}
              AND {where_ac1}
            ORDER BY
                CASE
                    WHEN AC2.AC2_FILIAL = ? THEN 0
                    WHEN RTRIM(ISNULL(AC2.AC2_FILIAL, '')) = '' THEN 1
                    ELSE 2
                END
        """
        branch_order = requested_branch or ""
        return sql, (
            process_code,
            stage_code,
            *branch_params,
            *params_ac1,
            branch_order,
        )

    def _history_event_from_row(self, row: dict) -> LMPHistoryEvent:
        return LMPHistoryEvent(
            revision=row["revision"],
            process_code=row["process_code"],
            stage_code=row["stage_code"],
            process_description=row.get("process_description") or None,
            stage_description=row.get("stage_description") or None,
            start_date=row.get("start_date") or None,
            start_time=row.get("start_time") or None,
            limit_date=row.get("limit_date") or None,
            limit_time=row.get("limit_time") or None,
            end_date=row.get("end_date") or None,
            end_time=row.get("end_time") or None,
            duration_minutes=int(row["duration_minutes"] or 0)
            if row.get("duration_minutes") not in (None, "")
            else None,
            status=row.get("status") or None,
            history_flag=row.get("history_flag") or None,
            is_engineering=bool(row.get("is_engineering")),
            next_revision=row.get("next_revision") or None,
            next_process_code=row.get("next_process_code") or None,
            next_stage_code=row.get("next_stage_code") or None,
            next_start_date=row.get("next_start_date") or None,
            previous_revision=row.get("previous_revision") or None,
            previous_process_code=row.get("previous_process_code") or None,
            previous_stage_code=row.get("previous_stage_code") or None,
        )

    def _attach_history_labels(
        self,
        events: list[LMPHistoryEvent],
        *,
        requested_branch: str | None,
    ) -> list[LMPHistoryEvent]:
        if not events:
            return events

        cache: dict[tuple[str, str], tuple[str | None, str | None]] = {}
        enriched: list[LMPHistoryEvent] = []

        with self as repo:
            for event in events:
                key = (event.process_code, event.stage_code)
                if key not in cache:
                    sql, params = self._sql_history_stage_labels_lmp(
                        requested_branch=requested_branch,
                        process_code=event.process_code,
                        stage_code=event.stage_code,
                    )
                    label_row = repo.execute_one(sql, params)
                    cache[key] = (
                        (label_row or {}).get("process_description"),
                        (label_row or {}).get("stage_description"),
                    )

                process_description, stage_description = cache[key]
                enriched.append(
                    LMPHistoryEvent(
                        revision=event.revision,
                        process_code=event.process_code,
                        stage_code=event.stage_code,
                        process_description=process_description,
                        stage_description=stage_description,
                        start_date=event.start_date,
                        start_time=event.start_time,
                        limit_date=event.limit_date,
                        limit_time=event.limit_time,
                        end_date=event.end_date,
                        end_time=event.end_time,
                        duration_minutes=event.duration_minutes,
                        status=event.status,
                        history_flag=event.history_flag,
                        is_engineering=event.is_engineering,
                        next_revision=event.next_revision,
                        next_process_code=event.next_process_code,
                        next_stage_code=event.next_stage_code,
                        next_start_date=event.next_start_date,
                        previous_revision=event.previous_revision,
                        previous_process_code=event.previous_process_code,
                        previous_stage_code=event.previous_stage_code,
                    )
                )

        return enriched

    def _sql_history_events_lmp(
        self,
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        where_aij, params_aij = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", requested_branch),
            )
        )
        where_eng, params_eng = self._sql_engineering_support_process_stage_condition(
            "E.AIJ_PROVEN",
            "E.AIJ_STAGE",
        )
        eng_minutes_expr = self._sql_event_engineering_minutes_expr("E")

        win = """PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
                        ORDER BY
                            A.AIJ_REVISA,
                            A.AIJ_DTINIC,
                            A.AIJ_HRINIC,
                            A.AIJ_STAGE,
                            A.R_E_C_N_O_"""

        sql = f"""
            WITH EventosOV AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_REVISA,
                    A.AIJ_PROVEN,
                    A.AIJ_STAGE,
                    A.AIJ_DTINIC,
                    A.AIJ_HRINIC,
                    A.AIJ_DTLIMI,
                    A.AIJ_HRLIMI,
                    A.AIJ_DTENCE,
                    A.AIJ_HRENCE,
                    A.AIJ_HISTOR,
                    A.AIJ_STATUS,
                    A.R_E_C_N_O_,
                    LEAD(A.AIJ_REVISA) OVER ({win}) AS PROXIMA_REVISA_GLOBAL,
                    LEAD(A.AIJ_PROVEN) OVER ({win}) AS PROXIMO_PROVEN_GLOBAL,
                    LEAD(A.AIJ_STAGE) OVER ({win}) AS PROXIMO_STAGE_GLOBAL,
                    LEAD(A.AIJ_DTINIC) OVER ({win}) AS PROXIMO_DTINIC_GLOBAL,
                    LEAD(A.AIJ_HRINIC) OVER ({win}) AS PROXIMO_HRINIC_GLOBAL,
                    LAG(A.AIJ_REVISA) OVER ({win}) AS REVISA_ANTERIOR,
                    LAG(A.AIJ_PROVEN) OVER ({win}) AS PROVEN_ANTERIOR,
                    LAG(A.AIJ_STAGE) OVER ({win}) AS STAGE_ANTERIOR
                FROM AIJ010 A
                WHERE {where_aij}
                  AND A.AIJ_NROPOR = ?
            )
            SELECT
                E.AIJ_REVISA AS revision,
                E.AIJ_PROVEN AS process_code,
                E.AIJ_STAGE AS stage_code,
                LTRIM(RTRIM(PRC.process_description)) AS process_description,
                LTRIM(RTRIM(STG.stage_description)) AS stage_description,
                E.AIJ_DTINIC AS start_date,
                E.AIJ_HRINIC AS start_time,
                E.AIJ_DTLIMI AS limit_date,
                E.AIJ_HRLIMI AS limit_time,
                E.AIJ_DTENCE AS end_date,
                E.AIJ_HRENCE AS end_time,
                {eng_minutes_expr.strip()} AS duration_minutes,
                E.AIJ_STATUS AS status,
                E.AIJ_HISTOR AS history_flag,
                E.PROXIMA_REVISA_GLOBAL AS next_revision,
                E.PROXIMO_PROVEN_GLOBAL AS next_process_code,
                E.PROXIMO_STAGE_GLOBAL AS next_stage_code,
                E.PROXIMO_DTINIC_GLOBAL AS next_start_date,
                E.REVISA_ANTERIOR AS previous_revision,
                E.PROVEN_ANTERIOR AS previous_process_code,
                E.STAGE_ANTERIOR AS previous_stage_code,
                CASE WHEN {where_eng} THEN 1 ELSE 0 END AS is_engineering
            FROM EventosOV E
            OUTER APPLY (
                SELECT TOP 1
                    AC1.AC1_DESCRI AS process_description
                FROM AC1010 AC1
                WHERE AC1.D_E_L_E_T_ = '{self.settings.active_delete_flag}'
                  AND AC1.AC1_PROVEN = E.AIJ_PROVEN
                  AND (
                      RTRIM(ISNULL(AC1.AC1_FILIAL, '')) = ''
                      OR AC1.AC1_FILIAL = E.AIJ_FILIAL
                  )
                ORDER BY
                    CASE
                        WHEN AC1.AC1_FILIAL = E.AIJ_FILIAL THEN 0
                        WHEN RTRIM(ISNULL(AC1.AC1_FILIAL, '')) = '' THEN 1
                        ELSE 2
                    END
            ) PRC
            OUTER APPLY (
                SELECT TOP 1
                    AC2.AC2_DESCRI AS stage_description
                FROM AC2010 AC2
                WHERE AC2.D_E_L_E_T_ = '{self.settings.active_delete_flag}'
                  AND AC2.AC2_PROVEN = E.AIJ_PROVEN
                  AND AC2.AC2_STAGE = E.AIJ_STAGE
                  AND (
                      RTRIM(ISNULL(AC2.AC2_FILIAL, '')) = ''
                      OR AC2.AC2_FILIAL = E.AIJ_FILIAL
                  )
                ORDER BY
                    CASE
                        WHEN AC2.AC2_FILIAL = E.AIJ_FILIAL THEN 0
                        WHEN RTRIM(ISNULL(AC2.AC2_FILIAL, '')) = '' THEN 1
                        ELSE 2
                    END
            ) STG
            ORDER BY
                E.AIJ_REVISA,
                E.AIJ_DTINIC,
                E.AIJ_HRINIC,
                E.AIJ_STAGE,
                E.R_E_C_N_O_
        """

        return sql, (*params_aij, *params_eng)

    # =========================
    # STAGED EXECUTION (single batch com temp tables)
    # =========================

    _TEMP_CANDIDATES = "#Delpi_CandidateLMPs"
    _TEMP_ENG_RESUMO = "#Delpi_EngResumo"
    _TEMP_PI_COUNT = "#Delpi_PICount"

    def _build_staged_batch(
        self,
        request: ListLMPRequest,
        *,
        include_qtd_pi: bool,
        lmp_only: bool = False,
        eng_resumo_lite: bool = False,
        final_select: str,
        final_params: tuple = (),
    ) -> Tuple[str, tuple]:
        """
        Monta um batch SQL único que:
        1. Limpa temp tables residuais (pooling)
        2. Cria temp tables por fase (SET NOCOUNT ON)
        3. Executa o SELECT final (SET NOCOUNT OFF)
        """
        lmp_only_candidates = self._candidate_scope_lmp_only(request)
        cte_candidates, params_candidates = self._sql_candidate_lmps_cte(
            request,
            lmp_only=lmp_only_candidates,
        )

        cte_hist, params_hist = self._sql_historico_ov_cte(
            scope_cte_name=self._TEMP_CANDIDATES,
            requested_branch=request.branch,
            date_start=request.date_start,
            date_end=request.date_end,
            eng_resumo_lite=eng_resumo_lite,
            per_candidate_revision=(
                self._uses_per_revision_candidate_listing()
                and self._has_listing_period_filter(
                    request.date_start,
                    request.date_end,
                )
            ),
        )

        parts = [
            "SET NOCOUNT ON;",
            f"DROP TABLE IF EXISTS {self._TEMP_PI_COUNT};",
            f"DROP TABLE IF EXISTS {self._TEMP_ENG_RESUMO};",
            f"DROP TABLE IF EXISTS {self._TEMP_CANDIDATES};",
            f"WITH\n{cte_candidates}\nSELECT * INTO {self._TEMP_CANDIDATES} FROM CandidateLMPs;",
            f"WITH\n{cte_hist}\nSELECT * INTO {self._TEMP_ENG_RESUMO} FROM EngenhariaResumoUltimaRevisao;",
        ]
        all_params: list = [*params_candidates, *params_hist]

        if include_qtd_pi:
            cte_prod, params_prod = self._sql_produtos_lmp_cte(
                scope_cte_name=self._TEMP_CANDIDATES,
                requested_branch=request.branch,
            )
            cte_pi, params_pi = self._sql_pi_total_by_ov_ctes_from_produtos_lmp()
            parts.append(
                f"WITH\n{cte_prod},\n{cte_pi}\n"
                f"SELECT * INTO {self._TEMP_PI_COUNT} FROM PI_COUNT_BY_OV;"
            )
            all_params.extend([*params_prod, *params_pi])

        parts.append("SET NOCOUNT OFF;")
        parts.append(f"{final_select}")
        all_params.extend(final_params)

        return "\n".join(parts), tuple(all_params)

    def _inline_staged_relations(self) -> tuple[str, str, str]:
        return "CandidateLMPs", "EngenhariaResumoUltimaRevisao", "PI_COUNT_BY_OV"

    def _build_dashboard_summary_inline_sql(
        self,
        request: ListLMPRequest,
        *,
        include_qtd_pi: bool,
        final_select: str,
        final_params: tuple = (),
    ) -> Tuple[str, tuple]:
        """
        Monta um único WITH encadeado (sem temp tables).

        O summary do dashboard usa `_build_staged_batch` — no SQL Server, materializar
        candidatos/engenharia em temp tables reduz o cold path (~2s vs ~9s inline).
        """
        lmp_only_candidates = self._candidate_scope_lmp_only(request)
        cte_candidates, params_candidates = self._sql_candidate_lmps_cte(
            request,
            lmp_only=lmp_only_candidates,
        )
        cte_hist, params_hist = self._sql_historico_ov_cte(
            scope_cte_name="CandidateLMPs",
            requested_branch=request.branch,
            date_start=request.date_start,
            date_end=request.date_end,
            eng_resumo_lite=True,
            per_candidate_revision=(
                self._uses_per_revision_candidate_listing()
                and self._has_listing_period_filter(
                    request.date_start,
                    request.date_end,
                )
            ),
        )

        ctes = [cte_candidates, cte_hist]
        all_params: list = [*params_candidates, *params_hist]

        if include_qtd_pi:
            cte_prod, params_prod = self._sql_produtos_lmp_cte(
                scope_cte_name="CandidateLMPs",
                requested_branch=request.branch,
            )
            cte_pi, params_pi = self._sql_pi_total_by_ov_ctes_from_produtos_lmp()
            ctes.extend([cte_prod, cte_pi])
            all_params.extend([*params_prod, *params_pi])

        all_params.extend(final_params)
        cte_block = ",\n".join(ctes)
        sql = f"WITH\n{cte_block}\n{final_select}"
        return sql, tuple(all_params)

    def _staged_final_select(
        self,
        *,
        include_qtd_pi: bool,
        order_by: bool,
        summary_only: bool = False,
        candidates_relation: str | None = None,
        eng_resumo_relation: str | None = None,
        pi_count_relation: str | None = None,
    ) -> str:
        candidates = candidates_relation or self._TEMP_CANDIDATES
        eng_resumo = eng_resumo_relation or self._TEMP_ENG_RESUMO
        pi_count = pi_count_relation or self._TEMP_PI_COUNT
        qtd_pi_select = "ISNULL(PI.QTD_PI, 0) AS qtd_pi" if include_qtd_pi else "0 AS qtd_pi"
        qtd_pi_join = f"""
            LEFT JOIN {pi_count} PI
                ON PI.ADJ_FILIAL = C.AD1_FILIAL
               AND PI.ADJ_NROPOR = C.AD1_NROPOR
               AND PI.ADJ_REVISA = C.AD1_REVISA
        """ if include_qtd_pi else ""
        qtd_pi_group_by = ",\n                PI.QTD_PI" if include_qtd_pi else ""
        residence_filter = self._engineering_residence_filter_sql()
        listing_kind_expr = self._effective_listing_kind_expr()
        order_clause = """
            ORDER BY
                C.LMP_START_DATE DESC,
                C.AD1_NROPOR DESC
        """ if order_by else ""
        eng_join_revision = self._staged_eng_resumo_join_revision_sql()
        cycle_index_expr = self._staged_cycle_index_expr()
        cycle_index_group_by = self._staged_cycle_index_group_by()

        if summary_only:
            return f"""
                SELECT
                    C.AD1_FILIAL AS branch,
                    C.AD1_NROPOR AS sale_number,
                    C.AD1_DESCRI AS sale_description,
                    {listing_kind_expr} AS listing_kind,
                    C.LMP_START_DATE AS start_date,
                    C.LMP_END_DATE AS end_date,
                    C.AD1_REVISA AS homolog_revision,
                    H.MEASUREMENT_REVISION AS measurement_revision,
                    C.LMP_START_DATE AS homolog_date,
                    {cycle_index_expr},
                    H.ENGINEERING_STATUS AS engineering_status,
                    H.TEMPO_TOTAL_MINUTOS_ENG AS engineering_total_minutes,
                    {qtd_pi_select}
                FROM {candidates} C
                LEFT JOIN {eng_resumo} H
                    ON H.AIJ_FILIAL = C.AD1_FILIAL
                   AND H.AIJ_NROPOR = C.AD1_NROPOR
                   {eng_join_revision}
                {qtd_pi_join}
                {residence_filter}
                GROUP BY
                    C.AD1_FILIAL,
                    C.AD1_NROPOR,
                    C.AD1_DESCRI,
                    C.LISTING_KIND,
                    C.HAS_SAMPLE_ANCHOR,
                    C.HAS_LMP_FINALIZED,
                    C.LMP_START_DATE,
                    C.LMP_END_DATE,
                    C.AD1_REVISA,
                    H.MEASUREMENT_REVISION,
                    H.ENGINEERING_STATUS,
                    H.TEMPO_TOTAL_MINUTOS_ENG,
                    H.TEMPO_MINUTOS_AMOSTRA_ENG
                    {cycle_index_group_by}
                    {qtd_pi_group_by}
                {order_clause}
            """

        return f"""
            SELECT
                C.AD1_FILIAL AS branch,
                C.AD1_NROPOR AS sale_number,
                C.AD1_DESCRI AS sale_description,
                {listing_kind_expr} AS listing_kind,
                C.LMP_START_DATE AS start_date,
                C.LMP_END_DATE AS end_date,
                H.ENGINEERING_STATUS AS engineering_status,
                H.QTD_PASSAGENS_ENG AS qtd_engineering_entries,
                H.QTD_PASSAGENS_ENCERRADAS AS qtd_engineering_closed,
                H.QTD_AVANCOU_ENG AS qtd_advanced_from_engineering,
                H.QTD_RETORNOU_ENG AS qtd_returned_from_engineering,
                H.TEMPO_TOTAL_MINUTOS_ENG AS engineering_total_minutes,
                {qtd_pi_select}
            FROM {candidates} C
            LEFT JOIN {eng_resumo} H
                ON H.AIJ_FILIAL = C.AD1_FILIAL
               AND H.AIJ_NROPOR = C.AD1_NROPOR
               {eng_join_revision}
            {qtd_pi_join}
            {residence_filter}
            GROUP BY
                C.AD1_FILIAL,
                C.AD1_NROPOR,
                C.AD1_DESCRI,
                C.LISTING_KIND,
                C.HAS_SAMPLE_ANCHOR,
                C.HAS_LMP_FINALIZED,
                C.LMP_START_DATE,
                C.LMP_END_DATE,
                H.ENGINEERING_STATUS,
                H.QTD_PASSAGENS_ENG,
                H.QTD_PASSAGENS_ENCERRADAS,
                H.QTD_AVANCOU_ENG,
                H.QTD_RETORNOU_ENG,
                H.TEMPO_TOTAL_MINUTOS_ENG,
                H.TEMPO_MINUTOS_AMOSTRA_ENG
                {cycle_index_group_by}
                {qtd_pi_group_by}
            {order_clause}
        """

    def _staged_count_select(self, *, include_qtd_pi: bool) -> str:
        qtd_pi_join = f"""
            LEFT JOIN {self._TEMP_PI_COUNT} PI
                ON PI.ADJ_FILIAL = C.AD1_FILIAL
               AND PI.ADJ_NROPOR = C.AD1_NROPOR
               AND PI.ADJ_REVISA = C.AD1_REVISA
        """ if include_qtd_pi else ""
        qtd_pi_group_by = ",\n                    PI.QTD_PI" if include_qtd_pi else ""
        residence_filter = self._engineering_residence_filter_sql()
        listing_kind_expr = self._effective_listing_kind_expr()
        eng_join_revision = self._staged_eng_resumo_join_revision_sql()
        cycle_index_group_by = self._staged_cycle_index_group_by()

        return f"""
            SELECT COUNT(*) AS total
            FROM (
                SELECT
                    C.AD1_FILIAL,
                    C.AD1_NROPOR,
                    {listing_kind_expr} AS listing_kind
                FROM {self._TEMP_CANDIDATES} C
                LEFT JOIN {self._TEMP_ENG_RESUMO} H
                    ON H.AIJ_FILIAL = C.AD1_FILIAL
                   AND H.AIJ_NROPOR = C.AD1_NROPOR
                   {eng_join_revision}
                {qtd_pi_join}
                {residence_filter}
                GROUP BY
                    C.AD1_FILIAL,
                    C.AD1_NROPOR,
                    C.AD1_DESCRI,
                    C.LISTING_KIND,
                    C.HAS_SAMPLE_ANCHOR,
                    C.HAS_LMP_FINALIZED,
                    C.LMP_START_DATE,
                    C.LMP_END_DATE,
                    C.AD1_REVISA,
                    H.ENGINEERING_STATUS,
                    H.QTD_PASSAGENS_ENG,
                    H.QTD_PASSAGENS_ENCERRADAS,
                    H.QTD_AVANCOU_ENG,
                    H.QTD_RETORNOU_ENG,
                    H.TEMPO_TOTAL_MINUTOS_ENG,
                    H.TEMPO_MINUTOS_AMOSTRA_ENG
                    {cycle_index_group_by}
                    {qtd_pi_group_by}
            ) EFFECTIVE_LISTING_ROWS
        """

    # =========================
    # PUBLIC METHODS
    # =========================
    def list_lmps(self, request: ListLMPRequest) -> List[LMP]:
        include_qtd_pi = self._resolve_include_qtd_pi(request)
        final_select = self._staged_final_select(
            include_qtd_pi=include_qtd_pi, order_by=True,
        )
        residence_params = self._staged_residence_final_params(
            residence_filter_count=1,
            listing_kind_reclass_count=1,
        )
        final_select, final_params = self._apply_effective_listing_type_filter_to_select(
            request,
            final_select,
            residence_params,
        )
        batch_sql, batch_params = self._build_staged_batch(
            request,
            include_qtd_pi=include_qtd_pi,
            final_select=final_select,
            final_params=final_params,
        )
        with self as repo:
            rows = repo.execute_batch_query(batch_sql, batch_params)
        return [LMP(**row) for row in rows]

    def list_lmps_page(self, request: ListLMPRequest) -> Page[LMP]:
        if not request.page_size:
            rows = self.list_lmps(request)
            total = len(rows)
            return Page(
                items=rows,
                total=total,
                page=1,
                page_size=total,
            )

        include_qtd_pi = self._resolve_include_qtd_pi(request)
        page = request.page or 1
        page_size = request.page_size or 0
        offset = (page - 1) * page_size

        count_select = self._staged_count_select(include_qtd_pi=include_qtd_pi)
        rows_select = self._staged_final_select(
            include_qtd_pi=include_qtd_pi, order_by=True,
        )
        query_params = self._staged_residence_final_params(
            residence_filter_count=1,
            listing_kind_reclass_count=1,
        )
        count_select, count_params = self._apply_effective_listing_type_filter_to_select(
            request,
            count_select,
            query_params,
        )
        rows_select, rows_params = self._apply_effective_listing_type_filter_to_select(
            request,
            rows_select,
            query_params,
        )
        combined_final = f"""
            {count_select};
            {rows_select}
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
        """
        batch_sql, batch_params = self._build_staged_batch(
            request,
            include_qtd_pi=include_qtd_pi,
            final_select=combined_final,
            final_params=(
                *count_params,
                *rows_params,
                offset,
                page_size,
            ),
        )

        with self as repo:
            repo.cursor.execute(batch_sql, batch_params)

            while repo.cursor.description is None:
                if not repo.cursor.nextset():
                    return Page(items=[], total=0, page=page, page_size=page_size)

            total_row = repo.cursor.fetchone()
            total = int(total_row[0] if total_row else 0)

            if not repo.cursor.nextset() or repo.cursor.description is None:
                return Page(items=[], total=total, page=page, page_size=page_size)

            columns = [desc[0] for desc in repo.cursor.description]
            raw_rows = repo.cursor.fetchall()
            rows = [
                repo._normalize_row(dict(zip(columns, row)))
                for row in raw_rows
            ]

        return Page(
            items=[LMP(**row) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_lmp(self, request: GetLMPRequest) -> LMP:
        requested_branch = self._get_request_branch(request)

        sql_header, params_header = self._sql_header_lmp(request)
        sql_products, params_products = self._sql_products_lmp(
            requested_branch=requested_branch,
            sale_number=request.sale_number,
        )
        sql_qtd_pi, params_qtd_pi = self._sql_qtd_pi_lmp_total(requested_branch=requested_branch)

        with self as repo:
            header_row = repo.execute_one(
                sql_header,
                params_header,
            )

            if not header_row:
                raise ValueError(
                    f"OV não encontrada na listagem de engenharia: {request.sale_number}"
                )

            product_rows = repo.execute_query(
                sql_products,
                params_products,
            )

            qtd_pi = repo.execute_scalar(
                sql_qtd_pi,
                (*params_qtd_pi, request.sale_number),
            )

        products = [LMPProduct(**row) for row in product_rows]

        return LMP(
            branch=header_row.get("branch"),
            sale_number=header_row["sale_number"],
            sale_description=header_row["sale_description"],
            listing_kind=header_row.get("listing_kind"),
            start_date=header_row.get("start_date"),
            end_date=header_row.get("end_date"),
            reference_revision=header_row.get("reference_revision"),
            measurement_revision=header_row.get("measurement_revision"),
            engineering_status=header_row.get("engineering_status"),
            qtd_engineering_entries=int(header_row.get("qtd_engineering_entries") or 0),
            qtd_engineering_closed=int(header_row.get("qtd_engineering_closed") or 0),
            qtd_advanced_from_engineering=int(header_row.get("qtd_advanced_from_engineering") or 0),
            qtd_returned_from_engineering=int(header_row.get("qtd_returned_from_engineering") or 0),
            engineering_total_minutes=int(header_row.get("engineering_total_minutes") or 0),
            qtd_pi=int(qtd_pi or 0),
            costumer_code=header_row.get("costumer_code"),
            costumer_store=header_row.get("costumer_store"),
            costumer_name=header_row.get("costumer_name"),
            seller_code=header_row.get("seller_code"),
            seller_name=header_row.get("seller_name"),
            list_products=products,
            list_history=[],
        )

    def list_ov_products(
        self,
        *,
        sale_number: str,
        requested_branch: str | None = None,
    ) -> list[LMPProduct]:
        sql_products, params_products = self._sql_products_lmp(
            requested_branch=requested_branch,
            sale_number=sale_number,
        )

        with self as repo:
            product_rows = repo.execute_query(
                sql_products,
                params_products,
            )

        return [
            LMPProduct(
                code=str(row.get("code") or "").strip(),
                description=str(row.get("description") or "").strip(),
                group_code=row.get("group_code"),
                type=row.get("type"),
                qtd_pi=int(row["qtd_pi"])
                if row.get("qtd_pi") not in (None, "")
                else None,
            )
            for row in product_rows
            if str(row.get("code") or "").strip()
        ]

    def _sql_history_panel_context_lite(
        self,
        *,
        sale_number: str,
        requested_branch: str | None = None,
        revision: str | None = None,
    ) -> Tuple[str, tuple]:
        where_ad1, params_ad1 = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "AD1.D_E_L_E_T_"),
                self._branch_filter(qb, "AD1.AD1_FILIAL", requested_branch),
                qb.eq("AD1.AD1_NROPOR", sale_number.strip()),
            )
        )
        revision_filter = ""
        revision_params: tuple = ()
        normalized_revision = str(revision or "").strip()
        if normalized_revision:
            revision_filter = "AND AD1.AD1_REVISA = ?"
            revision_params = (normalized_revision,)
        revision_order = "" if normalized_revision else "ORDER BY AD1.AD1_REVISA DESC"

        sql = f"""
            SELECT TOP 1
                AD1.AD1_FILIAL AS branch,
                AD1.AD1_REVISA AS reference_revision,
                AD1.AD1_DATA AS panel_start_date
            FROM AD1010 AD1
            WHERE {where_ad1}
              {revision_filter}
            {revision_order}
        """
        return sql, (*params_ad1, *revision_params)

    def get_lmp_history_panel_context(self, request: GetLmpHistoryRequest) -> dict:
        requested_branch = self._get_request_branch(request)
        sql, params = self._sql_history_panel_context_lite(
            sale_number=request.sale_number,
            requested_branch=requested_branch,
            revision=request.revision,
        )

        with self as repo:
            header_row = repo.execute_one(sql, params)

        if not header_row:
            raise ValueError(
                f"OV não encontrada na listagem de engenharia: {request.sale_number}"
            )

        return {
            "branch": header_row.get("branch"),
            "reference_revision": header_row.get("reference_revision"),
            "panel_start_date": header_row.get("panel_start_date"),
        }

    def get_lmp_panel_context(self, request: GetLMPRequest) -> dict:
        sql_header, params_header = self._sql_header_lmp(request)

        with self as repo:
            header_row = repo.execute_one(
                sql_header,
                params_header,
            )

        if not header_row:
            raise ValueError(
                f"OV não encontrada na listagem de engenharia: {request.sale_number}"
            )

        return {
            "branch": header_row.get("branch"),
            "reference_revision": header_row.get("reference_revision"),
            "panel_start_date": header_row.get("start_date"),
        }

    def get_lmp_history_events(
        self,
        request: GetLmpHistoryRequest,
    ) -> list[LMPHistoryEvent]:
        requested_branch = self._get_request_branch(request)
        sql_history, params_eng, params_aij, revision_params = self._sql_history_events_lmp_lite(
            requested_branch=requested_branch,
            revision=request.revision,
        )
        query_params = (
            *params_eng,
            *params_aij,
            request.sale_number,
            *revision_params,
        )

        with self as repo:
            history_rows = repo.execute_query(
                sql_history,
                query_params,
            )

        events = [self._history_event_from_row(row) for row in history_rows]
        return self._attach_history_labels(
            events,
            requested_branch=requested_branch,
        )

    def get_lmp_history_flow(
        self,
        request: GetLmpHistoryRequest,
    ) -> list[LMPHistoryEvent]:
        requested_branch = self._get_request_branch(request)
        sql_flow, params_aij, revision_params, params_eng, params_eng_next = (
            self._sql_history_flow_lmp(
                requested_branch=requested_branch,
                revision=request.revision,
            )
        )
        query_params = (
            *params_aij,
            request.sale_number,
            *revision_params,
            *params_eng,
            *params_eng_next,
            *params_eng,
        )

        with self as repo:
            flow_rows = repo.execute_query(
                sql_flow,
                query_params,
            )

        events = [self._history_event_from_row(row) for row in flow_rows]
        return self._attach_history_labels(
            events,
            requested_branch=requested_branch,
        )

    def get_lmp_dashboard_summary(self, request: ListLMPRequest) -> list[dict]:
        include_qtd_pi = self._resolve_include_qtd_pi(request)
        cache_key = lmp_dashboard_summary_rows_cache_key(
            date_start=request.date_start,
            date_end=request.date_end,
            branch=request.branch,
            listing_type=request.listing_type,
            include_qtd_pi=include_qtd_pi,
        )
        cached = get_cached_lmp_dashboard_summary_rows(cache_key)
        if cached is not None:
            return cached

        final_select = self._staged_final_select(
            include_qtd_pi=include_qtd_pi,
            order_by=False,
            summary_only=True,
        )
        residence_params = self._staged_residence_final_params(
            residence_filter_count=1,
            listing_kind_reclass_count=1,
        )
        final_select, final_params = self._apply_effective_listing_type_filter_to_select(
            request,
            final_select,
            residence_params,
        )
        batch_sql, batch_params = self._build_staged_batch(
            request,
            include_qtd_pi=include_qtd_pi,
            eng_resumo_lite=True,
            final_select=final_select,
            final_params=final_params,
        )

        with self as repo:
            rows = repo.execute_batch_query(batch_sql, batch_params)

        normalized = [
            {
                "branch": row.get("branch"),
                "sale_number": row.get("sale_number"),
                "sale_description": (row.get("sale_description") or "").strip(),
                "listing_kind": row.get("listing_kind"),
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date"),
                "homolog_revision": row.get("homolog_revision"),
                "measurement_revision": row.get("measurement_revision"),
                "homolog_date": row.get("homolog_date"),
                "cycle_index": int(row.get("cycle_index") or 1),
                "engineering_status": row.get("engineering_status"),
                "engineering_total_minutes": int(row.get("engineering_total_minutes") or 0),
                "qtd_pi": int(row.get("qtd_pi") or 0),
            }
            for row in rows
        ]
        set_cached_lmp_dashboard_summary_rows(cache_key, normalized)
        return normalized