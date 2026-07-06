from app.infrastructure.persistence.totvs.retrabalho.retrabalho_sql import (
    RETRABALHO_HORAS_IMPRODUTIVAS_VIEW,
    build_resumo_query,
)


def test_resumo_query_uses_view_with_nolock_and_branch_filter() -> None:
    query, params = build_resumo_query(
        start_date="2025-07-06",
        end_date="2026-07-06",
        branch="01",
    )

    assert RETRABALHO_HORAS_IMPRODUTIVAS_VIEW in query
    assert "WITH (NOLOCK)" in query
    assert "DATA_REFERENCIA >= ?" in query
    assert "LTRIM(RTRIM(FILIAL)) = ?" in query
    assert "LTRIM(RTRIM(MOTIVO)) = ?" in query
    assert params == ("2025-07-06", "2026-07-06", "01", "RT")
