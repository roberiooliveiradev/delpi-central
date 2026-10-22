"""External Data API adapter for the company-registry port (X2).

Implements ``CompanyRegistryProvider`` over the shared internal service:
``GET {EXTERNAL_DATA_API_BASE_URL}/v1/cnpj/{cnpj}`` authenticated with the
individual S2S credential (``X-Delpi-Service-Authorization``) — the same
``delpi_auth`` machinery used for api-delpi calls. The end-user Bearer is
never forwarded; no direct BrasilAPI call ever happens here.

Mapping: DTO v1 → ``ExternalRegistrySnapshot`` using the same S1
source_field keys as the legacy local adapter. ``contact.*`` stays
``None`` — X1 deliberately withholds business contact attributes until
LGPD treatment authorization; this is a documented intentional
difference, not parity failure. Per-user (``actor``) limiting stays at
the route; consumer/cnpj/global caps belong to external-data-api.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Mapping

import requests
from delpi_auth.service_contract import (
    SERVICE_AUTHORIZATION_HEADER,
    build_service_authorization,
)
from delpi_auth.service_errors import ServiceAuthError

from app.application.services.supplier_enrichment.contracts import (
    CompanyRegistryProvider,
    EnrichmentSourceUnavailableError,
    RegistryLimiterUnavailableError,
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
from app.infrastructure.gateways.delpi_s2s_gateway import get_s2s_token_provider

logger = logging.getLogger("supplies-api.external_data_registry")

DEFAULT_BASE_URL = "http://external-data-api:8000"

_CNPJ_FORMATTING = (".", "/", "-")

Transport = Callable[..., Any]


def _requests_transport(url: str, *, headers: dict, timeout: float) -> Any:
    return requests.get(url, headers=headers, timeout=timeout)


class ExternalDataApiCompanyRegistryProvider(CompanyRegistryProvider):
    """Registry reads via the shared ``external-data-api`` (S2S)."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        transport: Transport | None = None,
        token_provider: Any | None = None,
    ) -> None:
        self._base_url = (
            base_url or getattr(Settings, "EXTERNAL_DATA_API_BASE_URL", "")
        ).rstrip("/") or DEFAULT_BASE_URL
        self._timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else float(
                getattr(Settings, "EXTERNAL_DATA_API_TIMEOUT_SECONDS", 10) or 10
            )
        )
        self._transport = transport or _requests_transport
        self._token_provider = token_provider

    def fetch(self, tax_id: str) -> ExternalRegistrySnapshot:
        tax_id = digits_only(tax_id)
        if len(tax_id) != 14:
            raise RegistryTaxIdInvalidError(
                "tax id is not a numeric 14-digit CNPJ"
            )

        headers = {
            "Accept": "application/json",
            SERVICE_AUTHORIZATION_HEADER: build_service_authorization(
                self._service_token()
            ),
        }
        url = f"{self._base_url}/v1/cnpj/{tax_id}"
        try:
            response = self._transport(url, headers=headers, timeout=self._timeout)
        except Exception as exc:
            logger.warning("external_data_fetch_failed kind=transport")
            raise EnrichmentSourceUnavailableError(
                "external data service unreachable"
            ) from exc

        return self._snapshot_from_response(response, tax_id)

    # --- internals ---------------------------------------------------------

    def _service_token(self) -> str:
        provider = self._token_provider or get_s2s_token_provider()
        try:
            return provider.get_token()
        except ServiceAuthError as exc:
            logger.warning("external_data_s2s_token_unavailable code=%s", exc.code)
            raise EnrichmentSourceUnavailableError(
                "external data s2s authentication unavailable"
            ) from exc

    def _snapshot_from_response(
        self, response: Any, tax_id: str
    ) -> ExternalRegistrySnapshot:
        status = getattr(response, "status_code", None)
        if status == 200:
            pass
        elif status == 400:
            raise RegistryTaxIdInvalidError("external data rejected the CNPJ")
        elif status == 404:
            raise RegistryTaxIdNotFoundError("CNPJ not found by external data")
        elif status in (401, 403):
            # Technical-credential denial is a service fault, never a user
            # permission denial — do not surface it as such.
            logger.warning("external_data_denied status=%s", status)
            raise EnrichmentSourceUnavailableError(
                "external data service denied the service credential"
            )
        elif status == 429:
            raise RegistryRateLimitedError(
                "external data rate limit reached",
                retry_after=_retry_after(response),
            )
        elif status == 502:
            raise RegistryResponseInvalidError(
                "external data received an invalid upstream response"
            )
        elif status == 504:
            raise EnrichmentSourceUnavailableError(
                "external data provider timed out"
            )
        elif status == 503:
            code = _error_code(response)
            if code == "EXTERNAL_DATA_LIMITER_UNAVAILABLE":
                raise RegistryLimiterUnavailableError(
                    "external data rate limiter unavailable"
                )
            raise EnrichmentSourceUnavailableError(
                "external data service unavailable"
            )
        elif isinstance(status, int) and status >= 500:
            raise EnrichmentSourceUnavailableError(
                "external data service unavailable"
            )
        else:
            raise RegistryResponseInvalidError(
                f"unexpected external data status {status}"
            )

        try:
            payload = response.json()
        except Exception as exc:
            raise RegistryResponseInvalidError(
                "external data returned non-JSON payload"
            ) from exc
        return self._snapshot_from_payload(payload, tax_id)

    def _snapshot_from_payload(
        self, payload: Any, tax_id: str
    ) -> ExternalRegistrySnapshot:
        if not isinstance(payload, Mapping):
            raise RegistryResponseInvalidError(
                "external data payload is not an object"
            )

        returned = digits_only(payload.get("tax_id"))
        if returned != tax_id:
            raise RegistryResponseInvalidError(
                "external data CNPJ diverges from query"
            )

        source = payload.get("source")
        if not isinstance(source, Mapping):
            raise RegistryResponseInvalidError(
                "external data payload lacks source metadata"
            )
        provider_id = str(source.get("provider_id") or "").strip()
        source_type = str(source.get("source_type") or "").strip().upper()
        retrieved_at = str(source.get("retrieved_at") or "").strip()
        if not provider_id or not retrieved_at:
            raise RegistryResponseInvalidError(
                "external data source metadata incomplete"
            )
        if source_type != "THIRD_PARTY_API":
            # Never allow a shared-service response to masquerade as an
            # official/government source inside S1/S2 audit.
            raise RegistryResponseInvalidError(
                "external data source type is not THIRD_PARTY_API"
            )

        address = payload.get("address") or {}
        registration = payload.get("registration") or {}
        contact = payload.get("contact") or {}
        if not isinstance(address, Mapping):
            address = {}
        if not isinstance(registration, Mapping):
            registration = {}
        if not isinstance(contact, Mapping):
            contact = {}

        fields: dict[str, str | None] = {
            "company.tax_id": tax_id,
            "company.legal_name": _text(payload.get("legal_name")),
            "company.trade_name": _text(payload.get("trade_name")),
            "address.street": self._compose_street(address),
            "address.district": _text(address.get("district")),
            "address.postal_code": digits_only(address.get("postal_code"))
            or None,
            "address.state": _text(address.get("state")),
            "address.city": _text(address.get("city")),
            "address.ibge_city_code": _digits_or_none(
                address.get("ibge_city_code")
            ),
            # X1 LGPD restriction: contact attributes are deliberately null.
            "contact.area_code": _text(contact.get("area_code")),
            "contact.phone": _text(contact.get("phone")),
            "contact.email": _text(contact.get("email")),
            "company.registration_status": _text(
                registration.get("status")
            ),
            "company.main_cnae": _text(registration.get("main_cnae")),
            "company.legal_nature": _text(registration.get("legal_nature")),
            "company.opening_date": _text(registration.get("opening_date")),
        }

        return ExternalRegistrySnapshot(
            tax_id=tax_id,
            source_id=provider_id,
            retrieved_at=retrieved_at,
            fields=fields,
            source_reference=f"{provider_id}:cnpj-…{tax_id[-4:]}",
        )

    @staticmethod
    def _compose_street(address: Mapping[str, Any]) -> str | None:
        """Recompose the S1 street field the same way the local adapter did:
        number is appended only when the street does not already embed it.""" 
        street = _text(address.get("street")) or ""
        number = _text(address.get("number"))
        if number and number != "S/N" and not street.strip().endswith(number):
            street = f"{street}, {number}" if street else number
        complement = _text(address.get("complement"))
        if complement:
            street = f"{street} {complement}".strip()
        return street or None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _digits_or_none(value: Any) -> str | None:
    digits = digits_only(value)
    return digits or None


def _retry_after(response: Any) -> int | None:
    headers = getattr(response, "headers", None) or {}
    raw = None
    if isinstance(headers, Mapping):
        raw = headers.get("Retry-After") or headers.get("retry-after")
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _error_code(response: Any) -> str:
    try:
        payload = response.json()
    except Exception:
        return ""
    if isinstance(payload, Mapping):
        return str(payload.get("code") or "")
    return ""
