"""Comex import provider — allowlist, streaming, checksum, errors."""

from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal

import pytest

from app.application.contracts import (
    InvalidResponseError,
    ProviderUnavailableError,
    RateLimitedError,
)
from app.infrastructure.providers.comex_import_provider import (
    ComexImportProvider,
)

CSV = (
    '"CO_ANO";"CO_MES";"CO_NCM";"CO_UNID";"CO_PAIS";"SG_UF_NCM";'
    '"CO_VIA";"CO_URF";"QT_ESTAT";"KG_LIQUIDO";"VL_FOB";"VL_FRETE";'
    '"VL_SEGURO"\n'
    '"2025";"07";"12345678";"10";"249";"MG";"01";"0727600";'
    "72920000;72920000;9908156;871036;3615\n"
    '"2025";"07";"12345678";"10";"160";"SC";"01";"0727600";'
    "3900;175;1922;46;0\n"
).encode("utf-8")


class _Resp:
    def __init__(self, status=200, body=CSV, chunk=8192):
        self.status_code = status
        self._body = body
        self._chunk = chunk
        self.headers = {}
        self.closed = False

    def iter_content(self, chunk_size=1):
        for i in range(0, len(self._body), chunk_size):
            yield self._body[i : i + chunk_size]

    def close(self):
        self.closed = True


def _provider(resp, **over):
    calls = []

    def transport(url, *, headers, timeout, verify):
        calls.append(url)
        return resp

    base = dict(
        url_template="https://balanca.economia.gov.br/IMP_{year}.csv",
        allowed_hosts=frozenset({"balanca.economia.gov.br"}),
        transport=transport,
        verify=True,
    )
    base.update(over)
    return ComexImportProvider(**base), calls


def test_streams_and_aggregates_with_checksum():
    provider, calls = _provider(_Resp())
    result = provider.fetch_year(2025, approved_ncm_codes=frozenset({"12345678"}))
    assert calls[0].startswith("https://balanca.economia.gov.br/IMP_2025")
    assert result.dataset_year == 2025
    assert result.source_checksum == hashlib.sha256(CSV).hexdigest()
    assert result.bytes_read == len(CSV)
    assert len(result.aggregates) == 2
    first = result.aggregates[0]
    assert first.reference_month == date(2025, 7, 1)
    assert first.ncm_code == "12345678"
    # Sorted by (month, ncm, country, state) — country "160" comes first:
    # SUM(VL_FOB) / (SUM(KG_LIQUIDO)/1000) = 1922*1000/175.
    assert first.country_code == "160"
    assert first.unit_value_usd_per_t == Decimal("1922") * Decimal(
        "1000"
    ) / Decimal("175")
    second = result.aggregates[1]
    assert second.country_code == "249"
    assert second.unit_value_usd_per_t == Decimal("9908156") * Decimal(
        "1000"
    ) / Decimal("72920000")


def test_host_allowlist_blocks_ssrf():
    provider, _ = _provider(_Resp(), url_template="https://evil.example/{year}.csv")
    with pytest.raises(InvalidResponseError):
        provider.fetch_year(2025, approved_ncm_codes=frozenset({"12345678"}))


def test_byte_cap_rejects_oversized_file():
    provider, _ = _provider(_Resp(), max_bytes=100)
    with pytest.raises(InvalidResponseError, match="byte cap"):
        provider.fetch_year(2025, approved_ncm_codes=frozenset({"12345678"}))


@pytest.mark.parametrize("status", [403, 404, 500])
def test_http_errors_fail_closed(status):
    provider, _ = _provider(_Resp(status=status))
    with pytest.raises(ProviderUnavailableError):
        provider.fetch_year(2025, approved_ncm_codes=frozenset({"12345678"}))


def test_rate_limit_is_distinct():
    provider, _ = _provider(_Resp(status=429))
    with pytest.raises(RateLimitedError):
        provider.fetch_year(2025, approved_ncm_codes=frozenset({"12345678"}))


def test_malformed_csv_is_rejected():
    provider, _ = _provider(_Resp(body=b"not;a;comex;csv\n"))
    with pytest.raises(InvalidResponseError):
        provider.fetch_year(2025, approved_ncm_codes=frozenset({"12345678"}))
