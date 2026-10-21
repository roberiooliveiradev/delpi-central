"""Port — provider externo de consulta de endereço por CEP."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.domain.addresses.postal_address import PostalAddressResult


@runtime_checkable
class PostalAddressProviderPort(Protocol):
    """Cada provider resolve um CEP de 8 dígitos ou prova inexistência.

    Contrato:
    - retorna ``PostalAddressResult`` quando o provider encontra o CEP;
    - retorna ``None`` somente quando o provider respondeu e comprovou
      que o CEP não existe na sua base;
    - levanta ``PostalAddressProviderError`` para falha técnica
      (timeout, rede, HTTP inesperado, payload inválido) — nunca para
      not-found.
    """

    @property
    def name(self) -> str:
        """Identificador estável do provider (ex.: ``viacep``)."""
        ...

    def lookup(self, postal_code: str) -> PostalAddressResult | None:
        ...
