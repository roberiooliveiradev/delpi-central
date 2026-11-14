"""Tradução das letras do Protheus para o vocabulário da skill, antes do motor."""

from __future__ import annotations

_YES_NO = {"S": "Sim", "N": "Nao", "SIM": "Sim", "NAO": "Nao", "Sim": "Sim", "Nao": "Nao"}
_BOOK = {"T": "Tributado", "I": "Isento", "O": "Outros", "N": "N", "Tributado": "Tributado", "Isento": "Isento", "Outros": "Outros"}

FIELD_CODES = {
    "Vlr Total": "total",
    "Vlr Mercadorias": "goods",
    "ICMS ST": "st",
    "Desconto": "discount",
    "Série": "series",
    "ICMS": "icms",
    "Base ICMS": "base",
    "IPI": "ipi",
    "pCredSN (%)": "simple_rate",
    "Vlr Item": "amount",
    "CFOP": "cfop",
    "Tomador": "taker",
    "Alíq. ICMS": "rate",
    "CST": "cst",
    "Chave": "key",
    "Espécie": "species",
    "Número": "number",
    "CNPJ": "supplier",
    "Origem": "origin",
    "CST (origem)": "origin",
    "Frete": "freight",
    "Despesa": "expense",
    "Seguro": "insurance",
    "ICMS livro": "book_icms",
}

FIELD_LABELS = {code: label for label, code in FIELD_CODES.items() if label != "CST (origem)"}


def yes_no(value: str) -> str:
    text = str(value or "").strip()
    return _YES_NO.get(text, text)


def book_word(value: str) -> str:
    text = str(value or "").strip()
    return _BOOK.get(text, text)


def field_code(label: str) -> str:
    return FIELD_CODES.get(label, "field")


def field_label(code: str, stable_key: str = "") -> str:
    """Rótulo de leitura. A origem da mercadoria permanece «CST (origem)» na chave estável."""
    if "CST (origem)" in (stable_key or ""):
        return "CST (origem)"
    return FIELD_LABELS.get(code, code)


def stored_field(label: str) -> str:
    return field_code(label)


def stable_occurrence_key(
    *,
    branch: str,
    access_key: str,
    rule_id: str,
    field: str,
    item: str = "",
    number: str = "",
    series: str = "",
    supplier: str = "",
    store: str = "",
) -> str:
    # «CST (origem)» continua literal na chave: o status já gravado usa esse texto.
    code = field if field == "CST (origem)" else (field_code(field) if field in FIELD_CODES else field)
    item_part = item or ""
    key = "".join(ch for ch in (access_key or "") if ch.isdigit())
    if len(key) == 44:
        return f"{branch}|{key}|{rule_id}|{code}|{item_part}"
    return f"{branch}|doc:{number}|{series}|{supplier}|{store}|{rule_id}|{code}|{item_part}"
