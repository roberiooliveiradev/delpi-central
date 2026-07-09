from app.domain.services.quality.nonconformity_query_filter_service import (
    match_nonconformity_status_codes,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def apply_nonconformity_text_filters(
    qb: QueryBuilder,
    *,
    status: str | None,
    item_code: str | None,
    description: str | None,
) -> None:
    if item_code and str(item_code).strip():
        qb.like("QI2_ITEM", str(item_code).strip(), case_insensitive=False)

    if description and str(description).strip():
        qb.like("QI2_DESCR", str(description).strip(), case_insensitive=True)

    if not status or not str(status).strip():
        return

    status_term = str(status).strip()
    matched_codes = match_nonconformity_status_codes(status_term)
    if matched_codes:
        qb.in_list("QI2_STATUS", matched_codes)
        return

    qb.like("QI2_STATUS", status_term, case_insensitive=False)
