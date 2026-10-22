"""Domain model for the external-data bounded context (X1).

``ExternalDataCnpjResponseV1`` is the frozen internal contract from X0 —
an allowlisted, minimized projection of a third-party company registry.
It carries no SA2 field names, no raw provider payload and no personal
partner/QSA data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SOURCE_TYPE_THIRD_PARTY = "THIRD_PARTY_API"
SCHEMA_VERSION_V1 = "v1"


def digits_only(value: object) -> str:
    """Strip non-digits from a scalar; returns "" for None/non-scalar."""
    if value is None:
        return ""
    return "".join(ch for ch in str(value) if ch.isdigit())


@dataclass(frozen=True)
class SourceMetadata:
    provider_id: str
    source_type: str
    retrieved_at: str
    correlation_id: str
    schema_version: str = SCHEMA_VERSION_V1

    def to_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "source_type": self.source_type,
            "retrieved_at": self.retrieved_at,
            "correlation_id": self.correlation_id,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class ExternalDataCnpjResponseV1:
    """Frozen response contract — ``GET /v1/cnpj/{cnpj}`` (X0 §4).

    ``contact`` attributes stay ``None`` until purpose/minimization for
    potentially personal business contacts is institutionally authorized.
    """

    tax_id: str
    legal_name: str | None
    trade_name: str | None
    street: str | None
    number: str | None
    complement: str | None
    district: str | None
    postal_code: str | None
    city: str | None
    state: str | None
    ibge_city_code: str | None
    registration_status: str | None
    main_cnae: str | None
    legal_nature: str | None
    opening_date: str | None
    source: SourceMetadata
    area_code: str | None = None
    phone: str | None = None
    email: str | None = None

    def to_dict(self) -> dict:
        return {
            "tax_id": self.tax_id,
            "legal_name": self.legal_name,
            "trade_name": self.trade_name,
            "address": {
                "street": self.street,
                "number": self.number,
                "complement": self.complement,
                "district": self.district,
                "postal_code": self.postal_code,
                "city": self.city,
                "state": self.state,
                "ibge_city_code": self.ibge_city_code,
            },
            "contact": {
                "area_code": self.area_code,
                "phone": self.phone,
                "email": self.email,
            },
            "registration": {
                "status": self.registration_status,
                "main_cnae": self.main_cnae,
                "legal_nature": self.legal_nature,
                "opening_date": self.opening_date,
            },
            "source": self.source.to_dict(),
        }
