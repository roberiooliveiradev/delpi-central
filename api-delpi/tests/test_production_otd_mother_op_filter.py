from app.infrastructure.persistence.totvs.production_repositories.on_time_delivery_repository import (
    OnTimeDeliveryRepository,
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
