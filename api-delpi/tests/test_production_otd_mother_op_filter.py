from app.infrastructure.persistence.totvs.production_repositories.on_time_delivery_repository import (
    OnTimeDeliveryRepository,
)
from app.infrastructure.persistence.totvs.production_repositories.production_otd_sql_filters import (
    sc2_otd_on_time_sql,
    sc2_otd_status_case_sql,
    sc2_otd_universe_sql,
)
from app.infrastructure.persistence.totvs.production_repositories.production_pa_sql_filters import (
    SC2_MOTHER_OP_SEQUENCE_SQL,
    SC2_PA_PRODUCT_CODE_PREFIX_SQL,
)


def test_otd_mother_op_sequence_filter_constant() -> None:
    assert "C2_SEQUEN" in SC2_MOTHER_OP_SEQUENCE_SQL
    assert "'001'" in SC2_MOTHER_OP_SEQUENCE_SQL


def test_otd_base_where_includes_only_mother_op_filter() -> None:
    repository = OnTimeDeliveryRepository()
    where_clause, _params = repository._build_base_where(
        branch="01",
        start_date="2026-06-01",
        end_date="2026-06-30",
    )

    assert SC2_MOTHER_OP_SEQUENCE_SQL in where_clause
    assert SC2_PA_PRODUCT_CODE_PREFIX_SQL not in where_clause
    assert "B1_TIPO" not in where_clause


def test_otd_universe_includes_open_overdue_ops() -> None:
    """OP em andamento com due vencido entra no denominador como atraso."""
    repository = OnTimeDeliveryRepository()
    where_clause, _params = repository._build_base_where(
        branch="01",
        start_date="2026-06-01",
        end_date="2026-06-30",
    )

    assert sc2_otd_universe_sql("OP") in where_clause
    assert "GETDATE()" in where_clause
    assert "LTRIM(RTRIM(OP.C2_DATRF)) = ''" in where_clause
    # Não exige mais só finalizadas: remove o filtro exclusivo antigo.
    assert "OP.C2_DATRF IS NOT NULL" not in where_clause.split(sc2_otd_universe_sql("OP"))[0]


def test_otd_on_time_requires_filled_finish_date() -> None:
    expr = sc2_otd_on_time_sql("")
    assert "C2_DATRF IS NOT NULL" in expr
    assert "LTRIM(RTRIM(C2_DATRF)) <> ''" in expr
    assert "<=" in expr


def test_otd_status_marks_open_overdue_as_late() -> None:
    case_sql = sc2_otd_status_case_sql("OP")
    assert "THEN 'late'" in case_sql
    assert "THEN 'open'" in case_sql
    assert "GETDATE()" in case_sql
    # Aberta + due < hoje → late antes do ramo open
    late_idx = case_sql.index("THEN 'late'")
    open_idx = case_sql.index("THEN 'open'")
    assert late_idx < open_idx
