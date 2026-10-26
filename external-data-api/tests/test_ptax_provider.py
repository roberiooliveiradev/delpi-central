"""PTAX OData provider — normalization and failure modes (PROC-0076)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.application.contracts import (
    InvalidResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
)
from app.infrastructure.providers.ptax_fx_provider import PtaxFxProvider
import requests


def _resp(status=200, payload=None, headers=None):
    class _R:
        def __init__(self):
            self.status_code = status
            self.headers = headers or {}
            self.content = b"x"

        def json(self):
            if payload is None:
                raise ValueError("not json")
            return payload

    return _R()


def _provider(transport):
    return PtaxFxProvider(
        base_url="https://olinda.test/v1", transport=transport
    )


PTAX_PAYLOAD = {
    "value": [
        {
            "cotacaoCompra": 5.4001,
            "cotacaoVenda": 5.4005,
            "dataHoraCotacao": "2026-01-05 13:04:00.000",
            "tipoBoletim": "Abertura",
        },
        {
            "cotacaoCompra": 5.4100,
            "cotacaoVenda": 5.4200,
            "dataHoraCotacao": "2026-01-05 17:05:00.000",
            "tipoBoletim": "Fechamento",
        },
        {
            "cotacaoCompra": 5.4200,
            "cotacaoVenda": 5.4300,
            "dataHoraCotacao": "2026-01-06 17:06:00.000",
            "tipoBoletim": "Fechamento",
        },
    ]
}


def test_fetch_normalizes_closing_bulletins():
    provider = _provider(lambda url, headers, timeout: _resp(200, PTAX_PAYLOAD))
    rows = provider.fetch_period(date(2026, 1, 5), date(2026, 1, 10))
    assert [r["reference_date"] for r in rows] == [
        date(2026, 1, 5),
        date(2026, 1, 6),
    ]
    # Only the closing bulletin values are kept — the opening row is ignored.
    assert rows[0]["sell"] == Decimal("5.42")
    assert rows[0]["buy"] == Decimal("5.41")


def test_fetch_url_uses_us_date_format():
    seen = {}

    def transport(url, headers, timeout):
        seen["url"] = url
        return _resp(200, {"value": []})

    _provider(transport).fetch_period(date(2026, 1, 5), date(2026, 1, 10))
    assert "01-05-2026" in seen["url"]
    assert "01-10-2026" in seen["url"]


def test_to_observations_expands_buy_and_sell():
    rows = [{"reference_date": date(2026, 1, 5), "buy": Decimal("5.41"), "sell": Decimal("5.42")}]
    obs = PtaxFxProvider.to_observations(
        rows, source_id="bcb-ptax",
        retrieved_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
    )
    kinds = {o["rate_kind"] for o in obs}
    assert kinds == {"ptax_closing_buy", "ptax_closing_sell"}
    assert all(o["pair_code"] == "USD/BRL" for o in obs)


def test_rate_limited_429_with_retry_after():
    provider = _provider(
        lambda url, headers, timeout: _resp(429, headers={"Retry-After": "30"})
    )
    with pytest.raises(RateLimitedError) as exc:
        provider.fetch_period(date(2026, 1, 5), date(2026, 1, 10))
    assert exc.value.retry_after == 30


@pytest.mark.parametrize("status", [401, 403, 500, 502, 503])
def test_unavailable_statuses(status):
    provider = _provider(lambda url, headers, timeout: _resp(status))
    with pytest.raises(ProviderUnavailableError):
        provider.fetch_period(date(2026, 1, 5), date(2026, 1, 10))


def test_timeout_maps_504():
    def transport(url, headers, timeout):
        raise requests.Timeout("slow")

    with pytest.raises(ProviderTimeoutError):
        _provider(transport).fetch_period(
            date(2026, 1, 5), date(2026, 1, 10)
        )


def test_transport_failure_maps_503():
    def transport(url, headers, timeout):
        raise requests.ConnectionError("down")

    with pytest.raises(ProviderUnavailableError):
        _provider(transport).fetch_period(
            date(2026, 1, 5), date(2026, 1, 10)
        )


def test_invalid_payload_rejected():
    provider = _provider(lambda url, headers, timeout: _resp(200, {"oops": []}))
    with pytest.raises(InvalidResponseError):
        provider.fetch_period(date(2026, 1, 5), date(2026, 1, 10))


def test_unparsable_rows_rejected_when_no_valid_closing():
    payload = {"value": [{"tipoBoletim": "Fechamento", "cotacaoCompra": "x",
                          "cotacaoVenda": "y", "dataHoraCotacao": "zzz"}]}
    provider = _provider(lambda url, headers, timeout: _resp(200, payload))
    with pytest.raises(InvalidResponseError):
        provider.fetch_period(date(2026, 1, 5), date(2026, 1, 10))


def test_non_positive_rates_rejected():
    payload = {"value": [{"tipoBoletim": "Fechamento", "cotacaoCompra": 0,
                          "cotacaoVenda": -1, "dataHoraCotacao": "2026-01-05 17:00:00"}]}
    provider = _provider(lambda url, headers, timeout: _resp(200, payload))
    with pytest.raises(InvalidResponseError):
        provider.fetch_period(date(2026, 1, 5), date(2026, 1, 10))
