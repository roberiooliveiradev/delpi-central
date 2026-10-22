"""BrasilAPI CNPJ v1 adapter for the company-registry port (S3.1).

- Community third-party provider: ``provider_id=brasilapi-cnpj-v1``,
  conceptually ``THIRD_PARTY_API`` — never claimed as a government source.
- ``fetch()`` is the only public surface; it returns an
  ``ExternalRegistrySnapshot`` built from an allowlist of documented fields
  (https://github.com/BrasilAPI/BrasilAPI — pages/docs/doc/cnpj.json).
- QSA, partners, CPFs and any unmapped field are never read, projected or
  logged. The raw payload is never persisted.
- No retries: BrasilAPI is a free community endpoint; upstream 5xx/timeout
  maps to fail-closed ``EnrichmentSourceUnavailableError`` and HTTP 429 is
  honoured via ``Retry-After`` instead of being retried.
- CNPJ alfanumérico is accepted by BrasilAPI but the S1 domain is
  digits-only: non-numeric tax ids fail closed before any network call.
"""

from __future__ import annotations

import hashlib
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

import requests

from app.application.services.supplier_enrichment.contracts import (
    CompanyRegistryProvider,
    EnrichmentSourceUnavailableError,
    RegistryAccessDeniedError,
    RegistryRateLimitedError,
    RegistryResponseInvalidError,
    RegistryTaxIdInvalidError,
    RegistryTaxIdNotFoundError,
)
from app.domain.supplier_enrichment.models import (
    ExternalRegistrySnapshot,
    digits_only,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.gateways.registry_rate_limits import (
    InMemoryRegistryRateLimiter,
    build_registry_rate_limiter,
)

logger = logging.getLogger("supplies-api.brasilapi_registry")

PROVIDER_ID = "brasilapi-cnpj-v1"
DEFAULT_BASE_URL = "https://brasilapi.com.br/api"

_CNPJ_FORMATTING = (".", "/", "-")

Transport = Callable[..., Any]


def _requests_transport(url: str, *, timeout: float) -> Any:
    return requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=timeout,
    )


_shared_limiter: Any = None
_shared_limiter_lock = threading.Lock()


def registry_rate_limiter() -> Any:
    """Process-wide shared query limiter for every provider instance.

    S3.1 rework fixed the per-request limiter lifecycle; S3.2 delegates the
    backend to ``build_registry_rate_limiter`` — ``process_local`` (default,
    single-worker only) or ``distributed`` (Redis shared across workers,
    fail-closed when unavailable).
    """
    global _shared_limiter
    if _shared_limiter is None:
        with _shared_limiter_lock:
            if _shared_limiter is None:
                _shared_limiter = build_registry_rate_limiter()
    return _shared_limiter


def reset_registry_rate_limiter() -> None:
    """Test hook — drop the cached limiter so config changes take effect."""
    global _shared_limiter
    with _shared_limiter_lock:
        _shared_limiter = None


class BrasilApiCompanyRegistryProvider(CompanyRegistryProvider):
    """Company-registry adapter for the public BrasilAPI CNPJ v1 endpoint."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        transport: Transport | None = None,
        rate_limiter: InMemoryRegistryRateLimiter | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._base_url = (
            base_url or getattr(Settings, "BRASILAPI_BASE_URL", "")
        ).rstrip("/") or DEFAULT_BASE_URL
        self._timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else float(getattr(Settings, "BRASILAPI_TIMEOUT_SECONDS", 6) or 6)
        )
        self._transport = transport or _requests_transport
        self._limiter = rate_limiter or registry_rate_limiter()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def fetch(self, tax_id: str) -> ExternalRegistrySnapshot:
        tax_id = digits_only(tax_id)
        if len(tax_id) != 14:
            # S1 identity is digits-only CNPJ; alphanumeric CNPJs are an
            # explicit incompatibility, not a silent fallback.
            raise RegistryTaxIdInvalidError(
                "tax id is not a numeric 14-digit CNPJ"
            )
        # cnpj key is hashed — full tax ids never appear as observable
        # storage keys. global aggregates all workers' provider usage.
        cnpj_key = hashlib.sha256(tax_id.encode()).hexdigest()[:20]
        self._limiter.acquire_many([("cnpj", cnpj_key), ("global", "all")])

        url = f"{self._base_url}/cnpj/v1/{tax_id}"
        try:
            response = self._transport(url, timeout=self._timeout)
        except Exception as exc:
            logger.warning("brasilapi_fetch_failed kind=transport")
            raise EnrichmentSourceUnavailableError(
                "company registry provider unreachable"
            ) from exc

        return self._snapshot_from_response(response, tax_id)

    # --- internals ---------------------------------------------------------

    def _snapshot_from_response(
        self, response: Any, tax_id: str
    ) -> ExternalRegistrySnapshot:
        status = getattr(response, "status_code", None)
        if status == 200:
            pass
        elif status == 400:
            raise RegistryTaxIdInvalidError("provider rejected the CNPJ")
        elif status == 404:
            raise RegistryTaxIdNotFoundError("CNPJ not found by provider")
        elif status == 403:
            raise RegistryAccessDeniedError("provider denied the request")
        elif status == 429:
            retry_after = self._retry_after(response)
            raise RegistryRateLimitedError(
                "provider rate limit reached", retry_after=retry_after
            )
        elif isinstance(status, int) and status >= 500:
            raise EnrichmentSourceUnavailableError(
                "company registry provider unavailable"
            )
        else:
            raise RegistryResponseInvalidError(
                f"unexpected provider status {status}"
            )

        try:
            payload = response.json()
        except Exception as exc:
            raise RegistryResponseInvalidError(
                "provider returned non-JSON payload"
            ) from exc
        return self._snapshot_from_payload(payload, tax_id)

    @staticmethod
    def _retry_after(response: Any) -> int | None:
        headers = getattr(response, "headers", None) or {}
        raw = None
        if isinstance(headers, Mapping):
            raw = headers.get("Retry-After") or headers.get("retry-after")
        try:
            return int(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    def _snapshot_from_payload(
        self, payload: Any, tax_id: str
    ) -> ExternalRegistrySnapshot:
        if not isinstance(payload, Mapping):
            raise RegistryResponseInvalidError("provider payload is not an object")

        returned = str(payload.get("cnpj") or "")
        for sep in _CNPJ_FORMATTING:
            returned = returned.replace(sep, "")
        if returned != tax_id:
            raise RegistryResponseInvalidError("provider CNPJ diverges from query")

        phone_raw = digits_only(payload.get("ddd_telefone_1"))
        street = self._compose_street(payload)

        fields: dict[str, str | None] = {
            "company.tax_id": tax_id,
            "company.legal_name": _text(payload.get("razao_social")),
            "company.trade_name": _text(payload.get("nome_fantasia")),
            "address.street": street,
            "address.district": _text(payload.get("bairro")),
            "address.postal_code": digits_only(payload.get("cep")) or None,
            "address.state": _text(payload.get("uf")),
            "address.city": _text(payload.get("municipio")),
            "address.ibge_city_code": _digits_or_none(
                payload.get("codigo_municipio_ibge")
            ),
            "contact.area_code": phone_raw[:2] or None,
            "contact.phone": phone_raw[2:] or None,
            "contact.email": _text(payload.get("email")),
            "company.registration_status": _text(
                payload.get("descricao_situacao_cadastral")
            ),
            "company.main_cnae": self._compose_cnae(payload),
            "company.legal_nature": _text(payload.get("natureza_juridica")),
            "company.opening_date": _text(payload.get("data_inicio_atividade")),
        }

        retrieved_at = self._clock().isoformat()
        return ExternalRegistrySnapshot(
            tax_id=tax_id,
            source_id=PROVIDER_ID,
            retrieved_at=retrieved_at,
            fields=fields,
            source_reference=f"{PROVIDER_ID}:cnpj-…{tax_id[-4:]}",
        )

    @staticmethod
    def _compose_street(payload: Mapping[str, Any]) -> str | None:
        parts = [
            _text(payload.get("descricao_tipo_de_logradouro")),
            _text(payload.get("logradouro")),
        ]
        street = " ".join(p for p in parts if p)
        number = _text(payload.get("numero"))
        if number and number != "S/N" and not street.strip().endswith(number):
            street = f"{street}, {number}" if street else number
        complement = _text(payload.get("complemento"))
        if complement:
            street = f"{street} {complement}".strip()
        return street or None

    @staticmethod
    def _compose_cnae(payload: Mapping[str, Any]) -> str | None:
        code = _digits_or_none(payload.get("cnae_fiscal"))
        desc = _text(payload.get("cnae_fiscal_descricao"))
        if code and desc:
            return f"{code} - {desc}"
        return code or desc


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _digits_or_none(value: Any) -> str | None:
    digits = digits_only(value)
    return digits or None
