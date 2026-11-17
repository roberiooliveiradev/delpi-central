"""Normalize PUT product fields and build the delpiproduto upstream body.

Upstream contract (source: docs/13-fontes-totvs-protheus/04. Estoque/
DLP04I01.PRW — WSMETHOD PUT incProd): the custom REST class reads a flat
JSON object and unconditionally maps ALL 22 B1_* keys into an array for
MATA010 in altera mode (MSExecAuto op 4). Missing keys crash upstream
(VAL() on nil → "expected C->U") and empty values overwrite the record —
so this surface is a FULL-REPRESENTATION PUT, never a partial update.

B1_COD identifies the record and comes from the URL path — the client sends
the remaining 21 fields as a complete snapshot (read current state first).
The class has no codusr field: user attribution lives in our integration
tracking ledger.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from app.domain.integrations.protheus_rest import (
    ProtheusRestConfig,
    ProtheusRestError,
)

PRODUCT_CODE_PATTERN = r"^[A-Za-z0-9]{1,15}$"
PRODUCT_UPDATE_PATH = "delpiproduto/v1/IncProduto/alterar"

# Full field set consumed by the upstream handler (B1_COD excluded — it is
# the record key injected from the URL path). `numeric` marks columns the
# handler wraps in VAL(), which tolerate numeric strings.
PRODUCT_FIELD_SPECS: dict[str, dict[str, Any]] = {
    "B1_GRUPO": {"max_length": 4},
    "B1_DESC": {"max_length": 100},
    "B1_REFEREN": {"max_length": 60},
    "B1_REFCANT": {"max_length": 60},
    "B1_CODDES": {"max_length": 30},
    "B1_TIPO": {"max_length": 2},
    "B1_YHOHS": {"max_length": 1},
    "B1_POSIPI": {"max_length": 10},
    "B1_LOCPAD": {"max_length": 15},
    "B1_UM": {"max_length": 2},
    "B1_SEGUM": {"max_length": 2},
    "B1_TE": {"max_length": 15},
    "B1_TS": {"max_length": 15},
    "B1_PICMRET": {"max_length": 15, "numeric": True},
    "B1_CONV": {"max_length": 15, "numeric": True},
    "B1_TIPCONV": {"max_length": 1},
    "B1_TPMAT": {"max_length": 15},
    "B1_ESPECIE": {"max_length": 10},
    "B1_EX_NCM": {"max_length": 2},
    "B1_EX_NBM": {"max_length": 2},
    "B1_ORIGEM": {"max_length": 1},
}

# Reserved identity fields — never accepted from the client (lowercased).
_FORBIDDEN_KEYS = frozenset(
    {
        "b1_cod",
        "codusr",
        "user_id",
        "usr_id",
        "protheus_user_id",
    }
)


def validate_product_code(product_code: str) -> str:
    normalized = str(product_code or "").strip()
    if not re.fullmatch(PRODUCT_CODE_PATTERN, normalized):
        raise ProtheusRestError(
            "Identificador de produto inválido. Informe de 1 a 15 caracteres "
            "alfanuméricos (B1_COD).",
            code="PROTHEUS_PRODUCT_ID_INVALID",
            status_code=422,
            recoverable=False,
        )
    return normalized


def product_update_url(config: ProtheusRestConfig) -> str:
    """Full URL of the delpiproduto alterar method.

    Derived from the resolved suppliers path: the URI root shared by every
    custom class (`/restall` on production, `/rest` on the TST server) is
    the prefix of suppliers_path before the ``/delpi/`` class segment.
    Fails closed when the marker is absent — never guess a write target.
    """
    base = config.suppliers_base_url.rstrip("/")
    marker = "/delpi/"
    idx = base.find(marker)
    if idx == -1:
        raise ProtheusRestError(
            "Não foi possível derivar a rota de produto a partir da "
            "configuração Protheus resolvida.",
            code="PROTHEUS_CONFIG_INVALID",
            status_code=503,
        )
    return f"{base[:idx]}/{PRODUCT_UPDATE_PATH}"


def _normalize_value(field: str, value: Any) -> str:
    if isinstance(value, bool):
        raise ProtheusRestError(
            f"Campo {field} deve ser texto ou número, não booleano.",
            code="PROTHEUS_PRODUCT_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    if value is None:
        raise ProtheusRestError(
            f"Campo {field} não pode ser nulo — envie o valor atual "
            "(string vazia é aceita quando o campo está vazio no cadastro).",
            code="PROTHEUS_PRODUCT_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    if isinstance(value, (int, float)):
        text = str(value)
    elif isinstance(value, str):
        text = value
    else:
        raise ProtheusRestError(
            f"Campo {field} deve ser texto ou número.",
            code="PROTHEUS_PRODUCT_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )
    normalized = text.strip()
    max_length = int(PRODUCT_FIELD_SPECS[field]["max_length"])
    if len(normalized) > max_length:
        raise ProtheusRestError(
            f"Campo {field} excede {max_length} caracteres.",
            code="PROTHEUS_PRODUCT_FIELD_TOO_LONG",
            status_code=422,
            recoverable=False,
        )
    if PRODUCT_FIELD_SPECS[field].get("numeric") and normalized:
        try:
            float(normalized)
        except ValueError:
            raise ProtheusRestError(
                f"Campo {field} deve ser numérico.",
                code="PROTHEUS_PRODUCT_PAYLOAD_INVALID",
                status_code=422,
                recoverable=False,
            ) from None
    return normalized


def normalize_product_update_fields(raw: Mapping[str, Any] | None) -> dict[str, str]:
    """Full-representation contract: all 21 client fields must be present.

    Upstream maps every key unconditionally — a partial body would blank
    unspecified columns on the product record. Empty string is a valid
    value (it mirrors the current record); null is rejected as ambiguous.
    """
    if raw is None or isinstance(raw, list) or not isinstance(raw, Mapping):
        raise ProtheusRestError(
            "Campo product deve ser um objeto JSON com a representação "
            "completa dos campos do produto.",
            code="PROTHEUS_PRODUCT_PAYLOAD_INVALID",
            status_code=422,
            recoverable=False,
        )

    lowered_keys = {str(k).strip().lower() for k in raw}
    forbidden = _FORBIDDEN_KEYS & lowered_keys
    if forbidden:
        raise ProtheusRestError(
            "Identidade do produto ou do usuário não pode ser enviada nesta rota.",
            code="PROTHEUS_IDENTITY_CLIENT_FORBIDDEN",
            status_code=422,
            recoverable=False,
        )

    unknown = [str(k) for k in raw.keys() if str(k) not in PRODUCT_FIELD_SPECS]
    if unknown:
        raise ProtheusRestError(
            "Campos não reconhecidos no contrato de produto: "
            + ", ".join(sorted(unknown)[:10])
            + ".",
            code="PROTHEUS_PRODUCT_FIELD_UNKNOWN",
            status_code=422,
            recoverable=False,
        )

    missing = [field for field in PRODUCT_FIELD_SPECS if field not in raw]
    if missing:
        raise ProtheusRestError(
            "A alteração de produto exige a representação completa — "
            "campos ausentes: "
            + ", ".join(sorted(missing))
            + ". Leia o cadastro atual e reenvie todos os campos.",
            code="PROTHEUS_PRODUCT_FULL_REPRESENTATION_REQUIRED",
            status_code=422,
            recoverable=False,
        )

    return {
        field: _normalize_value(field, raw[field]) for field in PRODUCT_FIELD_SPECS
    }


def build_upstream_product_update_body(
    *, product_code: str, fields: Mapping[str, str]
) -> dict[str, Any]:
    """Flat B1_* object — delpiproduto reads B1_COD to locate the record."""
    body: dict[str, Any] = {"B1_COD": product_code}
    body.update(fields)
    return body
