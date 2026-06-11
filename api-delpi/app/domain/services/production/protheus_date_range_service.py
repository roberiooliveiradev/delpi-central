from datetime import datetime, timedelta

from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class ProtheusDateRangeService:
    @staticmethod
    def _convert(value: str) -> str:
        converted = QueryBuilder().convert_date_to_protheus(value)
        if not converted:
            raise ValueError("Data inválida. Use YYYY-MM-DD ou DD/MM/YYYY.")
        return converted

    @classmethod
    def resolve_reference_date(cls, value: str | None) -> str:
        if value:
            return cls._convert(value)
        return datetime.now().strftime("%Y%m%d")

    @classmethod
    def default_month_period(cls) -> tuple[str, str]:
        now = datetime.now()
        start = now.replace(day=1).strftime("%Y%m%d")
        if now.month == 12:
            end_exclusive = now.replace(
                year=now.year + 1,
                month=1,
                day=1,
            ).strftime("%Y%m%d")
        else:
            end_exclusive = now.replace(month=now.month + 1, day=1).strftime("%Y%m%d")
        return start, end_exclusive

    @classmethod
    def resolve_closed_open_period(
        cls,
        *,
        date_start: str | None = None,
        date_end: str | None = None,
    ) -> tuple[str, str]:
        if not date_start and not date_end:
            return cls.default_month_period()

        default_start, _ = cls.default_month_period()
        start = cls._convert(date_start) if date_start else default_start

        if date_end:
            end_base = cls._convert(date_end)
            parsed = datetime.strptime(end_base, "%Y%m%d")
            end_exclusive = (parsed + timedelta(days=1)).strftime("%Y%m%d")
        else:
            parsed = datetime.strptime(start, "%Y%m%d")
            if parsed.month == 12:
                end_exclusive = parsed.replace(
                    year=parsed.year + 1,
                    month=1,
                    day=1,
                ).strftime("%Y%m%d")
            else:
                end_exclusive = parsed.replace(
                    month=parsed.month + 1,
                    day=1,
                ).strftime("%Y%m%d")

        return start, end_exclusive

    @classmethod
    def exclusive_end_from_start(cls, start: str) -> str:
        parsed = datetime.strptime(start, "%Y%m%d")
        return (parsed + timedelta(days=1)).strftime("%Y%m%d")
