"""Normaliza datas de query para o formato do Portal RH (DD-MM-YYYY)."""


def normalize_portal_rh_date(value: str | None) -> str | None:
    if value is None:
        return None

    trimmed = value.strip()
    if not trimmed:
        return None

    # HTML / ISO: YYYY-MM-DD
    if (
        len(trimmed) == 10
        and trimmed[4] == "-"
        and trimmed[7] == "-"
    ):
        year, month, day = trimmed.split("-")
        if len(year) == 4 and len(month) == 2 and len(day) == 2:
            return f"{day}-{month}-{year}"

    return trimmed
