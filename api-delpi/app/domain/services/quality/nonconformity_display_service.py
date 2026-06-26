"""Formatação de exibição de registros QI2 (não conformidade / PPM)."""

# Rótulos alinhados ao combobox SX3 (QI2_TIPO / QI2_STATUS) do Protheus.
_NONCONFORMITY_TYPE_LABELS: dict[str, str] = {
    "1": "Interna",
    "2": "Cliente",
    "3": "Fornecedor",
}

_NONCONFORMITY_STATUS_LABELS: dict[str, str] = {
    "1": "Registrada",
    "2": "Em análise",
    "3": "Procede",
    "4": "Não procede",
    "5": "Cancelada",
}


def _normalize_code(value: object | None) -> str:
    return str(value or "").strip()


def resolve_nonconformity_type_label(type_code: object | None) -> str | None:
    code = _normalize_code(type_code)
    if not code:
        return None
    return _NONCONFORMITY_TYPE_LABELS.get(code, f"Tipo {code}")


def resolve_nonconformity_status_label(status_code: object | None) -> str | None:
    code = _normalize_code(status_code)
    if not code:
        return None
    return _NONCONFORMITY_STATUS_LABELS.get(code, f"Situação {code}")


def format_nonconformity_code(fnc: str | None) -> str | None:
    """Converte QI2_FNC (ex.: 000000002292026) para o padrão TOTVS (ex.: 229/2026)."""
    if fnc is None:
        return None

    raw = str(fnc).strip()
    if not raw:
        return None

    if len(raw) < 5:
        return raw

    year = raw[-4:]
    if not year.isdigit():
        return raw

    sequence = raw[:-4].lstrip("0") or "0"
    if not sequence.isdigit():
        return raw

    return f"{int(sequence)}/{year}"


def normalize_optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_memo_text(value: object | None) -> str | None:
    text = normalize_optional_text(value)
    if not text:
        return None
    return (
        text.replace("\\13\\10", "\n")
        .replace("\\13", "\n")
        .replace("\\10", "\n")
        .strip()
        or None
    )
