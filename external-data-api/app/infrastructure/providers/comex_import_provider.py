"""MDIC Comex Stat — official import CSV provider (PROC-0076 R2).

Downloads the official annual import file (``IMP_<year>.csv``) from the
allowlisted MDIC host and aggregates it via
``comex_csv_normalizer.normalize_import_csv``. Streaming-only: chunks are
decoded incrementally, hashed for provenance and bounded by a hard byte
cap — the ~175 MB annual file is never materialized in memory.

Produced aggregates are monthly FOB totals / net weight / derived
USD-per-ton unit values for *approved NCMs only* — an import-value
indicator, never a metal spot quote.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable
from urllib.parse import urlparse

import requests

from app.application.contracts import (
    InvalidResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.providers.comex_csv_normalizer import (
    ComexCsvContractError,
    MonthlyImportAggregate,
    normalize_import_csv,
)

logger = logging.getLogger("external-data-api.comex")

Transport = Callable[..., Any]

CHUNK_SIZE = 512 * 1024


@dataclass(frozen=True)
class ComexFetchResult:
    dataset_year: int
    source_checksum: str
    bytes_read: int
    aggregates: list[MonthlyImportAggregate] = field(default_factory=list)


def _requests_transport(url: str, *, headers: dict, timeout: float, verify) -> Any:
    return requests.get(
        url, headers=headers, timeout=timeout, stream=True, verify=verify
    )


class ComexImportProvider:
    """Bounded, checksummed downloader for the official MDIC CSV."""

    provider_id = "mdic-comex-stat"

    def __init__(
        self,
        *,
        url_template: str | None = None,
        allowed_hosts: frozenset[str] | None = None,
        timeout_seconds: float | None = None,
        max_bytes: int | None = None,
        transport: Transport | None = None,
        verify: Any = None,
    ) -> None:
        self._url_template = (
            url_template or Settings.COMEX_IMPORT_URL_TEMPLATE
        )
        self._allowed_hosts = allowed_hosts or Settings.COMEX_ALLOWED_HOSTS
        self._timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else Settings.COMEX_TIMEOUT_SECONDS
        )
        self._max_bytes = max_bytes or Settings.COMEX_MAX_DOWNLOAD_BYTES
        self._transport = transport or _requests_transport
        self._verify = (
            verify if verify is not None else Settings.COMEX_CA_BUNDLE
        )

    def _url_for_year(self, year: int) -> str:
        url = self._url_template.format(year=year)
        host = (urlparse(url).hostname or "").lower()
        if host not in self._allowed_hosts:
            raise InvalidResponseError(
                "comex download host is not on the allowlist"
            )
        return url

    def fetch_year(
        self, year: int, *, approved_ncm_codes: frozenset[str]
    ) -> ComexFetchResult:
        """Download + aggregate one official annual file.

        ``approved_ncm_codes`` comes from the catalog allowlist — the
        provider never guesses or broadens it.
        """
        url = self._url_for_year(year)
        headers = {
            "Accept": "text/csv",
            "User-Agent": Settings.EXTERNAL_DATA_USER_AGENT,
        }
        try:
            response = self._transport(
                url, headers=headers, timeout=self._timeout,
                verify=self._verify,
            )
        except requests.Timeout as exc:
            raise ProviderTimeoutError("comex download timed out") from exc
        except requests.RequestException as exc:
            logger.warning("comex_transport_failure")
            raise ProviderUnavailableError("comex request failed") from exc

        status = getattr(response, "status_code", 0)
        if status == 429:
            retry_after = None
            try:
                retry_after = int(response.headers.get("Retry-After") or 0)
            except (TypeError, ValueError):
                retry_after = None
            raise RateLimitedError(
                "comex rate limited", retry_after=retry_after or None
            )
        if status in (401, 403):
            raise ProviderUnavailableError("comex access denied")
        if status == 404:
            raise ProviderUnavailableError("comex dataset not found")
        if status >= 500:
            raise ProviderUnavailableError("comex server error")
        if status != 200:
            raise ProviderUnavailableError(
                f"comex unexpected status {status}"
            )

        checksum = hashlib.sha256()
        bytes_read = 0
        pending = bytearray()

        def lines() -> Iterable[str]:
            nonlocal bytes_read
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                bytes_read += len(chunk)
                if bytes_read > self._max_bytes:
                    raise InvalidResponseError(
                        "comex download exceeded the byte cap"
                    )
                checksum.update(chunk)
                pending.extend(chunk)
                while True:
                    newline = pending.find(b"\n")
                    if newline < 0:
                        break
                    raw = bytes(pending[: newline + 1])
                    del pending[: newline + 1]
                    try:
                        yield raw.decode("utf-8-sig")
                    except UnicodeDecodeError as exc:
                        raise InvalidResponseError(
                            "comex file is not valid UTF-8"
                        ) from exc
            if pending:
                yield bytes(pending).decode("utf-8-sig")

        try:
            aggregates = normalize_import_csv(
                lines(), approved_ncm_codes=approved_ncm_codes
            )
        except ComexCsvContractError as exc:
            raise InvalidResponseError(f"comex file rejected: {exc}") from exc
        finally:
            try:
                response.close()
            except Exception:
                pass

        return ComexFetchResult(
            dataset_year=year,
            source_checksum=checksum.hexdigest(),
            bytes_read=bytes_read,
            aggregates=aggregates,
        )


def build_comex_provider(**overrides) -> ComexImportProvider:
    return ComexImportProvider(**overrides)
