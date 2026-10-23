"""Normalize PUT supplier fields and build the upstream array body.

PUT allowlist (PO decision F3.3 + E5 homologation): the F3.3 cadastral
set plus the 26 fields that proved PUT persistence in DELPI_TST01
(X4.FIELDS.E5). EXCLUDED from PUT: fiscal document (tax_id), identity
(supplier_code/supplier_store) and the 3 E3 fields without proven
upstream PUT semantics (simp_regime_code, linked_customer_code,
linked_customer_store). The live-write gate PROTHEUS_SUPPLIER_UPDATE_ENABLED
stays OFF until productive activation is separately authorized.

Omitted keys are not sent (partial PUT). Explicit null/empty is rejected —
clear semantics remain TO_INVENTORY.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from app.application.services.integrations.protheus_supplier_create_payload import (
    SUPPLIER_FIELD_SPECS,
    normalize_supplier_field_value,
    validate_codusr,
)
from app.domain.integrations.protheus_rest import SUPPLIER_ID_PATTERN, ProtheusRestError

# Cadastral fields excluded from PUT: fiscal document (immutable here) and
# the store, which is part of the supplier identity (code+store).
_PUT_EXCLUDED = frozenset({"tax_id", "supplier_store"})

# PUT allowlist — explicit, evidence-based. The F3.3 cadastral set plus the
# 26 E3 fields that proved PUT persistence in the E5 controlled assay
# (DELPI_TST01 read-after-write, doc X4-FIELDS-E5-*), plus the E6 retest
# results: simp_regime_code and linked_customer_store are
# PUT_PERSISTENCE_PROVEN; linked_customer_code enters ONLY as the
# mandatory companion of the composite pair — upstream ignores code
# changes on PUT (6d verdict), so the use case pins it to the current
# value. NOT derived from the POST allowlist.
PUT_EDITABLE_FIELDS = frozenset(
    {
        "person_type",
        "supplier_name",
        "supplier_short_name",
        "address",
        "district",
        "postal_code",
        "state",
        "city",
        "city_code",
        "area_code",
        "phone",
        "state_registration",
        "municipal_registration",
        "contact_name",
        "email",
        "payment_condition_code",
        "country_code",
        "bacen_country_code",
        "accounting_account",
        "financial_nature_code",
        "rohs_indicator",
        "payment_method_code",
        # --- X4.FIELDS.E5 — PUT_PERSISTENCE_PROVEN em DELPI_TST01 ----------
        "address_number",
        "po_box",
        "commercial_contact_name",
        "fax",
        "website",
        "responsible_name",
        "icms_contributor",
        "simples_nacional",
        "inss_withholding",
        "iss_withholding",
        "csll_withholding",
        "cofins_withholding",
        "pis_withholding",
        "irf_calculation",
        "inp_calculation",
        "tax_group_code",
        "legal_entity_type",
        "pb_regime_code",
        "cnae_code",
        "risk_code",
        "swift_code",
        "purchase_price_table_code",
        "carrier_code",
        "segment_code",
        "administrator_code",
        "linked_employee_code",
        # --- X4.FIELDS.E6 — retestes 6a/6c/6d em DELPI_TST01 -----------------
        # simp_regime_code: PUT_PERSISTENCE_PROVEN (1→2, REST+SQL).
        # linked_customer_store: PUT_PERSISTENCE_PROVEN — mas somente quando o
        #   par (código+loja) viaja junto; loja sozinha é ignorada upstream.
        # linked_customer_code: NÃO é alterável via PUT (upstream ignora o
        #   valor novo no par — veredito PUT_IGNORED em 6d). Entra na allowlist
        #   apenas como COMPANION obrigatório do par composto; o use case
        #   garante que o código enviado == código atual (rejeita divergência).
        "simp_regime_code",
        "linked_customer_code",
        "linked_customer_store",
    }
)

_UPDATE_SPECS: dict[str, dict[str, Any]] = {
    field: SUPPLIER_FIELD_SPECS[field] for field in PUT_EDITABLE_FIELDS
}

# Fields that identify the supplier record or the ERP context — never writable.
_IMMUTABLE_FIELDS = frozenset(
    {
        "tax_id",
        "supplier_code",
        "supplier_store",
        "a2_cod",
        "a2_loja",
        "a2_filial",
    }
)

_FORBIDDEN_IDENTITY = frozenset(
    {"codusr", "user_id", "usr_id", "protheus_user_id", "supplier_id"}
)


def validate_supplier_id(supplier_id: str) -> str:
    normalized = str(supplier_id or "").strip()
    if not re.fullmatch(SUPPLIER_ID_PATTERN, normalized):
        raise ProtheusRestError(
            "Identificador de fornecedor inválido. Informe exatamente 8 dígitos "
            "(6 do código + 2 da loja).",
            code="PROTHEUS_SUPPLIER_ID_INVALID",
            status_code=422,
            recoverable=False,
        )
    return normalized


def normalize_supplier_update_fields(raw: Mapping[str, Any] | None) -> dict[str, str]:
    if isinstance(raw, list):
        raise ProtheusRestError(
            "A API DELPI recebe fornecedor como objeto; o array é montado no backend.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    if raw is None or not isinstance(raw, Mapping):
        raise ProtheusRestError(
            "Campo fornecedor deve ser um objeto JSON com os campos a alterar.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )

    lowered_keys = {str(k).strip().lower(): k for k in raw}
    forbidden = _FORBIDDEN_IDENTITY & lowered_keys.keys()
    if forbidden:
        raise ProtheusRestError(
            "Identidade do fornecedor ou do usuário não pode ser alterada nesta rota.",
            code="PROTHEUS_IDENTITY_CLIENT_FORBIDDEN",
            status_code=422,
            recoverable=False,
        )
    immutable = _IMMUTABLE_FIELDS & lowered_keys.keys()
    if immutable:
        raise ProtheusRestError(
            "Campo protegido da identidade cadastral não é editável: "
            + ", ".join(sorted(immutable))
            + ".",
            code="PROTHEUS_SUPPLIER_FIELD_IMMUTABLE",
            status_code=422,
            recoverable=False,
        )

    unknown = [str(k) for k in raw.keys() if str(k) not in _UPDATE_SPECS]
    if unknown:
        raise ProtheusRestError(
            "Campos não comprovados para alteração: "
            + ", ".join(sorted(unknown)[:10])
            + ".",
            code="PROTHEUS_SUPPLIER_FIELD_NOT_EDITABLE",
            status_code=422,
            recoverable=False,
        )

    out: dict[str, str] = {}
    for field in _UPDATE_SPECS:
        if field not in raw:
            continue
        value = raw[field]
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise ProtheusRestError(
                f"Limpeza explícita de {field} não está homologada. Omita o campo para preservá-lo.",
                code="PROTHEUS_SUPPLIER_CLEAR_NOT_SUPPORTED",
                status_code=422,
                recoverable=False,
            )
        out[field] = normalize_supplier_field_value(field, value)

    # Composite pair (E6): upstream requires code+store together and the
    # code alone is rejected (400) — reject it here with a clear error.
    if "linked_customer_code" in out and "linked_customer_store" not in out:
        raise ProtheusRestError(
            "linked_customer_code não é alterável isoladamente — "
            "o vínculo exige o par código+loja.",
            code="PROTHEUS_SUPPLIER_LINKED_PAIR_REQUIRED",
            status_code=422,
            recoverable=False,
        )

    # Conditional (SX3 WHEN): cnae_code only applies to person_type J/X —
    # enforceable here only when both keys arrive in the same partial PUT;
    # otherwise the upstream contract owns the check.
    if (
        out.get("cnae_code")
        and out.get("person_type") == "F"
    ):
        raise ProtheusRestError(
            "Campo cnae_code não se aplica a pessoa física (person_type=F).",
            code="PROTHEUS_SUPPLIER_FIELD_CONDITIONAL",
            status_code=422,
            recoverable=False,
        )

    if not out:
        raise ProtheusRestError(
            "Informe ao menos um campo comprovado para alteração.",
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    return out


def build_upstream_update_body(*, codusr: str, fields: Mapping[str, str]) -> dict[str, Any]:
    # Live evidence (F4, fornecedor 002469/01): upstream accepts `fornecedor`
    # as an OBJECT — the array form documented in the external contract
    # returns HTTP 500 for every payload (incl. non-existent IDs).
    return {
        "codusr": validate_codusr(codusr),
        "fornecedor": dict(fields),
    }
