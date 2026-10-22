"""Application contract — typed errors and the provider port (X1).

Error codes mirror the frozen X0 table; routes map ``http_status`` +
``code`` into the shared platform envelope ``{"detail", "code"}``.
"""

from __future__ import annotations

from typing import Mapping, Protocol


class ExternalDataError(RuntimeError):
    http_status = 500
    code = "EXTERNAL_DATA_ERROR"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail or self.code)


class InvalidTaxIdError(ExternalDataError):
    http_status = 400
    code = "EXTERNAL_DATA_INVALID_TAX_ID"


class TaxIdNotFoundError(ExternalDataError):
    http_status = 404
    code = "EXTERNAL_DATA_TAX_ID_NOT_FOUND"


class RateLimitedError(ExternalDataError):
    http_status = 429
    code = "EXTERNAL_DATA_RATE_LIMITED"

    def __init__(self, detail: str | None = None, *, retry_after: int | None = None) -> None:
        super().__init__(detail)
        self.retry_after = retry_after


class InvalidResponseError(ExternalDataError):
    http_status = 502
    code = "EXTERNAL_DATA_INVALID_RESPONSE"


class ProviderUnavailableError(ExternalDataError):
    http_status = 503
    code = "EXTERNAL_DATA_PROVIDER_UNAVAILABLE"


class LimiterUnavailableError(ExternalDataError):
    http_status = 503
    code = "EXTERNAL_DATA_LIMITER_UNAVAILABLE"


class ProviderTimeoutError(ExternalDataError):
    http_status = 504
    code = "EXTERNAL_DATA_PROVIDER_TIMEOUT"


class CnpjDataSource(Protocol):
    """Port: fetch a normalized CNPJ record from an external source."""

    def fetch(self, tax_id: str, *, correlation_id: str) -> Mapping:
        ...
