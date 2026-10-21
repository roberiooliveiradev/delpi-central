"""Postal-address provider (ViaCEP) — CEP → proposta de endereço.

Provider público aprovado pelo PO para homologação. A URL base é uma
constante de configuração e o path é sempre `/<8 dígitos>/json/` — o
cliente nunca injeta URL arbitrária (anti-SSRF). Sem credenciais, sem
persistência do retorno, timeout curto e resposta sanitizada.
"""

from __future__ import annotations

import re
from typing import Any

import requests

from app.infrastructure.config.settings import Settings

_DIGITS = re.compile(r"\D")


class PostalAddressGatewayError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


def normalize_postal_code(value: str) -> str:
    """CEP com ou sem máscara → 8 dígitos; rejeita qualquer outra forma."""
    digits = _DIGITS.sub("", value or "")
    if len(digits) != 8:
        raise ValueError("CEP deve conter exatamente 8 dígitos.")
    return digits


class PostalAddressGateway:
    """GET {base}/<cep>/json/ — retorna proposta ou ``None`` quando não acha."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            base_url or Settings.POSTAL_ADDRESS_PROVIDER_URL
        ).rstrip("/")
        self.timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else Settings.POSTAL_ADDRESS_TIMEOUT_SECONDS
        )

    def lookup(self, postal_code: str) -> dict[str, Any] | None:
        digits = normalize_postal_code(postal_code)
        try:
            response = requests.get(
                f"{self.base_url}/{digits}/json/", timeout=self.timeout
            )
        except requests.Timeout as exc:
            raise PostalAddressGatewayError(
                "postal address provider timeout", status_code=None
            ) from exc
        except requests.RequestException as exc:
            raise PostalAddressGatewayError(
                "postal address provider unreachable", status_code=None
            ) from exc
        if response.status_code != 200:
            raise PostalAddressGatewayError(
                "postal address provider error",
                status_code=response.status_code,
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise PostalAddressGatewayError(
                "postal address provider invalid response", status_code=502
            ) from exc
        if not isinstance(data, dict):
            raise PostalAddressGatewayError(
                "postal address provider invalid response", status_code=502
            )
        erro = data.get("erro")
        if erro is True or str(erro).strip().lower() in {"true", "1", "sim"}:
            return None
        return {
            "postal_code": digits,
            "street": str(data.get("logradouro") or "").strip(),
            "district": str(data.get("bairro") or "").strip(),
            "city": str(data.get("localidade") or "").strip(),
            "state": str(data.get("uf") or "").strip().upper(),
            "ibge_city_code": str(data.get("ibge") or "").strip(),
            "source": "viacep",
            "found": True,
        }
