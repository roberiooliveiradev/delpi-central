"""Normaliza datas de query dos dashboards para o formato da Strategic Indicators API (DD-MM-YYYY)."""


def normalize_si_period_date(value: str | None) -> str | None:
    if value is None:
        return None

    trimmed = value.strip()
    if not trimmed:
        return None

    # HTML / ISO: YYYY-MM-DD
    if len(trimmed) == 10 and trimmed[4] == "-" and trimmed[7] == "-":
        year, month, day = trimmed.split("-")
        if len(year) == 4 and len(month) == 2 and len(day) == 2:
            return f"{day}-{month}-{year}"

    return trimmed
