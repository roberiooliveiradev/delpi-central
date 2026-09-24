"""Improvement package contract projection for GPT catalog + OpenAPI.

Owner of validation remains GuidedImprovementPackageService.
This module only documents the nesting/fields consumers must send —
it does not validate or normalize flat payloads.
"""

from __future__ import annotations

from typing import Any

from tm_app.core.catalogs import (
    BENEFICIO_CALCULO_CATEGORIA,
    BENEFICIO_CALCULO_CATEGORIA_DEFAULT,
    CENARIO_TIPO,
    RECORRENCIAS,
    TIPO_INVESTIMENTO,
)

# Nested keys under baseline / scenario (service reads these exact names).
PACKAGE_BLOCK_KEYS = ("revision", "measurement", "investments")

# Nested package envelope shared by validate + commit.
PACKAGE_CORE_KEYS = (
    "process",
    "instance",
    "baseline",
    "scenario",
)

# Top-level keys of gpt_commit_improvement_package (includes write flags).
PACKAGE_TOP_LEVEL_KEYS = (
    "dry_run",
    "activate_scenario",
    "recalculate",
    *PACKAGE_CORE_KEYS,
)

# Revision fields accepted inside package blocks (processo_id/instancia_id injected on create).
PACKAGE_REVISION_FIELDS = (
    "id",
    "revisao_id",
    "versao_revisao",
    "cenario_tipo",
    "data_inicio_vigencia",
    "revisao_ativa",
    "revisao_referencia_id",
    "beneficio_calculo_categoria",
    "descricao_revisao",
    "motivo_revisao",
    "data_implantacao",
    "data_fim_vigencia",
    "observacoes",
)

# Measurement fields inside package (revisao_id injected by service).
PACKAGE_MEASUREMENT_FIELDS = (
    "volume_mensal",
    "tempo_medio_execucao_min",
    "tempo_retrabalho_min",
    "percentual_retrabalho",
    "percentual_erro",
    "quantidade_erros_mes",
    "custo_hora_mao_obra",
    "custo_unitario_erro",
    "custo_unitario_retrabalho",
    "custo_outros_desperdicios",
    "base_referencia_mes",
    "observacoes",
)

# Required when creating a new revision block (reuse-by-id may omit).
PACKAGE_MEASUREMENT_REQUIRED_FIELDS = (
    "volume_mensal",
    "tempo_medio_execucao_min",
)

# Explicit null is meaningful (clear / open vigencia). Omitted key ≠ null.
PACKAGE_REVISION_NULLABLE_CLEARABLE = frozenset(
    {
        "data_fim_vigencia",
        "data_implantacao",
        "descricao_revisao",
        "motivo_revisao",
        "observacoes",
    }
)

# Investment item fields inside scenario.investments[] (revisao_id injected).
PACKAGE_INVESTMENT_FIELDS = (
    "tipo_investimento",
    "descricao_item",
    "quantidade",
    "valor_unitario",
    "recorrencia",
    "categoria_investimento",
    "data_investimento",
    "meses_vigencia",
    "centro_custo",
    "observacoes",
)

NESTING_RULES = [
    "Never put revision fields flat under scenario (e.g. scenario.versao_revisao).",
    "Always use scenario.revision.{fields} and baseline.revision.{fields}.",
    "Never put processo_id/instancia_id on scenario root; use process and instance.",
    "measurement belongs under baseline.measurement or scenario.measurement.",
    "New revision blocks REQUIRE measurement with volume_mensal + tempo_medio_execucao_min.",
    "data_fim_vigencia: omitted = leave unset/open; explicit null = clear (open vigencia); date = set. Never invent today.",
    "investments belongs only under scenario.investments (array; [] allowed).",
    "beneficio_calculo_categoria belongs on revision, not measurement.",
    "Flat package shapes are invalid: validate/dry_run returns ready=false with missing.",
    "Do not invent alternate dialetos; only this nested envelope is canonical.",
]

OPERATIONAL_SEQUENCE = [
    "READ CONTRACT (gpt_get_catalog.registration_guide.package_hints)",
    "RESOLVE IDs / CONTEXT (gpt_search_records / gpt_get_process_context)",
    "PREPARE nested package payload",
    "VALIDATE PACKAGE (gpt_validate_improvement_package) = PREPARE WORKFLOW",
    "REQUIRE ready=true (ready=false is checklist, not tool failure)",
    "SHOW USER the exact package / proposal",
    "EXPLICIT CONFIRMATION",
    "COMMIT (gpt_commit_proposal) — ACT stage; not gpt_commit_improvement_package",
    "AUTHORITATIVE READ-BACK / VERIFY (gpt_get_record / gpt_get_process_context)",
    "OPTIONAL RECALCULATE (recalculate flag bound in proposal; only after successful commit)",
]


def _reuse_existing_example() -> dict[str, Any]:
    return {
        "dry_run": True,
        "activate_scenario": False,
        "recalculate": False,
        "process": {"processo_id": "<uuid>"},
        "instance": {"instancia_id": "<uuid>"},
        "scenario": {
            "revision": {
                "revisao_referencia_id": "<uuid>",
                "versao_revisao": "2.1.0",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "YYYY-MM-DD",
                "data_implantacao": "YYYY-MM-DD",
                "descricao_revisao": "...",
                "motivo_revisao": "...",
                "beneficio_calculo_categoria": BENEFICIO_CALCULO_CATEGORIA_DEFAULT,
            },
            "measurement": {
                "volume_mensal": 0,
                "tempo_medio_execucao_min": 0,
                "percentual_retrabalho": 0,
                "percentual_erro": 0,
                "base_referencia_mes": "YYYY-MM",
            },
            "investments": [],
        },
    }


def _create_new_example() -> dict[str, Any]:
    return {
        "dry_run": True,
        "activate_scenario": False,
        "recalculate": False,
        "process": {
            "nome_processo": "Nome do processo",
            "status_processo": "ativo",
            "descricao_processo": "...",
        },
        "instance": {
            "filial_id": "01",
            "setor_ids": ["<setor_id_or_codigo>"],
            "resumo_melhoria": "...",
            "fase_melhoria": "planejado",
            "prioridade": "media",
        },
        "baseline": {
            "revision": {
                "versao_revisao": "1.0.0",
                "data_inicio_vigencia": "YYYY-MM-DD",
            },
            "measurement": {
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 30,
            },
        },
        "scenario": {
            "revision": {
                "versao_revisao": "2.0.0",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "YYYY-MM-DD",
                "beneficio_calculo_categoria": BENEFICIO_CALCULO_CATEGORIA_DEFAULT,
            },
            "measurement": {
                "volume_mensal": 100,
                "tempo_medio_execucao_min": 10,
            },
            "investments": [
                {
                    "tipo_investimento": "unico",
                    "descricao_item": "Licença",
                    "valor_unitario": 0,
                    "recorrencia": "unico",
                }
            ],
        },
    }


def _baseline_plus_scenario_example() -> dict[str, Any]:
    """Same package creates baseline then scenario; reference can be omitted on scenario."""
    example = _create_new_example()
    # Service injects revisao_referencia_id from baseline created in the same package.
    example["scenario"]["revision"].pop("revisao_referencia_id", None)
    return example


def build_package_hints() -> dict[str, Any]:
    """Structured package contract exposed via gpt_get_catalog."""
    return {
        "operationId": "gpt_validate_improvement_package",
        "validate_operationId": "gpt_validate_improvement_package",
        "commit_operationId": "gpt_commit_proposal",
        "prepare_then_commit": True,
        "dry_run_first": False,
        "process_context_operationId": "gpt_get_process_context",
        "compatibility": (
            "Legacy HTTP gpt_commit_improvement_package / dry_run remain "
            "LEGACY_TRANSITIONAL (include_in_schema=False). "
            "Specialists must use gpt_validate_improvement_package then gpt_commit_proposal."
        ),
        "canonical_package_shape": {
            "top_level": list(PACKAGE_TOP_LEVEL_KEYS),
            "validate_top_level": list(PACKAGE_CORE_KEYS),
            "commit_top_level": list(PACKAGE_TOP_LEVEL_KEYS),
            "process": "Reuse with {id|processo_id} OR create with nome_processo+status_processo (+optional fields).",
            "instance": (
                "Reuse with {id|instancia_id} OR create with setor_ids and "
                "filial_id|todas_filiais_ativas."
            ),
            "baseline": {
                "keys": ["revision", "measurement"],
                "notes": [
                    "Optional block. When present, revision.cenario_tipo is forced to baseline.",
                    "baseline.revision must NOT include revisao_referencia_id.",
                    "Creating a new baseline.revision REQUIRES baseline.measurement "
                    "(volume_mensal + tempo_medio_execucao_min).",
                ],
            },
            "scenario": {
                "keys": list(PACKAGE_BLOCK_KEYS),
                "notes": [
                    "Optional if baseline-only package.",
                    "When present, scenario.revision is REQUIRED (never flat fields).",
                    "cenario_tipo must be melhoria|automacao|correcao (not baseline).",
                    "revisao_referencia_id required unless baseline is created in same package.",
                    "Creating a new scenario.revision REQUIRES scenario.measurement "
                    "(volume_mensal + tempo_medio_execucao_min). investments may be [].",
                ],
            },
            "revision_fields": list(PACKAGE_REVISION_FIELDS),
            "measurement_fields": list(PACKAGE_MEASUREMENT_FIELDS),
            "measurement_required_fields": list(PACKAGE_MEASUREMENT_REQUIRED_FIELDS),
            "investment_fields": list(PACKAGE_INVESTMENT_FIELDS),
            "enums": {
                "cenario_tipo": list(CENARIO_TIPO),
                "beneficio_calculo_categoria": list(BENEFICIO_CALCULO_CATEGORIA),
                "tipo_investimento": list(TIPO_INVESTIMENTO),
                "recorrencia": list(RECORRENCIAS),
            },
        },
        "nesting_rules": list(NESTING_RULES),
        "operational_sequence": list(OPERATIONAL_SEQUENCE),
        "reuse_existing_example": _reuse_existing_example(),
        "validate_example": {
            "process": {"processo_id": "<uuid>"},
            "instance": {"instancia_id": "<uuid>"},
            "scenario": _reuse_existing_example()["scenario"],
        },
        "create_new_example": _create_new_example(),
        "baseline_plus_scenario_example": _baseline_plus_scenario_example(),
        "dry_run_semantics": {
            "incomplete_http_status": 200,
            "incomplete_means": "success=true, data.ready=false, data.missing=[...], no writes",
            "ready_true_means": "shape complete for commit attempt; AuthZ/domain still apply on write",
            "ready_false_is_not_tool_failure": True,
        },
        "governed_document_writes": {
            "diagram": "Use only when surface_supports.persist_diagram_via_gpt=true and live manage authorization succeeds.",
            "decomposition": "Use only when surface_supports.persist_decomposition_via_gpt=true and live manage authorization succeeds.",
            "flow": "PREPARE → SHOW → CONFIRM → COMMIT → AUTHORITATIVE READ-BACK → VERIFY",
            "support_is_not_authorization": True,
            "commit_via": "gpt_commit_proposal",
            "note": "COMMIT is the ACT stage; not a direct create/update Action.",
        },
        "ui_only_persist": [
            "binary evidence uploads",
            "binary evidence downloads",
            "meeting-minute handwritten signature",
            "meeting-minute PDF binary",
            "public magic-link signing",
        ],
        "gpt_governed_parity": {
            "evidence_link_metadata": [
                "gpt_list_evidence",
                "gpt_manage_evidence",
            ],
            "process_timeline": ["gpt_get_process_timeline"],
            "shared_resource_cost_adjustment": [
                "gpt_adjust_shared_resource_cost"
            ],
            "meeting_minute_extras": ["gpt_meeting_minute_manage"],
            "not_exposed": [
                "arbitrary HTTP proxy",
                "collaboration locks",
                "realtime/websocket internals",
                "JSON backup/import restore",
                "engineering S2S integration",
                "authorization metadata as model authority",
            ],
        },
        "conversational_draft_ok": [
            "Mermaid AS-IS/TO-BE drafts",
            "diagnostic hypotheses",
            "TO-BE proposals",
        ],
    }


def openapi_revision_properties() -> dict[str, Any]:
    props: dict[str, Any] = {
        "id": {"type": "string", "description": "Existing revisao_id alias for update/reuse."},
        "revisao_id": {"type": "string", "description": "Existing revision id for update/reuse."},
        "versao_revisao": {"type": "string", "description": "Required on create (e.g. 2.1.0)."},
        "cenario_tipo": {
            "type": "string",
            "enum": list(CENARIO_TIPO),
            "description": "Required on create for scenario; forced to baseline in baseline block.",
        },
        "data_inicio_vigencia": {
            "type": "string",
            "description": "Required on create (YYYY-MM-DD).",
        },
        "revisao_ativa": {"type": "boolean", "default": False},
        "revisao_referencia_id": {
            "type": "string",
            "description": (
                "Required for non-baseline create unless baseline is created in the same package."
            ),
        },
        "beneficio_calculo_categoria": {
            "type": "string",
            "enum": list(BENEFICIO_CALCULO_CATEGORIA),
            "default": BENEFICIO_CALCULO_CATEGORIA_DEFAULT,
            "description": "Belongs on revision, not measurement.",
        },
        "descricao_revisao": {"type": "string"},
        "motivo_revisao": {"type": "string"},
        "data_implantacao": {"type": "string", "description": "YYYY-MM-DD", "nullable": True},
        "data_fim_vigencia": {
            "type": "string",
            "format": "date",
            "nullable": True,
            "description": (
                "YYYY-MM-DD end date, or null for open vigencia. "
                "Omitted on create = leave NULL (do not invent today). "
                "Omitted on update (GPT) = keep current; explicit null = clear."
            ),
        },
        "observacoes": {"type": "string"},
    }
    return props


def openapi_measurement_properties() -> dict[str, Any]:
    return {
        "volume_mensal": {"type": "number", "default": 0},
        "tempo_medio_execucao_min": {"type": "number", "default": 0},
        "tempo_retrabalho_min": {"type": "number", "default": 0},
        "percentual_retrabalho": {"type": "number", "default": 0},
        "percentual_erro": {"type": "number", "default": 0},
        "quantidade_erros_mes": {"type": "number", "default": 0},
        "custo_hora_mao_obra": {"type": "number", "default": 0},
        "custo_unitario_erro": {"type": "number", "default": 0},
        "custo_unitario_retrabalho": {"type": "number", "default": 0},
        "custo_outros_desperdicios": {"type": "number", "default": 0},
        "base_referencia_mes": {
            "type": "string",
            "description": "Optional YYYY-MM reference month.",
        },
        "observacoes": {"type": "string"},
    }


def openapi_investment_properties() -> dict[str, Any]:
    return {
        "tipo_investimento": {"type": "string", "enum": list(TIPO_INVESTIMENTO)},
        "descricao_item": {"type": "string"},
        "quantidade": {"type": "number", "default": 1},
        "valor_unitario": {"type": "number", "default": 0},
        "recorrencia": {"type": "string", "enum": list(RECORRENCIAS), "default": "unico"},
        "categoria_investimento": {"type": "string"},
        "data_investimento": {"type": "string"},
        "meses_vigencia": {"type": "integer"},
        "centro_custo": {"type": "string"},
        "observacoes": {"type": "string"},
    }
