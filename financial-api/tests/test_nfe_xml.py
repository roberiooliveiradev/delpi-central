"""Parser da NF-e modelo 55. Sem rede e sem XML em log."""

from __future__ import annotations

from datetime import date

import pytest

from financial_app.domain.errors import NfeXmlRejected, QuestorInvalidResponse
from financial_app.domain.fiscal_access_key import access_key_check_digit_ok, access_key_model
from financial_app.domain.services.fiscal_calendar_date import fiscal_calendar_date
from financial_app.infrastructure.xml.nfe_xml import parse_nfe_xml
from nfe_xml_samples import nfe_access_key, nfe_xml

KEY = nfe_access_key()
MAX_BYTES = 100_000


def test_published_portal_example_matches_the_fiscal_check_digit() -> None:
    published = "35260947132675000158550010000856451625949749"
    assert len(published) == 44
    assert access_key_model(published) == "55"
    assert access_key_check_digit_ok(published)


def test_nfeproc_namespace_reads_key_from_id_and_protocol() -> None:
    parsed = parse_nfe_xml(nfe_xml(KEY), max_bytes=MAX_BYTES, expected_access_key=KEY)
    assert parsed.access_key == KEY
    assert parsed.model == "55"
    assert parsed.series == "001"
    assert parsed.number == "000085645"
    assert parsed.issuer_cnpj == "47132675000158"
    assert parsed.emission_date == date(2026, 10, 2)


def test_key_can_come_from_protocol_or_from_inf_nfe_id() -> None:
    from_protocol = parse_nfe_xml(nfe_xml(KEY, include_id=False), max_bytes=MAX_BYTES)
    from_id = parse_nfe_xml(nfe_xml(KEY, include_protocol=False, wrapped=False), max_bytes=MAX_BYTES)
    assert from_protocol.access_key == KEY
    assert from_id.access_key == KEY


def test_divergent_keys_are_rejected() -> None:
    other = nfe_access_key(number="000085646")
    with pytest.raises(NfeXmlRejected) as caught:
        parse_nfe_xml(nfe_xml(KEY, protocol_key=other), max_bytes=MAX_BYTES, expected_access_key=KEY)
    assert caught.value.code == "access_key_mismatch"


def test_listing_key_must_match_the_xml() -> None:
    other = nfe_access_key(number="000085646")
    with pytest.raises(NfeXmlRejected) as caught:
        parse_nfe_xml(nfe_xml(KEY), max_bytes=MAX_BYTES, expected_access_key=other)
    assert caught.value.code == "access_key_mismatch"


def test_invalid_key_and_check_digit_are_rejected() -> None:
    broken = KEY[:-1] + ("0" if KEY[-1] != "0" else "1")
    with pytest.raises(NfeXmlRejected) as caught:
        parse_nfe_xml(nfe_xml(broken), max_bytes=MAX_BYTES)
    assert caught.value.code == "invalid_access_key"
    with pytest.raises(NfeXmlRejected):
        parse_nfe_xml(b"<nfeProc><NFe><infNFe Id='NFe123'><ide><mod>55</mod></ide></infNFe></NFe></nfeProc>", max_bytes=MAX_BYTES)


def test_model_other_than_55_is_rejected() -> None:
    with pytest.raises(NfeXmlRejected) as caught:
        parse_nfe_xml(nfe_xml(KEY, model="65"), max_bytes=MAX_BYTES)
    assert caught.value.code == "invalid_model"
    cte_key = nfe_access_key(model="57")
    with pytest.raises(NfeXmlRejected) as caught_model:
        parse_nfe_xml(nfe_xml(cte_key, model="57"), max_bytes=MAX_BYTES)
    assert caught_model.value.code == "invalid_model"


def test_malformed_dtd_entity_and_oversized_payloads_are_rejected() -> None:
    with pytest.raises(QuestorInvalidResponse):
        parse_nfe_xml(b"<nfeProc>", max_bytes=MAX_BYTES)
    with pytest.raises(QuestorInvalidResponse):
        parse_nfe_xml(b"<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><nfeProc/>", max_bytes=MAX_BYTES)
    with pytest.raises(QuestorInvalidResponse):
        parse_nfe_xml(b"<!ENTITY xxe SYSTEM 'http://evil.example/x'> <nfeProc/>", max_bytes=MAX_BYTES)
    with pytest.raises(QuestorInvalidResponse):
        parse_nfe_xml(b"<nfeProc>" + b"x" * 80, max_bytes=32)
    with pytest.raises(QuestorInvalidResponse):
        parse_nfe_xml(b"<html>login</html>", max_bytes=MAX_BYTES)


def test_fiscal_emission_date_uses_sao_paulo_calendar() -> None:
    on_cutoff = parse_nfe_xml(
        nfe_xml(KEY, dh_emi="2026-10-02T00:00:00-03:00"),
        max_bytes=MAX_BYTES,
    )
    after_cutoff = parse_nfe_xml(
        nfe_xml(KEY, dh_emi="2026-10-05T15:00:00-03:00"),
        max_bytes=MAX_BYTES,
    )
    before_cutoff = parse_nfe_xml(
        nfe_xml(KEY, dh_emi="2026-10-01T23:59:59-03:00"),
        max_bytes=MAX_BYTES,
    )
    utc_still_previous_day = parse_nfe_xml(
        nfe_xml(KEY, dh_emi="2026-10-02T02:00:00Z"),
        max_bytes=MAX_BYTES,
    )
    utc_already_cutoff = parse_nfe_xml(
        nfe_xml(KEY, dh_emi="2026-10-02T03:00:00Z"),
        max_bytes=MAX_BYTES,
    )
    naive_local = fiscal_calendar_date("2026-10-02T00:30:00")
    assert on_cutoff.emission_date == date(2026, 10, 2)
    assert after_cutoff.emission_date == date(2026, 10, 5)
    assert before_cutoff.emission_date == date(2026, 10, 1)
    assert utc_still_previous_day.emission_date == date(2026, 10, 1)
    assert utc_already_cutoff.emission_date == date(2026, 10, 2)
    assert naive_local == date(2026, 10, 2)
