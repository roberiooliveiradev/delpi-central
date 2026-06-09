from datetime import datetime, timedelta

from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def to_protheus_date(value: str | None) -> str | None:
    return QueryBuilder().convert_date_to_protheus(value)


def exclusive_end_date(value: str | None) -> str | None:
    protheus_date = to_protheus_date(value)
    if not protheus_date:
        return None
    parsed = datetime.strptime(protheus_date, "%Y%m%d")
    return (parsed + timedelta(days=1)).strftime("%Y%m%d")
