"""LookupPostalAddressUseCase — consulta estruturada de CEP com fallback.

Política contratada da cadeia (INT-CEP-01, preserva o comportamento
homologado no Portal Suprimentos):

- provider que encontra o CEP → retorna imediatamente (ordem: ViaCEP →
  BrasilAPI);
- not-found comprovado em um provider → consulta o próximo (coberturas
  distintas — ex.: 89120000/Timbó não existe no ViaCEP mas existe na
  BrasilAPI open-cep);
- falha técnica de um provider → consulta o próximo;
- erro só é propagado quando algum provider falhou e nenhum encontrou —
  indisponibilidade nunca vira ``found=False``;
- ``found=False`` somente quando todos responderam definitivamente que o
  CEP não existe.
"""

from __future__ import annotations

from typing import Sequence

from app.domain.addresses.postal_address import (
    PostalAddressProviderError,
    PostalAddressResult,
    normalize_postal_code,
)
from app.domain.ports.addresses.postal_address_provider_port import (
    PostalAddressProviderPort,
)


class LookupPostalAddressUseCase:
    def __init__(self, providers: Sequence[PostalAddressProviderPort]) -> None:
        if not providers:
            raise ValueError("at least one postal address provider is required")
        self._providers = tuple(providers)

    def execute(self, postal_code: str) -> PostalAddressResult:
        digits = normalize_postal_code(postal_code)
        last_error: PostalAddressProviderError | None = None
        for provider in self._providers:
            try:
                result = provider.lookup(digits)
            except PostalAddressProviderError as exc:
                last_error = exc
                continue
            if result is not None:
                return result
        if last_error is not None:
            raise last_error
        return PostalAddressResult.not_found(digits)
