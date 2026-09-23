"""Normalização de listas de código de produto Protheus (``B1_COD`` / ``B2_COD``)."""

from __future__ import annotations

from typing import Sequence

# Teto para proteger o limite de parâmetros do SQL Server.
MAX_PRODUCT_CODES = 2000
MAX_PRODUCT_CODE_LENGTH = 20


def normalize_product_codes(
    value: str | Sequence[str] | None,
) -> tuple[str, ...] | None:
    """Normaliza códigos de produto vindos de query repetível ou CSV.

    ``None`` significa **sem filtro**. Uma tupla vazia significa **filtro
    explícito que não casa nada**: quem informou uma lista e recebeu tudo de
    volta calcularia cobertura de estoque sobre produtos que não pediu.
    """
    if value is None:
        return None

    if isinstance(value, str):
        raw_parts: list[str] = value.split(",")
    elif isinstance(value, (list, tuple)):
        raw_parts = [part for item in value for part in str(item or "").split(",")]
    else:
        return None

    codes: list[str] = []
    seen: set[str] = set()

    for part in raw_parts:
        code = str(part or "").strip()
        if not code or len(code) > MAX_PRODUCT_CODE_LENGTH or code in seen:
            continue
        seen.add(code)
        codes.append(code)
        if len(codes) >= MAX_PRODUCT_CODES:
            break

    return tuple(codes)


def require_product_codes(value: Sequence[str] | None) -> tuple[str, ...]:
    """Lista de códigos para rotas em lote (pode ser vazia).

    Diferente de ``normalize_product_codes`` (filtro opcional de query que
    trunca), ultrapassar o teto aqui é erro — quem chama um batch com milhares
    de códigos precisa fatiar, não perder itens em silêncio.
    """
    if value is None:
        return ()

    if isinstance(value, str):
        raw_parts: list[str] = value.split(",")
    elif isinstance(value, (list, tuple)):
        raw_parts = [part for item in value for part in str(item or "").split(",")]
    else:
        return ()

    codes: list[str] = []
    seen: set[str] = set()
    for part in raw_parts:
        code = str(part or "").strip()
        if not code or len(code) > MAX_PRODUCT_CODE_LENGTH or code in seen:
            continue
        seen.add(code)
        codes.append(code)

    if len(codes) > MAX_PRODUCT_CODES:
        raise ValueError(
            "product_codes excede o limite de "
            f"{MAX_PRODUCT_CODES} códigos por requisição."
        )
    return tuple(codes)
