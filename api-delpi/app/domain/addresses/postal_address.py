"""Postal address lookup — domain types.

Capacidade genérica e reutilizável: um CEP brasileiro normalizado pode
resolver um endereço completo (`result_type="street"`) ou apenas o
município (`result_type="municipality"` — CEP geral de cidade). O domínio
não conhece HTTP, provider ou Protheus: `ibge_city_code` permanece o
código IBGE de 7 dígitos do provider — conciliação com CC2 é regra do
consumidor TOTVS, não deste contrato.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_DIGITS = re.compile(r"\D")


def normalize_postal_code(value: str) -> str:
    """CEP com ou sem máscara → 8 dígitos; rejeita qualquer outra forma."""
    digits = _DIGITS.sub("", value or "")
    if len(digits) != 8:
        raise ValueError("CEP deve conter exatamente 8 dígitos.")
    return digits


class PostalAddressProviderError(RuntimeError):
    """Falha técnica de provider (timeout, rede, HTTP ou payload inválido).

    Nunca representa "CEP inexistente" — inexistência é ``None``/``found=False``.
    """

    def __init__(self, message: str, *, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class PostalAddressResult:
    """Resultado estruturado — campos indisponíveis ficam ``None``."""

    postal_code: str
    found: bool
    street: str | None = None
    district: str | None = None
    city: str | None = None
    state: str | None = None
    ibge_city_code: str | None = None
    source: str = ""
    result_type: str = "municipality"

    def to_dict(self) -> dict[str, Any]:
        return {
            "postal_code": self.postal_code,
            "found": self.found,
            "street": self.street,
            "district": self.district,
            "city": self.city,
            "state": self.state,
            "ibge_city_code": self.ibge_city_code,
            "source": self.source,
            "result_type": self.result_type,
        }

    @staticmethod
    def not_found(postal_code: str) -> "PostalAddressResult":
        return PostalAddressResult(
            postal_code=postal_code,
            found=False,
            source="postal_address_providers",
        )
