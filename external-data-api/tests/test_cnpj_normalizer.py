"""Normalizer — BrasilAPI payload → ExternalDataCnpjResponseV1 (DTO v1)."""

from __future__ import annotations

import pytest

from app.application.contracts import InvalidResponseError
from app.infrastructure.normalization.brasilapi_cnpj_normalizer import (
    normalize_brasilapi_cnpj,
)
from tests.conftest import BRASILAPI_PAYLOAD

ARGS = dict(tax_id="19131243000197", retrieved_at="2026-10-22T12:00:00Z", correlation_id="corr-1")


def test_full_payload_maps_allowlist():
    dto = normalize_brasilapi_cnpj(BRASILAPI_PAYLOAD, **ARGS).to_dict()

    assert dto["tax_id"] == "19131243000197"
    assert dto["legal_name"] == "OPEN KNOWLEDGE BRASIL"
    assert dto["trade_name"] == "REDE PELO CONHECIMENTO LIVRE"
    assert dto["address"]["street"] == "ALAMEDA FRANCA, 243"
    assert dto["address"]["number"] == "243"
    assert dto["address"]["complement"] == "APT 34"
    assert dto["address"]["district"] == "JARDIM PAULISTA"
    assert dto["address"]["postal_code"] == "01422000"
    assert dto["address"]["city"] == "SAO PAULO"
    assert dto["address"]["state"] == "SP"
    assert dto["address"]["ibge_city_code"] == "3550308"
    assert dto["registration"]["status"] == "ATIVA"
    assert dto["registration"]["main_cnae"] == (
        "9430800 - Associacoes de defesa de direitos sociais"
    )
    assert dto["registration"]["legal_nature"] == "Associacao Privada"
    assert dto["registration"]["opening_date"] == "2013-10-03"


def test_source_metadata_is_third_party():
    dto = normalize_brasilapi_cnpj(BRASILAPI_PAYLOAD, **ARGS).to_dict()
    assert dto["source"]["provider_id"] == "brasilapi-cnpj-v1"
    assert dto["source"]["source_type"] == "THIRD_PARTY_API"
    assert dto["source"]["retrieved_at"] == "2026-10-22T12:00:00Z"
    assert dto["source"]["correlation_id"] == "corr-1"
    assert dto["source"]["schema_version"] == "v1"


def test_contact_stays_null_until_authorized():
    dto = normalize_brasilapi_cnpj(BRASILAPI_PAYLOAD, **ARGS).to_dict()
    assert dto["contact"] == {"area_code": None, "phone": None, "email": None}


def test_qsa_and_personal_fields_never_project():
    dto = normalize_brasilapi_cnpj(BRASILAPI_PAYLOAD, **ARGS).to_dict()
    serialized = str(dto)
    assert "qsa" not in serialized.lower()
    assert "SOCIO" not in serialized
    assert "cpf" not in serialized.lower()


def test_cnpj_mismatch_rejected():
    payload = dict(BRASILAPI_PAYLOAD, cnpj="00000000000191")
    with pytest.raises(InvalidResponseError):
        normalize_brasilapi_cnpj(payload, **ARGS)


def test_formatted_returned_cnpj_accepted():
    payload = dict(BRASILAPI_PAYLOAD, cnpj="19.131.243/0001-97")
    dto = normalize_brasilapi_cnpj(payload, **ARGS).to_dict()
    assert dto["tax_id"] == "19131243000197"


def test_non_mapping_payload_rejected():
    with pytest.raises(InvalidResponseError):
        normalize_brasilapi_cnpj(["not", "a", "dict"], **ARGS)


def test_missing_optionals_stay_null():
    payload = {"cnpj": "19131243000197"}
    dto = normalize_brasilapi_cnpj(payload, **ARGS).to_dict()
    assert dto["legal_name"] is None
    assert dto["address"]["street"] is None
    assert dto["address"]["ibge_city_code"] is None
    assert dto["registration"]["main_cnae"] is None


def test_street_dedup_when_logradouro_embeds_number():
    # `logradouro` already carries "243"; it must not be appended again to
    # `street` — the number lives in its own field.
    dto = normalize_brasilapi_cnpj(BRASILAPI_PAYLOAD, **ARGS).to_dict()
    assert dto["address"]["street"] == "ALAMEDA FRANCA, 243"
    assert dto["address"]["street"].count("243") == 1


def test_no_sa2_field_names():
    dto = normalize_brasilapi_cnpj(BRASILAPI_PAYLOAD, **ARGS).to_dict()
    assert "A2_CGC" not in str(dto)
