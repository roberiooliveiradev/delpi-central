# R4 — Apresentação, guidance e vocabulário: prompt e registro de evidências

**PLANO:** [125](../125-orchestration-complete-refactoring-finite-plan.md) · **RUNBOOK:** [130](../130-orchestration-refactor-r0-r7-execution-playbook.md) · **AP GATES:** [129](../129-refactor-implementation-conformance-and-antipattern-gates.md)  
**TASK_ID:** `DELIA-C3-ORCHESTRATION-R4-PRESENTATION-GUIDANCE-REFACTOR-01` · **LOTES:** M06–M07 · **ESTADO DO DOCUMENTO:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`.  
**Autorização:** decisão explícita e subsequente da coordenação/PO (task order R4) sobre critérios e residual pré-R4 — exatamente o mecanismo exigido pelo parecer independente do doc 145 §8 (`ACCEPT_WITH_RESIDUAL`, "autorizar R4 somente por decisão subsequente explícita sobre critérios e residual"). Escopo fixado: refatoração exclusivamente estrutural; O2/DAVI/TÉO/VISTA/seleção semântica/recuperação não reabertos.

## Prompt pronto para Devin — executar SOMENTE quando gate liberado

> Execute integralmente `DELIA-ORCH-REFAC-R4-BOUNDED-01` conforme o plano 125, protocolo 129 e runbook 130 §4. Sem pedir microconfirmações; STOP quando não existir autorização/contrato/owner, não por conveniência. Reancore HEAD/origin/main/status/authorities, confirme que a etapa anterior recebeu parecer independente e congele o BASE_SHA. Faça o menor diff possível dentro da whitelist. Execute baseline/RED→GREEN/paridade, suíte backend completa e provas de arquitetura, segurança, generalização e outcomes impactados. Se detectar regressão reparável dentro do contrato, execute automaticamente UM rework bounded com novo RED, reaplique toda a matriz e remova código legado obsoleto; se ainda falhar, STOP. Preencha este documento com evidências reais, registre README/ledger no final e envie report à coordenação. Não se autoaceite, não execute deploy ou próxima etapa sem gate.

**Objetivo:** Isolar renderização sem violar o SKIP_WITH_DECISION do documento 117; melhorar coesão apenas com destinos provados.

## Documento obrigatório — preenchido pelo executor

**STATUS:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` · `DEPLOY_STATUS=EXECUTED`

| Campo | Evidência |
|---|---|
| PLAN_ID / STEP / TASK_ID | DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01 / R4 / `DELIA-C3-ORCHESTRATION-R4-PRESENTATION-GUIDANCE-REFACTOR-01` |
| AUTHORIZATION_REF / PHASE_FROM_16_LEDGER | Task order explícita R4 (decisão subsequente sobre critérios e residual exigida por doc 145 §8); ledger: gate pré-R4 `EXECUTED_AND_DEPLOYED`, `R4_AUTHORIZED=NO` → aceito como não-bloqueante para escopo estritamente estrutural pela ordem competente |
| HEAD_BEFORE / ORIGIN_MAIN / GIT_STATUS / BASE_SHA | `42b7d71ce6` → pull ff-only → `1d45cac3ba` → fetch+ff-only → `0668cdeb3c`; worktree limpa fora do escopo R4 |
| AUTHORITIES_READ / CP_RQ / FROZEN_DECISIONS | 16→50→17→49→51→52→21→20→25; arquitetura/product spec; ADR58; S4/117; 125/129/130; R0–R3 evidence; 139–145; ledger no HEAD / CP_RQ=acoplamento orquestração↔apresentação residual / FROZEN: S4-117 (guidance), AUTHZ, PREPARE/ACT, contratos MCP, CRI on/off |
| GOAL / ENTRY_GATES / ALLOWED_FILES / FORBIDDEN_FILES | reduzir acoplamento legítimo apresentação↔orquestração com paridade byte / gates: owner existente, DAG acíclico, sem import de orchestration na apresentação / ALLOWED: `conversational_response.py`, `orchestration.py`, imports de testes/scripts, docs / FORBIDDEN: novos módulos, planner/seleção/recovery/AuthZ, DAVI/TÉO/VISTA, instruções O2 |
| FUNCTION_MAP / OWNER / REAL_CONSUMER / CONTRACT | ver tabela § Evidência específica R4 |
| EXISTING_EQUIVALENT / REUSE_DECISION / NEW_FILE_GATE | `YES_PARTIAL` / `EXTEND` (owner existente `conversational_response.py`) / `NEW_ABSTRACTIONS=0`, `NEW_FILES=1` (somente teste de paridade) |
| ACTUAL_FILES / SCOPED_DIFF / CONTRACT_COMPAT | `conversational_response.py` 730→1306, `orchestration.py` 11400→10969 (+import list), `scripts/cri_activation_eval.py` (import repoint), 9 testes (import repoint) + `test_r4_presentation_parity.py` (novo) / diff apenas move + imports / contratos observáveis preservados |
| IMPORT_DAG_BEFORE_AFTER / DUPLICATE_CHECK / ARCH_TESTS | antes: `orchestration → conversational_response` (já existia desde R3); depois: mesma direção única, `conversational_response` **não** importa `orchestration`; `conversational_response → outcome_assessment` (estendido) / duplicate check via AST: zero símbolo duplicado nos dois módulos / `audit_platform_guardrails` 0, `audit_backend_boundaries` 0, `audit_architecture_phase3` OK (43 testes) |
| LEGACY_CURRENT / DEPRECATED_ACTIVE / OBSOLETE_PROVEN / DELETED | zero legado retido: símbolos movidos removidos de `orchestration.py`; nenhum shim/alias de compatibilidade adicionado; testes repontados ao owner canônico |
| BASELINE_TESTS / RED_GREEN / FULL_BACKEND / SECURITY / GENERALIZATION | baseline: suite verde no HEAD / RED→GREEN: 19 testes de caracterização literais criados **antes** da migração (verdes) e mantidos verdes após / FULL_BACKEND: suite completa `delia-api` exit 0 no SHA `aca0f22e59` / SECURITY: sanitizer `_sanitize_renderable` único em `outcome_assessment` (importado, não copiado); `_md_leaf` escaping inalterado; injeção não eleva / GENERALIZATION: comportamento determinístico idêntico por construção verbatim |
| D4/D5/D5-R/D5-schema/D8/D8-R/N1 / CRI_ON_OFF | caminhos cobertos deterministicamente: `test_cri_e3_conversational_presentation` (94), `test_i02/i04` guidance+documental, `test_presentation_v2_*`, `test_stage05/06`, `test_q02c` comparação tipada / `CRI_OFF_LIVE=TEST_NOT_RUN` (residual mantido) |
| AI_EVAL_SHA_MODEL_CONFIG / BUSINESS_OUTCOME / POSTCONDITION | `LOCAL_MODEL_EVAL=NOT_RUN` — refatoração pura com paridade determinística provada; comportamento não comprovável deterministicamente = nenhum / outcome de negócio inalterado por construção |
| AP01_AP20_EVIDENCE_WITH_STATUS / CI_VS_MANUAL | gates executados: owner existente (AP-reuse PASS), DAG acíclico (PASS), sem sanitizer duplicado (PASS), sem novo módulo preventivo (PASS — M07 SKIP), paridade (PASS), suite completa (PASS) / auditorias executadas localmente, mesmos scripts do CI |
| REGRESSION_DELTA / FIRST_DIVERGENT_STAGE / NO_REGRESSION_FOR_EVALUATED_SCOPE | zero regressão detectada / n/a / PASS para todo escopo testável deterministicamente |
| AUTO_REWORK_USED / REWORK_RED_GREEN / REWORK_FINAL_MATRIX | 0 / n/a / n/a |
| RESIDUAL_SEARCH / ROLLBACK / SECURITY_SECRETS | residual pesquisado: M07 guidance mantido por decisão 117 (ver § abaixo); `O2=KNOWN_RESIDUAL` funcional independente / rollback: `git checkout` do SHA anterior + imagem `513ee033b0c6` retida / zero secrets no diff |
| FINAL_HEAD / ORIGIN_MAIN_FINAL / PUSH_VERIFIED | `aca0f22e59` (impl) + `457088b40a` (docs) → origin/main `457088b40a` / `YES` ff-only |
| README_LEDGER_UPDATED / DELETIONS_RATIONALE | README + ledger + plano 125 atualizados neste commit de docs / nenhuma deleção funcional — apenas reloc |
| EXECUTION_DRIFT / RESIDUALS / STOP_REASON | `NONE` — nenhuma instrução O2, nenhum reabrir DAVI/TÉO/VISTA, nenhuma mudança funcional / residuais mantidos: O2 INCONCLUSIVE, CRI_OFF_LIVE TEST_NOT_RUN, tokens indisponíveis, variabilidade seleção D1, password-grant a confirmar / sem STOP |
| EXECUTOR_VERDICT / COORDINATION_REVIEW_REQUIRED | `IMPLEMENTED_STRUCTURE_ONLY — evidence ready for independent review` / `YES` |
| DEPLOY | `[1/1] delia-api` canonical `up-prod-sequential.sh --build delia-api`; new image `8a3fe498f488`; rollback `513ee033b0c6` retida; health 200, unauth POST 401, 1 turno autenticado 200/GROUNDED; zero LLM-matrix em prod |

## Evidência específica da etapa R4 — matriz MOVE/KEEP/SKIP

### M06 — apresentação pura → `conversational_response.py` (owner existente, `REUSE_DECISION=EXTEND`)

| ORIGIN SYMBOL | NEW OWNER/FILE | CONTRACT/CONSUMERS | BEFORE/AFTER IMPORTS | TESTS | OLD SYMBOL REMOVED? | LEGACY/COMPAT DECISION |
|---|---|---|---|---|---|---|
| `MAX_RENDER_CONTENT_CHARS`, `_PRESENTATION_INTENTS`, `_INSUFFICIENCY_CONTENT`, `EMPTY_RESULT_TEXT`, `_ITEMS_KEY`, `_MD_ESCAPABLE`, `_MD_ESCAPE`, `_MD_LINE_BREAKS` | `conversational_response.py` | bounds/textos da projeção determinística; consumidos por helpers movidos e por seams mantidos na orquestração (guidance md, prior) | orchestration passa a importar `MAX_RENDER_CONTENT_CHARS` de cr | suite completa + paridade | sim | sem alias |
| `_render_synthesis` | `conversational_response.py` | consumers: orchestrator (2 sites) + stage05/06 + `cri_activation_eval` | +`_synthesis_selections`, `MAX_SYNTHESIS_FIELDS` de `outcome_assessment` | stage05/06 + paridade literal | sim | sem shim |
| `_proven_field_differences`, `_selected_proven_differences` | `conversational_response.py` | comparação tipada (q02c), síntese | idem | q02c + paridade | sim | sem shim |
| `_insufficiency_content` | `conversational_response.py` | composição honesta de insuficiência | — | paridade literal pt-BR | sim | sem shim |
| `_compose_answer`, `_detail_header`, `_detail_lines`, `_list_header` | `conversational_response.py` | frases/cabeçalhos pt-BR | `field_clause_label`/`field_display_label`/`records_are_prior_excerpts` já eram cr | stage06, i04, c3_labels + paridade | sim | sem shim |
| `_format_structured`, `_format_list`, `_format_records`, `_business_lines` | `conversational_response.py` | projeção estruturada/business plain | +`MAX_RENDER_LIST_ITEMS`, `_CONTROL_PLANE_KEYS`, `_RESOLVER_ENVELOPE_KEYS` de `outcome_assessment` | paridade + guidance consumers | sim | sem shim |
| `_md_leaf`, `_md_format_structured`, `_md_format_list`, `_md_format_records`, `_md_business_lines` | `conversational_response.py` | projeção Markdown literal/escapada | idem + `_md_leaf` interno | presentation_v2 + paridade | sim | sem shim |

**Direção do DAG (inalterada):** `orchestration → conversational_response → outcome_assessment`. Nenhum import novo de `orchestration` em apresentação; nenhum ciclo; nenhum sanitizer duplicado (`_sanitize_renderable` permanece único em `outcome_assessment`).

### M07 — guidance — `SKIP_WITH_DECISION` / `KEEP` (decisão S4/117 preservada)

| SYMBOL | DECISION | RAZÃO |
|---|---|---|
| `_guidance_section_records`, `_iter_guidance_doc_items`, `_guidance_hit_count`, `_render_guidance_value`, `_guidance_family_for_key` | `SKIP_WITH_DECISION` | Projeção de evidência owner→records alimenta `outcome_facts`/`_resolver_entities` (boundary de evidência, não de apresentação); depende de `_GUIDANCE_*`, `_RESOLVER_ENVELOPE_KEYS`, `_CONTROL_PLANE_KEYS` e da classificação de famílias — decisão 117 congela extração sem boundary+consumer reais novos. Nenhum destino existente recebe essa semântica sem acoplar evidência a apresentação. |
| `_select_guidance_records`, `_deterministic_guidance_content`, `_pack_guidance_sections`, `_omitted_sections_line`, `_md_guidance_content` | `SKIP_WITH_DECISION` | Composição determinística entrelaçada com seleção de evidência guidance e com os mesmos envelopes/control-plane constants; extraí-los isoladamente para o compositor criaria dependência cr→constantes guidance ou cópia. Nenhum novo consumer/boundary provado — `guidance_projection.py` segue bloqueado por 117. |
| `_prior_excerpt_records`, `_prior_paragraph_units`, `_is_prior_list_item`, `MAX_PRIOR_EXCERPTS` | `KEEP` | Projeção de evidência de sessão (gera records selecionáveis para síntese), não apresentação; `MAX_PRIOR_EXCERPTS` compartilhado com guidance. |
| seams de render do orquestrador (`RenderedSpecialistOutcome`, `_synthesis_records`, `_surface_inquiry_content`, `_live_interop_surface_lines`, `_candidate_clarification_content`, `_argument_completeness_gaps`, helpers de comparação/index) | `KEEP` | Glue legítimo do coordenador: inspeção de superfície, clarificação de argumentos, montagem de fatos — decisões de fluxo/evidência, não formatação. |

**Caso negativo adversarial executado:** tentativa de mover `_business_lines`/`_md_business_lines` para `interaction/presentation.py` foi descartada — criaria segundo owner de projeção business divergente do compositor e duplicaria o boundary CRI/non-CRI. Decisão: `conversational_response.py` (compositor existente), sem terceiro módulo.

## Provas de paridade

- `test_r4_presentation_parity.py` (novo, 19 casos): saídas literais pt-BR de `_compose_answer`, `_detail_*`, `_list_header`, `_proven_field_differences`, `_render_synthesis` (answer/list/inválido), `_format_*` (control-plane filter, vazio), `_business_lines` (envelope + empty explícito), `_md_leaf` (escaping), `_md_business_lines`, `_insufficiency_content` — verdes antes e depois do move.
- Suite completa delia-api: exit 0 no SHA `aca0f22e59` (mesma árvore que a testada).
- Auditores de arquitetura: `test_audit_platform_guardrails`, `test_audit_backend_boundaries`, `test_audit_architecture_phase3` — 43 verdes, 0 findings.
- `CRI_ON=CRI v5 ativo` sem alteração de comportamento; `CRI_OFF_LIVE=TEST_NOT_RUN` (residual mantido do ciclo anterior).

## Residuals (preservados, não criados)

- `O2_STATUS=KNOWN_RESIDUAL` — cenário terminal bala permanece `INCONCLUSIVE` funcional; esta etapa é estritamente estrutural e não toca seleção/recuperação.
- `CRI_OFF_LIVE=TEST_NOT_RUN`; `REAL_TOKEN_USAGE=NOT_AVAILABLE`; variabilidade de seleção D1; confirmação password-grant (doc 144 §7).
- Fase do roadmap **não** avança por esta refatoração; aceite independente pendente.

### Revisão independente (preencher SOMENTE pela coordenação)

`REVIEW_SHA=PENDING` · `REVIEW_VERDICT=PENDING` · `ACCEPTANCE_REASON=PENDING` · `NEXT_STAGE_AUTHORIZED=NO`.
