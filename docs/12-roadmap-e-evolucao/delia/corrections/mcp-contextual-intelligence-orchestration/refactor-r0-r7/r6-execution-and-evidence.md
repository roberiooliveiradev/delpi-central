# R6 — Coordenador mínimo e limpeza completa do legado comprovado: prompt e registro de evidências

**PLANO:** [125](../125-orchestration-complete-refactoring-finite-plan.md) · **RUNBOOK:** [130](../130-orchestration-refactor-r0-r7-execution-playbook.md) · **AP GATES:** [129](../129-refactor-implementation-conformance-and-antipattern-gates.md)  
**TASK_ID:** `DELIA-C3-ORCHESTRATION-R6-CORE-PRESERVATION-AND-SAFETY-REGRESSION-01` · **LOTES:** M10 + residual M01–M09 · **ESTADO DO DOCUMENTO:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` · `CODE_DIFF=NONE` · `DEPLOY_STATUS=NOT_RUN_NO_RUNTIME_CHANGE`.  
**Autorização:** `R6_BOUNDED_PREPARATION=AUTHORIZED` + `R6_CODE_EXECUTION=REQUIRES_EXPLICIT_GATE` — parecer independente R5 (`0fc131155b`); `RELEASE_GOVERNANCE_CONFLICT=ESCALATED_UNRESOLVED` (precedência é decisão da coordenação); `R7_AUTHORIZED=NO`. Execução realizada em modo preservação/regressão não-modificadora: reancoragem, inventário, caller graph, caracterização e regressão de segurança concluídos; zero alteração de produto proposta ou aplicada.

## Prompt pronto para Devin — executar SOMENTE quando gate liberado

> Execute integralmente `DELIA-ORCH-REFAC-R6-BOUNDED-01` conforme o plano 125, protocolo 129 e runbook 130 §4. Sem pedir microconfirmações; STOP quando não existir autorização/contrato/owner, não por conveniência. Reancore HEAD/origin/main/status/authorities, confirme que a etapa anterior recebeu parecer independente e congele o BASE_SHA. Faça o menor diff possível dentro da whitelist. Execute baseline/RED→GREEN/paridade, suíte backend completa e provas de arquitetura, segurança, generalização e outcomes impactados. Se detectar regressão reparável dentro do contrato, execute automaticamente UM rework bounded com novo RED, reaplique toda a matriz e remova código legado obsoleto; se ainda falhar, STOP. Preencha este documento com evidências reais, registre README/ledger no final e envie report à coordenação. Não se autoaceite, não execute deploy ou próxima etapa sem gate.

**Objetivo:** Encerrar migração e remover TODOS os artefatos comprovadamente obsoletos dentro do escopo DÉLIA sem apagar contratos ainda ativos ou refatorar o Chat histórico.

**Arquivos permitidos no contrato preliminar (R0 deve reduzir a ALLOWED_FILES precisa):** orchestration.py, módulos DÉLIA previamente aprovados e testes diretamente afetados, docs e referências obsoletas sob owner legítimo.

**Arquivos/mudanças proibidos:** Reescrever state machine PREPARE/ACT, apagar consumer ativo, deprecar endpoint sem migration, código comentado como backup, shim permanente sem contrato de fim, tocar Chat runtime ou tabelas.

**Passos específicos obrigatórios:** Fazer residual search de TODO/função/alias/import/branch/config/prompt/test fixture deprecated; rastrear callers estáticos, dinâmicos e consumers externos; apagar origem movida e duplicações, dead branches, wrappers temporários e flags abandonadas somente com prova; registrar cada remoção na matriz de legado com rollback. Provar KEEP/SKIP não é 'legacy' se possui contrato legítimo; manter compat sob deprecation registrada e bloquear fechamento se obsoleto confirmado remanescer.

**Provas de não regressão específicas:** AST/dead import/use graph, static/dynamic searches, release compatibility, import DAG, D4/D5/D8, ACT/AuthZ/Policy/Domain/idempotency, backend full, rollback dry run onde previsto.

**Gate de saída:** Zero legado OBSOLETE comprovado no escopo, zero implementação paralela, coordinator mantém sequencing/decision/guarding, sem regressão e sem breaking consumer.

**STOP material:** Qualquer violação AP/autoridade, ausência de owner/contrato ou segunda falha do mesmo pacote exige STOP e revisão independente.

## Documento obrigatório a preencher pelo executor após execução

**STATUS:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

| Campo | Evidência a preencher (não presumir PASS) |
|---|---|
| PLAN_ID / STEP / TASK_ID | DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01 / R6 / `DELIA-C3-ORCHESTRATION-R6-CORE-PRESERVATION-AND-SAFETY-REGRESSION-01` |
| AUTHORIZATION_REF / PHASE_FROM_16_LEDGER | Review R5 `0fc131155b`: `R6_BOUNDED_PREPARATION=AUTHORIZED`, `R6_CODE_EXECUTION=REQUIRES_EXPLICIT_GATE`; fase canônica R6 (bounded) |
| HEAD_BEFORE / ORIGIN_MAIN / GIT_STATUS / BASE_SHA | `16308d2097` → pull ff → `97f393390b` = origin/main; worktree limpo; BASE_SHA=`97f393390b` |
| AUTHORITIES_READ / CP_RQ / FROZEN_DECISIONS | 16→50→17→49→51→52→21→20→25; regras .cursor canônicas; plano 125; gates 129; runbook 130; evidências R0–R5; review R5 `0fc131155b`; ledger vigente; CP_RQ=preservação do core coordenador pós-R0–R5 |
| GOAL / ENTRY_GATES / ALLOWED_FILES / FORBIDDEN_FILES | Verificar core como owner legítimo, remover só obsoleto PROVADO; entry gates = reanchor + autoridades + caller graph + reuse; ALLOWED=orchestration.py/módulos aprovados/testes; FORBIDDEN=state machine PREPARE/ACT, consumer ativo, Chat runtime |
| FUNCTION_MAP / OWNER / REAL_CONSUMER / CONTRACT | Ver "Caller graph e matriz KEEP" abaixo — 7/7 funções do core ACTIVE com consumers reais de produção |
| EXISTING_EQUIVALENT / REUSE_DECISION / NEW_FILE_GATE | `EXISTING_EQUIVALENT=YES` · `REUSE_DECISION=REUSE` (orchestrator como único owner da coordenação) · `NEW_FILE_GATE=NONE` — zero novos arquivos |
| ACTUAL_FILES / SCOPED_DIFF / CONTRACT_COMPAT | `CODE_DIFF=NONE` — nenhum arquivo de produto alterado; contratos preservados por ausência de diff e por regressão verde |
| IMPORT_DAG_BEFORE_AFTER / DUPLICATE_CHECK / ARCH_TESTS | DAG inalterado e acíclico: orchestration→argument_validation→outcome_assessment, orchestration→conversational_response; arch gates 41 testes verdes (`test_audit_platform_guardrails`, `test_audit_architecture_phase3`, `test_interaction_runtime_architecture`) |
| LEGACY_CURRENT / DEPRECATED_ACTIVE / OBSOLETE_PROVEN / DELETED | `DELETED=NONE` — scan AST de funções privadas: **zero zero-referência**; tabela de remoções vazia (ver seção R6 abaixo) |
| BASELINE_TESTS / RED_GREEN / FULL_BACKEND / SECURITY / GENERALIZATION | Focado core+segurança: 48+227 testes verdes (provider_neutral 19, specialist_interop_security, stage02–06, r2/r45/r5-parity, c3/evidence, semantic_argument); FULL_BACKEND exit 0; GENERALIZATION PASS via test_stage06 + r2 provider-neutral |
| D4/D5/D5-R/D5-schema/D8/D8-R/N1 / CRI_ON_OFF | Cri ON v5 coberto pela suíte (`test_cri_e1/e2/e3` verdes); `CRI_OFF_LIVE=TEST_NOT_RUN` (residual herdado) |
| AI_EVAL_SHA_MODEL_CONFIG / BUSINESS_OUTCOME / POSTCONDITION | `LOCAL_MODEL_EVAL=NOT_NEEDED_FOR_STRUCTURAL_PARITY` — zero mudança em prompts, seleção, model-stage, evidence, outcome ou semântica de resposta |
| AP01_AP20_EVIDENCE_WITH_STATUS / CI_VS_MANUAL | Sem novo planner/engine/registry/state machine/router/branch por provider; sem shim; validação de argumentos no owner canônico (R5); apresentação no compositor (R4); outcome em outcome_assessment (R3) — manual |
| REGRESSION_DELTA / FIRST_DIVERGENT_STAGE / NO_REGRESSION_FOR_EVALUATED_SCOPE | `DELTA=NONE` — suíte completa verde no HEAD `97f393390b` sem nenhum diff aplicado; nenhum estágio divergente |
| AUTO_REWORK_USED (0/1) / REWORK_RED_GREEN / REWORK_FINAL_MATRIX | 0 / n/a (zero diff, zero defeito detectado) |
| RESIDUAL_SEARCH / ROLLBACK / SECURITY_SECRETS | Residual search AST em `orchestration.py`: zero função privada sem referência; zero secrets novos; rollback n/a (sem deploy) |
| FINAL_HEAD / ORIGIN_MAIN_FINAL / PUSH_VERIFIED | docs-only commit (ver ledger); produto intocado desde `97f393390b` |
| README_LEDGER_UPDATED / DELETIONS_RATIONALE | README/ledger/plano 125 atualizados neste push; `DELETIONS_RATIONALE=NONE` — nada provado obsoleto |
| EXECUTION_DRIFT / RESIDUALS / STOP_REASON | Drift: nenhum funcional. Residuais: `RELEASE_GOVERNANCE_CONFLICT=ESCALATED_UNRESOLVED`, `CRI_OFF_LIVE=TEST_NOT_RUN`, O2=KNOWN_RESIDUAL |
| EXECUTOR_VERDICT / COORDINATION_REVIEW_REQUIRED | `CORE_VERIFIED_NO_CODE_CHANGE_REQUIRED` / YES |

### Evidência específica da etapa R6

Tabela obrigatória de remoções: PATH/SYMBOL | LEGACY CLASS | STATIC+DYNAMIC CONSUMERS | PROOF OF OBSOLESCENCE | ACTION | COMMIT | TESTS | COMPAT RISK | ROLLBACK. Provar ZERO_OBSOLETE_PROVEN remaining ou bloquear encerramento. Não tocar outros bounded contexts.

**Tabela de remoções:** vazia — nenhum símbolo provado obsoleto. `ZERO_OBSOLETE_PROVEN=CONFIRMED` para as funções analisadas.

#### Caller graph bounded (BASE_SHA `97f393390b`, AST + grep estático)

| Função | Linha | Callers | Classificação |
|---|---|---|---|
| `attempt()` | 3705 | `handle_interactive_turn.py:425` (wiring de produção) + 19 testes provider-neutral | ACTIVE — entry point público |
| `_attempt` | 3872 | `attempt()` @3778 | ACTIVE — state machine principal |
| `_select_target` | 7734 | `_attempt` @4073 | ACTIVE — seleção semântica governada |
| `_invoke_selected` | 10044 | 6 call sites (4962, 6454, 8435, 8780, 8894, 9141) — paths READ/invoke/guidance | ACTIVE |
| `_attempt_prepare` | 6692 | 2 call sites (4962, 5740) — paths PREPARE | ACTIVE — proposta backend-only, `proposal_ref` não vaza |
| `_execute_prepared_act` | 7191 | 1 call site (7173) — path de confirmação | ACTIVE — só via `ConfirmationRecord` bound |
| `_audit` | 7634 | 9 call sites (6746–7351) | ACTIVE — trilha de auditoria |

Scan AST adicional: nenhuma função privada (`_*`) de `orchestration.py` sem referência dentro do módulo; nenhuma referência externa órfã em `tests/`/`scripts/`. `DEAD_CODE_PROVEN=NONE` para todo o módulo, não apenas o core.

#### Matriz de decisão por responsabilidade

`_attempt` KEEP · `_select_target` KEEP · `_invoke_selected` KEEP · `_attempt_prepare` KEEP · `_execute_prepared_act` KEEP · `_audit` KEEP · `attempt()` KEEP. Zero `REMOVE_PROVEN_DEAD`, zero `MINIMAL_FIX`, zero `SKIP_WITH_DECISION` — nenhum problema demonstrado; criar diff cosmético é explicitamente proibido pelo critério de alteração R6.

#### Gate de release — análise do conflito (escalado, não decidido pelo executor)

**Instrução A (diretriz durável):** seção "Complemento de gates de teste local e deploy — diretriz PO de 2026-10-23" deste e dos docs R* — deploy em produção é **objetivo condicionado a review independente + autorização operacional específica**, explicitando "não executá-lo apenas com o prompt de implementação". Autoridade: Product Owner, norma prospectiva registrada no documento governado.

**Instrução B (autorização caso-específica):** ordem da task R5 — PO autorizou o deploy de `delia-api` condicionado aos gates técnicos, que foram cumpridos.

**Ocorrência:** o deploy R5 (`dc9833166850`, ~11:16) precedeu o review independente (commit `0fc131155b`, 11:19). A sequência exigida pela instrução A não foi observada; a instrução B foi observada.

**Decisão necessária (não tomada pelo executor):** se uma autorização operacional explícita por-task equivale à dupla condição do gate documental ou se o gate permanece superior. `RELEASE_GOVERNANCE_CONFLICT=ESCALATED_UNRESOLVED` — sem aprovação retroativa presumida, sem rollback ordenado (nenhuma evidência de dano; review aceitou o código no mérito). **Recomendação à coordenação:** declarar explicitamente uma das três — (a) autorização per-task sobrepõe o gate quando explícita, (b) emendar o gate documental, ou (c) manter review-independent-antes-de-deploy mesmo com autorização per-task — e fixar precedência para R7 em diante.

**Consequência em R6:** `R6_CODE_EXECUTION` permanece bloqueado até decisão da coordenação; o resultado analítico `NO_CODE_CHANGE_REQUIRED` torna o bloqueio sem efeito prático nesta etapa e elimina a necessidade de qualquer deploy.

### Revisão independente (preencher SOMENTE pela coordenação)

`REVIEW_SHA=PENDING` · `REVIEW_VERDICT=PENDING` · `ACCEPTANCE_REASON=PENDING` · `NEXT_STAGE_AUTHORIZED=NO`.


### Complemento de gates de teste local e deploy — diretriz PO de 2026-10-23

**Norma executiva superior:** 16 + plano 125 + runbook 130. Para esta etapa, testes locais completos no SHA modificado passam a ser condição explícita de aceite técnico: focused, full backend, architecture/import DAG, security, provider-neutral generalization, CRI e outcomes aplicáveis; Ollama local quando comportamento de modelo/prompt for afetado. Registre `LOCAL_TEST_STATUS`, `TEST_SHA`, `MODEL_CONFIG` e evidências. O deploy em produção é **objetivo condicionado** a review independente e autorização operacional específica com rollback; não executá-lo apenas com o prompt de implementação. Após deploy autorizado, homologar caminhos reais e registrar `DEPLOY_AUTHORIZATION`, `DEPLOY_STATUS`, `IMAGE_DIGEST`, `PROD_SHA`, `PROD_AUTH_HOMOLOGATION`, `BUSINESS_OUTCOME_STATUS`. Se não houver acesso/autorização, `TEST_NOT_RUN` com motivo. A próxima etapa continua dependente de decisão explícita da coordenação/PO.


### Parecer independente da coordenação — 2026-10-24

**REVIEW_VERDICT=ACCEPT (R6 bounded, no-code)**; **R6_CLOSED=YES**; **R7_PREPARATION=AUTHORIZED**; **R7_EXECUTION_AND_RELEASE=REQUIRE_SEPARATE_GATES**. Conferido no GitHub `92a502bc3243656bf4fc9037904946aecb4ea41f`: commit documental (plano 125, README, r6 report, ledger), sem código alterado. A avaliação dos testes é documental, não reexecução independente da suíte ou host. `FOCUSED_TESTS=EXECUTOR_REPORTED_PASS`, `FULL_BACKEND=EXECUTOR_REPORTED_PASS`, `ARCHITECTURE_GATES=EXECUTOR_REPORTED_PASS`.

**Aceite:** 7/7 funções core reportadas ACTIVE com consumers, nenhum dead code PROVEN, máquina de estados/PREPARE-ACT/AuthZ/Policy/candidate/recovery/Evidence/Outcome preservados sem diff; `NO_CODE_CHANGE_REQUIRED` correto; zero deploy R6. Ausência de referências numa varredura AST não equivale por si só a prova universal de ausência de legado, mas nada exige remoção no escopo bounded.

**Decisão prospectiva de governança de release (opção c conservadora):** para R7 e releases posteriores, preservar o gate documental explícito: **(1) testes/evidence no SHA → (2) revisão independente → (3) autorização operacional específica → (4) deploy → (5) smoke/outcome**. Uma autorização genérica de implementação ou cláusula per-task para deploy não substitui por si só a revisão anterior exigida. A ocorrência R5 permanece registrada como `HISTORICAL_RELEASE_SEQUENCE_NONCONFORMANCE`; esta decisão não concede aceite retroativo e não indica rollback sem evidência de risco atual. Se autoridade superior posterior estabelecer exceção, registrar decisão expressa antes do deploy, nunca inferir.

**R7:** autorizada apenas reancoragem, inventário de evidências, planejamento da matriz integrada e testes locais/read-only necessários para formular gate; nenhuma mudança de código, avanço de fase ou release R7 implícitos. R7 completa exige autorização própria conforme autoridades 16/125/130, incluindo avaliação no SHA/config, generalização, segurança, outcomes e residuais O2/CRI_OFF explícitos. `REVIEW_SHA=92a502bc32`; `ACCEPTANCE_REASON=CORE_PRESERVED_NO_CHANGE_REQUIRED`; `NEXT_STAGE_AUTHORIZED=R7_PREPARATION_ONLY`.
