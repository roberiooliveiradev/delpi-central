from app.domain.services.quality.nonconformity_query_filter_service import (
    match_nonconformity_status_codes,
)
from app.infrastructure.persistence.totvs.nonconformity_repositories.nonconformity_query_filters import (
    apply_nonconformity_text_filters,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def test_match_nonconformity_status_codes_by_label_fragment() -> None:
    assert match_nonconformity_status_codes("procede") == ["3"]
    assert match_nonconformity_status_codes("análise") == ["2"]


def test_match_nonconformity_status_codes_by_code() -> None:
    assert match_nonconformity_status_codes("4") == ["4"]


def test_apply_nonconformity_text_filters_uses_like_for_item() -> None:
    qb = QueryBuilder()
    apply_nonconformity_text_filters(
        qb,
        status=None,
        item_code="9048",
        description=None,
    )
    where, params = qb.build()

    assert "QI2_ITEM LIKE ?" in where
    assert params == ["%9048%"]


def test_apply_nonconformity_text_filters_uses_like_for_description() -> None:
    qb = QueryBuilder()
    apply_nonconformity_text_filters(
        qb,
        status=None,
        item_code=None,
        description="cabO",
    )
    where, params = qb.build()

    assert "LOWER(QI2_DESCR) LIKE ?" in where
    assert params == ["%cabo%"]
