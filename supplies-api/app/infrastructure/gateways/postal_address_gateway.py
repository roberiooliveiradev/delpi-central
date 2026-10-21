"""Postal-address providers — CEP → proposta de endereço.

Cadeia aprovada: ViaCEP (rico em logradouro/bairro) com fallback BrasilAPI
(cobertura open-cep maior — ex.: CEPs de cidade única ausentes no ViaCEP
como 89120000/Timbó-SC). URLs base são constantes de configuração e o
path é sempre derivado dos 8 dígitos validados — o cliente nunca injeta
URL arbitrária (anti-SSRF). Sem credenciais, sem persistência do retorno,
timeout curto e resposta sanitizada. Falha técnica de um provider aciona
o próximo; CEP inexistente em todos retorna ``found:false`` de verdade.
"""

from __future__ import annotations

import re
from typing import Any

import requests

from app.infrastructure.config.settings import Settings

_DIGITS = re.compile(r"\D")
_USER_AGENT = "minha-delpi-supplies-api/1.0 (+https://minhadelpi.com.br)"


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
    """Consulta os providers em ordem; retorna proposta ou ``None``.

    Not-found comprovado em um provider aciona o seguinte (cobertura
    diferente entre bases públicas). Falha técnica também aciona o
    seguinte; erro só é propagado quando **nenhum** provider respondeu.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        fallback_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else Settings.POSTAL_ADDRESS_TIMEOUT_SECONDS
        )
        self._providers: tuple[tuple[str, str], ...] = (
            (
                "viacep",
                (base_url or Settings.POSTAL_ADDRESS_PROVIDER_URL).rstrip("/")
                + "/{cep}/json/",
            ),
            (
                "brasilapi",
                (
                    fallback_url
                    or Settings.POSTAL_ADDRESS_FALLBACK_URL
                ).rstrip("/")
                + "/{cep}",
            ),
        )

    def _request(self, url: str) -> dict[str, Any]:
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
            )
        except requests.Timeout as exc:
            raise PostalAddressGatewayError(
                "postal address provider timeout", status_code=None
            ) from exc
        except requests.RequestException as exc:
            raise PostalAddressGatewayError(
                "postal address provider unreachable", status_code=None
            ) from exc
        if response.status_code == 404:
            return {"_not_found": True}
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
        return data

    @staticmethod
    def _parse(provider: str, data: dict[str, Any], digits: str) -> dict | None:
        if provider == "viacep":
            erro = data.get("erro")
            if erro is True or str(erro).strip().lower() in {
                "true",
                "1",
                "sim",
            }:
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
        if provider == "brasilapi":
            # BrasilAPI v1: {cep,state,city,neighborhood,street,ibge:{city}}
            # Sem city/state o payload não é endereço utilizável → not-found.
            if not str(data.get("state") or "").strip() or not str(
                data.get("city") or ""
            ).strip():
                return None
            ibge = data.get("ibge")
            ibge_city = (
                str(ibge.get("city") or "").strip()
                if isinstance(ibge, dict)
                else ""
            )
            return {
                "postal_code": digits,
                "street": str(data.get("street") or "").strip(),
                "district": str(data.get("neighborhood") or "").strip(),
                "city": str(data.get("city") or "").strip(),
                "state": str(data.get("state") or "").strip().upper(),
                "ibge_city_code": ibge_city,
                "source": "brasilapi",
                "found": True,
            }
        raise PostalAddressGatewayError(
            "postal address provider invalid response", status_code=502
        )

    def lookup(self, postal_code: str) -> dict[str, Any] | None:
        digits = normalize_postal_code(postal_code)
        last_error: PostalAddressGatewayError | None = None
        for provider, url_template in self._providers:
            try:
                data = self._request(url_template.format(cep=digits))
            except PostalAddressGatewayError as exc:
                last_error = exc
                continue
            if data.get("_not_found"):
                continue
            result = self._parse(provider, data, digits)
            if result is not None:
                return result
        if last_error is not None:
            raise last_error
        return None
