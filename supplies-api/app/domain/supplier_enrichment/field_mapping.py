"""Field mapping policy — canonical SA2 keys vs external CNPJ source fields.

Limits and SA2 column names follow the canonical matrix
``api-delpi/docs/integrations/protheus-rest-supplier-post-field-matrix.md``
(SX3 proven). Only mapped fields are compared; internal purchasing/financial
fields are never enriched by a company-registry source.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

MAPPING_VERSION_V1 = "cnpj-sa2-v1"
NORMALIZATION_VERSION_V1 = "norm-v1"


class FieldClass(str, Enum):
    """How a mapped field participates in enrichment."""

    PROTECTED = "PROTECTED"
    COMPARABLE = "COMPARABLE"
    INFORMATION_ONLY = "INFORMATION_ONLY"


class Normalizer(str, Enum):
    TEXT = "text"
    DIGITS = "digits"
    UF = "uf"
    EMAIL = "email"


@dataclass(frozen=True)
class FieldSpec:
    field_key: str
    section_key: str
    sa2_field: str
    field_class: FieldClass
    source_field: str | None
    max_length: int | None
    normalizer: Normalizer = Normalizer.TEXT
    # External short/trade name is not presumed equivalent to A2_NREDUZ.
    requires_equivalence_rule: bool = False
    # Contact fields need an approved trusted-source policy before apply.
    requires_trusted_source_policy: bool = False
    # Indivisible group: only applied after canonical conciliation.
    dependency_group: str | None = None


@dataclass(frozen=True)
class FieldMappingPolicy:
    version: str
    specs: tuple[FieldSpec, ...]

    def spec_for(self, field_key: str) -> FieldSpec | None:
        for spec in self.specs:
            if spec.field_key == field_key:
                return spec
        return None


MUNICIPALITY_GROUP = "municipality"

CNPJ_SA2_MAPPING_V1 = FieldMappingPolicy(
    version=MAPPING_VERSION_V1,
    specs=(
        FieldSpec(
            field_key="tax_id",
            section_key="identification",
            sa2_field="A2_CGC",
            field_class=FieldClass.PROTECTED,
            source_field="company.tax_id",
            max_length=14,
            normalizer=Normalizer.DIGITS,
        ),
        FieldSpec(
            field_key="supplier_name",
            section_key="identification",
            sa2_field="A2_NOME",
            field_class=FieldClass.COMPARABLE,
            source_field="company.legal_name",
            max_length=50,
        ),
        FieldSpec(
            field_key="supplier_short_name",
            section_key="identification",
            sa2_field="A2_NREDUZ",
            field_class=FieldClass.COMPARABLE,
            source_field="company.trade_name",
            max_length=20,
            requires_equivalence_rule=True,
        ),
        FieldSpec(
            field_key="address",
            section_key="address",
            sa2_field="A2_END",
            field_class=FieldClass.COMPARABLE,
            source_field="address.street",
            max_length=40,
        ),
        FieldSpec(
            field_key="district",
            section_key="address",
            sa2_field="A2_BAIRRO",
            field_class=FieldClass.COMPARABLE,
            source_field="address.district",
            max_length=20,
        ),
        FieldSpec(
            field_key="postal_code",
            section_key="address",
            sa2_field="A2_CEP",
            field_class=FieldClass.COMPARABLE,
            source_field="address.postal_code",
            max_length=8,
            normalizer=Normalizer.DIGITS,
        ),
        FieldSpec(
            field_key="state",
            section_key="address",
            sa2_field="A2_EST",
            field_class=FieldClass.COMPARABLE,
            source_field="address.state",
            max_length=2,
            normalizer=Normalizer.UF,
            dependency_group=MUNICIPALITY_GROUP,
        ),
        FieldSpec(
            field_key="city",
            section_key="address",
            sa2_field="A2_MUN",
            field_class=FieldClass.COMPARABLE,
            source_field="address.city",
            max_length=25,
            dependency_group=MUNICIPALITY_GROUP,
        ),
        FieldSpec(
            field_key="city_code",
            section_key="address",
            sa2_field="A2_COD_MUN",
            field_class=FieldClass.COMPARABLE,
            source_field="address.ibge_city_code",
            max_length=5,
            normalizer=Normalizer.DIGITS,
            dependency_group=MUNICIPALITY_GROUP,
        ),
        FieldSpec(
            field_key="area_code",
            section_key="contact",
            sa2_field="A2_DDD",
            field_class=FieldClass.COMPARABLE,
            source_field="contact.area_code",
            max_length=3,
            normalizer=Normalizer.DIGITS,
            requires_trusted_source_policy=True,
        ),
        FieldSpec(
            field_key="phone",
            section_key="contact",
            sa2_field="A2_TEL",
            field_class=FieldClass.COMPARABLE,
            source_field="contact.phone",
            max_length=50,
            normalizer=Normalizer.DIGITS,
            requires_trusted_source_policy=True,
        ),
        FieldSpec(
            field_key="email",
            section_key="contact",
            sa2_field="A2_EMAIL",
            field_class=FieldClass.COMPARABLE,
            source_field="contact.email",
            max_length=50,
            normalizer=Normalizer.EMAIL,
            requires_trusted_source_policy=True,
        ),
        FieldSpec(
            field_key="registration_status",
            section_key="information",
            sa2_field="",
            field_class=FieldClass.INFORMATION_ONLY,
            source_field="company.registration_status",
            max_length=None,
        ),
        FieldSpec(
            field_key="main_cnae",
            section_key="information",
            sa2_field="",
            field_class=FieldClass.INFORMATION_ONLY,
            source_field="company.main_cnae",
            max_length=None,
        ),
        FieldSpec(
            field_key="legal_nature",
            section_key="information",
            sa2_field="",
            field_class=FieldClass.INFORMATION_ONLY,
            source_field="company.legal_nature",
            max_length=None,
        ),
        FieldSpec(
            field_key="opening_date",
            section_key="information",
            sa2_field="",
            field_class=FieldClass.INFORMATION_ONLY,
            source_field="company.opening_date",
            max_length=None,
        ),
    ),
)
