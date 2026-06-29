from app.infrastructure.persistence.totvs.production_repositories.on_time_delivery_repository import (
    OnTimeDeliveryRepository,
)
from app.infrastructure.persistence.totvs.production_repositories.production_pa_sql_filters import (
    SC2_MOTHER_OP_SEQUENCE_SQL,
    SC2_PA_PRODUCT_CODE_PREFIXES,
    SC2_PA_PRODUCT_CODE_PREFIX_SQL,
)


def test_otd_mother_op_sequence_filter_constant() -> None:
    assert "C2_SEQUEN" in SC2_MOTHER_OP_SEQUENCE_SQL
    assert "'001'" in SC2_MOTHER_OP_SEQUENCE_SQL


def test_otd_pa_product_prefixes_include_business_codes() -> None:
    assert SC2_PA_PRODUCT_CODE_PREFIXES == ("9026", "8000", "8001")
    for prefix in SC2_PA_PRODUCT_CODE_PREFIXES:
        assert f"LIKE '{prefix}%'" in SC2_PA_PRODUCT_CODE_PREFIX_SQL


def test_otd_base_where_includes_mother_op_and_pa_prefix_filters() -> None:
    repository = OnTimeDeliveryRepository()
    where_clause, _params = repository._build_base_where(
        branch="01",
        start_date="2026-06-01",
        end_date="2026-06-30",
    )

    assert SC2_MOTHER_OP_SEQUENCE_SQL in where_clause
    assert SC2_PA_PRODUCT_CODE_PREFIX_SQL in where_clause
