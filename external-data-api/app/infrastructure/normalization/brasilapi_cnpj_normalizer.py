"""Pure normalizer — BrasilAPI CNPJ v1 payload → ``ExternalDataCnpjResponseV1``.

Allowlist only: fields documented in the public schema
(github.com/BrasilAPI/BrasilAPI — pages/docs/doc/cnpj.json). ``qsa``,
partners, CPFs, ``ddd_telefone_2`` and every unmapped field are never
read. ``contact`` attributes stay ``None`` until the treatment purpose
for potentially personal business contacts is authorized (X1 §7).
"""

from __future__ import annotations

from typing import Any, Mapping

from app.application.contracts import InvalidResponseError
from app.domain.external_data import (
    SOURCE_TYPE_THIRD_PARTY,
    ExternalDataCnpjResponseV1,
    SourceMetadata,
    digits_only,
)

PROVIDER_ID = "brasilapi-cnpj-v1"

_CNPJ_FORMATTING = (".", "/", "-")


def normalize_brasilapi_cnpj(
    payload: Any,
    *,
    tax_id: str,
    retrieved_at: str,
    correlation_id: str,
) -> ExternalDataCnpjResponseV1:
    if not isinstance(payload, Mapping):
        raise InvalidResponseError("provider payload is not an object")

    returned = str(payload.get("cnpj") or "")
    for sep in _CNPJ_FORMATTING:
        returned = returned.replace(sep, "")
    if returned != tax_id:
        raise InvalidResponseError("provider CNPJ diverges from query")

    return ExternalDataCnpjResponseV1(
        tax_id=tax_id,
        legal_name=_text(payload.get("razao_social")),
        trade_name=_text(payload.get("nome_fantasia")),
        street=_compose_street(payload),
        number=_text(payload.get("numero")),
        complement=_text(payload.get("complemento")),
        district=_text(payload.get("bairro")),
        postal_code=digits_only(payload.get("cep")) or None,
        city=_text(payload.get("municipio")),
        state=_text(payload.get("uf")),
        ibge_city_code=_digits_or_none(payload.get("codigo_municipio_ibge")),
        registration_status=_text(payload.get("descricao_situacao_cadastral")),
        main_cnae=_compose_cnae(payload),
        legal_nature=_text(payload.get("natureza_juridica")),
        opening_date=_text(payload.get("data_inicio_atividade")),
        source=SourceMetadata(
            provider_id=PROVIDER_ID,
            source_type=SOURCE_TYPE_THIRD_PARTY,
            retrieved_at=retrieved_at,
            correlation_id=correlation_id,
        ),
        # contact.* intentionally None — see module docstring.
    )


def _compose_street(payload: Mapping[str, Any]) -> str | None:
    """Street type + name; BrasilAPI ``logradouro`` often embeds the number,
    so the number is kept in its own DTO field rather than appended."""
    parts = [
        _text(payload.get("descricao_tipo_de_logradouro")),
        _text(payload.get("logradouro")),
    ]
    street = " ".join(p for p in parts if p)
    return street or None


def _compose_cnae(payload: Mapping[str, Any]) -> str | None:
    code = _digits_or_none(payload.get("cnae_fiscal"))
    desc = _text(payload.get("cnae_fiscal_descricao"))
    if code and desc:
        return f"{code} - {desc}"
    return code or desc


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _digits_or_none(value: Any) -> str | None:
    digits = digits_only(value)
    return digits or None
