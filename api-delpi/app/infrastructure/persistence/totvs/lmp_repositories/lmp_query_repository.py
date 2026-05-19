from typing import List, Tuple

from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.models.page import Page
from app.domain.entities.lmp.lmp import LMP
from app.domain.entities.lmp.lmp_product import LMPProduct
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.lmp_repositories.lmp_query_settings import (
    LMPQuerySettings,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class LMPQueryRepository(BaseRepository, LMPQueryRepositoryPort):
    LISTING_KIND_LMP = "LMP"
    LISTING_KIND_SAMPLE = "AMOSTRA"

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

    def _resolve_listing_type_filter(
        self,
        request: ListLMPRequest,
        *,
        lmp_only: bool = False,
    ) -> str | None:
        if lmp_only:
            return self.LISTING_KIND_LMP

        raw = getattr(request, "listing_type", None)
        if raw is None:
            return None

        normalized = str(raw).strip().lower()
        if normalized in ("", "todos", "all"):
            return None
        if normalized == "lmp":
            return self.LISTING_KIND_LMP
        if normalized in ("amostra", "amostras", "sample"):
            return self.LISTING_KIND_SAMPLE

        raise ValueError(
            "listing_type inválido. Valores aceitos: Todos, LMP ou Amostra."
        )

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
        base_sql, base_params = self._sql_lmp_base_rows_dataset_query(
            request,
            include_qtd_pi=include_qtd_pi,
            order_by=False,
        )

        sql = f"""
            SELECT COUNT(*) AS total
            FROM (
                {base_sql}
            ) BASE_ROWS
        """
        return sql, base_params

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
    ) -> Tuple[str, tuple]:
        ctes_sql, ctes_params = self._sql_lmp_base_dataset_ctes(
            request,
            include_qtd_pi=include_qtd_pi,
            lmp_only=True,
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

    def _sql_candidate_lmps_cte(
        self,
        request: ListLMPRequest,
        *,
        lmp_only: bool = False,
    ) -> Tuple[str, tuple]:
        listing_filter = self._resolve_listing_type_filter(
            request,
            lmp_only=lmp_only,
        )
        include_lmp = listing_filter in (None, self.LISTING_KIND_LMP)
        include_sample = (not lmp_only) and listing_filter in (
            None,
            self.LISTING_KIND_SAMPLE,
        )

        cte_lmp, params_lmp = self._sql_lmp_marker_cte(request.branch)
        cte_sample, params_sample = self._sql_sample_marker_cte(request.branch)
        where_ad1, params_ad1 = self._sql_filter_ad1_active_branch("AD1", request.branch)

        candidate_parts: list[str] = []
        candidate_params: list = []

        if include_lmp:
            qb_lmp = QueryBuilder()
            qb_lmp.date_range(
                field="L.LMP_START_DATE",
                start=request.date_start,
                end=request.date_end,
            )
            where_period_lmp, params_period_lmp = qb_lmp.build()

            candidate_parts.append(f"""
                SELECT DISTINCT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA,
                    AD1.AD1_DESCRI,
                    ? AS LISTING_KIND,
                    L.LMP_START_DATE,
                    L.LMP_END_DATE
                FROM AD1010 AD1
                INNER JOIN LMPEventos L
                    ON L.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND L.AIJ_NROPOR = AD1.AD1_NROPOR
                WHERE {where_ad1}
                  AND {where_period_lmp}
            """)
            candidate_params.extend(
                [
                    self.LISTING_KIND_LMP,
                    *params_ad1,
                    *params_period_lmp,
                ]
            )

        if include_sample:
            qb_sample = QueryBuilder()
            qb_sample.date_range(
                field="S.SAMPLE_START_DATE",
                start=request.date_start,
                end=request.date_end,
            )
            where_period_sample, params_period_sample = qb_sample.build()

            candidate_parts.append(f"""
                SELECT DISTINCT
                    AD1.AD1_FILIAL,
                    AD1.AD1_NROPOR,
                    AD1.AD1_REVISA,
                    AD1.AD1_DESCRI,
                    ? AS LISTING_KIND,
                    S.SAMPLE_START_DATE AS LMP_START_DATE,
                    S.SAMPLE_END_DATE AS LMP_END_DATE
                FROM AD1010 AD1
                INNER JOIN SampleEventos S
                    ON S.AIJ_FILIAL = AD1.AD1_FILIAL
                   AND S.AIJ_NROPOR = AD1.AD1_NROPOR
                WHERE {where_ad1}
                  AND {where_period_sample}
                  AND NOT EXISTS (
                      SELECT 1
                      FROM LMPEventos L2
                      WHERE L2.AIJ_FILIAL = AD1.AD1_FILIAL
                        AND L2.AIJ_NROPOR = AD1.AD1_NROPOR
                  )
            """)
            candidate_params.extend(
                [
                    self.LISTING_KIND_SAMPLE,
                    *params_ad1,
                    *params_period_sample,
                ]
            )

        if not candidate_parts:
            sql = f"""
                {cte_lmp},
                {cte_sample},
                CandidateLMPs AS (
                    SELECT
                        CAST(NULL AS VARCHAR(2)) AS AD1_FILIAL,
                        CAST(NULL AS VARCHAR(20)) AS AD1_NROPOR,
                        CAST(NULL AS VARCHAR(3)) AS AD1_REVISA,
                        CAST(NULL AS VARCHAR(254)) AS AD1_DESCRI,
                        CAST(NULL AS VARCHAR(10)) AS LISTING_KIND,
                        CAST(NULL AS VARCHAR(8)) AS LMP_START_DATE,
                        CAST(NULL AS VARCHAR(8)) AS LMP_END_DATE
                    WHERE 1 = 0
                )
            """
            return sql, (*params_lmp, *params_sample)

        union_sql = "\n                UNION ALL\n".join(candidate_parts)
        marker_ctes = [cte_lmp]
        marker_params: list = [*params_lmp]
        if include_sample:
            marker_ctes.append(cte_sample)
            marker_params.extend(params_sample)

        marker_ctes_sql = ",\n".join(marker_ctes)
        sql = f"""
            {marker_ctes_sql},

            CandidateLMPs AS (
                {union_sql}
            )
        """

        params = (*marker_params, *candidate_params)
        return sql, params

    def _sql_historico_ov_cte(
        self,
        scope_cte_name: str | None = None,
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        where_aij_base_a, params_aij_base_a = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", requested_branch),
            )
        )

        where_evento_global_x, params_evento_global_x = self._build_filter_sql(
            lambda qb: self._branch_filter(qb, "X.AIJ_FILIAL", requested_branch)
        )

        where_eng_support_e, params_eng_support_e = self._sql_engineering_support_process_stage_condition(
            "E.AIJ_PROVEN",
            "E.AIJ_STAGE",
        )

        where_eng_support_x, params_eng_support_x = self._sql_engineering_support_process_stage_condition(
            "X.AIJ_PROVEN",
            "X.AIJ_STAGE",
        )

        where_lmp_anchor_rank_e, params_lmp_anchor_rank_e = self._sql_lmp_anchor_process_stage_condition(
            "R.AIJ_PROVEN",
            "R.AIJ_STAGE",
        )

        scope_join_a = ""
        if scope_cte_name:
            scope_join_a = f"""
                INNER JOIN {scope_cte_name} SCOPE_A
                    ON SCOPE_A.AD1_FILIAL = A.AIJ_FILIAL
                   AND SCOPE_A.AD1_NROPOR = A.AIJ_NROPOR
            """

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
                    ROW_NUMBER() OVER (
                        PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
                        ORDER BY
                            A.AIJ_REVISA,
                            A.AIJ_DTINIC,
                            A.AIJ_HRINIC,
                            A.AIJ_STAGE,
                            A.R_E_C_N_O_
                    ) AS ORDEM_GLOBAL
                FROM AIJ010 A
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
                    E.ORDEM_GLOBAL,
                    NEXT_EVT.PROXIMA_REVISA_GLOBAL,
                    NEXT_EVT.PROXIMO_PROVEN_GLOBAL,
                    NEXT_EVT.PROXIMO_STAGE_GLOBAL,
                    NEXT_EVT.PROXIMO_DTINIC_GLOBAL,
                    NEXT_EVT.PROXIMO_HRINIC_GLOBAL,
                    NEXT_EVT.PROXIMO_DTENCE_GLOBAL,
                    NEXT_EVT.PROXIMO_HRENCE_GLOBAL,
                    NEXT_EVT.PROXIMO_EH_ENG_GLOBAL
                FROM TodosEventosOV E
                OUTER APPLY (
                    SELECT TOP 1
                        X.AIJ_REVISA AS PROXIMA_REVISA_GLOBAL,
                        X.AIJ_PROVEN AS PROXIMO_PROVEN_GLOBAL,
                        X.AIJ_STAGE AS PROXIMO_STAGE_GLOBAL,
                        X.AIJ_DTINIC AS PROXIMO_DTINIC_GLOBAL,
                        X.AIJ_HRINIC AS PROXIMO_HRINIC_GLOBAL,
                        X.AIJ_DTENCE AS PROXIMO_DTENCE_GLOBAL,
                        X.AIJ_HRENCE AS PROXIMO_HRENCE_GLOBAL,
                        CASE
                            WHEN {where_eng_support_x} THEN 1
                            ELSE 0
                        END AS PROXIMO_EH_ENG_GLOBAL
                    FROM TodosEventosOV X
                    WHERE {where_evento_global_x}
                      AND X.AIJ_FILIAL = E.AIJ_FILIAL
                      AND X.AIJ_NROPOR = E.AIJ_NROPOR
                      AND X.ORDEM_GLOBAL > E.ORDEM_GLOBAL
                      AND (
                            X.AIJ_DTINIC > E.AIJ_DTINIC
                            OR (
                                X.AIJ_DTINIC = E.AIJ_DTINIC
                                AND ISNULL(X.AIJ_HRINIC, '') > ISNULL(E.AIJ_HRINIC, '')
                            )
                          )
                    ORDER BY
                        X.AIJ_DTINIC,
                        X.AIJ_HRINIC,
                        X.AIJ_REVISA,
                        X.AIJ_STAGE,
                        X.R_E_C_N_O_
                ) NEXT_EVT
                WHERE {where_eng_support_e}
            ),

            UltimaRevisaoEngenharia AS (
                SELECT
                    E.AIJ_FILIAL,
                    E.AIJ_NROPOR,
                    MAX(E.AIJ_REVISA) AS ULTIMA_REVISA
                FROM EngenhariaEventos E
                GROUP BY
                    E.AIJ_FILIAL,
                    E.AIJ_NROPOR
            ),

            StatusUltimaRevisaoEngenharia AS (
                SELECT
                    E.AIJ_FILIAL,
                    E.AIJ_NROPOR,
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
                INNER JOIN UltimaRevisaoEngenharia U
                    ON U.AIJ_FILIAL = E.AIJ_FILIAL
                   AND U.AIJ_NROPOR = E.AIJ_NROPOR
                   AND U.ULTIMA_REVISA = E.AIJ_REVISA
                GROUP BY
                    E.AIJ_FILIAL,
                    E.AIJ_NROPOR
            ),

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

            EngenhariaResumoUltimaRevisao AS (
                SELECT
                    E.AIJ_FILIAL,
                    E.AIJ_NROPOR,
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
                    SUM(
                        CASE
                            WHEN ISNULL(E.AIJ_DTINIC, '') <> ''
                             AND ISNULL(E.AIJ_HRINIC, '') <> ''
                            THEN DATEDIFF(
                                MINUTE,
                                CAST(
                                    CONCAT(
                                        SUBSTRING(E.AIJ_DTINIC, 1, 4), '-',
                                        SUBSTRING(E.AIJ_DTINIC, 5, 2), '-',
                                        SUBSTRING(E.AIJ_DTINIC, 7, 2), ' ',
                                        E.AIJ_HRINIC, ':00'
                                    ) AS DATETIME
                                ),
                                CASE
                                    WHEN ISNULL(E.AIJ_DTENCE, '') <> ''
                                     AND ISNULL(E.AIJ_HRENCE, '') <> ''
                                    THEN CAST(
                                        CONCAT(
                                            SUBSTRING(E.AIJ_DTENCE, 1, 4), '-',
                                            SUBSTRING(E.AIJ_DTENCE, 5, 2), '-',
                                            SUBSTRING(E.AIJ_DTENCE, 7, 2), ' ',
                                            E.AIJ_HRENCE, ':00'
                                        ) AS DATETIME
                                    )
                                    WHEN ISNULL(E.PROXIMO_DTINIC_GLOBAL, '') <> ''
                                     AND ISNULL(E.PROXIMO_HRINIC_GLOBAL, '') <> ''
                                    THEN CAST(
                                        CONCAT(
                                            SUBSTRING(E.PROXIMO_DTINIC_GLOBAL, 1, 4), '-',
                                            SUBSTRING(E.PROXIMO_DTINIC_GLOBAL, 5, 2), '-',
                                            SUBSTRING(E.PROXIMO_DTINIC_GLOBAL, 7, 2), ' ',
                                            E.PROXIMO_HRINIC_GLOBAL, ':00'
                                        ) AS DATETIME
                                    )
                                    ELSE GETDATE()
                                END
                            )
                            ELSE 0
                        END
                    ) AS TEMPO_TOTAL_MINUTOS_ENG,
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
                    ) AS QTD_RETORNOU_ENG,
                    S.ENGINEERING_STATUS AS ENGINEERING_STATUS
                FROM EngenhariaEventos E
                INNER JOIN UltimaRevisaoMedicaoEngenharia M
                    ON M.AIJ_FILIAL = E.AIJ_FILIAL
                   AND M.AIJ_NROPOR = E.AIJ_NROPOR
                   AND M.ULTIMA_REVISA_MEDICAO = E.AIJ_REVISA
                INNER JOIN StatusUltimaRevisaoEngenharia S
                    ON S.AIJ_FILIAL = E.AIJ_FILIAL
                   AND S.AIJ_NROPOR = E.AIJ_NROPOR
                GROUP BY
                    E.AIJ_FILIAL,
                    E.AIJ_NROPOR,
                    S.ENGINEERING_STATUS
            )
        """

        params = (
            *params_aij_base_a,
            *params_eng_support_x,
            *params_evento_global_x,
            *params_eng_support_e,
            self._engineering_status_returned_label(),
            self._engineering_status_in_progress_label(),
            self._engineering_status_finished_label(),
            self._engineering_status_partial_label(),
            *params_lmp_anchor_rank_e,
        )
        return sql, params

    def _sql_lmp_marker_cte(
        self,
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        where_aij_base, params_aij_base = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", requested_branch),
            )
        )

        where_lmp_anchor, params_lmp_anchor = self._sql_lmp_anchor_process_stage_condition(
            "A.AIJ_PROVEN",
            "A.AIJ_STAGE",
        )

        sql = f"""
            LMPAnchorEventos AS (
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
                    ROW_NUMBER() OVER (
                        PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
                        ORDER BY
                            A.AIJ_REVISA DESC,
                            A.AIJ_DTINIC DESC,
                            A.AIJ_HRINIC DESC,
                            A.R_E_C_N_O_ DESC
                    ) AS RN_DESC
                FROM AIJ010 A
                WHERE {where_aij_base}
                  AND {where_lmp_anchor}
            ),

            LMPAnchorResolvido AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA,
                    A.AIJ_PROVEN,
                    A.AIJ_STAGE,
                    A.AIJ_DTINIC AS LMP_START_DATE,
                    COALESCE(
                        NULLIF(A.AIJ_DTENCE, ''),
                        NEXT_EVT.NEXT_DATE
                    ) AS LMP_END_DATE,
                    A.RN_DESC
                FROM LMPAnchorEventos A
                OUTER APPLY (
                    SELECT TOP 1
                        COALESCE(
                            NULLIF(X.AIJ_DTENCE, ''),
                            NULLIF(X.AIJ_DTINIC, '')
                        ) AS NEXT_DATE
                    FROM AIJ010 X
                    WHERE X.D_E_L_E_T_ = ''
                      AND X.AIJ_FILIAL = A.AIJ_FILIAL
                      AND X.AIJ_NROPOR = A.AIJ_NROPOR
                      AND (
                            X.AIJ_REVISA > A.AIJ_REVISA
                            OR (
                                X.AIJ_REVISA = A.AIJ_REVISA
                                AND (
                                    X.AIJ_DTINIC > A.AIJ_DTINIC
                                    OR (
                                        X.AIJ_DTINIC = A.AIJ_DTINIC
                                        AND ISNULL(X.AIJ_HRINIC, '') > ISNULL(A.AIJ_HRINIC, '')
                                    )
                                    OR (
                                        X.AIJ_DTINIC = A.AIJ_DTINIC
                                        AND ISNULL(X.AIJ_HRINIC, '') = ISNULL(A.AIJ_HRINIC, '')
                                        AND X.R_E_C_N_O_ > A.R_E_C_N_O_
                                    )
                                )
                            )
                      )
                    ORDER BY
                        X.AIJ_DTINIC ASC,
                        X.AIJ_HRINIC ASC,
                        X.AIJ_REVISA ASC,
                        X.R_E_C_N_O_ ASC
                ) NEXT_EVT
            ),

            LMPEventos AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.LMP_START_DATE,
                    A.LMP_END_DATE,
                    1 AS QTD_PASSAGENS_LMP,
                    CASE
                        WHEN ISNULL(A.LMP_END_DATE, '') <> '' THEN 1
                        ELSE 0
                    END AS QTD_PASSAGENS_LMP_ENCERRADAS
                FROM LMPAnchorResolvido A
                WHERE A.RN_DESC = 1
            )
        """

        params = (
            *params_aij_base,
            *params_lmp_anchor,
        )
        return sql, params

    def _sql_sample_marker_cte(
        self,
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        where_aij_base, params_aij_base = self._build_filter_sql(
            lambda qb: (
                self._active_filter(qb, "A.D_E_L_E_T_"),
                self._branch_filter(qb, "A.AIJ_FILIAL", requested_branch),
            )
        )

        where_sample_anchor, params_sample_anchor = (
            self._sql_sample_anchor_process_stage_condition(
                "A.AIJ_PROVEN",
                "A.AIJ_STAGE",
            )
        )

        sql = f"""
            SampleAnchorEventos AS (
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
                    ROW_NUMBER() OVER (
                        PARTITION BY A.AIJ_FILIAL, A.AIJ_NROPOR
                        ORDER BY
                            A.AIJ_REVISA DESC,
                            A.AIJ_DTINIC DESC,
                            A.AIJ_HRINIC DESC,
                            A.R_E_C_N_O_ DESC
                    ) AS RN_DESC
                FROM AIJ010 A
                WHERE {where_aij_base}
                  AND {where_sample_anchor}
            ),

            SampleAnchorResolvido AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.AIJ_REVISA,
                    A.AIJ_PROVEN,
                    A.AIJ_STAGE,
                    A.AIJ_DTINIC AS SAMPLE_START_DATE,
                    COALESCE(
                        NULLIF(A.AIJ_DTENCE, ''),
                        NEXT_EVT.NEXT_DATE
                    ) AS SAMPLE_END_DATE,
                    A.RN_DESC
                FROM SampleAnchorEventos A
                OUTER APPLY (
                    SELECT TOP 1
                        COALESCE(
                            NULLIF(X.AIJ_DTENCE, ''),
                            NULLIF(X.AIJ_DTINIC, '')
                        ) AS NEXT_DATE
                    FROM AIJ010 X
                    WHERE X.D_E_L_E_T_ = ''
                      AND X.AIJ_FILIAL = A.AIJ_FILIAL
                      AND X.AIJ_NROPOR = A.AIJ_NROPOR
                      AND (
                            X.AIJ_REVISA > A.AIJ_REVISA
                            OR (
                                X.AIJ_REVISA = A.AIJ_REVISA
                                AND (
                                    X.AIJ_DTINIC > A.AIJ_DTINIC
                                    OR (
                                        X.AIJ_DTINIC = A.AIJ_DTINIC
                                        AND ISNULL(X.AIJ_HRINIC, '') > ISNULL(A.AIJ_HRINIC, '')
                                    )
                                    OR (
                                        X.AIJ_DTINIC = A.AIJ_DTINIC
                                        AND ISNULL(X.AIJ_HRINIC, '') = ISNULL(A.AIJ_HRINIC, '')
                                        AND X.R_E_C_N_O_ > A.R_E_C_N_O_
                                    )
                                )
                            )
                      )
                    ORDER BY
                        X.AIJ_DTINIC ASC,
                        X.AIJ_HRINIC ASC,
                        X.AIJ_REVISA ASC,
                        X.R_E_C_N_O_ ASC
                ) NEXT_EVT
            ),

            SampleEventos AS (
                SELECT
                    A.AIJ_FILIAL,
                    A.AIJ_NROPOR,
                    A.SAMPLE_START_DATE,
                    A.SAMPLE_END_DATE
                FROM SampleAnchorResolvido A
                WHERE A.RN_DESC = 1
            )
        """

        params = (
            *params_aij_base,
            *params_sample_anchor,
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

    def _sql_header_lmp(
        self,
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        cte_lmp, params_lmp = self._sql_lmp_marker_cte(requested_branch)
        cte_sample, params_sample = self._sql_sample_marker_cte(requested_branch)
        cte_hist, params_hist = self._sql_historico_ov_cte(requested_branch=requested_branch)
        where_ad1, params_ad1 = self._sql_filter_ad1_active_branch("AD1", requested_branch)
        where_sa1, params_sa1 = self._sql_filter_sa1_active("SA1")
        where_sa3, params_sa3 = self._sql_filter_sa3_active("SA3")

        sql = f"""
            WITH
            {cte_lmp},
            {cte_sample},
            {cte_hist}
            SELECT TOP 1
                AD1.AD1_FILIAL AS branch,
                AD1.AD1_NROPOR AS sale_number,
                AD1.AD1_DESCRI AS sale_description,
                CASE
                    WHEN L.AIJ_NROPOR IS NOT NULL THEN ?
                    ELSE ?
                END AS listing_kind,
                COALESCE(L.LMP_START_DATE, S.SAMPLE_START_DATE) AS start_date,
                COALESCE(L.LMP_END_DATE, S.SAMPLE_END_DATE) AS end_date,
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
            LEFT JOIN LMPEventos L
                ON L.AIJ_FILIAL = AD1.AD1_FILIAL
               AND L.AIJ_NROPOR = AD1.AD1_NROPOR
            LEFT JOIN SampleEventos S
                ON S.AIJ_FILIAL = AD1.AD1_FILIAL
               AND S.AIJ_NROPOR = AD1.AD1_NROPOR
            LEFT JOIN EngenhariaResumoUltimaRevisao H
                ON H.AIJ_FILIAL = AD1.AD1_FILIAL
               AND H.AIJ_NROPOR = AD1.AD1_NROPOR
            LEFT JOIN SA1010 SA1
                ON SA1.A1_COD = AD1.AD1_CODCLI
               AND SA1.A1_LOJA = AD1.AD1_LOJCLI
               AND {where_sa1}
            LEFT JOIN SA3010 SA3
                ON SA3.A3_COD = AD1.AD1_VEND
               AND {where_sa3}
            WHERE {where_ad1}
              AND AD1.AD1_NROPOR = ?
              AND (L.AIJ_NROPOR IS NOT NULL OR S.AIJ_NROPOR IS NOT NULL)
            ORDER BY AD1.AD1_REVISA DESC
        """

        params = (
            *params_lmp,
            *params_sample,
            *params_hist,
            self.LISTING_KIND_LMP,
            self.LISTING_KIND_SAMPLE,
            *params_sa1,
            *params_sa3,
            *params_ad1,
        )
        return sql, params

    def _sql_products_lmp(
        self,
        requested_branch: str | None = None,
    ) -> Tuple[str, tuple]:
        cte_prod, params_prod = self._sql_produtos_lmp_cte(requested_branch=requested_branch)
        cte_pi, params_pi = self._sql_pi_por_referencia_ctes_from_produtos_lmp()
        where_sb1, params_sb1 = self._sql_filter_sb1_active("SB1")

        sql = f"""
            WITH
            {cte_prod},
            {cte_pi}
            SELECT
                SB1.B1_GRUPO AS group_code,
                SB1.B1_COD AS code,
                SB1.B1_DESC AS description,
                SB1.B1_TIPO AS type,
                ISNULL(PI.QTD_PI, 0) AS qtd_pi
            FROM ProdutosLMP P
            INNER JOIN SB1010 SB1
                ON SB1.B1_COD = P.ADJ_PROD
               AND {where_sb1}
            LEFT JOIN PI_COUNT_BY_PRODUCT PI
                ON PI.ADJ_FILIAL = P.ADJ_FILIAL
               AND PI.ADJ_NROPOR = P.ADJ_NROPOR
               AND PI.ADJ_REVISA = P.ADJ_REVISA
               AND PI.ADJ_PROD = P.ADJ_PROD
            WHERE P.ADJ_NROPOR = ?
            ORDER BY SB1.B1_COD
        """

        params = (*params_prod, *params_pi, *params_sb1)
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

    # =========================
    # PUBLIC METHODS
    # =========================
    def list_lmps(self, request: ListLMPRequest) -> List[LMP]:
        sql, params = self._sql_lmp_base_rows_query(
            request,
            include_qtd_pi=True,
        )

        with self as repo:
            rows = repo.execute_query(sql, params)
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

        count_sql, count_params = self._sql_lmp_base_rows_count_query(
            request,
            include_qtd_pi=True,
        )
        page_sql, page_params = self._sql_lmp_base_rows_paged_query(
            request,
            include_qtd_pi=True,
        )

        with self as repo:
            total_row = repo.execute_one(count_sql, count_params)
            total = int((total_row or {}).get("total") or 0)

            rows = repo.execute_query(page_sql, page_params)

        return Page(
            items=[LMP(**row) for row in rows],
            total=total,
            page=request.page or 1,
            page_size=request.page_size,
        )

    def get_lmp(self, request: GetLMPRequest) -> LMP:
        requested_branch = self._get_request_branch(request)

        sql_header, params_header = self._sql_header_lmp(requested_branch=requested_branch)
        sql_products, params_products = self._sql_products_lmp(requested_branch=requested_branch)
        sql_qtd_pi, params_qtd_pi = self._sql_qtd_pi_lmp_total(requested_branch=requested_branch)

        with self as repo:
            header_row = repo.execute_one(
                sql_header,
                (*params_header, request.sale_number),
            )

            if not header_row:
                raise ValueError(
                    f"LMP ou amostra não encontrada: {request.sale_number}"
                )

            product_rows = repo.execute_query(
                sql_products,
                (*params_products, request.sale_number),
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
        )

    def get_lmp_dashboard_summary(self, request: ListLMPRequest) -> list[dict]:
        sql, params = self._sql_lmp_summary_rows_query(
            request,
            include_qtd_pi=True,
        )

        with self as repo:
            rows = repo.execute_query(sql, params)

        return [
            {
                "branch": row.get("branch"),
                "sale_number": row.get("sale_number"),
                "start_date": row.get("start_date"),
                "end_date": row.get("end_date"),
                "engineering_status": row.get("engineering_status"),
                "engineering_total_minutes": int(row.get("engineering_total_minutes") or 0),
                "qtd_pi": int(row.get("qtd_pi") or 0),
            }
            for row in rows
        ]