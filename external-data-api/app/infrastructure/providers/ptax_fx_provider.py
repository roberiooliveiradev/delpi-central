"""Banco Central do Brasil — PTAX OData provider (PROC-0076).

Endpoint: ``odata/CotacaoDolarPeriodo`` on the official open-data OData
service (https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1). The
``/odata/`` path segment is mandatory — the service rejects function
calls without it with ``403 Access Denied`` (verified against live
contract, R5.S3). The dataset is published under ODbL by BCB;
attribution is carried in the catalog.

Live contract (verified 2026-10-27): ``CotacaoDolarPeriodo`` returns
exactly one row per business day — the closing bulletin — with fields
``cotacaoCompra``, ``cotacaoVenda`` and ``dataHoraCotacao``; it does
NOT emit ``tipoBoletim``. We persist both buy and sell rates under
distinct ``rate_kind`` values (``ptax_closing_buy`` /
``ptax_closing_sell``). ``reference_date`` is the date part of
``dataHoraCotacao`` (America/Sao_Paulo business day), never the fetch
time. Missing days stay missing — no forward-fill.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

import requests

from app.application.contracts import (
    InvalidResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
)
from app.domain.market_data import (
    PAIR_USD_BRL,
    PROVIDER_BCB_PTAX,
    RATE_KIND_PTAX_CLOSING_BUY,
    RATE_KIND_PTAX_CLOSING_SELL,
)
from app.infrastructure.config.settings import Settings

logger = logging.getLogger("external-data-api.ptax")

Transport = Callable[..., Any]

_CLOSING_BULLETIN = "Fechamento"
_MAX_PAGES = 8


def _requests_transport(url: str, *, headers: dict, timeout: float) -> Any:
    return requests.get(url, headers=headers, timeout=timeout)


def _parse_datetime(raw: Any) -> datetime:
    text = str(raw or "").strip()
    if not text:
        raise ValueError("empty dataHoraCotacao")
    # BCB returns "YYYY-MM-DD HH:MM:SS.fff" or ISO-8601 with T.
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _parse_rate(raw: Any) -> Decimal:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid rate value") from exc
    if value <= 0:
        raise ValueError("non-positive rate")
    return value


class PtaxFxProvider:
    """Fetches USD/BRL closing-bulletin observations from the PTAX API."""

    provider_id = PROVIDER_BCB_PTAX

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        transport: Transport | None = None,
    ) -> None:
        self._base_url = (base_url or Settings.PTAX_BASE_URL).rstrip("/")
        self._timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else Settings.PTAX_TIMEOUT_SECONDS
        )
        self._transport = transport or _requests_transport

    def fetch_period(
        self, date_from: date, date_to: date
    ) -> list[dict[str, Any]]:
        """Return normalized observations: {reference_date, buy, sell}."""
        path = (
            "/CotacaoDolarPeriodo"
            if self._base_url.endswith("/odata")
            else "/odata/CotacaoDolarPeriodo"
        )
        url = (
            f"{self._base_url}{path}"
            f"(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
            f"?@dataInicial='{date_from:%m-%d-%Y}'"
            f"&@dataFinalCotacao='{date_to:%m-%d-%Y}'"
            "&$format=json&$top=1000"
        )
        headers = {
            "Accept": "application/json",
            "User-Agent": Settings.EXTERNAL_DATA_USER_AGENT,
        }
        rows: list[dict[str, Any]] = []
        for _ in range(_MAX_PAGES):
            payload = self._request(url, headers=headers)
            if not isinstance(payload, dict) or not isinstance(
                payload.get("value"), list
            ):
                raise InvalidResponseError("ptax payload missing 'value' list")
            rows.extend(payload["value"])
            url = payload.get("@odata.nextLink")
            if not url:
                break
        else:
            raise ProviderUnavailableError("ptax pagination bound exceeded")
        return self._normalize_rows(rows)

    def _request(self, url: str, *, headers: dict) -> Any:
        try:
            response = self._transport(url, headers=headers, timeout=self._timeout)
        except requests.Timeout as exc:
            raise ProviderTimeoutError("ptax request timed out") from exc
        except requests.RequestException as exc:
            logger.warning("ptax_transport_failure")
            raise ProviderUnavailableError("ptax request failed") from exc

        status = getattr(response, "status_code", 0)
        if status == 429:
            retry_after = None
            try:
                retry_after = int(response.headers.get("Retry-After") or 0)
            except (TypeError, ValueError):
                retry_after = None
            raise RateLimitedError(
                "ptax rate limited", retry_after=retry_after or None
            )
        if status in (401, 403):
            raise ProviderUnavailableError("ptax access denied")
        if status >= 500:
            raise ProviderUnavailableError("ptax server error")
        if status != 200:
            raise ProviderUnavailableError(f"ptax unexpected status {status}")

        try:
            return response.json()
        except ValueError as exc:
            raise InvalidResponseError("ptax non-JSON response") from exc

    def _normalize_rows(self, rows: list[Any]) -> list[dict[str, Any]]:
        if not isinstance(rows, list):
            raise InvalidResponseError("ptax payload missing 'value' list")

        by_date: dict[date, dict[str, Any]] = {}
        invalid_rows = 0
        for row in rows:
            if not isinstance(row, dict):
                invalid_rows += 1
                continue
            # The endpoint emits only closing bulletins; when the legacy
            # ``tipoBoletim`` field is present we still enforce it, and
            # its absence means the row already is the closing bulletin.
            boletim = row.get("tipoBoletim")
            if boletim is not None and str(boletim).strip() != _CLOSING_BULLETIN:
                continue
            try:
                stamp = _parse_datetime(row.get("dataHoraCotacao"))
                ref_date = stamp.date()
                buy = _parse_rate(row.get("cotacaoCompra"))
                sell = _parse_rate(row.get("cotacaoVenda"))
            except ValueError:
                invalid_rows += 1
                continue
            by_date[ref_date] = {
                "reference_date": ref_date,
                "buy": buy,
                "sell": sell,
            }

        if not by_date and rows:
            raise InvalidResponseError(
                "ptax payload had rows but none parsed as closing bulletin"
            )
        return [by_date[k] for k in sorted(by_date)]

    @staticmethod
    def to_observations(
        rows: list[dict[str, Any]], *, source_id: str, retrieved_at
    ) -> list[dict[str, Any]]:
        """Expand each closing bulletin into buy + sell rate rows."""
        observations = []
        for row in rows:
            for rate_kind, key in (
                (RATE_KIND_PTAX_CLOSING_BUY, "buy"),
                (RATE_KIND_PTAX_CLOSING_SELL, "sell"),
            ):
                observations.append(
                    {
                        "pair_code": PAIR_USD_BRL,
                        "rate_kind": rate_kind,
                        "reference_date": row["reference_date"],
                        "value": row[key],
                        "source_id": source_id,
                        "source_record_key": (
                            f"ptax:{row['reference_date'].isoformat()}"
                        ),
                        "retrieved_at": retrieved_at,
                    }
                )
        return observations


def build_ptax_provider(**overrides) -> PtaxFxProvider:
    return PtaxFxProvider(**overrides)
