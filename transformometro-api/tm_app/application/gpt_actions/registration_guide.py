"""Registration guide for Custom GPT specialists (catalog payload).

Single source of field/enum guidance for guided process + improvement signup.
Enums come from tm_app.core.catalogs — do not duplicate literals here.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.gpt_actions.improvement_package_contract import (
    build_package_hints,
)
from tm_app.core.catalogs import (
    BENEFICIO_CALCULO_CATEGORIA,
    BENEFICIO_CALCULO_CATEGORIA_DEFAULT,
    CENARIO_TIPO,
    FASE_MELHORIA,
    PRIORIDADE_MELHORIA,
    RECORRENCIAS,
    STATUS_FILIAL,
    STATUS_INSTANCIA,
    STATUS_PROCESSO,
    STATUS_SETOR,
    TIPO_INVESTIMENTO,
)


def build_registration_guide() -> dict[str, Any]:
    """Structured guide returned inside gpt_get_catalog."""
    package_hints = build_package_hints()
    # Operational policy for inconclusive consequential commit (TÉO regression).
    package_hints["commit_result_unknown"] = {
        "do_not_claim_success": True,
        "inspect_read_current_state_before_retry": True,
        "avoid_duplicate_write": True,
        "no_http_bypass": True,
        "no_silent_create_update_substitute": True,
        "no_retry_loop": True,
        "package_change_invalidates_confirmation": True,
        "success_requires": ["authoritative_commit_result", "read_back", "verify"],
        "notes": [
            "If gpt_commit_improvement_package is unavailable/disabled or returns no authoritative result, treat persistence as UNKNOWN.",
            "Do not claim saved/cadastrado/gravado.",
            "Before retry of an identical package, read current state when possible to avoid duplicates.",
            "If any package field changes, previous confirmation is invalid.",
        ],
    }
    package_hints["persistence_outcome_states"] = [
        "VALIDATED",
        "CONFIRMED",
        "COMMIT_ATTEMPTED",
        "COMMIT_CONFIRMED",
        "PERSISTED",
        "VERIFIED",
    ]
    return {
        "concepts": {
            "process": (
                "Master process (processo-mestre): corporate initiative name. "
                "Not tied to a single unit until an instance exists."
            ),
            "instance": (
                "Operational improvement (melhoria): process × unit × department(s). "
                "API entity `instance` / field `instancia_id`."
            ),
            "revision": (
                "Calculable scenario with validity dates, measurement and costs. "
                "Types: baseline (before) or melhoria|automacao|correcao (after). "
                "data_fim_vigencia: omit = open vigencia; null = clear; date = set. "
                "Never invent today's date when omitted."
            ),
            "measurement": (
                "Monthly operating metrics for one revision (upsert by revisao_id). "
                "Required on new baseline/scenario revision in improvement packages "
                "(volume_mensal + tempo_medio_execucao_min)."
            ),
            "investment": "One-time or recurring cost lines on a non-baseline revision.",
            "decomposition_tree": (
                "Process WBS / mapeamento macro (entity=decomposition_tree, id=processo_id). "
                "Shared tree for all instances/revisions."
            ),
            "revision_decomposition_overlay": (
                "Per-revision mapeamento delta (entity=revision_decomposition_overlay, "
                "id=revisao_id). AS-IS vs TO-BE differences on top of the shared tree — "
                "not free-text prose."
            ),
            "process_diagram": (
                "Process macro flowchart (entity=process_diagram, id=processo_id). "
                "format=flowchart_v1; Mermaid is server-derived. Alias: diagrama / diagrama macro."
            ),
            "branch": (
                "Operational unit / filial (entity=branch). Catalog admin write; "
                "prefer reusing access_scope filiais when possible."
            ),
            "department": (
                "Department / setor (entity=department) linked to one or more units. "
                "Catalog write; prefer access_scope setores when possible."
            ),
            "meeting_minute": (
                "Transforma+ meeting minute / ata (entity=meeting_minute). "
                "Handwritten signature remains UI-only."
            ),
        },
        "write_contract_rules": {
            "priority": (
                "entity_schemas.<entity> is the primary write contract. "
                "If the generic Action signature diverges, follow the entity schema. "
                "Document entities (decomposition_*/process_diagram/instance_*_scope/"
                "revision_*_overlay/impact_effort_matrix) are listed in entity_schemas — "
                "do not treat catalog.entities presence alone as 'no write contract'."
            ),
            "action_wrapper": (
                "Always send {data:{...}}. Put canonical fields at data.<field>. "
                "Do not nest entity fields under data.conteudo/payload/attributes/metadata "
                "unless that entity contract requires it (document entities use conteudo)."
            ),
            "anti_pattern": (
                "shared_resource with nome_recurso/tipo_custo/recorrencia inside data.conteudo "
                "is invalid; those fields belong directly under data. "
                "Also invalid: inventing entity names like 'mapeamento'/'diagrama'/'ata'/'filial'/'setor' — "
                "use decomposition_tree / revision_decomposition_overlay / process_diagram / "
                "meeting_minute / branch / department."
            ),
            "before_write": [
                "Call gpt_get_catalog and read entity_schemas for the exact entity.",
                "Check required fields, exact names, enums, dates, numeric types, IDs.",
                "Use IDs from authoritative read-back for relationships (e.g. resource_link).",
                "User confirmation does not waive contract validation.",
            ],
            "on_validation_error": [
                "Do not repeat the same payload shape.",
                "Reread catalog; fix to entity schema.",
                "Authoritative read-back before retry to avoid partial persistence or duplicates.",
                "If contract remains unresolved: do not improvise; do not write.",
            ],
            "success_requires": [
                "authoritative write result",
                "read_back",
                "verify",
            ],
        },
        "registration_flow": [
            {
                "step": 1,
                "id": "resolve_scope",
                "ask": [
                    "Which unit (filial) and department(s) (setor)?",
                    "Is this a new master process or an existing one?",
                ],
                "actions": [
                    "Call gpt_get_catalog and reuse filiais/setores from access_scope.",
                    "Search process with gpt_search_records entity=process before creating.",
                ],
            },
            {
                "step": 2,
                "id": "process_and_instance",
                "ask": [
                    "Process name and short description of what changed.",
                    "Improvement title/summary, phase and priority if known.",
                ],
                "actions": [
                    "Create or reuse process, then instance (or use improvement package).",
                    "Always keep instancia_id for later revisions.",
                ],
            },
            {
                "step": 3,
                "id": "baseline",
                "ask": [
                    "As-is monthly volume, average time (min), rework/error rates, labor hourly cost.",
                    "Baseline version label (e.g. v1.0) and start date (YYYY-MM-DD).",
                ],
                "actions": [
                    "Create revision cenario_tipo=baseline with instancia_id.",
                    "Upsert measurement on that revisao_id.",
                    "Never activate a baseline as the operational current revision.",
                ],
            },
            {
                "step": 4,
                "id": "scenario",
                "ask": [
                    "To-be metrics after the improvement.",
                    "Scenario type: melhoria, automacao, or correcao.",
                    "Investment items (description, amount, type).",
                    "Whether to activate now and recalculate the dashboard.",
                ],
                "actions": [
                    "Create non-baseline revision with revisao_referencia_id = baseline (or prior active).",
                    "Upsert measurement + investments.",
                    "Prefer gpt_validate_improvement_package then gpt_commit_improvement_package.",
                    "Activate only the scenario revision when the user confirms.",
                ],
            },
            {
                "step": 5,
                "id": "governed_followups",
                "ask": [],
                "actions": [
                    "WBS/mapeamento: entity_schemas.decomposition_tree then "
                    "revision_decomposition_overlay (and instance_decomposition_scope when needed).",
                    "Diagrams: entity_schemas.process_diagram then revision_diagram_overlay "
                    "(and instance_diagram_scope when needed).",
                    "Always PREPARE → SHOW → CONFIRM → WRITE → VERIFY; manage AuthZ required.",
                    "Point user to Minha DELPI UI for evidence uploads and meeting-minute handwritten signatures.",
                    "Offer gpt_analyze for KPIs after recalculate.",
                ],
            },
        ],
        "entity_schemas": {
            "branch": {
                "required": ["codigo_filial", "nome_filial"],
                "optional": ["status_filial"],
                "enums": {"status_filial": list(STATUS_FILIAL)},
                "defaults": {"status_filial": "ativo"},
                "notes": [
                    "Create requires unrestricted catalog admin.",
                    "Update by filial_id: nome_filial + status_filial (codigo_filial immutable).",
                    "Prefer gpt_get_catalog.access_scope filiais before creating a new unit.",
                    "Alias: filial → branch.",
                ],
            },
            "department": {
                "required": ["setor_id", "nome_setor", "filiais"],
                "optional": ["status_setor"],
                "enums": {"status_setor": list(STATUS_SETOR)},
                "defaults": {"status_setor": "ativo"},
                "notes": [
                    "Create: setor_id is the department code/id; filiais is a non-empty list of unit codes.",
                    "Update by setor_id path: uses codigo_setor (not setor_id) + nome_setor + filiais + status_setor.",
                    "Each filial in filiais must be an active unit.",
                    "Alias: setor → department.",
                ],
            },
            "process": {
                "required": ["nome_processo", "status_processo"],
                "optional": [
                    "descricao_processo",
                    "gestor_responsavel",
                    "objetivo_processo",
                    "codigo_processo",
                    "familia_processo",
                    "agrupador_ferramenta",
                    "filial_id",
                    "setor_id",
                    "todas_filiais_ativas",
                    "filial_ids",
                    "setor_ids",
                ],
                "enums": {"status_processo": list(STATUS_PROCESSO)},
                "defaults": {},
                "notes": [
                    "filial_id+setor_id on create also creates the first instance.",
                    "Otherwise create instance separately with processo_id.",
                ],
            },
            "instance": {
                "required": ["setor_ids"],
                "optional": [
                    "filial_id",
                    "todas_filiais_ativas",
                    "rotulo_instancia",
                    "status_instancia",
                    "resumo_melhoria",
                    "responsavel_local",
                    "fase_melhoria",
                    "data_alvo_go_live",
                    "prioridade",
                ],
                "enums": {
                    "fase_melhoria": list(FASE_MELHORIA),
                    "prioridade": list(PRIORIDADE_MELHORIA),
                    "status_instancia": list(STATUS_INSTANCIA),
                },
                "defaults": {
                    "fase_melhoria": "planejado",
                    "prioridade": "media",
                    "status_instancia": "ativo",
                    "todas_filiais_ativas": False,
                },
                "notes": [
                    "Need filial_id OR todas_filiais_ativas=true.",
                    "setor_ids must have at least one department.",
                    "Create body also needs processo_id in data.",
                    "Corporate/all-units instance: todas_filiais_ativas=true and omit filial_id "
                    "(use gpt_create_record entity=instance; improvement package still needs "
                    "baseline or scenario for revisions).",
                ],
            },
            "revision": {
                "required": [
                    "processo_id",
                    "versao_revisao",
                    "cenario_tipo",
                    "data_inicio_vigencia",
                ],
                "optional": [
                    "instancia_id",
                    "revisao_ativa",
                    "revisao_referencia_id",
                    "beneficio_calculo_categoria",
                    "descricao_revisao",
                    "motivo_revisao",
                    "data_implantacao",
                    "data_fim_vigencia",
                    "observacoes",
                ],
                "enums": {
                    "cenario_tipo": list(CENARIO_TIPO),
                    "beneficio_calculo_categoria": list(BENEFICIO_CALCULO_CATEGORIA),
                },
                "defaults": {
                    "revisao_ativa": False,
                    "beneficio_calculo_categoria": BENEFICIO_CALCULO_CATEGORIA_DEFAULT,
                },
                "notes": [
                    "Always pass instancia_id for guided flows.",
                    "baseline must NOT set revisao_referencia_id.",
                    "Non-baseline REQUIRES revisao_referencia_id.",
                    "Do not set revisao_ativa=true on create for baseline; use activate on scenario.",
                ],
            },
            "measurement": {
                "required": ["revisao_id"],
                "optional": [
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
                ],
                "enums": {},
                "defaults": {
                    "volume_mensal": 0,
                    "tempo_medio_execucao_min": 0,
                    "tempo_retrabalho_min": 0,
                    "percentual_retrabalho": 0,
                    "percentual_erro": 0,
                    "quantidade_erros_mes": 0,
                    "custo_hora_mao_obra": 0,
                    "custo_unitario_erro": 0,
                    "custo_unitario_retrabalho": 0,
                    "custo_outros_desperdicios": 0,
                },
                "notes": [
                    "Upsert: create and update share the same payload shape.",
                    "Ask for as-is (baseline) and to-be (scenario) numbers separately.",
                ],
            },
            "investment": {
                "required": ["revisao_id", "tipo_investimento", "descricao_item"],
                "optional": [
                    "quantidade",
                    "valor_unitario",
                    "recorrencia",
                    "categoria_investimento",
                    "data_investimento",
                    "meses_vigencia",
                    "centro_custo",
                    "observacoes",
                ],
                "enums": {
                    "tipo_investimento": list(TIPO_INVESTIMENTO),
                    "recorrencia": list(RECORRENCIAS),
                },
                "defaults": {"quantidade": 1, "valor_unitario": 0, "recorrencia": "unico"},
                "notes": ["Usually attached to the scenario revision, not baseline."],
            },
            "shared_resource": {
                "required": ["nome_recurso", "tipo_custo", "recorrencia"],
                "optional": [
                    "valor_total_recorrente",
                    "criterio_rateio",
                    "escopo_recurso",
                    "base_competencia",
                    "status_recurso",
                    "categoria_recurso",
                    "fornecedor",
                    "data_inicio_vigencia",
                    "data_fim_vigencia",
                    "centro_custo",
                    "observacoes",
                    "codigo_recurso",
                ],
                "enums": {},
                "defaults": {
                    "criterio_rateio": "igualitario",
                    "escopo_recurso": "empresa",
                    "base_competencia": "mensal_cheio",
                    "status_recurso": "ativo",
                    "valor_total_recorrente": 0,
                },
                "notes": [
                    "Catalog resource only. Monthly amount history uses entity=resource_cost.",
                    "Update merges omitted fields from the current row.",
                    "Put nome_recurso/tipo_custo/recorrencia directly under data — never under data.conteudo.",
                ],
            },
            "resource_cost": {
                "required": [
                    "recurso_compartilhado_id",
                    "valor_mensal",
                    "data_inicio_vigencia",
                ],
                "optional": ["data_fim_vigencia", "observacoes", "recurso_id"],
                "enums": {},
                "defaults": {},
                "notes": [
                    "Create: recurso_compartilhado_id (or recurso_id) + valor_mensal + data_inicio_vigencia.",
                    "Update by recurso_custo_id: may send only valor_mensal; other fields merge.",
                    "Prefer updating the active open line in place when the user asks to change the monthly value.",
                    "data_fim_vigencia null means open vigência.",
                ],
            },
            "resource_link": {
                "required": ["revisao_id", "recurso_compartilhado_id"],
                "optional": [
                    "ativo",
                    "data_inicio_uso",
                    "data_fim_uso",
                    "peso_rateio",
                    "observacoes",
                ],
                "enums": {},
                "defaults": {"ativo": True},
                "notes": [
                    "Links a shared resource to a revision for rateio.",
                    "Use real revisao_id and recurso_compartilhado_id from read-back; never invent IDs.",
                ],
            },
            "meeting_minute": {
                "required": ["unit_code", "title", "meeting_date"],
                "optional": [
                    "meeting_type",
                    "start_time",
                    "end_time",
                    "location",
                    "responsible_user_id",
                    "responsible_name",
                    "chair_name",
                    "secretary_name",
                    "agenda_html",
                    "body_html",
                    "decisions_html",
                    "pending_html",
                    "observations_html",
                    "participants",
                    "signers",
                ],
                "enums": {},
                "defaults": {"meeting_type": "ordinary"},
                "notes": [
                    "Create/update via gpt_create_record / gpt_update_record entity=meeting_minute.",
                    "unit_code is the filial code (zero-padded to 2 digits by backend).",
                    "Workflow send/finalize/cancel uses gpt_meeting_minute_workflow — not create/update.",
                    "Handwritten signature and evidence uploads remain UI-only (package_hints.ui_only_persist).",
                    "Alias: ata → meeting_minute.",
                ],
            },
            "decomposition_tree": {
                "required": ["processo_id", "conteudo"],
                "optional": [],
                "enums": {},
                "defaults": {},
                "notes": [
                    "Upsert via gpt_create_record or gpt_update_record (id=processo_id).",
                    "conteudo.format must be decomposition_tree_v1; format_version=1.",
                    "conteudo.nodes[]: id, level (processo_chave|tarefa|sub_tarefa), "
                    "ordem, label, parent_id (null for processo_chave).",
                    "This is the shared WBS/mapeamento macro — not per-revision prose.",
                    "Requires manage access on the process.",
                ],
            },
            "instance_decomposition_scope": {
                "required": ["instancia_id"],
                "optional": [
                    "node_ids",
                    "inherit_all",
                    "include_descendants",
                ],
                "enums": {},
                "defaults": {"inherit_all": True, "include_descendants": True},
                "notes": [
                    "Upsert; id on update path = instancia_id.",
                    "Which WBS nodes from the process tree apply to this instance.",
                    "Fields go under data (not inside conteudo).",
                ],
            },
            "revision_decomposition_overlay": {
                "required": ["revisao_id", "conteudo"],
                "optional": [],
                "enums": {},
                "defaults": {},
                "notes": [
                    "Canonical name for 'mapeamento por revisão'. Upsert; id=revisao_id.",
                    "conteudo.format must be decomposition_overlay_v1; format_version=1.",
                    "conteudo fields: node_overrides{}, disabled_node_ids[], extra_nodes[].",
                    "node_overrides.<node_id>.highlight in asis|tobe|changed|removed.",
                    "Do NOT put free-text flow narratives as conteudo; model steps as "
                    "tree nodes (decomposition_tree) and/or overlay extras/overrides.",
                    "Requires manage access on the revision's instance/process.",
                ],
            },
            "process_diagram": {
                "required": ["processo_id", "conteudo"],
                "optional": [],
                "enums": {},
                "defaults": {},
                "notes": [
                    "Upsert; id=processo_id. conteudo.format=flowchart_v1; format_version=1.",
                    "conteudo: nodes[], edges[] (lanes optional). Mermaid is DERIVED BY SERVER.",
                    "Macro flowchart of the master process (not revision-specific alone).",
                ],
            },
            "instance_diagram_scope": {
                "required": ["instancia_id"],
                "optional": [
                    "node_ids",
                    "inherit_all",
                    "include_boundary_edges",
                ],
                "enums": {},
                "defaults": {"inherit_all": True, "include_boundary_edges": False},
                "notes": [
                    "Upsert; id=instancia_id. Scope of macro diagram nodes for the instance.",
                    "Fields under data (not conteudo). Unlike WBS scope, no include_descendants.",
                ],
            },
            "revision_diagram_overlay": {
                "required": ["revisao_id", "conteudo"],
                "optional": [],
                "enums": {},
                "defaults": {},
                "notes": [
                    "Upsert; id=revisao_id. conteudo.format=flowchart_overlay_v1; format_version=1.",
                    "conteudo fields: modo, node_overrides{}, edge_overrides{}, "
                    "removed_node_ids[], removed_edge_ids[], extra_nodes[], extra_edges[].",
                    "Per-revision diagram delta on top of the process macro flowchart.",
                    "Requires manage access on the revision's instance/process.",
                ],
            },
            "impact_effort_matrix": {
                "required": ["revisao_id"],
                "optional": ["modo", "inputs_manuais", "overrides"],
                "enums": {},
                "defaults": {},
                "notes": [
                    "Update only (no create). id=revisao_id.",
                    "Use gpt_update_record entity=impact_effort_matrix.",
                ],
            },
        },
        "package_hints": package_hints,
    }
