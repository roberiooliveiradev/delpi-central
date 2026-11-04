"""Request tipado — lookup SB1 por identidade exata em lote."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sb1IdentityLookupItem:
    """Par opcional código interno / referência do cliente."""

    client_key: str
    product_code: str | None
    customer_reference: str | None


@dataclass(frozen=True)
class Sb1IdentityLookupRequest:
    """Escopo declarado (filial) + pares a resolver. Sem efeitos colaterais."""

    branch: str
    items: tuple[Sb1IdentityLookupItem, ...]
