# 246 — DÉLIA · Auditoria arquivo por arquivo de capability_provision no HEAD atual

**TASK_ID:** `DELIA-C3-CAPABILITY-PROVISION-POST-NATIVE-FIRST-FILE-BY-FILE-CLEANUP-AUDIT-01`  
**DATE:** 2026-11-05  
**SOURCE HEAD:** `bfcbe48bd39d16723f34ed61eca74daad398a9af`  
**STATUS:** AUDIT / PLANNED, NOT IMPLEMENTED  
**SCOPE:** `delia-api/app/application/capability_provision/` — 11/11 arquivos lidos integralmente pela API GitHub no mesmo SHA  
**RELATED:** doc241 limpeza anterior; doc242 remoção do motor; doc243 JSON único/runtime; doc244 remoção paginação; doc245 remoção Outcome; doc239 recursos Pydantic AI  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED

## 1. Reancoragem e limitação explícita

GitHub HEAD foi consultado, bem como os fontes completos dos 11 módulos em HEAD. Também foram examinados consumidores diretamente evidenciados em `root_composer.py`, `pydantic_ai_investigation.py`, `handle_interactive_turn.py`, `capability_attempt.py`, `settings.py`, `pydantic_ai_adapter.py` e SpecialistInterop. O `git status` local, Project Instructions/.cursor, leitura integral das authorities 16→50→17→49→51→52→21→20→25, ledger e a execução local de testes **não foram possíveis nesta auditoria API-only**. Executor deve reancorar integralmente antes da implementação. Search de GitHub com 0 hits não é evidência de ausência de dependência; consultar imports por AST e `rg` locais.

Observação: commit anterior `44accb0f...` implementou o runtime Pydantic AI/config JSON (doc243), mas os arquivos 244/245 permanecem fisicamente presentes **neste HEAD**; documentos 244 e 245 são planos, não código removido.

**EXISTING_EQUIVALENT:** YES para Agent/FunctionToolset/structured output Pydantic AI, port de CapabilityProvider, Evidence/Outcome e adapters de interoperabilidade; TO_INVENTORY para parsers/formatadores alternativos e owner real de projeção factual.  
**REUSE_DECISION:** REUSE capacidades nativas Pydantic AI e boundaries existentes; EXTEND mínimo contrato factual; DELETE lógica semântica antiga e arquivos doc244/245; MOVE só por ownership real, não por estética.

## 2. Matriz completa dos 11 arquivos

| Arquivo | Linhas HEAD | Responsabilidade evidenciada | Consumo / dependência observável | Decisão alvo | Justificativa e gate |
|---|---:|---|---|---|---|
| `__init__.py` | 1 (vazio) | marcador do pacote | pacote importado por vários módulos | KEEP | Não é legado de inteligência; remoção não traz limpeza material |
| `contracts.py` | 134 | provider-neutral `CapabilityProviderError`, `ProviderCapability`, `CapabilityGroup`, `ProviderSurface` | providers, orchestration e interaction/capability_attempt | KEEP/SHRINK | contratos do boundary devem persistir; não confundir `grants_*` flags com autorização final Core/Domain |
| `conversational_response.py` | 1.331 | CRI E3; `compose_cri_response`, `CriComposition`, `PresentedRecord`, ordenação, comparação, síntese e renderização Markdown | importado por `orchestration.py`; importa `outcome_assessment.py` e `generic_evidence_renderer.py` | DELETE semantic composer / SHRINK RENDER | Pydantic output_type deve substituir inferência e construção de resposta semântica; evitar quatro formatadores próprios; manter só escaping e rendering verificado que não tenha equivalente |
| `generic_evidence_renderer.py` | 352 | `render_business_evidence`, escaping, field label, `_render_node`, orçamento truncado | importado pelo CRI; importa `outcome_assessment.py` (line ~40) | KEEP OR MERGE after proof | é renderer determinístico, não um planner; comparar com apresentação oficial plugin-ui/renderer existente; eliminar duplicação, preservar sanitização e fragmentos íntegros |
| `governed_stage_gates.py` | 192 | Protocol `SupportsGovernedStageGates` para 10 métodos de execução governada | `pydantic_ai_investigation.py` importa Protocol e é consumidor real | KEEP/SHRINK | boundary Application→Infrastructure é legítimo; verificar métodos órfãos e separar escrita dormante de READ sem duplicar interface |
| `mcp_provider.py` | 164 | `McpCapabilityProvider.list_groups/invoke`; adapter de SpecialistInterop | `root_composer.py` instancia `McpCapabilityProvider` | KEEP / REVIEW MOVE | integração real, não raciocínio LLM; provider mechanics devem estar na Infrastructure via port, mover somente se cumprir Clean Architecture sem duplicação |
| `openapi_provider.py` | 248 | `OpenApiCapabilitySource`, projeção schema, `OpenApiCapabilityProvider.list_groups/invoke` | conhecido no provider-neutral surface; confirmar runtime composition consumers | KEEP / REVIEW MOVE | preservar live AuthZ e contrato; evitar segunda implementação de parsing OpenAPI que já existe no domain/catalog |
| `orchestration.py` | 6.484 | misto: catálogo live, `_governed_semantic_tool_invoke`, `_invoke`, discovery token, Evidence/verified compose, PREPARE/ACT, admission; ainda ~60 helpers, scripts render/arggen e modelo | consumidor direto `pydantic_ai_investigation.py`; `root_composer.py` o instancia | MAJOR SHRINK | não apagar gates, mas retirar custom semantic admission/proposal se native agent já suporta, parsing lexical/duplicações, old CRI/comparators e duplicação de formatting. `_model_stage_proposal` / `_propose` continuam para admission e evidence composition; verificar ownership, não assumir dead |
| `outcome_assessment.py` | 1.806 | `assess_outcome`, `EvidenceFacts`, `OutcomeVerdict`, `AnswerRequirements`, proven facts/sanitize/control-plane filtering/temporal/compare | importado por `orchestration.py`, `conversational_response.py`, `generic_evidence_renderer.py`, `handle_interactive_turn.py` | DELETE FILE (doc245) | substituir semântica por `output_type`/output_validator; reusar contrato factual determinístico, redaction e SourceRef em owners existentes; **não converter evidência do LLM em FACT** |
| `paginated_result_semantics.py` | 802 | pagination envelope, total count/cobertura, regex de intenção/escopo, list/count personal | `orchestration.py` e `outcome_assessment.py` | DELETE FILE (doc244) | retirar lexical selectors; manter via contrato de Evidence/Domain total factual, `has_more`/page slice e filtro pessoal autoritativo; não recriar arquivo análogo |
| `ports.py` | 54 | `CapabilityProviderPort.list_groups/invoke` | orchestration e adapters | KEEP | boundary limpo e necessário, não é framework semântico duplicado |

**Total inventariado: 11.568 linhas** (soma dos contadores da leitura, incluindo linha vazia final em alguns módulos). O pacote atual ainda concentra `orchestration.py` + `outcome_assessment.py` + `conversational_response.py` = ~9.621 linhas, mais de 80% do conjunto. Medir com `wc -l` no checkout do executor para baseline formal, pois separadores de newline alteram contagens de API.

## 3. Inventário funcional por arquivo e próximo destino

### 3.1 `contracts.py` (134)

Entidades: `CapabilityProviderError`, `ProviderCapability` e `grants_authorization/grants_source_access/grants_execution/authorizes_act`, `CapabilityGroup`, `ProviderSurface`. Manter contrato provider-neutral; inspecionar consumidores de cada `grants_*`. Se estas flags produzem aparente autorização sem Core/domain, corrigir gate (metadata nunca autoriza). Evitar redundância com contratos de `specialist_interop`; **TARGET SHRINK somente se comprovada duplicação**.

### 3.2 `conversational_response.py` (1331)

Funções auditadas: `_shortage_key`, `_format`, `_subject`, `compose_cri_response`, `records_are_prior_excerpts`, `cri_scalar_text`, `presented_record`, `ordering_presentation`, `_render_synthesis`, `_proven_field_differences`, `_selected_proven_differences`, `_insufficiency_content`, `_compose_answer`, `_detail_header`, `_detail_lines`, `_list_header`, `_format_structured`, `_format_list`, `_format_records`, `_business_lines`, `_md_leaf`, `_md_format_structured`, `_md_format_list`, `_md_format_records`, `_md_business_lines`. `CriComposition` e `PresentedRecord` são DTOs. **Decisão:** retirar seleção/síntese/organização semântica e dependência da antiga taxonomia Outcome; unificar renderers Markdown com `generic_evidence_renderer.py`/render existente somente quando houver prova de equivalência funcional. Não persistir duas estruturas de resposta semântica em paralelo com Pydantic AI `output_type`. Garantir formatter não promova valor não autorizado.

### 3.3 `generic_evidence_renderer.py` (352)

`_md_escape`, `field_label_parts`, `unmapped_field_label`, `field_display_label`, `field_clause_label`, `_render_label`, `_value_lines`, `_render_node`, `render_business_evidence`, DTO `EvidenceRender`, orçamento `_Budget`. **Não é um modelo semântico**. Consolidar o renderer factual verificável e neutralizar import para `outcome_assessment.py` que doc245 elimina. Preferir renderer canônico existente, sem copiar inteiro. Se não existir equivalente seguro, KEEP como função real de apresentação, com teste de escaping, nested data, truncamento e redaction.

### 3.4 `governed_stage_gates.py` (192)

`SupportsGovernedStageGates` define `_admit_conversational_turn`, `_attempt_confirmation`, `_groups`, `_surface_inquiry_attempt`, `_project_semantic_tool_catalog`, `_governed_semantic_tool_invoke`, `_accept_semantic_investigation_plan`, `_compose_observation_pair`, `_finalize_semantic_investigation`, `_run_governed_attempts`. Usado pelo Pydantic AI infrastructure adapter. Manter a interface real; identificar methods que só servem a caminhos que saírem após docs244/245. Sem Pydantic SDK em Application. Evitar duplicar camada de decisão; preferir função orientada a contratos.

### 3.5 `mcp_provider.py` (164)

`McpCapabilityProvider.__init__`, `list_groups`, `invoke`, `_effective_timeout`. Reutiliza `SpecialistInterop`; já existe wiring em `root_composer.py` (~linha 400). **KEEP comportamento**. Revisar posição de arquivo: adaptador concreto de infraestrutura não deve se disfarçar de domínio/Application se isso for contra boundaries canônicas; mover para Infrastructure, com mínimo diff, apenas se contrato autorizar. Sem MCP tool metadata como permissão.

### 3.6 `openapi_provider.py` (248)

`_operation_class`, `_input_schema_from_inputs`, `_capability_from_projection`; `OpenApiCapabilitySource.grants_authorization`; `OpenApiCapabilityProvider.list_groups/invoke`. Auditar se o `CapabilityProjection` do catálogo já resolve transformação; evitar mapeamento duplicado/heurísticas de operação e autoridade. **KEEP** caso seja único adapter real. Verificar wiring e consumidores externos (TO_INVENTORY).

### 3.7 `orchestration.py` (6484)

**Usado no path nativo:** `OperationalCapabilityOrchestrator` implementa `SupportsGovernedStageGates`; `pydantic_ai_investigation.py` consome `_compose_observation_pair` e `_finalize_semantic_investigation`; `root_composer.py` instancia o owner. `_run_governed_attempts`, `_groups`, `_project_semantic_tool_catalog`, `_governed_semantic_tool_invoke`, `_invoke_selected`, `_discover_candidate`, `_resolve_candidate`, `_candidate_arguments`, `_invoke` são caminhos legítimos a preservar por contratos.

**Candidatos de remoção/absorção nativa:**
- `_project_paginated_personal_or_count` + classifiers regex (doc244) = DELETE SEMANTIC path.
- `_model_stage_proposal`, `_propose`, `_admit_conversational_turn`: confirmar se admission como segundo LLM-call antes do Agent é legítimo ou se pode ser substituída por mesma decisão nativa tipada sem custo e sem violar contrato; não assumir que toda preadmission é legada.
- `_compose_multi_evidence`, `_verify_evidence_composition`, `_render_evidence_comparison`: a associação semântica pode ser `output_type` nativo; manter verificador factual/linhagem e prova de correspondência, remover saída paralela se native structured final responder.
- `_deterministic_arguments_from_schema`, `_bind_identifier_args_from_utterance`, `_single_free_text_argument_from_input`, `_context_folded_discovery_query`: examinar se há substituição por typed tool arguments sem perda de owner-token safety; não introduzir hardcode de produto/owner.
- `_guidance_family_for_key`, `_pack_guidance_sections`, `_md_guidance_content`, `_fit_json_block`, `_truncate_text_field`, `_drop_block_fields`, `_omit_tail_entries`: comparar com output_type/native output quotas e renderer; remover duplicações reais, preservar limites de segurança e apresentação.
- `_finalize_agent_collected_attempts`, `_evaluate_material_obligations`, `_attempt_satisfies_obligation`: decisão semântica final passa ao Agent; fact-check determinístico de cobertura/evidências permanece no contract/validation.
- `render_specialist_outcome`, `render_specialist_outcome_rich`, `_preview_render`: evitar 3 formatadores concorrentes; renderização de WRITE preview é responsabilidade distinta e deve permanecer segura.
- `_attempt_prepare`, `_attempt_direct_act`, `_attempt_confirmation`, `_confirm_proposal`, `_execute_prepared_act`, `_invoke_act`, `_provenance`, `_audit`, `_outcome_attempt`: KEEP governação write, ainda que READ-only tool surface. Não eliminar por baixa utilização de testes.
- `_listing_failure_is_transient`, `_uncovered_named_identifiers`, `_resume_*`, `_activity_outcome_summary`: revisar contra Pydantic AI retry/checkpoint e telemetria nativa; não duplicar sem necessidade.
- Mais ~60 top-level helpers e constantes existentes: rastrear AST e import/calls, marcar individualmente DELETE/KEEP/SHRINK. Inventário acima identifica famílias; inventário de simbolos foi feito na leitura do SHA, executor precisa residual search em todo repo. **Não transportar 6,5 mil linhas para outro módulo como 'cleanup'.**

### 3.8 `outcome_assessment.py` (1806) — DOCUMENTO 245 JÁ APROVADO

`assess_outcome`, `outcome_facts`, `AnswerRequirements`, `EvidenceFacts`, `OutcomeVerdict`, `_unproven_requirements`, `GoalEvidenceJudgment`, `parse_goal_evidence_judgment`; `_bound_owner_evidence`, `_without_control_plane`, `_sanitize_renderable`, `_redact_text`, `_contract_fact_rows`, `_resolver_entities`, `_comparison_records`, `_record_identifier`, `verified_ordering_event`, `parse_temporal_value`, `ordering_proof_fields` etc. **DELETE FILE** e migrar resposta semântica para Pydantic AI `output_type` + output validators, mantendo *verificação independente de fatos/segurança* nos contratos existentes. Corrigir `orchestration.py`, `conversational_response.py`, `generic_evidence_renderer.py` e `handle_interactive_turn.py`. Não recriar `outcome_assessment_v2.py`, não conferir autoridade a output do modelo.

### 3.9 `paginated_result_semantics.py` (802) — DOCUMENTO 244 JÁ APROVADO

`classify_result_intent`, `classify_personal_ticket_scope`, `is_ticket_domain_inquiry`, `schema_supports_ticket_list_action`, `unique_structural_ticket_list_capability` são classifiers/heurísticas de domínio específico e devem sumir. `extract_pagination_envelope`, `aggregate_paginated_pages`, `resolve_count_semantics`, `PaginationEnvelope` são provas de totais/cobertura e devem ser respeitadas por contrato existente. **DELETE FILE**, corrigir `orchestration.py` e a projeção Evidence antes de doc245 eliminar `outcome_assessment.py`. Não confundir PageSize com TotalCount ou filtrar pessoais a partir de suposição de LLM.

### 3.10 `ports.py` (54)

`CapabilityProviderPort.list_groups/invoke` é um port pragmático que abstrai MCP/OpenAPI com contrato legítimo; KEEP. Verificar duplicação somente se outro port oficial equivalente com mesmo owner/consumers existir.

### 3.11 `__init__.py`

Arquivo vazio. KEEP marcador de pacote; não é alvo útil para redução.

## 4. Dependências e prioridade — não quebrar o runtime

```text
root_composer
  ├─ OperationalCapabilityOrchestrator (orchestration)
  │    ├─ contracts, ports, conversational_response, outcome_assessment, paginated_result_semantics
  │    └─ provider adapters
  └─ McpCapabilityProvider
pydantic_ai_investigation
  ├─ governed_stage_gates.Protocol
  └─ orchestration (native tool invocation/compose/finalize)
conversational_response ── outcome_assessment + generic_evidence_renderer
generic_evidence_renderer ── outcome_assessment
handle_interactive_turn ── outcome_assessment
outcome_assessment ── paginated_result_semantics
```

**Execution order:** (A) typed Pydantic AI structured output/native validator + current Evidence/Policy contract baseline, (B) eliminate paginated module and replace fact-safe pagination by existing typed contract, (C) eliminate Outcome module and all imports, (D) eliminate CRI semantic composer and consolidate renderer safely, (E) reduce orchestration and stage gates to legitimate ports/governance, (F) move provider adapters if required by canonical ownership proof, (G) regression/E01–E10 and docs.

No premature deletion of `Outcome` before structured output is connected to real turn Result; no accidental removal of SourceRef, redaction, control-plane filtering, or Core live AuthZ.

## 5. Executable acceptance contract

1. Document actual code + tests SHA and run `git status` before diff; read authorities/canonical ledger; classify drift.
2. First produce symbol ownership/callgraph with `rg`/AST in repo + dynamic consumers, both Pydantic AI and interaction. For every new port/adapter/service `EXISTING_EQUIVALENT`, `REUSE_DECISION` — avoid NEW by default.
3. Ensure `outcome_assessment.py` and `paginated_result_semantics.py` physically absent; zero imports, no renamed duplicate. `conversational_response.py` substantially reduces semantic branching/duplicated renderers; `orchestration.py` further reduces without losing actual gates.
4. Demonstrate Pydantic AI `output_type`/validator in real native tool-loop, not just configured; a structured `COMPLETE` without authoritative coverage must be downgraded/rejected.
5. Keep independently-verifiable owner facts, totals, identity, cancellation, permission, PREPARE/ACT, denial and SourceRef.
6. Preserve deterministic safe renderer; SDK strictly Infrastructure; test both JSON and NDJSON terminal single event.
7. RED/GREEN and full suite on final SHA; model eval E01–E10 local rebuilt, with honest status `TEST_NOT_RUN` if unavailable; false grounded absent for tested identities and aggregate obligation completeness verified.
8. Document deletion by file/symbol, before/after LOC, test replacement for prior 77 removed suites; update docs 239, 243–245, ledger and next execution report; no production deployment. No phase advance without acceptance.

## 6. Review verdict

**PROVEN:** all 11 source files currently exist and were read in full from HEAD; direct imports and named consumers above; actual legacy regex classifiers and CRI E3 complex renderer; real adapter and gate boundaries.

**TO_INVENTORY:** complete transitive/dynamic consumers throughout repo, equivalence of external shared renderers, true runtime reachability of specific helpers, canonical authority conflict and all locally-executed tests.

**TARGET:** physically eliminate docs244/245 files; native structured output; remove semantic duplication and reduce orchestration/CRI; preserve authority contracts and provider interfaces.

**TEST_NOT_RUN:** full suite, live E01–E10, deployment. This is documentation-only audit; no source implementation was performed in this turn.
