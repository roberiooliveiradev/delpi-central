"""Normaliza datas e filial de query dos dashboards para a Strategic Indicators API."""


def normalize_si_branch(branch: str | None) -> str | None:
    if branch is None:
        return None

    trimmed = branch.strip()
    if not trimmed:
        return None

    # TV/OpenAPI usam all|Todas = consolidado. SI resolve meta consolidada com
    # branch vazio/None — o literal "all" não casa com goal_scope_branch ''|01|02
    # e a Meta (comparable_goal) some do Resumo Transforma Mais / hubs.
    if trimmed.lower() in {"all", "todas", "todos"}:
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

    # Compacto TOTVS/legado: YYYYMMDD (ex.: /lmps/dashboard/summary).
    # Sem esta conversão o valor ia cru à SI, que só aceita DD-MM-YYYY ou
    # YYYY-MM-DD — resolve_period falhava e as metas sumiam em silêncio.
    if len(trimmed) == 8 and trimmed.isdigit():
        year, month, day = trimmed[:4], trimmed[4:6], trimmed[6:8]
        if "01" <= month <= "12" and "01" <= day <= "31":
            return f"{day}-{month}-{year}"

    return trimmed
