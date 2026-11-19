"""Normalize PUT product fields and build the delpiproduto upstream body.

Upstream contract v2 (DLP04I01.PRW — full-field catalog, 283 campos): a
classe lê um JSON flat e mapeia cada chave B1_* validada para o array
ExecAuto da MATA010 (op 4). PUT exige representação completa upstream —
a atualização parcial do cliente é expandida aqui via snapshot do
cadastro atual (read-merge-write), nunca reenviando apenas o delta.

Campos aceitos do cliente: qualquer subconjunto do catálogo elegível
(`PRODUCT_FIELD_SPECS`, gerado de contracts/sb1-field-matrix.json —
SX3 TST01==PROD). Campos protegidos/sistema/imutáveis são rejeitados.
B1_COD identifica o registro e vem do path — nunca do body. `codusr`
nunca é aceito do cliente: o ator real é resolvido via Core (sub do JWT)
e viaja no body upstream para auditoria `AIF_ZCDUSR` — além do ledger.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from app.application.services.integrations.protheus_product_field_catalog import (
    PRODUCT_FIELD_SPECS,
    PRODUCT_PROTECTED_FIELDS,
)
from app.domain.integrations.protheus_rest import (
    ProtheusRestConfig,
    ProtheusRestError,
)

PRODUCT_CODE_PATTERN = r"^[A-Za-z0-9]{1,15}$"
PRODUCT_UPDATE_PATH = "delpiproduto/v1/IncProduto/alterar"
PRODUCT_CREATE_PATH = "delpiproduto/v1/IncProduto/incluir"

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


def product_create_url(config: ProtheusRestConfig) -> str:
    """Full URL of the delpiproduto incluir method (same derivation)."""
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
    return f"{base[:idx]}/{PRODUCT_CREATE_PATH}"


def _err(message: str, code: str) -> ProtheusRestError:
    return ProtheusRestError(
        message, code=code, status_code=422, recoverable=False
    )


def _normalize_value(field: str, value: Any) -> str:
    """Normaliza um valor do cliente conforme a espécie SX3 (kind)."""
    if isinstance(value, bool):
        raise _err(
            f"Campo {field} deve ser texto, número ou data, não booleano.",
            "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
        )
    if value is None:
        raise _err(
            f"Campo {field} não pode ser nulo — omita o campo ou envie o "
            "valor desejado (ausência preserva o valor atual no merge).",
            "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
        )

    kind = str(PRODUCT_FIELD_SPECS[field]["kind"])
    max_length = int(PRODUCT_FIELD_SPECS[field]["max_length"])

    if isinstance(value, (int, float)):
        if kind != "N":
            raise _err(
                f"Campo {field} é caractere/data — envie texto.",
                "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
            )
        text = str(value)
    elif isinstance(value, str):
        text = value
    else:
        raise _err(
            f"Campo {field} deve ser texto ou número.",
            "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
        )

    normalized = text.strip()

    if kind == "N":
        if not normalized:
            raise _err(
                f"Campo {field} é numérico — envie um valor (ex.: 0), "
                "não texto vazio.",
                "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
            )
        # Mesma regra estrita do upstream (lIsNumStr): sinal só na
        # primeira posição, dígitos e no máximo um ponto — sem notação
        # científica, separador de milhar nem espaços internos.
        if not re.fullmatch(r"[+-]?\d+(\.\d+)?", normalized):
            raise _err(
                f"Campo {field} deve ser numérico (ex.: 12.5, -3, 0).",
                "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
            )
    if kind == "D" and normalized:
        if not re.fullmatch(r"\d{8}", normalized):
            raise _err(
                f"Campo {field} deve ser data AAAAMMDD (8 dígitos).",
                "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
            )
    if len(normalized) > max_length:
        raise _err(
            f"Campo {field} excede {max_length} caracteres.",
            "PROTHEUS_PRODUCT_FIELD_TOO_LONG",
        )
    return normalized


def normalize_product_update_fields(raw: Mapping[str, Any] | None) -> dict[str, str]:
    """Partial-update contract: cliente envia um SUBCONJUNTO de campos.

    Cada chave deve pertencer ao catálogo elegível; campo protegido ou
    desconhecido é rejeitado; null é rejeitado como ambíguo. A presença
    de ao menos um campo elegível é exigida — o merge com o snapshot
    atual acontece em seguida (nunca enviamos delta direto ao ExecAuto).
    """
    if raw is None or isinstance(raw, list) or not isinstance(raw, Mapping):
        raise _err(
            "Campo product deve ser um objeto JSON com os campos a alterar.",
            "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
        )
    if not raw:
        raise _err(
            "Informe ao menos um campo elegível para alterar.",
            "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
        )

    lowered_keys = {str(k).strip().lower() for k in raw}
    forbidden = _FORBIDDEN_KEYS & lowered_keys
    if forbidden:
        raise _err(
            "Identidade do produto ou do usuário não pode ser enviada nesta rota.",
            "PROTHEUS_IDENTITY_CLIENT_FORBIDDEN",
        )

    protected = [str(k) for k in raw.keys() if str(k) in PRODUCT_PROTECTED_FIELDS]
    if protected:
        raise _err(
            "Campos protegidos (imutáveis ou gerenciados pelo ERP) não "
            "podem ser alterados: " + ", ".join(sorted(protected)[:10]) + ".",
            "PROTHEUS_PRODUCT_FIELD_PROTECTED",
        )

    unknown = [str(k) for k in raw.keys() if str(k) not in PRODUCT_FIELD_SPECS]
    if unknown:
        raise _err(
            "Campos não reconhecidos no catálogo elegível de produto: "
            + ", ".join(sorted(unknown)[:10])
            + ". Consulte o contrato product.metadata.",
            "PROTHEUS_PRODUCT_FIELD_UNKNOWN",
        )

    return {str(k): _normalize_value(str(k), v) for k, v in raw.items()}


def _canonical_number(value: Any) -> str:
    """Número em texto simples — nunca notação científica (lIsNumStr).

    ``str(1e-7)``/``str(Decimal('1E-5'))`` produziriam expoente e seriam
    rejeitados no upstream. ``Decimal.normalize()`` remove zeros à direita
    da parte fracionária sem tocar em dígitos significativos; ``format(f)``
    expande o expoente sem truncar precisão (Decimal(10) → "10",
    Decimal("1E-7") → "0.0000001").
    """
    d = value if isinstance(value, Decimal) else Decimal(str(value))
    text = format(d.normalize(), "f")
    return text if text not in ("", "-0") else "0"


def snapshot_body_text(current: Any) -> str:
    """Serialização canônica de um valor lido da SB1 para o body upstream.

    Mesma forma que ``merge_product_update_fields`` produz — usada também
    no read-back para comparar intenção x persistido sem falsa divergência
    (``"5"`` enviado ≡ ``5.0`` gravado; ``"        "`` ≡ ``""``).
    """
    if current is None:
        return ""
    if isinstance(current, bool):
        # pyodbc nunca devolve bool p/ coluna numérica; guarda defensiva.
        return "1" if current else "0"
    if isinstance(current, (int, float, Decimal)):
        return _canonical_number(current)
    return str(current).rstrip()


def snapshot_value_matches(field: str, current: Any, expected: str) -> bool:
    """True quando o valor persistido na SB1 confere com a intenção enviada.

    Numéricos comparam por ``Decimal`` (``"5.50"`` enviado ≡ ``5.5``
    gravado); demais espécies comparam a serialização canônica do snapshot
    contra o texto enviado (``"        "`` ≡ ``""``; padding à direita
    ignorado).
    """
    if PRODUCT_FIELD_SPECS[field]["kind"] == "N":
        try:
            return Decimal(expected or "0") == Decimal(
                snapshot_body_text(current) or "0"
            )
        except (InvalidOperation, TypeError, ValueError):
            return False
    return snapshot_body_text(current) == expected


def merge_product_update_fields(
    *, snapshot: Mapping[str, Any], changes: Mapping[str, str]
) -> dict[str, str]:
    """Expande o delta do cliente na representação completa do catálogo.

    snapshot: linha atual da SB1 (todas as colunas elegíveis — vinda de
    ProductRepository.get_product_snapshot). Campos não alterados levam o
    valor atual do cadastro (RTRIM); campos alterados levam o valor
    normalizado do cliente. Ausência nunca vira vazio por omissão —
    somente se o cadastro atual estiver vazio.
    """
    merged: dict[str, str] = {}
    for field in PRODUCT_FIELD_SPECS:
        if field == "B1_COD":
            # Identidade vem do path/contrato governado — injetada por
            # build_upstream_product_update_body, nunca do snapshot/delta.
            continue
        if field in changes:
            merged[field] = changes[field]
            continue
        text = snapshot_body_text(snapshot.get(field))
        if PRODUCT_FIELD_SPECS[field]["kind"] == "N" and not text:
            # Numerico SB1 nunca e NULL no Protheus — ausencia persistida
            # equivale a 0; "" seria rejeitado pelo upstream (kind=N).
            text = "0"
        merged[field] = text
    return merged


def normalize_product_create_fields(raw: Mapping[str, Any] | None) -> tuple[str, dict[str, str]]:
    """Create contract: product object carries B1_COD + catalog fields.

    Unlike the update path, identity travels in the body (B1_COD required
    and validated); all remaining keys must belong to the eligible
    catalog minus B1_COD. No merge is possible — a create sends the
    fields the caller provides and the official routine applies its own
    defaults for the rest.
    """
    if raw is None or isinstance(raw, list) or not isinstance(raw, Mapping):
        raise _err(
            "Campo product deve ser um objeto JSON com B1_COD e os "
            "campos do novo produto.",
            "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
        )

    lowered = {str(k).strip().lower() for k in raw}
    forbidden = ({"codusr", "user_id", "usr_id", "protheus_user_id"} & lowered)
    if forbidden:
        raise _err(
            "Identidade do usuário não pode ser enviada nesta rota.",
            "PROTHEUS_IDENTITY_CLIENT_FORBIDDEN",
        )

    b1_key = next((k for k in raw if str(k).strip().upper() == "B1_COD"), None)
    if b1_key is None:
        raise _err(
            "B1_COD é obrigatório para criação de produto.",
            "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
        )
    code = validate_product_code(raw[b1_key])

    fields_raw = {str(k): v for k, v in raw.items() if k is not b1_key}
    if not fields_raw:
        raise _err(
            "Informe ao menos um campo elegível além de B1_COD.",
            "PROTHEUS_PRODUCT_PAYLOAD_INVALID",
        )
    protected = [k for k in fields_raw if k in PRODUCT_PROTECTED_FIELDS]
    if protected:
        raise _err(
            "Campos protegidos (gerenciados pelo ERP) não podem ser "
            "enviados: " + ", ".join(sorted(protected)[:10]) + ".",
            "PROTHEUS_PRODUCT_FIELD_PROTECTED",
        )
    unknown = [k for k in fields_raw if k not in PRODUCT_FIELD_SPECS]
    if unknown:
        raise _err(
            "Campos não reconhecidos no catálogo elegível de produto: "
            + ", ".join(sorted(unknown)[:10])
            + ". Consulte o contrato product.metadata.",
            "PROTHEUS_PRODUCT_FIELD_UNKNOWN",
        )
    return code, {k: _normalize_value(k, v) for k, v in fields_raw.items()}


def build_upstream_product_update_body(
    *, product_code: str, fields: Mapping[str, str], codusr: str | None = None
) -> dict[str, Any]:
    """Flat B1_* object — delpiproduto reads B1_COD to locate the record.

    `codusr` (ator real resolvido via Core) viaja como meta-campo fora do
    catálogo B1_* — o upstream grava em `AIF_ZCDUSR` para a auditoria não
    ficar cega (padrão Gabriel/MATA020; REST executa como usuário técnico).
    """
    body: dict[str, Any] = {"B1_COD": product_code}
    body.update(fields)
    if codusr:
        body["codusr"] = codusr
    return body
