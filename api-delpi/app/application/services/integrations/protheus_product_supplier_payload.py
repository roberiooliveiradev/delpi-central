"""Normalize SA5 product-supplier fields and build the delpiprodforn body.

Upstream contract (DLP04I02.PRW — MATA061 MVC headless): flat A5_* JSON.
Identity is the full model key (A5_PRODUTO + FORNECE/LOJA/FABR/FALOJA +
REFGRD); FABR/FALOJA/REFGRD may be empty strings (real records leave them
blank) but must be present. Editable attrs = the full SX3 catalog minus
identity/protected (PRODUCT_SUPPLIER_FIELD_SPECS, 113 campos) — the
upstream model validates field presence in the MdGridSA5 form.

A5_FILIAL never comes from the client — Protheus derives via xFilial.
`codusr` never comes from the client — resolved via Core, travels as
meta-field for AIF_ZCDUSR/ledger audit.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from app.application.services.integrations.protheus_product_supplier_field_catalog import (
    PRODUCT_SUPPLIER_FIELD_SPECS,
    PRODUCT_SUPPLIER_IDENTITY_FIELDS,
    PRODUCT_SUPPLIER_PROTECTED_FIELDS,
)
from app.domain.integrations.protheus_rest import (
    ProtheusRestConfig,
    ProtheusRestError,
)

PRODUCT_SUPPLIER_BASE_PATH = "delpiprodforn/v1/ProdForn"

# Identity keys the client supplies under `supplier` (A5_PRODUTO comes
# from the path; A5_FILIAL is derived upstream).
_CLIENT_IDENTITY = ("A5_FORNECE", "A5_LOJA", "A5_FABR", "A5_FALOJA", "A5_REFGRD")
# Identity members that must carry a non-empty value.
_REQUIRED_NONEMPTY = ("A5_FORNECE", "A5_LOJA")

_FORBIDDEN_KEYS = frozenset(
    {
        "a5_filial",
        "a5_produto",
        "codusr",
        "user_id",
        "usr_id",
        "protheus_user_id",
    }
)


def _err(message: str, code: str, status: int = 422) -> ProtheusRestError:
    return ProtheusRestError(message, code=code, status_code=status, recoverable=False)


def product_supplier_url(config: ProtheusRestConfig, method: str) -> str:
    """Full URL of a delpiprodforn method (same /delpi/ marker derivation)."""
    base = config.suppliers_base_url.rstrip("/")
    marker = "/delpi/"
    idx = base.find(marker)
    if idx == -1:
        raise ProtheusRestError(
            "Não foi possível derivar a rota de produto-fornecedor a "
            "partir da configuração Protheus resolvida.",
            code="PROTHEUS_CONFIG_INVALID",
            status_code=503,
        )
    return f"{base[:idx]}/{PRODUCT_SUPPLIER_BASE_PATH}/{method}"


def normalize_product_supplier_identity(raw: Mapping[str, Any] | None) -> dict[str, str]:
    """Full link identity: all five keys present, FORNECE/LOJA non-empty.

    FABR/FALOJA/REFGRD must be present and string-typed but may be "" —
    real links leave manufacturer/grade fields blank (proven TST01).
    """
    if raw is None or isinstance(raw, list) or not isinstance(raw, Mapping):
        raise _err(
            "Campo supplier deve ser um objeto JSON com a identidade do "
            "vínculo (fornecedor, loja, fabricante, loja fabricante, "
            "referência de grade).",
            "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
        )

    lowered = {str(k).strip().lower() for k in raw}
    if _FORBIDDEN_KEYS & lowered:
        raise _err(
            "Filial, produto e identidade do usuário não podem ser "
            "enviados pelo cliente.",
            "PROTHEUS_IDENTITY_CLIENT_FORBIDDEN",
        )

    upper = {str(k).strip().upper(): k for k in raw}
    identity: dict[str, str] = {}
    missing: list[str] = []
    for field in _CLIENT_IDENTITY:
        key = upper.get(field)
        if key is None:
            missing.append(field)
            continue
        value = raw[key]
        if not isinstance(value, str):
            raise _err(
                f"Campo {field} deve ser texto.",
                "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
            )
        text = value.strip()
        if field in _REQUIRED_NONEMPTY and not text:
            raise _err(
                f"Campo {field} é obrigatório e não pode ser vazio.",
                "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
            )
        spec = PRODUCT_SUPPLIER_FIELD_SPECS.get(field)
        if spec is not None and len(text) > int(spec["max_length"]):
            raise _err(
                f"Campo {field} excede {spec['max_length']} caracteres.",
                "PROTHEUS_PRODUCT_SUPPLIER_FIELD_TOO_LONG",
            )
        identity[field] = text
    if missing:
        raise _err(
            "Identidade do vínculo incompleta — faltam: "
            + ", ".join(missing)
            + ".",
            "PROTHEUS_PRODUCT_SUPPLIER_IDENTITY_INCOMPLETE",
        )
    return identity


def _normalize_attr_value(field: str, value: Any) -> str:
    if isinstance(value, bool):
        raise _err(
            f"Campo {field} deve ser texto, número ou data, não booleano.",
            "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
        )
    if value is None:
        raise _err(
            f"Campo {field} não pode ser nulo — omita o campo.",
            "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
        )

    kind = str(PRODUCT_SUPPLIER_FIELD_SPECS[field]["kind"])
    max_length = int(PRODUCT_SUPPLIER_FIELD_SPECS[field]["max_length"])

    if isinstance(value, (int, float)):
        if kind != "N":
            raise _err(
                f"Campo {field} é caractere/data — envie texto.",
                "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
            )
        text = str(value)
    elif isinstance(value, str):
        text = value
    else:
        raise _err(
            f"Campo {field} deve ser texto ou número.",
            "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
        )

    normalized = text.strip()

    if kind == "N":
        if not normalized:
            raise _err(
                f"Campo {field} é numérico — envie um valor (ex.: 0).",
                "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
            )
        if not re.fullmatch(r"[+-]?\d+(\.\d+)?", normalized):
            raise _err(
                f"Campo {field} deve ser numérico (ex.: 12.5, -3, 0).",
                "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
            )
    if kind == "D" and normalized:
        if not re.fullmatch(r"\d{8}", normalized):
            raise _err(
                f"Campo {field} deve ser data AAAAMMDD (8 dígitos).",
                "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
            )
    if len(normalized) > max_length:
        raise _err(
            f"Campo {field} excede {max_length} caracteres.",
            "PROTHEUS_PRODUCT_SUPPLIER_FIELD_TOO_LONG",
        )
    return normalized


def normalize_product_supplier_attrs(
    raw: Mapping[str, Any] | None, *, require_all: bool = False
) -> dict[str, str]:
    """Editable attrs: subset of the full SA5 catalog (update) or all
    SX3-required attrs (create). Values may be "" for character fields —
    the upstream model omits empty SetValue (FWWHEN guard).
    """
    if raw is None or isinstance(raw, list) or not isinstance(raw, Mapping):
        raise _err(
            "Campo attributes deve ser um objeto JSON com os campos do vínculo.",
            "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
        )

    lowered = {str(k).strip().lower() for k in raw}
    if _FORBIDDEN_KEYS & lowered:
        raise _err(
            "Filial, produto e identidade do usuário não podem ser "
            "enviados pelo cliente.",
            "PROTHEUS_IDENTITY_CLIENT_FORBIDDEN",
        )

    protected = [str(k) for k in raw if str(k).strip().upper() in PRODUCT_SUPPLIER_PROTECTED_FIELDS]
    if protected:
        raise _err(
            "Campos protegidos (gerenciados pelo ERP) não podem ser "
            "enviados: " + ", ".join(sorted(protected)[:10]) + ".",
            "PROTHEUS_PRODUCT_SUPPLIER_FIELD_PROTECTED",
        )
    identity_keys = [str(k) for k in raw if str(k).strip().upper() in PRODUCT_SUPPLIER_IDENTITY_FIELDS]
    if identity_keys:
        raise _err(
            "Campos de identidade devem ir no objeto supplier, não em "
            "attributes: " + ", ".join(sorted(identity_keys)) + ".",
            "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
        )

    upper_raw = {str(k).strip().upper(): v for k, v in raw.items()}
    unknown = [k for k in upper_raw if k not in PRODUCT_SUPPLIER_FIELD_SPECS]
    if unknown:
        raise _err(
            "Campos não reconhecidos no catálogo elegível de vínculo: "
            + ", ".join(sorted(unknown)[:10])
            + ".",
            "PROTHEUS_PRODUCT_SUPPLIER_FIELD_UNKNOWN",
        )

    attrs = {k: _normalize_attr_value(k, v) for k, v in upper_raw.items()}

    if require_all:
        required = ("A5_NOMEFOR", "A5_CODPRF", "A5_DESCPRF")
        missing = [f for f in required if not attrs.get(f)]
        if missing:
            raise _err(
                "Campos obrigatórios SX3 para criação do vínculo ausentes "
                "ou vazios: " + ", ".join(missing) + ".",
                "PROTHEUS_PRODUCT_SUPPLIER_REQUIRED_FIELDS",
            )
    elif not attrs:
        raise _err(
            "Informe ao menos um campo elegível para alterar.",
            "PROTHEUS_PRODUCT_SUPPLIER_PAYLOAD_INVALID",
        )
    return attrs


def build_upstream_product_supplier_body(
    *,
    product_code: str,
    identity: Mapping[str, str],
    attrs: Mapping[str, str] | None = None,
    codusr: str | None = None,
) -> dict[str, Any]:
    """Flat A5_* object — delpiprodforn reads the full model key."""
    body: dict[str, Any] = {"A5_PRODUTO": product_code}
    body.update(identity)
    if attrs:
        body.update(attrs)
    if codusr:
        body["codusr"] = codusr
    return body


def snapshot_value_matches(field: str, current: Any, expected: str) -> bool:
    """Persisted SA5 value vs sent intent — same semantics as SB1."""
    spec = PRODUCT_SUPPLIER_FIELD_SPECS.get(field)
    kind = str(spec["kind"]) if spec else "C"
    if kind == "N":
        try:
            lhs = Decimal(expected or "0")
            rhs = Decimal(str(current).strip() or "0")
            return lhs == rhs
        except (InvalidOperation, TypeError, ValueError):
            return False
    if current is None:
        return expected == ""
    return str(current).rstrip() == expected
