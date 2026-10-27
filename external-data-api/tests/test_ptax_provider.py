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


def test_fetch_url_includes_odata_segment():
    """Live contract: the service 403s function calls without /odata/."""
    seen = {}

    def transport(url, headers, timeout):
        seen["url"] = url
        return _resp(200, {"value": []})

    _provider(transport).fetch_period(date(2026, 1, 5), date(2026, 1, 10))
    assert "/odata/CotacaoDolarPeriodo" in seen["url"]
    assert "/v1/CotacaoDolarPeriodo" not in seen["url"]


def test_fetch_url_not_doubled_when_base_has_odata():
    seen = {}

    def transport(url, headers, timeout):
        seen["url"] = url
        return _resp(200, {"value": []})

    PtaxFxProvider(
        base_url="https://olinda.test/v1/odata", transport=transport
    ).fetch_period(date(2026, 1, 5), date(2026, 1, 10))
    assert "/odata/odata/" not in seen["url"]
    assert "/odata/CotacaoDolarPeriodo" in seen["url"]


def test_fetch_accepts_live_rows_without_tipo_boletim():
    """Live rows carry only cotacao*/dataHoraCotacao — no tipoBoletim."""
    payload = {
        "value": [
            {
                "cotacaoCompra": 5.4998,
                "cotacaoVenda": 5.5007,
                "dataHoraCotacao": "2026-10-26 13:09:51.106105",
            },
            {
                "cotacaoCompra": 5.0371,
                "cotacaoVenda": 5.0377,
                "dataHoraCotacao": "2026-10-23 13:07:14.754567",
            },
        ]
    }
    provider = _provider(lambda url, headers, timeout: _resp(200, payload))
    rows = provider.fetch_period(date(2026, 10, 20), date(2026, 10, 27))
    assert [r["reference_date"] for r in rows] == [
        date(2026, 10, 23),
        date(2026, 10, 26),
    ]
    assert rows[-1]["sell"] == Decimal("5.5007")
    assert rows[-1]["buy"] == Decimal("5.4998")


def test_fetch_follows_next_link_pagination():
    calls = []

    def transport(url, headers, timeout):
        calls.append(url)
        if len(calls) == 1:
            return _resp(
                200,
                {
                    "value": [
                        {
                            "cotacaoCompra": 5.4,
                            "cotacaoVenda": 5.41,
                            "dataHoraCotacao": "2026-01-05 13:04:00",
                        }
                    ],
                    "@odata.nextLink": "https://olinda.test/v1/odata/next",
                },
            )
        return _resp(
            200,
            {
                "value": [
                    {
                        "cotacaoCompra": 5.42,
                        "cotacaoVenda": 5.43,
                        "dataHoraCotacao": "2026-01-06 13:04:00",
                    }
                ]
            },
        )

    rows = _provider(transport).fetch_period(
        date(2026, 1, 5), date(2026, 1, 10)
    )
    assert len(calls) == 2
    assert [r["reference_date"] for r in rows] == [
        date(2026, 1, 5),
        date(2026, 1, 6),
    ]


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
