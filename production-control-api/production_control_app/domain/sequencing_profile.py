"""Perfil de sequenciamento por centro de trabalho (Regras de Sequenciamento — E1).

Fundação administrativa: modela e valida os critérios tipados que, em etapas
futuras, o motor de carga máquina consumirá. Nesta etapa o perfil é apenas
configuração persistida — criar/editar/vincular um perfil NÃO altera a fila
WORKING/PUBLISHED nem o motor atual (`machine_load_optimization.py`).

Regras de integridade do domínio:

* ``pa_due_date`` é obrigatório e sempre o primeiro critério — a entrega do PA
  continua sendo a prioridade soberana, como no motor vigente;
* tipos de critério desconhecidos ou duplicados são rejeitados;
* a ordem da lista é a precedência; a fila atual permanece desempate estável
  (regra do motor, não do perfil);
* parâmetros de ``material_code`` são tipados e fechados — nada de expressões
  arbitrárias nem código executável informado pelo usuário.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from production_control_app.domain.errors import SequencingProfileInvalid

# Tipos de critério conhecidos pelo domínio. Novos critérios entram aqui e no
# motor — nunca como string livre vinda do cliente.
CRITERION_PA_DUE_DATE = "pa_due_date"
CRITERION_TOOL_GROUP = "tool_group"
CRITERION_MATERIAL_CODE = "material_code"
CRITERION_TYPES: frozenset[str] = frozenset(
    {CRITERION_PA_DUE_DATE, CRITERION_TOOL_GROUP, CRITERION_MATERIAL_CODE}
)

PROFILE_STATUS_DRAFT = "draft"
PROFILE_STATUS_ACTIVE = "active"
PROFILE_STATUS_ARCHIVED = "archived"
PROFILE_STATUSES: frozenset[str] = frozenset(
    {PROFILE_STATUS_DRAFT, PROFILE_STATUS_ACTIVE, PROFILE_STATUS_ARCHIVED}
)

# Fonte de identificação do material: empenho da operação primeiro,
# fallback para os empenhos da OP. Única fonte tipada desta etapa.
MATERIAL_SOURCE_OPERATION_THEN_ORDER = "operation_then_order"
MATERIAL_SOURCES: frozenset[str] = frozenset({MATERIAL_SOURCE_OPERATION_THEN_ORDER})

# Tipos de material elegíveis — hoje só MP faz sentido para cabo.
MATERIAL_TYPE_MP = "MP"
MATERIAL_TYPES: frozenset[str] = frozenset({MATERIAL_TYPE_MP})

# Tratamento de material ausente/ambíguo: sinalizar — nunca escolher
# arbitrariamente entre vários códigos elegíveis.
MATERIAL_POLICY_FLAG = "flag"
MATERIAL_POLICIES: frozenset[str] = frozenset({MATERIAL_POLICY_FLAG})

_MAX_CRITERIA = 8
_MAX_GROUPS = 64


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _validate_material_params(params: Any) -> dict[str, Any]:
    if not isinstance(params, dict):
        raise SequencingProfileInvalid(
            "Critério material_code exige o objeto params."
        )
    allowed = {
        "material_type",
        "eligible_product_groups",
        "identity_source",
        "ignore_zeroed_allocations",
        "on_missing",
        "on_ambiguous",
    }
    unknown = set(params) - allowed
    if unknown:
        raise SequencingProfileInvalid(
            f"Parâmetros desconhecidos em material_code: {sorted(unknown)}."
        )

    material_type = str(params.get("material_type") or MATERIAL_TYPE_MP).strip().upper()
    if material_type not in MATERIAL_TYPES:
        raise SequencingProfileInvalid(
            f"Tipo de material inválido: {material_type}. Use {sorted(MATERIAL_TYPES)}."
        )

    groups = params.get("eligible_product_groups")
    if not isinstance(groups, list) or not groups:
        raise SequencingProfileInvalid(
            "material_code exige eligible_product_groups não vazio."
        )
    if len(groups) > _MAX_GROUPS:
        raise SequencingProfileInvalid(
            f"eligible_product_groups excede o limite de {_MAX_GROUPS}."
        )
    normalized_groups: list[str] = []
    for group in groups:
        code = str(group or "").strip()
        if not code or not code.isdigit() or len(code) > 10:
            raise SequencingProfileInvalid(
                f"Grupo de produto inválido em material_code: {group!r}."
            )
        normalized_groups.append(code)
    if len(set(normalized_groups)) != len(normalized_groups):
        raise SequencingProfileInvalid("eligible_product_groups contém grupos duplicados.")

    identity_source = str(
        params.get("identity_source") or MATERIAL_SOURCE_OPERATION_THEN_ORDER
    ).strip()
    if identity_source not in MATERIAL_SOURCES:
        raise SequencingProfileInvalid(
            f"Fonte de identificação inválida: {identity_source}."
        )

    ignore_zeroed = params.get("ignore_zeroed_allocations", True)
    if not _is_bool(ignore_zeroed):
        raise SequencingProfileInvalid(
            "ignore_zeroed_allocations deve ser booleano."
        )

    on_missing = str(params.get("on_missing") or MATERIAL_POLICY_FLAG).strip()
    on_ambiguous = str(params.get("on_ambiguous") or MATERIAL_POLICY_FLAG).strip()
    if on_missing not in MATERIAL_POLICIES:
        raise SequencingProfileInvalid(
            f"Política on_missing inválida: {on_missing}."
        )
    if on_ambiguous not in MATERIAL_POLICIES:
        raise SequencingProfileInvalid(
            f"Política on_ambiguous inválida: {on_ambiguous}."
        )

    return {
        "material_type": material_type,
        "eligible_product_groups": normalized_groups,
        "identity_source": identity_source,
        "ignore_zeroed_allocations": ignore_zeroed,
        "on_missing": on_missing,
        "on_ambiguous": on_ambiguous,
    }


def _validate_empty_params(criterion_type: str, params: Any) -> dict[str, Any]:
    if params is None:
        return {}
    if not isinstance(params, dict) or params:
        raise SequencingProfileInvalid(
            f"Critério {criterion_type} não aceita parâmetros."
        )
    return {}


def validate_criteria(criteria: Any) -> list[dict[str, Any]]:
    """Valida e normaliza a lista ordenada de critérios de um perfil.

    Retorna a lista normalizada (params tipados). A posição na lista é a
    precedência — índice 0 é o critério soberano.
    """
    if not isinstance(criteria, list) or not criteria:
        raise SequencingProfileInvalid("O perfil exige ao menos um critério.")
    if len(criteria) > _MAX_CRITERIA:
        raise SequencingProfileInvalid(
            f"O perfil aceita no máximo {_MAX_CRITERIA} critérios."
        )

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(criteria):
        if not isinstance(item, dict):
            raise SequencingProfileInvalid(
                f"Critério #{index + 1} deve ser um objeto com type/params."
            )
        criterion_type = str(item.get("type") or "").strip()
        if criterion_type not in CRITERION_TYPES:
            raise SequencingProfileInvalid(
                f"Tipo de critério desconhecido: {criterion_type or '<vazio>'}. "
                f"Use {sorted(CRITERION_TYPES)}."
            )
        if criterion_type in seen:
            raise SequencingProfileInvalid(
                f"Critério duplicado: {criterion_type}."
            )
        seen.add(criterion_type)
        params = (
            _validate_material_params(item.get("params"))
            if criterion_type == CRITERION_MATERIAL_CODE
            else _validate_empty_params(criterion_type, item.get("params"))
        )
        normalized.append({"type": criterion_type, "params": params})

    # A entrega do PA é a prioridade obrigatória e soberana — primeiro lugar,
    # exatamente como o motor vigente aplica antes de qualquer agrupamento.
    if normalized[0]["type"] != CRITERION_PA_DUE_DATE:
        raise SequencingProfileInvalid(
            "O primeiro critério deve ser pa_due_date — a entrega do PA é "
            "a prioridade obrigatória."
        )
    return normalized


def validate_status(status: Any, *, allow_none: bool = False) -> str | None:
    if status is None and allow_none:
        return None
    value = str(status or "").strip()
    if value not in PROFILE_STATUSES:
        raise SequencingProfileInvalid(
            f"Status de perfil inválido: {value or '<vazio>'}. "
            f"Use {sorted(PROFILE_STATUSES)}."
        )
    return value


def validate_name(name: Any) -> str:
    value = str(name or "").strip()
    if not value or len(value) > 120:
        raise SequencingProfileInvalid(
            "Nome do perfil é obrigatório (máx. 120 caracteres)."
        )
    return value


@dataclass(frozen=True)
class SequencingProfile:
    id: UUID
    name: str
    description: str | None
    status: str
    revision: int
    criteria: list[dict[str, Any]] = field(default_factory=list)
    # Filial em que o perfil foi criado (V019) — compõe, junto às filiais
    # onde está vinculado, o conjunto de filiais autorizadas a editá-lo.
    # NULL apenas em linhas legadas anteriores à V019.
    origin_branch: str | None = None
    created_at: datetime | None = None
    created_by: str | None = None
    updated_at: datetime | None = None
    updated_by: str | None = None


@dataclass(frozen=True)
class SequencingProfileRevision:
    profile_id: UUID
    revision: int
    action: str
    snapshot: dict[str, Any]
    actor: str | None
    occurred_at: datetime | None = None


@dataclass(frozen=True)
class SequencingProfileBinding:
    branch: str
    work_center: str
    profile_id: UUID
    assigned_by: str | None
    assigned_at: datetime | None = None
