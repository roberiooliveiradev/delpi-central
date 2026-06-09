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
