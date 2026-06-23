from __future__ import annotations

from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.application.dto.lmp.list_lmp_request import (
    LISTING_KIND_LMP,
    LISTING_KIND_OTHER,
    LISTING_KIND_SAMPLE,
    ListLMPRequest,
)
from app.infrastructure.persistence.totvs.lmp_repositories.lmp_query_repository import (
    LMPQueryRepository,
)
from app.infrastructure.persistence.totvs.lmp_repositories.lmp_query_settings import (
    LMPQuerySettings,
)


def _repository() -> LMPQueryRepository:
    return LMPQueryRepository(
        settings=LMPQuerySettings(min_engineering_residence_minutes=30),
    )


def test_listing_anchor_marker_prioritizes_lmp_over_sample() -> None:
    repo = _repository()

    sql, params = repo._sql_listing_anchor_marker_cte(
        requested_branch=None,
        date_start="20260401",
        date_end="20260501",
    )

    assert "WHEN R.LISTING_KIND = ? THEN 2" in sql
    assert "WHEN R.LISTING_KIND = ? THEN 1" in sql
    assert sql.index("THEN 2") < sql.index("THEN 1")
    assert "AD1.AD1_REVISA = A.AIJ_REVISA" in sql
    assert params.count("LMP") >= 3
    assert params.count("AMOSTRA") >= 2
    assert sql.count("?") == len(params)


def test_header_lmp_uses_period_measurement_when_dates_provided() -> None:
    repo = _repository()
    request = GetLMPRequest(
        sale_number="003578",
        date_start="20260601",
        date_end="20260630",
    )

    sql, params = repo._sql_header_lmp(request)

    assert "GetLmpCandidateScope" in sql
    assert "EngenhariaMinutosPorRevisao" in sql
    assert "TEMPO_MINUTOS_AMOSTRA_ENG" in sql
    assert "THEN 'AMOSTRA'" in sql
    assert request.sale_number in params


def test_header_lmp_exposes_reference_and_measurement_revision() -> None:
    repo = _repository()
    request = GetLMPRequest(
        sale_number="003578",
        date_start="20260601",
        date_end="20260630",
        branch="01",
    )

    sql, _params = repo._sql_header_lmp(request)

    assert "AD1.AD1_REVISA AS reference_revision" in sql
    assert "MREV.ULTIMA_REVISA_MEDICAO AS measurement_revision" in sql
    assert "UltimaRevisaoMedicaoEngenharia MREV" in sql


def test_history_events_lmp_queries_aij010_for_single_ov() -> None:
    repo = _repository()

    sql, params = repo._sql_history_events_lmp(requested_branch="01")

    assert "FROM AIJ010 A" in sql
    assert "FROM AC1010 AC1" in sql
    assert "FROM AC2010 AC2" in sql
    assert "process_description" in sql
    assert "stage_description" in sql
    assert "reference_revision" not in sql
    assert "AD1.AD1_REVISA AS reference_revision" not in sql
    assert "A.AIJ_NROPOR = ?" in sql
    assert "PROXIMO_DTINIC_GLOBAL" in sql
    assert "duration_minutes" in sql
    assert "is_engineering" in sql
    assert "01" in params


def test_historico_uses_period_revision_measurement_when_listing() -> None:
    repo = _repository()

    sql, _params = repo._sql_historico_ov_cte(
        scope_cte_name="CandidateLMPs",
        requested_branch=None,
        date_start="20260601",
        date_end="20260608",
    )

    assert "EngenhariaMinutosPorRevisao" in sql
    assert "RevisoesElegiveisMedicao" in sql
    assert "MINUTOS_REVISAO DESC" in sql
    assert "SCOPE_A.AD1_NROPOR = A.AIJ_NROPOR" in sql
    assert "SCOPE_A.AD1_REVISA = A.AIJ_REVISA" not in sql


def test_eng_support_reference_uses_current_revision() -> None:
    repo = _repository()

    sql, _params = repo._sql_eng_support_ov_reference_cte(
        requested_branch=None,
        date_start="20260401",
        date_end="20260501",
    )

    assert "INNER JOIN AD1010 AD1" in sql
    assert "AD1.AD1_REVISA = A.AIJ_REVISA" in sql
    assert "A.AIJ_REVISA" in sql


def test_staged_batch_applies_minimum_engineering_residence_filter_only_for_lmp() -> None:
    repo = _repository()
    request = ListLMPRequest(date_start="20260401", date_end="20260501")

    final_select = repo._staged_final_select(include_qtd_pi=False, order_by=True)
    batch_sql, batch_params = repo._build_staged_batch(
        request,
        include_qtd_pi=False,
        final_select=final_select,
        final_params=repo._staged_residence_final_params(
            residence_filter_count=1,
            listing_kind_reclass_count=1,
        ),
    )

    assert f"'{LISTING_KIND_SAMPLE}'" in batch_sql
    assert f"'{LISTING_KIND_OTHER}'" in batch_sql
    assert "C.LISTING_KIND = 'LMP'" in batch_sql
    assert "C.HAS_SAMPLE_ANCHOR = 1" in batch_sql
    assert "ISNULL(H.TEMPO_TOTAL_MINUTOS_ENG, 0) >= ?" in batch_sql
    assert "TEMPO_MINUTOS_AMOSTRA_ENG" in batch_sql
    assert "THEN 'AMOSTRA'" in batch_sql
    assert "THEN 'OUTRO'" in batch_sql
    assert batch_params[-2:] == (30, 30)


def test_engineering_residence_filter_sql_allows_sample_and_other_without_minutes() -> None:
    repo = _repository()

    sql = repo._engineering_residence_filter_sql()

    assert f"'{LISTING_KIND_SAMPLE}'" in sql
    assert f"'{LISTING_KIND_OTHER}'" in sql
    assert "C.LISTING_KIND = 'LMP'" in sql
    assert "ISNULL(H.TEMPO_TOTAL_MINUTOS_ENG, 0) >= ?" in sql


def test_effective_listing_kind_skips_reclass_when_lmp_finalized() -> None:
    repo = _repository()

    sql = repo._effective_listing_kind_expr()

    assert "C.HAS_LMP_FINALIZED = 0" in sql
    assert sql.count("C.HAS_LMP_FINALIZED = 0") == 2


def test_candidate_lmps_exposes_has_lmp_finalized_from_finalized_anchor() -> None:
    repo = _repository()
    request = ListLMPRequest(date_start="20260601", date_end="20260630")

    candidate_sql, _candidate_params = repo._sql_candidate_lmps_cte(
        request,
        lmp_only=False,
    )

    assert "HAS_LMP_FINALIZED" in candidate_sql
    assert "LmpFinalizedAnchorChosen LF" in candidate_sql


def test_get_lmp_candidate_scope_exposes_has_lmp_finalized() -> None:
    repo = _repository()

    sql = repo._sql_get_lmp_candidate_scope_cte(where_ad1="AD1.D_E_L_E_T_ = ''")

    assert "HAS_LMP_FINALIZED" in sql
    assert "LmpFinalizedAnchorChosen LF" in sql


def test_listing_period_omits_anchor_marker_date_filter() -> None:
    repo = _repository()

    start, end = repo._listing_anchor_period_dates("20260501", "20260531")

    assert start is None
    assert end is None
    assert repo._has_listing_period_filter("20260501", "20260531")


def test_candidate_period_filter_or_first_engineering_arrival() -> None:
    repo = LMPQueryRepository(
        settings=LMPQuerySettings(period_inclusion_policy="anchor_or_first_eng"),
    )
    request = ListLMPRequest(date_start="20260501", date_end="20260531")

    where_sql, _params = repo._sql_candidate_period_where_clause(
        request,
        anchor_date_sql="L.ANCHOR_START_DATE",
    )

    assert "L.ANCHOR_START_DATE" in where_sql
    assert "F.FIRST_ENG_DATE" in where_sql
    assert " OR " in where_sql


def test_candidate_period_filter_anchor_in_period_default() -> None:
    repo = _repository()
    request = ListLMPRequest(date_start="20260501", date_end="20260531")

    where_sql, _params = repo._sql_candidate_period_where_clause(
        request,
        anchor_date_sql="L.ANCHOR_START_DATE",
    )

    assert where_sql.strip().startswith("L.ANCHOR_START_DATE")
    assert "F.FIRST_ENG_DATE" not in where_sql
    assert " OR " not in where_sql


def test_candidate_lmps_includes_first_engineering_arrival_cte() -> None:
    repo = LMPQueryRepository(
        settings=LMPQuerySettings(period_inclusion_policy="anchor_or_first_eng"),
    )
    request = ListLMPRequest(date_start="20260501", date_end="20260531")

    candidate_sql, _candidate_params = repo._sql_candidate_lmps_cte(
        request,
        lmp_only=False,
    )

    assert "OvFirstEngineeringArrival AS" in candidate_sql
    assert "L.ANCHOR_START_DATE AS LMP_START_DATE" in candidate_sql
    assert "COALESCE(F.FIRST_ENG_DATE, L.ANCHOR_START_DATE)" not in candidate_sql


def test_header_lmp_uses_listing_anchor_start_with_period() -> None:
    repo = _repository()
    request = GetLMPRequest(
        sale_number="003578",
        date_start="20260501",
        date_end="20260531",
    )

    sql, _params = repo._sql_header_lmp(request)

    assert "COALESCE(L.ANCHOR_START_DATE, R.ANCHOR_START_DATE) AS start_date" in sql
    assert "OvFirstEngineeringArrival AS" not in sql
    assert "F.FIRST_ENG_DATE" not in sql


def test_paged_batch_passes_residence_filter_for_count_and_rows() -> None:
    repo = _repository()
    request = ListLMPRequest(
        date_start="20260401",
        date_end="20260501",
        page=2,
        page_size=10,
    )

    count_select = repo._staged_count_select(include_qtd_pi=False)
    rows_select = repo._staged_final_select(include_qtd_pi=False, order_by=True)
    query_params = repo._staged_residence_final_params(
        residence_filter_count=1,
        listing_kind_reclass_count=1,
    )
    count_select, count_params = repo._apply_effective_listing_type_filter_to_select(
        request,
        count_select,
        query_params,
    )
    rows_select, rows_params = repo._apply_effective_listing_type_filter_to_select(
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
    _batch_sql, batch_params = repo._build_staged_batch(
        request,
        include_qtd_pi=False,
        final_select=combined_final,
        final_params=(
            *count_params,
            *rows_params,
            10,
            10,
        ),
    )

    assert batch_params[-6:] == (30, 30, 30, 30, 10, 10)


def test_listing_type_filter_uses_effective_kind_not_anchor() -> None:
    repo = _repository()
    request = ListLMPRequest(
        date_start="20260601",
        date_end="20260608",
        listing_type="LMP",
    )

    final_select = repo._staged_final_select(include_qtd_pi=False, order_by=True)
    residence_params = repo._staged_residence_final_params(
        residence_filter_count=1,
        listing_kind_reclass_count=1,
    )
    filtered_select, filtered_params = (
        repo._apply_effective_listing_type_filter_to_select(
            request,
            final_select,
            residence_params,
        )
    )

    assert "EFFECTIVE_LISTING_ROWS" in filtered_select
    assert "EFFECTIVE_LISTING_ROWS.listing_kind = ?" in filtered_select
    assert filtered_params[-1] == LISTING_KIND_LMP

    candidate_sql, _candidate_params = repo._sql_candidate_lmps_cte(
        request,
        lmp_only=False,
    )
    assert "EngSupportOvRef" in candidate_sql
    assert "AND L.LISTING_KIND = ?" not in candidate_sql


def test_dashboard_summary_batch_uses_lite_eng_resumo_without_order_by() -> None:
    repo = _repository()
    request = ListLMPRequest(date_start="20260401", date_end="20260501")

    final_select = repo._staged_final_select(
        include_qtd_pi=False,
        order_by=False,
        summary_only=True,
    )
    batch_sql, _batch_params = repo._build_staged_batch(
        request,
        include_qtd_pi=False,
        eng_resumo_lite=True,
        final_select=final_select,
        final_params=repo._staged_residence_final_params(
            residence_filter_count=1,
            listing_kind_reclass_count=1,
        ),
    )

    assert "C.LMP_START_DATE DESC" not in batch_sql
    assert "QTD_PASSAGENS_ENG" not in batch_sql
    assert "QTD_RETORNOU_ENG" not in batch_sql
    assert "TEMPO_TOTAL_MINUTOS_ENG" in batch_sql
    assert "TEMPO_MINUTOS_AMOSTRA_ENG" in batch_sql
    assert "ENGINEERING_STATUS" in batch_sql


def test_lmp_only_candidate_cte_skips_eng_support_and_other_union() -> None:
    repo = _repository()
    request = ListLMPRequest(
        date_start="20260401",
        date_end="20260501",
        listing_type="lmp",
    )

    candidate_sql, _candidate_params = repo._sql_candidate_lmps_cte(
        request,
        lmp_only=True,
    )

    assert "EngSupportOvRef" not in candidate_sql
    assert f"? AS LISTING_KIND,\n                    0 AS HAS_SAMPLE_ANCHOR" not in candidate_sql
    assert "CandidateLMPs AS" in candidate_sql


def test_staged_batch_uses_lmp_only_candidates_when_listing_type_is_lmp() -> None:
    repo = _repository()
    request = ListLMPRequest(
        date_start="20260401",
        date_end="20260501",
        listing_type="lmp",
    )

    final_select = repo._staged_final_select(
        include_qtd_pi=False,
        order_by=False,
        summary_only=True,
    )
    batch_sql, _batch_params = repo._build_staged_batch(
        request,
        include_qtd_pi=False,
        eng_resumo_lite=True,
        final_select=final_select,
        final_params=repo._staged_residence_final_params(
            residence_filter_count=1,
            listing_kind_reclass_count=1,
        ),
    )

    assert "EngSupportOvRef" not in batch_sql


def test_products_lmp_resolves_pa_by_previous_code() -> None:
    repo = _repository()

    sql, _params = repo._sql_products_lmp()

    assert "B1_CODANT" in sql
    assert "9026%" in sql
    assert "OUTER APPLY" in sql
    assert "ResolvedProducts AS" in sql
    assert "ProductsForDisplay AS" in sql
    assert "UNION ALL" in sql
    assert "SB0.B1_COD = R.ADJ_PROD" in sql
    assert "GROUP BY" in sql
    assert "ORDER BY" in sql.split("GROUP BY")[-1]
    assert "WHEN PU.code LIKE '9026%' THEN 0" in sql


def test_full_staged_batch_keeps_eng_passagem_counts() -> None:
    repo = _repository()
    request = ListLMPRequest(date_start="20260401", date_end="20260501")

    final_select = repo._staged_final_select(include_qtd_pi=False, order_by=True)
    batch_sql, _batch_params = repo._build_staged_batch(
        request,
        include_qtd_pi=False,
        eng_resumo_lite=False,
        final_select=final_select,
        final_params=repo._staged_residence_final_params(
            residence_filter_count=1,
            listing_kind_reclass_count=1,
        ),
    )

    assert "QTD_PASSAGENS_ENG" in batch_sql
    assert "QTD_RETORNOU_ENG" in batch_sql
    assert "ORDER BY" in batch_sql


def test_candidate_period_filter_homolog_in_period_uses_lf_only() -> None:
    repo = LMPQueryRepository(
        settings=LMPQuerySettings(
            period_inclusion_policy="homolog_in_period",
        ),
    )
    request = ListLMPRequest(date_start="20260501", date_end="20260531")

    where_sql, _params = repo._sql_candidate_period_where_clause(
        request,
        anchor_date_sql="L.ANCHOR_START_DATE",
        homolog_date_sql="LF.ANCHOR_START_DATE",
    )

    assert "LF.ANCHOR_START_DATE" in where_sql
    assert "FIRST_ENG" not in where_sql
    assert " OR " not in where_sql


def test_candidate_period_other_branch_homolog_policy_uses_eng_support_date() -> None:
    repo = LMPQueryRepository(
        settings=LMPQuerySettings(period_inclusion_policy="homolog_in_period"),
    )
    request = ListLMPRequest(date_start="20260501", date_end="20260531")

    where_sql, _params = repo._sql_candidate_period_where_clause(
        request,
        anchor_date_sql="R.ANCHOR_START_DATE",
        homolog_date_sql="R.ANCHOR_START_DATE",
    )

    assert "R.ANCHOR_START_DATE" in where_sql
    assert "LF.ANCHOR_START_DATE" not in where_sql


def test_candidate_lmps_skips_first_eng_cte_when_anchor_in_period_default() -> None:
    repo = _repository()
    request = ListLMPRequest(date_start="20260501", date_end="20260531")

    candidate_sql, _params = repo._sql_candidate_lmps_cte(request, lmp_only=False)

    assert "OvFirstEngineeringArrival AS" not in candidate_sql


def test_candidate_lmps_skips_first_eng_cte_when_homolog_policy() -> None:
    repo = LMPQueryRepository(
        settings=LMPQuerySettings(
            period_inclusion_policy="homolog_in_period",
        ),
    )
    request = ListLMPRequest(date_start="20260501", date_end="20260531")

    candidate_sql, _params = repo._sql_candidate_lmps_cte(request, lmp_only=False)

    assert "OvFirstEngineeringArrival AS" not in candidate_sql


def test_strict_residence_after_homolog_reclassifies_finalized_lmp() -> None:
    repo = LMPQueryRepository(
        settings=LMPQuerySettings(
            strict_residence_after_homolog=True,
            min_engineering_residence_minutes=30,
        ),
    )

    sql = repo._effective_listing_kind_expr()

    assert "C.HAS_LMP_FINALIZED = 1" in sql
    assert "THEN 'OUTRO'" in sql
    assert sql.index("HAS_LMP_FINALIZED = 1") < sql.index("HAS_LMP_FINALIZED = 0")


def test_strict_residence_filter_drops_sample_bypass() -> None:
    repo = LMPQueryRepository(
        settings=LMPQuerySettings(strict_residence_after_homolog=True),
    )

    sql = repo._engineering_residence_filter_sql()

    assert "HAS_SAMPLE_ANCHOR" not in sql
    assert "TEMPO_TOTAL_MINUTOS_ENG" in sql


def test_dashboard_summary_select_exposes_revision_fields() -> None:
    repo = _repository()

    sql = repo._staged_final_select(include_qtd_pi=True, order_by=False, summary_only=True)

    assert "homolog_revision" in sql
    assert "measurement_revision" in sql
    assert "homolog_date" in sql
    assert "cycle_index" in sql
