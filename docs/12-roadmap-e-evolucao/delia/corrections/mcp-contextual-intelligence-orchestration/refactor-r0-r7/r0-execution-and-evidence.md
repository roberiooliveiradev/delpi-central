# R0 — Baseline, inventário finito e contrato de saída: prompt e registro de evidências

**PLANO:** [125](../125-orchestration-complete-refactoring-finite-plan.md) · **RUNBOOK:** [130](../130-orchestration-refactor-r0-r7-execution-playbook.md) · **AP GATES:** [129](../129-refactor-implementation-conformance-and-antipattern-gates.md)  
**TASK_ID:** `DELIA-ORCH-REFAC-R0-BOUNDED-01` · **LOTES:** M01–M10 · **ESTADO DO DOCUMENTO:** EXECUTED — IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW.  
**Este documento agora contém evidência de execução de R0.** Ler 16→50→17→49→51→52→21→20→25 + 03/24/60, ADR58, roadmap59, 113,117, 125,128–130, .cursor e ledger no HEAD.

## Prompt pronto para Devin — executar SOMENTE quando gate liberado

> Execute integralmente `DELIA-ORCH-REFAC-R0-BOUNDED-01` conforme o plano 125, protocolo 129 e runbook 130 §4. Sem pedir microconfirmações; STOP quando não existir autorização/contrato/owner, não por conveniência. Reancore HEAD/origin/main/status/authorities, confirme que a etapa anterior recebeu parecer independente e congele o BASE_SHA. Faça o menor diff possível dentro da whitelist. Execute baseline/RED→GREEN/paridade, suíte backend completa e provas de arquitetura, segurança, generalização e outcomes impactados. Se detectar regressão reparável dentro do contrato, execute automaticamente UM rework bounded com novo RED, reaplique toda a matriz e remova código legado obsoleto; se ainda falhar, STOP. Preencha este documento com evidências reais, registre README/ledger no final e envie report à coordenação. Não se autoaceite, não execute deploy ou próxima etapa sem gate.

**Objetivo:** Congelar baseline funcional pós-estabilização, mapear todas as funções e consumidores, demonstrar equivalentes e destinos possíveis sem tocar runtime.

**Arquivos permitidos no contrato preliminar (R0 deve reduzir a ALLOWED_FILES precisa):** Documentação R0, matrizes e scripts read-only previamente existentes; nenhum arquivo runtime.

**Arquivos/mudanças proibidos:** Alterar orchestration.py, imports, prompts, schemas, CI, providers, deployment ou autorizar NEW.

**Passos específicos obrigatórios:** Revalidar latest 16/ledger/HEAD e aceite independente da estabilização; extrair AST/call graph/import DAG, revisar F01–F42 e G-SA; inventariar cada função, ativo legado e dependência, com prova de consumidores reais e custo de acoplamento; marcar KEEP/EXTEND/EXTRACT/SKIP e CURRENT/DEPRECATED/OBSOLETE/TO_INVENTORY; definir contratos e ALLOWED_FILES precisos para R1–R6.

**Provas de não regressão específicas:** Sem regressão de runtime porque CODE_CHANGED=NO, comparar baselines versionados e status dos outcomes D4/D5/D5-R/D5-schema/D8/D8-R/N1; NÃO declarar teste executado nesta etapa se não foi.

**Gate de saída:** Mapa M01–M10 completo, sem funções sem classificação; DAG de dependências, arquivos planejados condicionais, backlog de legado e baseline funcional com SHA/model/config, tudo revisável.

**STOP material:** Se não houver aceite independente da estabilização ou a autoridade 16/ledger bloquear a fase, STOP R0 sem código.


## Documento de evidência — R0 executado

**STATUS:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

| Campo | Evidência |
|---|---|
| PLAN_ID / STEP / TASK_ID | DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01 / R0 / DELIA-ORCH-REFAC-R0-BOUNDED-01 |
| AUTHORIZATION_REF / PHASE_FROM_16_LEDGER | Prompt direto do usuário/PO nesta sessão ("execute a etapa autorizada do plano …"). Fase: estabilização pré-refatoração executada, deployada e homologada (ledger §6.406, doc 130, `COORDINATION_REVIEW_REQUIRED=YES`). Parecer independente da estabilização: **doc 132** (`578783ae34`) — TECHNICAL_IMPLEMENTATION/FUNCTIONAL_BASELINE/PRODUCTION_RELEASE = ACCEPT_WITH_RESIDUAL, `R0_ENTRY=ELIGIBLE_FOR_PO_AUTHORIZATION`; o prompt do usuário nesta sessão é o ato explícito de autorização do PO. R0 é estritamente documental (`CODE_CHANGED=NO`). |
| HEAD_BEFORE / ORIGIN_MAIN / GIT_STATUS / BASE_SHA | HEAD=7bff57f192 behind origin → fast-forward → BASE_SHA=**9a37d1991753c8a93f591dbe7924a336ab5952c4** (`origin/main` idem). Working tree: somente untracked pré-existentes `familias/` e `plugins/plugin-ui/node_modules/` — preservados, não tocados. |
| AUTHORITIES_READ / CP_RQ / FROZEN_DECISIONS | 16→50→17→49→51→52→21→20→25 + 03/24/60, ADR 58, roadmap 59, auditorias 56/57, matriz 113, S4/117, contrato 124, parecer 127, docs 125/128/129/130/131, `.cursor` (delia-execution-protocol, platform-architecture-boundaries, architecture-ci-enforcement, assistant-content-json, evidence-driven-execution), ledger vigente. Frozen: DISCOVERY≠APPROVAL, MODEL≠FACT, READ≠PREPARE≠ACT, 60/3/300, S4/117 SKIP, Q03/B1, standalone DÉLIA, no RPA runtime. |
| GOAL / ENTRY_GATES / ALLOWED_FILES / FORBIDDEN_FILES | GOAL: baseline funcional congelada + inventário finito M01–M10 + DAG + contratos/ALLOWED_FILES para R1–R6, sem tocar runtime. ALLOWED_FILES (R0): `docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/refactor-r0-r7/r0-execution-and-evidence.md`, `README.md` (índice), `docs/12-roadmap-e-evolucao/delia/evidence/execution-ledger.md`. Scripts read-only em /tmp (não commitados). FORBIDDEN respeitado: orchestration.py, imports, prompts, schemas, CI, providers, deployment — **zero arquivos runtime alterados** (`git status` confirma: somente docs no diff). |
| FUNCTION_MAP / OWNER / REAL_CONSUMER / CONTRACT | Ver tabela completa abaixo — 186 definições inventariadas por AST (122 funções de módulo + 63 métodos de `OperationalCapabilityOrchestrator` + 1 `_StageDeadlineExceeded`), 124 constantes de módulo (17 blocos de instrução + IDs/version + key-sets/budgets tipados). Owners mapeados por batch M01–M10. |
| EXISTING_EQUIVALENT / REUSE_DECISION / NEW_FILE_GATE | Por batch: M01→loader `cri_instruction_resource.py`+`cri_presentation.delpi.json` v4 (EXISTING=YES, EXTEND condicional R1); M02→`outcome_assessment.py`/`evidence_projection.py` (EXISTING=YES parcial / candidato condicional, gate R2); M03→owner único de trust projection a definir sem duplicar (EXISTING=TO_INVENTORY); M04→`outcome_assessment.py` (YES/EXTEND); M05→`conversational_response.py` (YES/EXTEND); M06→`conversational_response.py` (YES/EXTEND condicional a M02/M03); M07→SKIP_WITH_DECISION preservado (S4/117 — nenhuma evidência nova de boundary); M08→`interaction/argument_validation.py` (YES/EXTEND para validações puras); M09→KEEP no boundary model/coordinator; M10→KEEP coordinator. **NEW_FILE_GATE: nenhum arquivo novo recomendado; `evidence_projection.py` permanece candidato condicional — exige contrato independente + nenhum equivalente real (AP-02).** |
| ACTUAL_FILES / SCOPED_DIFF / CONTRACT_COMPAT | ACTUAL=apenas os 3 arquivos de documentação listados. CONTRACT_COMPAT=NONE (sem diff de runtime). |
| IMPORT_DAG_BEFORE_AFTER / DUPLICATE_CHECK / ARCH_TESTS | DAG BEFORE (AST): `orchestration.py` importa somente stdlib+typing e módulos `application/*` e `domain/*` (interaction.activity/argument_validation/capability_attempt/contracts/pending_proposals/turn_budget/turn_observability/workspace_context; model_invocation.{contracts,errors,governed_retries,invoke_model}; capability_provision.{contracts,conversational_response,outcome_assessment,paginated_result_semantics,ports}; specialist_interop.errors; domain.{capability_catalog,decision_path,evidence,model_invocation,planning,governed_write,specialist_interop}). **Zero imports de infrastructure/adapters/framework/provider.** Único consumidor runtime: `app/composition/root_composer.py` → `OperationalCapabilityOrchestrator`. `capability_attempt.py` NÃO importa orchestration (apenas docstring) — sem ciclo. 44 arquivos de teste importam internals (alto acoplamento de teste — parity de assinatura é obrigatória em R1–R6). DAG AFTER (planejado, condicional): orchestrator → leaves tipados (`outcome_assessment`, `conversational_response`, `argument_validation`, trust-projection owner único); **nenhum leaf importa orchestration**; sem import reverso/circular. Ver §"Import DAG" abaixo. ARCH_TESTS: existentes (`architecture-ci-enforcement` diff-aware) — não executados nesta etapa (sem diff). |
| LEGACY_CURRENT / DEPRECATED_ACTIVE / OBSOLETE_PROVEN / DELETED | Auditoria residual em HEAD: S01–S17, S20–S24 e alvos lexicais das doc 56/57 **já removidos** (0 ocorrências verificadas para 22 símbolos: `_COVERAGE_INQUIRY_POSITIVE`, `_is_information_coverage_inquiry`, `_GUIDANCE_PREREQ_CUE_RE`, `_guidance_intent_families`, `_PRIOR_TRANSFORM_CUE_RE`, `_LIVE_FACT_CUE_RE`, `_USER_LIST_ORDINAL_PATTERNS`, `_user_list_ordinal`, `_INDEX_INTENT_CLUSTERS`, `_index_text_tokens`, `_index_option_relevance_score`, `_rank_index_options_by_overlap`, `_index_selection_is_relevant`, `_EXTRACTION_FOLLOWUP_RE`, `_LIMITATION_FOLLOWUP_RE`, `_count_covered_extraction_units`, `_prior_extraction_incomplete`, `_MIN_USEFUL_CONTINUITY_CHARS`, `_recover_prior_extraction_after_invalid_index`, `_extraction_list_from_prior_excerpts`, `_prior_listing_hint`, `_token_covered_by_user_tokens`, `_free_string_grounded_in_user_input`, `experimental_arguments_budget_guard`). DEPRECATED_ACTIVE candidate: `render_specialist_outcome` (L4998) — **zero consumidores runtime em `app/`**; apenas testes de caracterização (6 arquivos) → decisão de remoção/realocação em R6 com coordenação. TO_INVENTORY: `_single_free_text_argument_from_input` (S18/F36 fallback ainda ativo, 1 chamada). Nenhum OBSOLETE_PROVEN deletável em R0 (etapa read-only). |
| BASELINE_TESTS / RED_GREEN / FULL_BACKEND / SECURITY / GENERALIZATION | BASELINE congelada no BASE_SHA: suíte backend completa executada no container `infra-delia-api:latest` com `/docs` montado — resultado registrado na seção Baseline abaixo (exit code e contagem literais). RED_GREEN=NOT_APPLICABLE (sem diff de código). SECURITY/GENERALIZATION: referência congelada à homologação produtiva doc 130 (401 fail-closed, N1 contido, sibling provider-neutral) — não reexecutadas por CODE_CHANGED=NO. |
| D4/D5/D5-R/D5-schema/D8/D8-R/N1 / CRI_ON_OFF | Baseline versionada doc 130/§6.406 em `6a896a695d` (runtime), modelo prod `moonshotai/kimi-k3`, imagem `1201882fdceb`: **7/7 PASS** (D8-R com nota de variância da busca semântica do owner). CRI on/off coberto pelos testes de composição na suíte. Não reexecutado em produção nesta etapa (sem diff). |
| AI_EVAL_SHA_MODEL_CONFIG / BUSINESS_OUTCOME / POSTCONDITION | Frozen: runtime `6a896a695d`, prod Kimi `moonshotai/kimi-k3`, local Ollama `delia-json`, config vigente em HEAD. BUSINESS_OUTCOME: homologação 7/7 documentada. POSTCONDITION: n/a (sem escrita). |
| AP01_AP20_EVIDENCE_WITH_STATUS / CI_VS_MANUAL | Ver tabela AP abaixo — todos NOT_APPLICABLE_COM_RATIONALE ou PASS documental (nenhum diff runtime existe para violar). CHECK_MANUALLY_REVIEWED: diff desta etapa = somente `.md`. |
| REGRESSION_DELTA / FIRST_DIVERGENT_STAGE / NO_REGRESSION_FOR_EVALUATED_SCOPE | Escopo avaliado = documentação; `CODE_CHANGED=NO` ⇒ impossível regredir runtime por esta etapa. Baseline de comparação congelada (suite no BASE_SHA + outcomes doc 130). NO_REGRESSION_FOR_EVALUATED_SCOPE=YES (escopo documental). |
| AUTO_REWORK_USED / REWORK_RED_GREEN / REWORK_FINAL_MATRIX | 0 / NOT_APPLICABLE / NOT_APPLICABLE |
| RESIDUAL_SEARCH / ROLLBACK / SECURITY_SECRETS | Residual search executada: 22 símbolos legados S01–S24 confirmados ausentes; `render_specialist_outcome` sem consumer runtime; demais símbolos flagados (F34/F36) mapeados como CURRENT/TO_INVENTORY com nota. ROLLBACK=git revert do commit de docs (risco zero runtime). SECURITY_SECRETS: nenhum secret/token em diffs; sondas temporárias em /tmp fora do repo. |
| FINAL_HEAD / ORIGIN_MAIN_FINAL / PUSH_VERIFIED | Preenchido no rodapé após push ff-only. |
| README_LEDGER_UPDATED / DELETIONS_RATIONALE | README index + ledger §6.407 nesta entrega. DELETIONS=NONE (read-only). |
| EXECUTION_DRIFT / RESIDUALS / STOP_REASON | DRIFT=NONE. RESIDUALS: (a) doc 132 ACCEPT_WITH_RESIDUAL — resíduos D8-R variância/rótulos aninhados/catálogo parcial herdados como limitações da baseline; (b) `render_specialist_outcome` DEPRECATED_ACTIVE? aguarda decisão R6; (c) `_single_free_text_argument_from_input` TO_INVENTORY; (d) M07 SKIP/117 preservado; (e) F26/F30/F41/F42 exigem ADR/decisão fora do refactor. |
| EXECUTOR_VERDICT / COORDINATION_REVIEW_REQUIRED | `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` — R0 documental completo: inventário finito AST-based de 186 defs + 124 constantes, DAG antes/depois, classificação M01–M10 sem função sem classe, backlog de legado, baseline congelada e ALLOWED_FILES precisos para R1–R6. **Não declaro ACCEPT nem libero R1** — revisão independente obrigatória. / YES |

### Baseline funcional congelada (BASE_SHA 9a37d19917)

- **Código de release em produção:** `6a896a695d` (imagem `sha256:1201882fdceb…`), verificado healthy + 401 fail-closed em §6.406.
- **Modelo/config:** prod `moonshotai/kimi-k3`; local Ollama `delia-json`; CRI ligado; budgets 60s/chamada, ≤3 tentativas, 300s/turno.
- **Outcomes homologados (doc 130):** D4=PASS, D5=PASS, D5-R=PASS, D5-schema=PASS, D8=PASS, D8-R=PASS (variância externa documentada), N1=PASS.
- **Suíte backend no BASE_SHA:** ver resultado literal abaixo (container `infra-delia-api:latest`, `pytest tests -x -q`, `/docs` montado).

```
pytest tests -x -q @ BASE_SHA 9a37d19917 (container infra-delia-api:latest, /app+/docs+/plugins mounted)
EXIT=0 — 2165 testes coletados, 2165 PASS, 0 FAIL
Progresso 1-100% completo sem falha; log integral: sessão execução (não commitado)

```

### Import DAG — BEFORE (AST, BASE_SHA)

```
orchestration.py
 ├─ stdlib: contextvars, dataclasses, hashlib, json, logging, re, time, uuid, typing
 ├─ application.interaction: activity, argument_validation, capability_attempt,
 │    contracts, pending_proposals, turn_budget, turn_observability, workspace_context
 ├─ application.model_invocation: contracts, errors, governed_retries, invoke_model
 ├─ application.capability_provision: contracts, conversational_response,
 │    outcome_assessment, paginated_result_semantics, ports
 ├─ application.specialist_interop.errors
 └─ domain: capability_catalog.model, decision_path.{model,rules}, evidence.model,
      model_invocation.model, planning.{model,rules}, governed_write.{model,rules},
      specialist_interop.{model,rules}, interaction.model

consumers: app/composition/root_composer.py → OperationalCapabilityOrchestrator (único import runtime)
           tests/* (44 arquivos) → internals (acoplamento de teste: exige paridade de assinatura)
nenhum import de infrastructure/adapters/framework — direção da dependência correta
```

### Import DAG — AFTER planejado (condicional, sujeito a gates R1–R6)

```
orchestration.py (coordinator)
 ├─ application.interaction.argument_validation   ← M08 validações puras (EXTEND)
 ├─ capability_provision.outcome_assessment       ← M02 projections + M04 (EXTEND)
 │      [ou evidence_projection.py SOMENTE se gate AP-02 provar contrato/consumidor]
 ├─ capability_provision.conversational_response  ← M05/M06 renderers (EXTEND)
 ├─ capability_provision.trust-projection owner único ← M03 (destino a decidir em R2;
 │      PROIBIDO duplicar sanitizers; candidato natural = módulo existente no boundary)
 ├─ model_invocation.*                            ← M09 (KEEP: proposals tipadas no coordinator)
 └─ domain/* (inalterado)

regra de inversão: leaves NUNCA importam orchestration.py; presentation consome DTO saneado;
M07 guidance permanece em orchestration.py (SKIP/117) salvo evidência nova de boundary.
```

### Matriz ENTRYPOINT → CAPABILITY → OWNER → CONTRACT → CONSUMERS → EXECUTION BOUNDARY → OUTCOME (doc 128 §7)

| Entrypoint | Capability | Owner | Contract (estado) | Executor | Outcome verifier |
|---|---|---|---|---|---|
| Conversa DÉLIA | interpretação→descoberta→evidência→PREPARE/ACT | DÉLIA Application | `attempt()`/`GovernedCapabilityAttempt` — PROVEN | ports/adapters → Domain API/MCP | `assess_outcome` + Domain postcondition |
| Work recorrente | objetivo/constraints/instância/reavaliação | DÉLIA Work | TARGET — sem contrato congelado | scheduler legítimo + Hub | Domain API (nunca status técnico) |
| Evento/Watch | observe/contextualize/advise | DÉLIA intelligence | TARGET/TO_INVENTORY | fonte de evento real | observation/decision candidate |
| App externo | análise/PREPARE por referência | DÉLIA (só se inteligência necessária) | PLANNED — NÃO endpoint existente | owner correto / Hub | typed response + provenance |
| Executor RPA | action preparada + idempotency | Automation Hub (execução); DÉLIA (decisão) | TARGET — físico TO_INVENTORY | RPA worker/Human Task | `VERIFIED_*` via Domain postcondition |
| Consulta determinística | leitura sem inteligência | Domain API/Core | contrato existente | owner direto (DÉLIA não é gateway) | domain result |

**Prova de desacoplamento conversacional (signatures AST):** das 186 definições, somente 5 funções recebem contexto de turno tipado (`_prior_observation_context`, `_context_folded_discovery_query`, `_group_summaries`, `_capability_payload`, `_unproven_identifier_inputs` — todas com `prior_turns`/`workspace_context` tipados, **nenhuma** depende de `ConversationTurn`/Markdown/HTTP/cookies). As projeções M02/M03/M06/M07 são funções puras payload→valor — materialmente separáveis do canal conversacional sem novos DTOs.

### Inventário finito por função (AST — 186 defs, BASE_SHA)

Colunas: BATCH (M01–M10) · STATUS (KEEP/EXTEND/EXTRACT?/SKIP_WITH_DECISION?/TO_INVENTORY — `?` = sujeito a gate da etapa, não autorização antecipada) · TARGET file preferencial · refs in-file (ocorrências do símbolo no arquivo, inclui a definição) · LEGACY/nota.

| SYMBOL | LINE | LINES | BATCH | STATUS | TARGET | CONSUMERS(in-file refs / ext) | LEGACY |
|---|---|---|---|---|---|---|---|
| `_lineage` | 843 | 10 | M01 | KEEP | orchestration.py (boundary semantico) | 4 refs in-file; - | lineage typed, not text |
| `_candidate_args_lineage` | 892 | 4 | M01 | KEEP | orchestration.py | 2 refs in-file; - | lineage |
| `_candidate_selection_lineage` | 898 | 4 | M01 | KEEP | orchestration.py | 2 refs in-file; - | lineage |
| `_is_candidate_bound` | 904 | 3 | M08 | KEEP | orchestration.py | 6 refs in-file; - | descriptor check |
| `_is_proposal_bound` | 909 | 5 | M08 | KEEP | orchestration.py | 2 refs in-file; - | descriptor check |
| `_requires_field` | 916 | 10 | M08 | EXTEND? | argument_validation.py | 3 refs in-file; - | pure schema |
| `_is_open_vocabulary` | 928 | 27 | M08 | EXTEND? | argument_validation.py | 5 refs in-file; - | pure schema |
| `_is_unconstrained_string` | 957 | 34 | M08 | EXTEND? | argument_validation.py | 3 refs in-file; - | pure schema |
| `_requires_owner_vocabulary` | 993 | 19 | M08 | EXTEND? | argument_validation.py | 4 refs in-file; - | pure schema |
| `_contract_declares_omit_returns_index` | 1014 | 34 | M08 | KEEP | orchestration.py | 2 refs in-file; - | owner contract check; F29 review |
| `_optional_unconstrained_string_keys` | 1050 | 22 | M08 | EXTEND? | argument_validation.py | 8 refs in-file; - | pure schema |
| `_index_catalog_entities` | 1074 | 37 | M08 | EXTEND? | argument_validation.py | 2 refs in-file; - | index eligibility |
| `_index_option_rows` | 1113 | 76 | M08 | EXTEND? | argument_validation.py | 3 refs in-file; - | index eligibility |
| `_index_declared_identifiers` | 1191 | 10 | M08 | EXTEND? | argument_validation.py | 2 refs in-file; - | index eligibility |
| `_post_self_index_argument_gaps` | 1203 | 38 | M08 | EXTEND? | argument_validation.py | 3 refs in-file; - | pure schema |
| `_project_selected_index_identifier` | 1243 | 16 | M08 | EXTEND? | argument_validation.py | 2 refs in-file; - | index binding |
| `_eligible_self_index_probe` | 1261 | 27 | M08 | EXTEND? | argument_validation.py | 2 refs in-file; - | eligibility |
| `_plan_views` | 1314 | 13 | M10 | KEEP | orchestration.py | 3 refs in-file; - | coordinator/pure helper |
| `_discovery_capability` | 1329 | 9 | M10 | KEEP | orchestration.py | 4 refs in-file; - | coordinator/pure helper |
| `_owner_eligible_action_count` | 1343 | 18 | M10 | KEEP | orchestration.py | 4 refs in-file; - | coordinator/pure helper |
| `_discovery_empty_result_class` | 1363 | 14 | M10 | KEEP | orchestration.py | 3 refs in-file; - | coordinator/pure helper |
| `_live_interop_surface_lines` | 1379 | 29 | M06 | EXTRACT? | conversational_response.py | 4 refs in-file; - | render |
| `_render_zero_candidate_discovery` | 1410 | 62 | M06 | EXTRACT? | conversational_response.py | 2 refs in-file; - | render |
| `_surface_inquiry_content` | 1477 | 60 | M06 | EXTRACT? | conversational_response.py | 2 refs in-file; - | D4 content |
| `_find_capability` | 1548 | 16 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator/pure helper |
| `_comparison_records` | 1566 | 12 | M02 | EXTRACT? | evidence_projection.py | 3 refs in-file; - | comparison evidence |
| `_comparable_scalar` | 1580 | 11 | M02 | EXTRACT? | evidence_projection.py | 7 refs in-file; - | comparison |
| `_compare_records` | 1626 | 128 | M02 | TO_INVENTORY | outcome_assessment.py | 2 refs in-file; - | F41/F42 contract drift — reconcile policy first |
| `_bound_owner_evidence` | 1756 | 30 | M02 | EXTRACT? | evidence_projection.py/outcome_assessment.py | 8 refs in-file; - | gate R2 |
| `_is_capability_descriptor` | 1859 | 16 | M03 | EXTRACT? | single trust-projection owner | 2 refs in-file; - | plan-named |
| `_without_control_plane` | 1877 | 17 | M03 | EXTRACT? | single trust-projection owner | 5 refs in-file; - | plan-named |
| `_contract_fact_rows` | 1896 | 138 | M02 | EXTRACT? | evidence_projection.py | 3 refs in-file; - | plan-named |
| `_compact_evidence` | 2036 | 37 | M02 | EXTRACT? | evidence_projection.py | 7 refs in-file; - | plan-named |
| `_evidence_rows` | 2075 | 27 | M02 | EXTRACT? | evidence_projection.py | 4 refs in-file; - | plan-named |
| `_missing_inputs` | 2104 | 10 | M02 | EXTRACT? | evidence_projection.py | 2 refs in-file; - | pure |
| `_extract_owner_entity_schemas` | 2127 | 28 | M02 | EXTRACT? | evidence_projection.py | 3 refs in-file; - | pure |
| `_entity_payload_slot` | 2157 | 15 | M02 | EXTRACT? | evidence_projection.py | 3 refs in-file; - | pure |
| `_value_present` | 2174 | 8 | M02 | EXTRACT? | evidence_projection.py | 4 refs in-file; - | pure |
| `_schema_required_gaps` | 2184 | 61 | M08 | EXTEND | argument_validation.py | 4 refs in-file; - | plan-named |
| `_apply_owner_declared_defaults` | 2247 | 13 | M08 | EXTEND | argument_validation.py | 3 refs in-file; - | plan-named |
| `_owner_entity_completeness_gaps` | 2262 | 48 | M08 | EXTEND? | argument_validation.py | 2 refs in-file; - | completeness |
| `_apply_entity_defaults_to_arguments` | 2312 | 20 | M08 | EXTEND? | argument_validation.py | 4 refs in-file; - | defaults |
| `_argument_completeness_gaps` | 2334 | 19 | M08 | EXTEND | argument_validation.py | 4 refs in-file; - | plan-named |
| `_wording_leaks_technical` | 2409 | 9 | M03 | EXTRACT? | single trust-projection owner | 2 refs in-file; - | F39 review gate |
| `_clarification_content` | 2420 | 25 | M06 | EXTRACT? | conversational_response.py | 3 refs in-file; - | user-facing text |
| `_synthesis_selections` | 2447 | 60 | M02 | EXTRACT? | evidence_projection.py | 3 refs in-file; - | selection shaping |
| `_render_synthesis` | 2509 | 88 | M06 | EXTRACT? | conversational_response.py | 3 refs in-file; - | plan-named; F26/F30 gate |
| `_proven_field_differences` | 2599 | 25 | M02 | EXTRACT? | evidence_projection.py | 4 refs in-file; - | comparison |
| `_selected_proven_differences` | 2626 | 20 | M02 | EXTRACT? | evidence_projection.py | 2 refs in-file; - | comparison |
| `_insufficiency_content` | 2656 | 3 | M06 | EXTRACT? | conversational_response.py | 6 refs in-file; - | user-facing text |
| `_is_prior_list_item` | 2661 | 2 | M02 | KEEP? | orchestration.py | 4 refs in-file; - | S16 pair |
| `_prior_paragraph_units` | 2665 | 43 | M02 | KEEP? | orchestration.py | 2 refs in-file; - | S16 pair |
| `_prior_excerpt_records` | 2710 | 28 | M02 | KEEP? | orchestration.py | 3 refs in-file; - | S16: presentation-only parsing of prior text |
| `_prior_transform_probe_eligible` | 2740 | 20 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator/pure helper |
| `_record_identifier` | 2800 | 36 | M02 | EXTRACT? | evidence_projection.py | 4 refs in-file; - | pure |
| `_compose_answer` | 2838 | 47 | M06 | EXTRACT? | conversational_response.py | 5 refs in-file; - | plan-named |
| `_detail_header` | 2887 | 11 | M06 | EXTRACT? | conversational_response.py | 2 refs in-file; - | plan-named |
| `_detail_lines` | 2900 | 21 | M06 | EXTRACT? | conversational_response.py | 2 refs in-file; - | plan-named |
| `_records_are_prior_excerpts` | 2923 | 14 | M02 | KEEP? | orchestration.py | 3 refs in-file; - | S16 pair |
| `_list_header` | 2939 | 21 | M06 | EXTRACT? | conversational_response.py | 2 refs in-file; - | render |
| `_project_paginated_personal_or_count` | 2962 | 54 | M10 | KEEP | orchestration.py | 3 refs in-file; - | coordinator/pure helper |
| `_unwrap_owner_payload` | 3047 | 13 | M02 | EXTRACT? | evidence_projection.py | 9 refs in-file; - | pure |
| `_resolver_entities` | 3062 | 41 | M10 | KEEP | orchestration.py | 5 refs in-file; - | resolver flow |
| `_guidance_family_for_key` | 3268 | 12 | M07 | SKIP_WITH_DECISION? | 117 | 3 refs in-file; - | plan-named |
| `_render_guidance_value` | 3313 | 37 | M07 | SKIP_WITH_DECISION? | 117 | 3 refs in-file; - | guidance-specific render |
| `_mapping_items_excluding_control` | 3352 | 8 | M03 | EXTRACT? | single trust-projection owner | 4 refs in-file; - | trust |
| `_guidance_hit_count` | 3362 | 6 | M07 | SKIP_WITH_DECISION? | 117 | 4 refs in-file; - | guidance |
| `_iter_guidance_doc_items` | 3370 | 38 | M07 | SKIP_WITH_DECISION? | 117 | 2 refs in-file; - | guidance |
| `_guidance_section_records` | 3410 | 55 | M07 | SKIP_WITH_DECISION? | 117 | 3 refs in-file; - | plan-named |
| `_omitted_sections_line` | 3467 | 21 | M07 | SKIP_WITH_DECISION? | 117 | 4 refs in-file; - | guidance |
| `_pack_guidance_sections` | 3490 | 53 | M07 | SKIP_WITH_DECISION? | 117 | 3 refs in-file; - | plan-named |
| `_deterministic_guidance_content` | 3545 | 41 | M07 | SKIP_WITH_DECISION? | 117 | 9 refs in-file; - | plan-named |
| `_explicit_empty_business_collection` | 3607 | 42 | M02 | EXTRACT? | evidence_projection.py | 2 refs in-file; - | envelope class |
| `_synthesis_records` | 3651 | 55 | M02 | EXTRACT? | evidence_projection.py | 4 refs in-file; - | record shaping |
| `_entity_identifier` | 3708 | 25 | M08 | EXTEND? | argument_validation.py | 6 refs in-file; - | arg binding aid |
| `_resolver_ambiguous` | 3735 | 17 | M10 | KEEP | orchestration.py | 2 refs in-file; - | resolver flow |
| `_prior_observation_context` | 3754 | 24 | M10 | KEEP | orchestration.py | 5 refs in-file; - | coordinator/pure helper |
| `_context_folded_discovery_query` | 3780 | 28 | M10 | KEEP | orchestration.py | 3 refs in-file; - | coordinator/pure helper |
| `_fill_missing_from_entity` | 3810 | 29 | M08 | EXTEND? | argument_validation.py | 2 refs in-file; - | arg fill |
| `_candidate_clarification_content` | 3841 | 45 | M06 | EXTRACT? | conversational_response.py | 2 refs in-file; - | user-facing text |
| `_resolved_values_proven` | 3888 | 19 | M08 | KEEP | orchestration.py | 4 refs in-file; - | S19/F34 provenance gate fail-closed |
| `_schema_declared_literals` | 3909 | 30 | M08 | EXTEND? | argument_validation.py | 2 refs in-file; - | pure schema |
| `_unproven_identifier_inputs` | 3941 | 49 | M08 | KEEP | orchestration.py | 8 refs in-file; - | S19/F34 provenance gate fail-closed |
| `_effective_confirmation_policy` | 3997 | 30 | M10 | KEEP | orchestration.py | 2 refs in-file; - | confirmation |
| `_schema_keys` | 4029 | 21 | M08 | EXTEND? | argument_validation.py | 13 refs in-file; - | pure schema |
| `_property_node` | 4052 | 10 | M08 | EXTEND? | argument_validation.py | 3 refs in-file; - | pure schema |
| `_sole_unconstrained_string_field` | 4064 | 23 | M08 | EXTEND? | argument_validation.py | 2 refs in-file; - | pure schema |
| `_single_free_text_argument_from_input` | 4089 | 17 | M08 | TO_INVENTORY | argument_validation.py | 2 refs in-file; - | S18/F36 fallback — legacy review |
| `_deterministic_arguments_from_schema` | 4108 | 48 | M08 | EXTEND? | argument_validation.py | 2 refs in-file; - | pure schema |
| `_index_selection_is_member` | 4158 | 13 | M08 | EXTEND? | argument_validation.py | 2 refs in-file; - | membership; F35 resolved |
| `_prior_supports_typed_attribute_compare` | 4173 | 31 | M02 | EXTRACT? | evidence_projection.py | 2 refs in-file; - | comparison |
| `_compare_insufficiency_attempt` | 4206 | 21 | M10 | KEEP | orchestration.py | 5 refs in-file; - | coordinator/pure helper |
| `_project_surface` | 4229 | 19 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator/pure helper |
| `_resolve_live_group_key` | 4250 | 22 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator/pure helper |
| `_group_summaries` | 4274 | 71 | M10 | KEEP | orchestration.py | 3 refs in-file; - | coordinator/pure helper |
| `_capability_payload` | 4347 | 45 | M10 | KEEP | orchestration.py | 4 refs in-file; - | coordinator/pure helper |
| `_canonical_key` | 4429 | 2 | M03 | EXTRACT? | single trust-projection owner | 78 refs in-file; - | plan-named; 78 refs |
| `_is_sensitive_key` | 4433 | 2 | M03 | EXTRACT? | single trust-projection owner | 2 refs in-file; - | trust |
| `_redact_text` | 4489 | 9 | M03 | EXTRACT? | single trust-projection owner | 18 refs in-file; - | plan-named |
| `_sanitize_renderable` | 4500 | 29 | M03 | EXTRACT? | single trust-projection owner | 12 refs in-file; - | plan-named |
| `_is_generic_status` | 4541 | 2 | M03 | EXTRACT? | single trust-projection owner | 2 refs in-file; - | trust |
| `_format_structured` | 4545 | 53 | M06 | EXTRACT? | conversational_response.py | 11 refs in-file; - | render |
| `_format_list` | 4600 | 33 | M06 | EXTRACT? | conversational_response.py | 2 refs in-file; - | render |
| `_format_records` | 4635 | 20 | M06 | EXTRACT? | conversational_response.py | 4 refs in-file; - | render |
| `_business_lines` | 4657 | 48 | M06 | EXTRACT? | conversational_response.py | 5 refs in-file; - | render |
| `_md_leaf` | 4743 | 6 | M06 | EXTRACT? | conversational_response.py | 16 refs in-file; - | render |
| `_md_format_structured` | 4751 | 50 | M06 | EXTRACT? | conversational_response.py | 7 refs in-file; - | plan-named |
| `_md_format_list` | 4803 | 42 | M06 | EXTRACT? | conversational_response.py | 2 refs in-file; - | render |
| `_md_format_records` | 4847 | 19 | M06 | EXTRACT? | conversational_response.py | 3 refs in-file; - | render |
| `_md_business_lines` | 4868 | 40 | M06 | EXTRACT? | conversational_response.py | 4 refs in-file; - | plan-named |
| `_select_guidance_records` | 4910 | 24 | M07 | SKIP_WITH_DECISION? | 117 | 3 refs in-file; - | plan-named |
| `_md_guidance_content` | 4936 | 44 | M07 | SKIP_WITH_DECISION? | 117 | 3 refs in-file; - | guidance render |
| `render_specialist_outcome` | 4998 | 14 | M06 | TO_INVENTORY | conversational_response.py | 1 refs in-file; - | 0 runtime consumers — DEPRECATED_ACTIVE candidate |
| `render_specialist_outcome_rich` | 5014 | 205 | M06 | EXTRACT? | conversational_response.py | 7 refs in-file; - | render |
| `_find_act_capability` | 5258 | 18 | M10 | KEEP | orchestration.py | 3 refs in-file; - | ACT lookup |
| `_act_arguments` | 5278 | 25 | M10 | KEEP | orchestration.py | 2 refs in-file; - | ACT args |
| `_preview_render` | 5305 | 28 | M06 | EXTRACT? | conversational_response.py | 2 refs in-file; - | preview |
| `_emit_activity` | 5438 | 10 | M10 | KEEP | orchestration.py | 9 refs in-file; - | coordinator/pure helper |
| `_cancel_observed` | 5510 | 5 | M10 | KEEP | orchestration.py | 6 refs in-file; - | coordinator/pure helper |
| `_resume_stage_key` | 5525 | 14 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator/pure helper |
| `_resume_invoke_key` | 5541 | 12 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator/pure helper |
| `_group_activity_refs` | 5555 | 18 | M10 | KEEP | orchestration.py | 5 refs in-file; - | coordinator/pure helper |
| `_activity_outcome_summary` | 5575 | 35 | M10 | KEEP | orchestration.py | 2 refs in-file; - | activity bookkeeping |
| `_StageDeadlineExceeded.__init__` | 5622 | 4 | M10 | KEEP | orchestration.py | 3 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator.__init__` | 5647 | 97 | M10 | KEEP | orchestration.py | 3 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator.attempt` | 5745 | 164 | M10 | KEEP | orchestration.py | 49 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._attempt` | 5910 | 1367 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._resolve_missing_inputs` | 7288 | 203 | M10 | KEEP | orchestration.py | 3 refs in-file; - | resolver flow |
| `OperationalCapabilityOrchestrator._select_resolver` | 7492 | 85 | M09 | KEEP | orchestration.py | 2 refs in-file; - | selection stage |
| `OperationalCapabilityOrchestrator._analysis_continuation` | 7578 | 109 | M10 | KEEP | orchestration.py | 2 refs in-file; - | continuation flow |
| `OperationalCapabilityOrchestrator._turn_goal_from_proposal` | 7748 | 112 | M09 | KEEP | orchestration.py | 3 refs in-file; - | plan-named |
| `OperationalCapabilityOrchestrator._understand_goal` | 7861 | 39 | M09 | KEEP | orchestration.py | 4 refs in-file; - | goal stage |
| `OperationalCapabilityOrchestrator._prior_result_turn` | 7902 | 10 | M10 | KEEP | orchestration.py | 4 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._prior_result_content` | 7914 | 15 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._budget_allows_resolver` | 7930 | 17 | M10 | KEEP | orchestration.py | 5 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._budget_allows_optional_index_probe` | 7948 | 25 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._prior_continuation_attempt` | 7974 | 200 | M10 | KEEP | orchestration.py | 2 refs in-file; - | continuation flow; S12-S14 resolved |
| `OperationalCapabilityOrchestrator._assess_native_path` | 8175 | 77 | M09 | KEEP | orchestration.py | 2 refs in-file; - | assessment stage |
| `OperationalCapabilityOrchestrator._select_foreign_capability` | 8253 | 77 | M09 | KEEP | orchestration.py | 2 refs in-file; - | selection stage |
| `OperationalCapabilityOrchestrator._invoke_foreign_evidence` | 8340 | 88 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._corroborate_attempt` | 8429 | 125 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._select_prepare_continuation` | 8555 | 71 | M09 | KEEP | orchestration.py | 2 refs in-file; - | selection stage |
| `OperationalCapabilityOrchestrator._attempt_prepare` | 8629 | 214 | M10 | KEEP | orchestration.py | 3 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._attempt_direct_act` | 8844 | 70 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._attempt_confirmation` | 8915 | 89 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._confirm_proposal` | 9005 | 122 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._execute_prepared_act` | 9128 | 107 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._invoke_act` | 9236 | 84 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._provenance` | 9321 | 33 | M10 | KEEP | orchestration.py | 3 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._apply_outcome_assessment` | 9355 | 45 | M04 | EXTEND | outcome_assessment.py | 2 refs in-file; - | plan-named |
| `OperationalCapabilityOrchestrator._outcome_facts` | 9402 | 61 | M04 | EXTEND | outcome_assessment.py | 2 refs in-file; - | plan-named |
| `OperationalCapabilityOrchestrator._cri_scalar_text` | 9470 | 24 | M05 | EXTEND | conversational_response.py | 3 refs in-file; - | plan-named |
| `OperationalCapabilityOrchestrator._cri_presented_record` | 9495 | 77 | M05 | EXTEND | conversational_response.py | 2 refs in-file; - | plan-named |
| `OperationalCapabilityOrchestrator._compose_cri_response` | 9573 | 100 | M05 | EXTEND | conversational_response.py | 2 refs in-file; - | plan-named |
| `OperationalCapabilityOrchestrator._outcome_attempt` | 9674 | 106 | M04 | EXTEND | outcome_assessment.py | 6 refs in-file; - | verdict projection |
| `OperationalCapabilityOrchestrator._audit` | 9781 | 31 | M10 | KEEP | orchestration.py | 10 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._groups` | 9815 | 36 | M10 | KEEP | orchestration.py | 3 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._fresh_group` | 9852 | 28 | M10 | KEEP | orchestration.py | 3 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._select_target` | 9881 | 105 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._build_plan` | 9987 | 81 | M10 | KEEP | orchestration.py | 4 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._log_plan` | 10070 | 14 | M10 | KEEP | orchestration.py | 6 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._model_stage_proposal` | 10085 | 268 | M09 | KEEP | orchestration.py | 4 refs in-file; - | plan-named |
| `OperationalCapabilityOrchestrator._propose` | 10354 | 69 | M09 | KEEP | orchestration.py | 17 refs in-file; - | plan-named |
| `OperationalCapabilityOrchestrator._clarification_question` | 10428 | 79 | M09 | KEEP | orchestration.py | 5 refs in-file; - | model-stage |
| `OperationalCapabilityOrchestrator._maybe_aggregate_paginated_count` | 10508 | 130 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._synthesize_content` | 10639 | 224 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._repair_once` | 10864 | 75 | M09 | KEEP | orchestration.py | 2 refs in-file; - | plan-named |
| `OperationalCapabilityOrchestrator._recover_owner_contract` | 10940 | 113 | M09 | KEEP | orchestration.py | 2 refs in-file; - | model-stage recovery |
| `OperationalCapabilityOrchestrator._admit_conversational_turn` | 11054 | 115 | M09 | KEEP | orchestration.py | 2 refs in-file; - | admission stage; S21 resolved |
| `OperationalCapabilityOrchestrator._surface_inquiry_attempt` | 11170 | 18 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._select_group` | 11189 | 64 | M09 | KEEP | orchestration.py | 2 refs in-file; - | selection stage; S20 resolved |
| `OperationalCapabilityOrchestrator._capability_from_selection_proposal` | 11255 | 47 | M09 | KEEP | orchestration.py | 3 refs in-file; - | proposal binding |
| `OperationalCapabilityOrchestrator._select_capability` | 11303 | 62 | M09 | KEEP | orchestration.py | 4 refs in-file; - | selection stage |
| `OperationalCapabilityOrchestrator._select_capability_with_goal` | 11366 | 79 | M09 | KEEP | orchestration.py | 2 refs in-file; - | selection stage |
| `OperationalCapabilityOrchestrator._propose_index_probe` | 11446 | 42 | M09 | KEEP | orchestration.py | 2 refs in-file; - | model-stage |
| `OperationalCapabilityOrchestrator._bind_arguments_from_index` | 11489 | 68 | M09 | KEEP | orchestration.py | 2 refs in-file; - | model-stage bound |
| `OperationalCapabilityOrchestrator._propose_index_identifier` | 11558 | 66 | M09 | KEEP | orchestration.py | 2 refs in-file; - | model-stage |
| `OperationalCapabilityOrchestrator._build_arguments` | 11625 | 131 | M08 | KEEP | orchestration.py | 12 refs in-file; - | plan-named; flow stays coordinator |
| `OperationalCapabilityOrchestrator._invoke_selected` | 11757 | 187 | M10 | KEEP | orchestration.py | 8 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._discover_candidate` | 11945 | 60 | M10 | KEEP | orchestration.py | 2 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._candidates_present` | 12007 | 7 | M10 | KEEP | orchestration.py | 4 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._resolve_candidate` | 12015 | 39 | M10 | KEEP | orchestration.py | 5 refs in-file; - | coordinator |
| `OperationalCapabilityOrchestrator._select_candidate` | 12055 | 67 | M09 | KEEP | orchestration.py | 2 refs in-file; - | F31 dedup candidate |
| `OperationalCapabilityOrchestrator._candidate_arguments` | 12123 | 53 | M09 | KEEP | orchestration.py | 3 refs in-file; - | model-stage |
| `OperationalCapabilityOrchestrator._propose_candidate_arguments` | 12177 | 35 | M09 | KEEP | orchestration.py | 2 refs in-file; - | F31 dedup candidate |
| `OperationalCapabilityOrchestrator._invoke` | 12213 | 194 | M10 | KEEP | orchestration.py | 13 refs in-file; - | coordinator |


### Constantes de módulo (124) — classificação por família

| Família | Símbolos | BATCH | STATUS | Nota |
|---|---|---|---|---|
| Instruction text + IDs + version | 17 blocos `*_INSTRUCTION` + `*_INSTRUCTION_ID` + `SELECTION_INSTRUCTION_VERSION` (L257–880, 5366–5369) | M01 | EXTRACT? → recurso versionado (`cri_instruction_resource.py` pattern) | snapshots/hash lineage obrigatórios; proposal schemas ficam em Python |
| User-facing content strings | `_INTENT_CLARIFICATION_CONTENT`, `_SELECTION_INCONCLUSIVE_CONTENT`, `_INSUFFICIENCY_CONTENT`, `_READINESS_NOTE`, `_OUTCOME_NOTE`, `EMPTY_RESULT_TEXT` | M01 | EXTRACT? → vocabulário JSON governado | falha closed se recurso inválido |
| Key-sets de contrato/tipagem | `_EVIDENCE_DROPPED_KEYS`, `_CAPABILITY_VOCABULARY_KEYS`, `_DISCOVERY_ENVELOPE_KEYS`, `_CAPABILITY_DESCRIPTOR_*`, `_ENTITY_*_KEYS`, `_RESOLVER_*`, `_CONTROL_PLANE_KEYS`, `_GUIDANCE_*`, `_ENVELOPE_SCALAR_KEYS`, `_COMPARISON_TECHNICAL_KEYS`, `_IDENTIFIER_*`, `_PRESENTATION_INTENTS`, `_PATH_FOREIGN_CLASSES`, `_PLAN_OPERATION_CHARACTER`, `_WRITE_OPERATION_CLASSES`, `_RESUMABLE_OPERATION_CLASSES`, `_REPAIRABLE_SURFACE_CODES`, `_OWNER_REMOTE_ERROR_CODES`, `_INCONCLUSIVE_*` | M02/M03/M07/M10 | KEEP | contratos tipados — NÃO mover para JSON (AP-14: lógica em JSON proibida) |
| Trust/sanitization sets | `_SENSITIVE_KEY_NAMES`, `_TEXT_REDACTIONS`, `_GENERIC_COMPLETION_TEXTS`, `_TECHNICAL_LEAK_MARKERS`, `REDACTION_MARKER`, `_SNAKE_CASE_TOKEN_RE`, `_UUID_VALUE_RE`, `_PRIOR_SENTENCE_SPLIT_RE`, `_MD_*` | M03/M06 | KEEP com owner único M03 | proteção RC1/RC2 centralizada |
| Budgets/limits | `MAX_*` (22), `MODEL_STAGE_TIMEOUT_SECONDS`, `MIN_VIABLE_MODEL_STAGE_SECONDS`, `CONVERSATIONAL_FALLBACK_RESERVE_SECONDS`, `DEFAULT_INTERACTION_TOTAL_BUDGET_SECONDS`, `MAX_GOVERNED_ATTEMPTS`, `_ATTEMPT_INDEX`, `_RESUME_STATE`, `_CANCEL_CHECK`, `_ACTIVITY_SINK`, `CANDIDATE_TOKEN_FIELD`, `PROPOSAL_HANDLE_FIELD`, `CONFIRMATION_POLICY_*`, `_ITEMS_KEY`, `_logger` | M09/M10 | KEEP | contratos de budget/tempo tipados; 60/3/300 congelado |

### ALLOWED_FILES precisos propostos para R1–R6 (contrato de saída R0)

| Etapa | ALLOWED_FILES | FORBIDDEN extra |
|---|---|---|
| R1 (M01) | `orchestration.py` (remoção de blocos de texto substituídos), `infrastructure/config/cri_instruction_resource.py` ou loader equivalente existente, `config/*.delpi.json` (novo recurso versionado se necessário), testes de snapshot/lineage | proposal schemas, instruction-ids, semantics |
| R2 (M02–M03) | `orchestration.py`, `capability_provision/outcome_assessment.py`, `capability_provision/evidence_projection.py` **somente se gate AP-02**, testes | duplicar sanitizer; import orchestration em leaf |
| R3 (M04–M05) | `orchestration.py`, `capability_provision/outcome_assessment.py`, `capability_provision/conversational_response.py`, testes | CRI escrever fatos; verdict no renderer |
| R4 (M06–M07) | `orchestration.py`, `capability_provision/conversational_response.py`, `interaction/presentation.py`, `config/cri_presentation.delpi.json`, testes | `guidance_projection.py` sem resolução formal S4/117 |
| R5 (M08–M09) | `orchestration.py`, `interaction/argument_validation.py`, testes | parser semântico, provider registry, alterar retries/budgets |
| R6 (M10 + residual) | `orchestration.py`, remoções de legado provado (ex.: `render_specialist_outcome` se decidido), testes | state machine, PREPARE/ACT, Policy/idempotency |

### Harmonização de auditorias anteriores (doc 56 S01–S25, doc 57 F26–F42, doc 113 G-SA1–10)

- **S01–S17, S20–S24:** símbolos removidos em remediações anteriores — 0 ocorrências confirmadas em HEAD (lista na tabela LEGACY acima). RESOLVED.
- **S05** `_prior_transform_probe_eligible`: ainda presente (L2740) — typed-goal gate; reclassificar CURRENT com nota (sinais typed, não lexical puro).
- **S16** prior-excerpt parsing: presente (L2661–2936) — parsing de apresentação para continuação; CURRENT conforme prescrição S16.
- **S18/F36** `_single_free_text_argument_from_input` (L4089): ativo, 1 caller — TO_INVENTORY para decisão R5/R6.
- **S19/F34** `_resolved_values_proven`/`_unproven_identifier_inputs` (L3888/3941): provenance gates fail-closed ativos — KEEP (recomendação original era manter + refs tipadas; refs tipadas presentes via `SourceRef`).
- **S25/F41/F42** `_compare_records` (L1626): drift de contrato com `COMPARISON_INSTRUCTION` — TO_INVENTORY; exige reconciliação de política (não enfraquecer comparabilidade silenciosamente).
- **F26/F30** síntese selection-only: preservado como decisão congelada — qualquer prosa factual do modelo exigiria ADR fora do refactor.
- **F27** `_GUIDANCE_SECTION_FAMILIES` (L3115+): coberto por M07 SKIP/117.
- **F28** classificadores externos `paginated_result_semantics`: fronteira cross-file documentada; KEEP fail-closed.
- **F29/F32** self-index/admission: partially resolved na refatoração provider-neutral; `_contract_declares_omit_returns_index`/`_eligible_self_index_probe` KEEP com nota de contract-review.
- **F31** candidate stages duplicam wiring de `_propose`: TO_INVENTORY para dedup interno em R5 (mesma decisão/contrato, menor wiring).
- **F33** continuation outcome: endereçado por D8-R + `_outcome_attempt`; CURRENT.
- **F35** veto lexical de index options: resolvido — `_index_selection_is_member` reduzido a membership (L4158).
- **F37/F38** budget/serial surface queries + optional probe unreachable: PERFORMANCE/MODEL_CALL investigação documental; sem ação de código em R0 — TO_INVENTORY para R5/R6.
- **F39** `_wording_leaks_technical`/`_GENERIC_COMPLETION_TEXTS`: gate de apresentação — KEEP com revisão PRESENTATION_GATE em R4.
- **F40** coverage regex override: `_COVERAGE_INQUIRY_*` removido — RESOLVED.
- **G-SA1–G-SA10:** mapeados para M01–M10 na tabela de funções (G-SA3/RC1-RC2 → M03; G-SA4 → M04; G-SA5 → M07 SKIP; G-SA6 → M06; G-SA9 governed chain → M10 KEEP).

### Tabela AP-01…AP-20 (R0 documental)

| Gate | Status | Evidência |
|---|---|---|
| AP-01 god module | PASS | nenhum módulo criado; proposta mantém responsabilidades separadas por batch |
| AP-02 NEW sem owner/consumer | PASS | 0 arquivos novos; `evidence_projection.py` marcado condicional (gate pendente) |
| AP-03 import circular/reverso | PASS | DAG AST comprova ausência; nenhum leaf importa orchestration |
| AP-04 duplicação | PASS | nenhuma duplicação introduzida; backlog exige owner único p/ sanitizers |
| AP-05/06 planner lexical/provider | PASS | nenhuma heurística introduzida; remoções lexicais anteriores confirmadas |
| AP-07/08/09/10/11 autoridade/RPA | NOT_APPLICABLE | sem diff runtime; RPA runtime não criado (proibido) |
| AP-12/13 evidence/CRI | NOT_APPLICABLE | sem diff runtime; fronteira evidence mapeada para owner legítimo |
| AP-14 JSON com lógica | PASS | key-sets/budgets tipados classificados KEEP-fora-de-JSON |
| AP-15 contrato quebrado | PASS | nenhum contrato alterado |
| AP-16 diff concorrente | PASS | escopo = 3 arquivos .md; untracked alheios preservados |
| AP-17 teste insuficiente | NOT_APPLICABLE | R0 documental; suite baseline executada para freeze (abaixo) |
| AP-18 secrets | PASS | nenhum secret em diffs/scripts |
| AP-19 consumer fake | PASS | nenhum consumer TARGET inventado; matriz entrypoint marcada TARGET/TO_INVENTORY |
| AP-20 decisão congelada | PASS | S4/117 preservado (M07 SKIP); Q03/B1 não reabertos |

### Revisão independente (preencher SOMENTE pela coordenação)

`REVIEW_SHA=PENDING` · `REVIEW_VERDICT=PENDING` · `ACCEPTANCE_REASON=PENDING` · `NEXT_STAGE_AUTHORIZED=NO`.

