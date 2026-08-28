"""Chave da OP Protheus (C2_OP / H8_OP) e identificadores de conjunto.

Espelha ``api-delpi`` ``protheus_production_orders``:
C2_OP = C2_NUM (6) + C2_ITEM (2) + C2_SEQUEN (3) = 11 posições.

Pacote (mãe + filhas da mesma estrutura) = C2_NUM + C2_ITEM (8 primeiros
dígitos). ``SEQUEN`` 001 é a mãe; 002+ são intermediários do mesmo pacote.

Agrupar só por C2_NUM (6) mistura itens distintos do mesmo número — ver
``padroes-totvs/ordem-producao-chave.md``.
"""

from __future__ import annotations

ORDER_NUMBER_LENGTH = 6
ORDER_ITEM_LENGTH = 2
ORDER_SEQUENCE_LENGTH = 3
ORDER_KEY_LENGTH = ORDER_NUMBER_LENGTH + ORDER_ITEM_LENGTH + ORDER_SEQUENCE_LENGTH
PACKAGE_KEY_LENGTH = ORDER_NUMBER_LENGTH + ORDER_ITEM_LENGTH


def normalize_order_code(value: str | None) -> str:
    return str(value or "").strip().upper()


def conjunto_key_from_order(production_order: str | None) -> str | None:
    """Extrai o C2_NUM (6 primeiros caracteres) — uso legado (carga máquina)."""
    code = normalize_order_code(production_order)
    if len(code) < ORDER_NUMBER_LENGTH:
        return None
    return code[:ORDER_NUMBER_LENGTH]


def package_key_from_order(production_order: str | None) -> str | None:
    """Extrai C2_NUM+C2_ITEM (8 primeiros) — pacote mãe + intermediários."""
    code = normalize_order_code(production_order)
    if len(code) < PACKAGE_KEY_LENGTH:
        return None
    return code[:PACKAGE_KEY_LENGTH]


def order_belongs_to_conjunto(production_order: str | None, conjunto_key: str | None) -> bool:
    """True se a OP compartilha o C2_NUM (6) — legado."""
    order = normalize_order_code(production_order)
    key = normalize_order_code(conjunto_key)
    if not order or len(key) != ORDER_NUMBER_LENGTH:
        return False
    return order.startswith(key)


def order_belongs_to_package(production_order: str | None, package_key: str | None) -> bool:
    """True se a OP pertence ao pacote (mesmo NUM+ITEM de 8 posições)."""
    order = normalize_order_code(production_order)
    key = normalize_order_code(package_key)
    if not order or len(key) != PACKAGE_KEY_LENGTH:
        return False
    return order.startswith(key)
