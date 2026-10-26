"""IBGE IPP provider — SIDRA contract, normalization, errors."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.application.contracts import (
    InvalidResponseError,
    ProviderUnavailableError,
    RateLimitedError,
)
from app.infrastructure.providers.ibge_ipp_provider import IbgeIppProvider

PAYLOAD = [
    {"NC": "Nível Territorial (Código)", "V": "Valor"},
    {
        "V": "184.02085", "D2C": "10008", "D3C": "202606", "D4C": "46641",
        "D1C": "1",
    },
    {
        "V": "182.48723", "D2C": "10008", "D3C": "202605", "D4C": "46641",
        "D1C": "1",
    },
]


class _Resp:
    def __init__(self, status=200, payload=None, raises=None):
        self.status_code = status
        self._payload = payload if payload is not None else PAYLOAD
        self._raises = raises
        self.headers = {}

    def json(self):
        if self._raises:
            raise self._raises
        return self._payload


def _provider(resp, **over):
    urls = []

    def transport(url, *, headers, timeout):
        urls.append(url)
        return resp

    base = dict(
        base_url="https://apisidra.ibge.gov.br",
        allowed_hosts=frozenset({"apisidra.ibge.gov.br"}),
        transport=transport,
    )
    base.update(over)
    return IbgeIppProvider(**base), urls


def _fetch(provider):
    return provider.fetch_series(
        table_code="6903",
        classification_code="842",
        variable_code="10008",
        activity_code="46641",
        month_from=date(2026, 5, 1),
        month_to=date(2026, 6, 1),
    )


def test_real_contract_url_and_decimal_values():
    provider, urls = _provider(_Resp())
    rows = _fetch(provider)
    assert "/t/6903/" in urls[0] and "/v/10008/" in urls[0]
    assert "c842/46641" in urls[0] and "p/202605-202606" in urls[0]
    assert [r["reference_month"] for r in rows] == [
        date(2026, 5, 1),
        date(2026, 6, 1),
    ]
    assert rows[1]["value"] == Decimal("184.02085")
    assert rows[1]["source_record_key"] == "sidra:10008:46641:202606"


def test_variable_mismatch_rejected():
    bad = list(PAYLOAD)
    bad[1] = dict(PAYLOAD[1], D2C="1396")
    provider, _ = _provider(_Resp(payload=bad))
    with pytest.raises(InvalidResponseError, match="variable"):
        _fetch(provider)


def test_activity_mismatch_rejected():
    bad = list(PAYLOAD)
    bad[1] = dict(PAYLOAD[1], D4C="46608")
    provider, _ = _provider(_Resp(payload=bad))
    with pytest.raises(InvalidResponseError, match="activity"):
        _fetch(provider)


def test_invalid_value_rejected():
    bad = list(PAYLOAD)
    bad[1] = dict(PAYLOAD[1], V="NaN")
    provider, _ = _provider(_Resp(payload=bad))
    with pytest.raises(InvalidResponseError):
        _fetch(provider)


def test_non_list_payload_rejected():
    provider, _ = _provider(_Resp(payload={"error": "x"}))
    with pytest.raises(InvalidResponseError):
        _fetch(provider)


@pytest.mark.parametrize("status", [403, 500])
def test_http_errors_fail_closed(status):
    provider, _ = _provider(_Resp(status=status))
    with pytest.raises(ProviderUnavailableError):
        _fetch(provider)


def test_rate_limit_is_distinct():
    provider, _ = _provider(_Resp(status=429))
    with pytest.raises(RateLimitedError):
        _fetch(provider)


def test_host_allowlist_blocks_ssrf():
    provider, _ = _provider(_Resp(), base_url="https://evil.example")
    with pytest.raises(InvalidResponseError):
        _fetch(provider)
