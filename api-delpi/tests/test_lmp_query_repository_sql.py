from __future__ import annotations

from app.application.dto.lmp.list_lmp_request import (
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
    assert "THEN 'AMOSTRA'" in batch_sql
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
            *repo._staged_residence_final_params(
                residence_filter_count=2,
                listing_kind_reclass_count=1,
            ),
            10,
            10,
        ),
    )

    assert batch_params[-5:] == (30, 30, 30, 10, 10)
