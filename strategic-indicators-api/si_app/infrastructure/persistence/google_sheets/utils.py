from datetime import datetime, date, timedelta
from typing import List, Optional


class Utils:
    
    def __init__(self):
        pass

    def validate_date_range(
        self,
        start_date_str: Optional[str],
        end_date_str: Optional[str],
    ) -> None:
        start_date = self.parse_date(start_date_str) if start_date_str else None
        end_date = self.parse_date(end_date_str) if end_date_str else None

        if start_date_str and start_date is None:
            raise ValueError("start_date inválida. Use formatos como YYYY-MM-DD ou DD/MM/YYYY.")

        if end_date_str and end_date is None:
            raise ValueError("end_date inválida. Use formatos como YYYY-MM-DD ou DD/MM/YYYY.")

        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date não pode ser maior que end_date.")

    def parse_date(self, value: Optional[str]) -> Optional[date]:
        if value is None:
            return None

        raw = str(value).strip()
        if not raw:
            return None

        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue

        return None
    
    def first_non_empty(self, row: dict, aliases: list[str]) -> Optional[str]:
        for alias in aliases:
            value = row.get(alias)
            if value is not None and str(value).strip() != "":
                return str(value).strip()
        return None

    def to_float(self, value) -> Optional[float]:
        if value is None or str(value).strip() == "":
            return None

        raw = str(value).strip()
        raw = raw.replace("R$", "").replace("%", "").replace(" ", "")

        if raw in {"-", "—"}:
            return None

        if "," in raw and "." in raw:
            raw = raw.replace(".", "").replace(",", ".")
        elif "," in raw:
            raw = raw.replace(",", ".")

        try:
            return float(raw)
        except ValueError:
            return None

    def empty_to_none(self, value):
        if value is None:
            return None

        value = str(value).strip()
        return value or None