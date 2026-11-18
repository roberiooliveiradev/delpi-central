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

# Campos em que a diferença numérica faz sentido. Código/identificação fica null.
NUMERIC_FIELD_CODES = {
    "total", "goods", "st", "discount", "icms", "base", "ipi", "simple_rate",
    "amount", "rate", "freight", "expense", "insurance", "book_icms",
}
CODE_FIELD_CODES = {
    "series", "cfop", "taker", "cst", "key", "species", "number", "supplier", "origin",
}


def difference_allowed(field: str) -> bool:
    """True só para valor monetário, quantidade ou percentual."""
    code = field_code(field) if field in FIELD_CODES else field
    if code in CODE_FIELD_CODES or field in {"CST", "CST (origem)", "Origem", "CFOP", "NCM", "Chave", "Série", "Espécie", "CNPJ", "UF", "Tomador", "Número"}:
        return False
    if code in NUMERIC_FIELD_CODES:
        return True
    # Campo desconhecido: não inventar diferença numérica.
    return False


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


def stable_key_v2_from_v1(stable_key: str, cause_of) -> str | None:
    """Deriva a chave v2 de uma chave v1 de status; None se já for v2 ou ilegível.

    `cause_of` é o mapa rule_id → cause_id do domínio (a migração injeta a
    função para manter este módulo livre de dependência de domínio).
    """
    parts = str(stable_key or "").split("|")
    if not parts or "cause:" in stable_key:
        return None
    branch = parts[0]
    if len(parts) >= 3 and parts[1].isdigit() and len(parts[1]) == 44:
        return f"{branch}|{parts[1]}|cause:{cause_of(parts[2])}"
    if len(parts) >= 6 and parts[1].startswith("doc:"):
        return f"{branch}|{'|'.join(parts[1:5])}|cause:{cause_of(parts[5])}"
    return None


def stable_occurrence_key_v2(
    *,
    branch: str,
    access_key: str,
    cause_id: str,
    number: str = "",
    series: str = "",
    supplier: str = "",
    store: str = "",
) -> str:
    """Chave v2 (FA-4/FA-5): filial + identidade da nota + causa."""
    key = "".join(ch for ch in (access_key or "") if ch.isdigit())
    if len(key) == 44:
        return f"{branch}|{key}|cause:{cause_id}"
    return f"{branch}|doc:{number}|{series}|{supplier}|{store}|cause:{cause_id}"
