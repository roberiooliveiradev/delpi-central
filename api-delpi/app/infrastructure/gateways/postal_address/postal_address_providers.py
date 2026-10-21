"""HTTP adapters for postal-address providers (ViaCEP, BrasilAPI).

Adapter layer — converte payloads externos em ``PostalAddressResult``.
URLs base vêm de ``Settings`` (servidor); o path é sempre derivado dos 8
dígitos já validados — nenhum cliente injeta URL arbitrária (anti-SSRF).
Sem credenciais, sem persistência do retorno e timeout curto por provider.
"""

from __future__ import annotations

import logging

import requests

from app.config import settings
from app.domain.addresses.postal_address import (
    PostalAddressProviderError,
    PostalAddressResult,
)
from app.domain.ports.addresses.postal_address_provider_port import (
    PostalAddressProviderPort,
)

logger = logging.getLogger("api-delpi.postal_address")

_USER_AGENT = "minha-delpi-api/1.0 (+https://minhadelpi.com.br)"


class _HttpPostalAddressProvider:
    """GET JSON com classificação: 404/not-found → ``None``; falha → erro."""

    name = "_base"

    def __init__(self, *, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def _url(self, digits: str) -> str:  # pragma: no cover - abstract
        raise NotImplementedError

    def _parse(
        self, data: dict, digits: str
    ) -> PostalAddressResult | None:  # pragma: no cover - abstract
        raise NotImplementedError

    def lookup(self, postal_code: str) -> PostalAddressResult | None:
        try:
            response = requests.get(
                self._url(postal_code),
                timeout=self._timeout,
                headers={
                    "User-Agent": _USER_AGENT,
                    "Accept": "application/json",
                },
                allow_redirects=False,
            )
        except requests.Timeout as exc:
            raise PostalAddressProviderError(
                f"{self.name} timeout", status_code=None
            ) from exc
        except requests.RequestException as exc:
            raise PostalAddressProviderError(
                f"{self.name} unreachable", status_code=None
            ) from exc
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise PostalAddressProviderError(
                f"{self.name} error", status_code=response.status_code
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise PostalAddressProviderError(
                f"{self.name} invalid response", status_code=502
            ) from exc
        if not isinstance(data, dict):
            raise PostalAddressProviderError(
                f"{self.name} invalid response", status_code=502
            )
        return self._parse(data, postal_code)


def _str_or_none(value) -> str | None:
    text = str(value or "").strip()
    return text or None


def _uf_or_none(value) -> str | None:
    text = _str_or_none(value)
    return text.upper() if text else None


class ViaCepPostalAddressProvider(_HttpPostalAddressProvider):
    """GET {base}/{cep}/json/ — ``{"erro":"true"}`` é o not-found do ViaCEP."""

    name = "viacep"

    def _url(self, digits: str) -> str:
        return f"{self._base_url}/{digits}/json/"

    def _parse(self, data: dict, digits: str) -> PostalAddressResult | None:
        erro = data.get("erro")
        if erro is True or str(erro).strip().lower() in {"true", "1", "sim"}:
            return None
        street = _str_or_none(data.get("logradouro"))
        return PostalAddressResult(
            postal_code=digits,
            found=True,
            street=street,
            district=_str_or_none(data.get("bairro")),
            city=_str_or_none(data.get("localidade")),
            state=_uf_or_none(data.get("uf")),
            ibge_city_code=_str_or_none(data.get("ibge")),
            source=self.name,
            result_type="street" if street else "municipality",
        )


class BrasilApiPostalAddressProvider(_HttpPostalAddressProvider):
    """GET {base}/{cep} — not-found real é 404; exige User-Agent próprio."""

    name = "brasilapi"

    def _url(self, digits: str) -> str:
        return f"{self._base_url}/{digits}"

    def _parse(self, data: dict, digits: str) -> PostalAddressResult | None:
        # Sem city/state o payload não é endereço utilizável → not-found.
        city = _str_or_none(data.get("city"))
        state = _uf_or_none(data.get("state"))
        if not city or not state:
            return None
        ibge = data.get("ibge")
        ibge_city = (
            _str_or_none(ibge.get("city")) if isinstance(ibge, dict) else None
        )
        street = _str_or_none(data.get("street"))
        return PostalAddressResult(
            postal_code=digits,
            found=True,
            street=street,
            district=_str_or_none(data.get("neighborhood")),
            city=city,
            state=state,
            ibge_city_code=ibge_city,
            source=self.name,
            result_type="street" if street else "municipality",
        )


def default_postal_address_providers() -> tuple[PostalAddressProviderPort, ...]:
    """Cadeia contratada: ViaCEP (dados ricos) → BrasilAPI (cobertura open-cep)."""
    return (
        ViaCepPostalAddressProvider(
            base_url=settings.POSTAL_ADDRESS_VIACEP_URL,
            timeout_seconds=settings.POSTAL_ADDRESS_TIMEOUT_SECONDS,
        ),
        BrasilApiPostalAddressProvider(
            base_url=settings.POSTAL_ADDRESS_BRASILAPI_URL,
            timeout_seconds=settings.POSTAL_ADDRESS_TIMEOUT_SECONDS,
        ),
    )
