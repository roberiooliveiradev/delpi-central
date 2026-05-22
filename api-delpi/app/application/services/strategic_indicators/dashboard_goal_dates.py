"""Normaliza datas e filial de query dos dashboards para a Strategic Indicators API."""


def normalize_si_branch(branch: str | None) -> str | None:
    if branch is None:
        return None

    trimmed = branch.strip()
    if not trimmed:
        return None

    if trimmed.isdigit() and len(trimmed) <= 2:
        return trimmed.zfill(2)

    return trimmed


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
