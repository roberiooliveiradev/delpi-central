# R5 — Validação de argumentos e propostas tipadas: prompt e registro de evidências

**PLANO:** [125](../125-orchestration-complete-refactoring-finite-plan.md) · **RUNBOOK:** [130](../130-orchestration-refactor-r0-r7-execution-playbook.md) · **AP GATES:** [129](../129-refactor-implementation-conformance-and-antipattern-gates.md)  
**TASK_ID:** `DELIA-C3-ORCHESTRATION-R5-SCHEMA-GOAL-MODEL-STAGE-REFACTOR-01` · **LOTES:** M08–M09 · **ESTADO DO DOCUMENTO:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW` · `DEPLOY_STATUS=EXECUTED`.  
**Autorização:** `R5_BOUNDED_ONLY=AUTHORIZED` — decisão explícita da coordenação no review independente de R4 (`8a9a960052`: `NEXT_STAGE_AUTHORIZED=R5_BOUNDED_ONLY`); `R6_AUTHORIZED=NO`, `R7_AUTHORIZED=NO`. Deploy autorizado pelo PO na mesma ordem, condicionado aos gates.

## Prompt pronto para Devin — executar SOMENTE quando gate liberado

> Execute integralmente `DELIA-ORCH-REFAC-R5-BOUNDED-01` conforme o plano 125, protocolo 129 e runbook 130 §4. Sem pedir microconfirmações; STOP quando não existir autorização/contrato/owner, não por conveniência. Reancore HEAD/origin/main/status/authorities, confirme que a etapa anterior recebeu parecer independente e congele o BASE_SHA. Faça o menor diff possível dentro da whitelist. Execute baseline/RED→GREEN/paridade, suíte backend completa e provas de arquitetura, segurança, generalização e outcomes impactados. Se detectar regressão reparável dentro do contrato, execute automaticamente UM rework bounded com novo RED, reaplique toda a matriz e remova código legado obsoleto; se ainda falhar, STOP. Preencha este documento com evidências reais, registre README/ledger no final e envie report à coordenação. Não se autoaceite, não execute deploy ou próxima etapa sem gate.

**Objetivo:** Reutilizar validações determinísticas equivalentes sem transferir interpretação de intenção do LLM para regex ou branch por provider.

**Arquivos permitidos no contrato preliminar (R0 deve reduzir a ALLOWED_FILES precisa):** interaction/argument_validation.py, model_invocation/contracts.py, glue em orchestration.py e testes dentro do escopo R0.

**Arquivos/mudanças proibidos:** Parser semântico paralelo, hardcode de operationId, alterações de budget/Policy, validação de autorização por JWT/cache, novo provider registry.

**Passos específicos obrigatórios:** Provar equivalência das validações de required/defaults/open-vocab; migrar callers sequencialmente; reduzir wiring duplicado onde houver contrato idêntico; preservar lineage, retries, cancelamento, candidate-token e follow-up; eliminar duplicações antigas.

**Provas de não regressão específicas:** Schema valid/invalid, missing/defaults, candidate/discovery, context follow-up D8-R, no-tool, rename/reorder provider, 60/3/300 e fail-closed, suite backend completa.

**Gate de saída:** Sem parser de intenção Python, validação com owner único e percurso de propostas governado intacto.

**STOP material:** Qualquer violação AP/autoridade, ausência de owner/contrato ou segunda falha do mesmo pacote exige STOP e revisão independente.

## Documento obrigatório a preencher pelo executor após execução

**STATUS:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

| Campo | Evidência a preencher (não presumir PASS) |
|---|---|
| PLAN_ID / STEP / TASK_ID | DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01 / R5 / `DELIA-C3-ORCHESTRATION-R5-SCHEMA-GOAL-MODEL-STAGE-REFACTOR-01` |
| AUTHORIZATION_REF / PHASE_FROM_16_LEDGER | review R4 `8a9a960052` → `R5_BOUNDED_ONLY` / ledger: R4 `EXECUTED_AND_DEPLOYED` aceito `ACCEPT_WITH_RESIDUAL` |
| HEAD_BEFORE / ORIGIN_MAIN / GIT_STATUS / BASE_SHA | `d2eb2aab26` → ff-only → `8a9a960052`; worktree limpa fora do escopo R5 |
| AUTHORITIES_READ / CP_RQ / FROZEN_DECISIONS | 16→50→17→49→51→52→21→20→25; arch/product spec; ADR58; S4/117; 125/129/130; R0–R4 evidence; review R4; ledger / CP_RQ=duplicação de schema/goal/model-stage contracts / FROZEN: planner semântico, 60/3/300, AuthZ, PREPARE/ACT, candidate-token, CRI, guidance M07 |
| GOAL / ENTRY_GATES / ALLOWED_FILES / FORBIDDEN_FILES | eliminar duplicação legítima de validação/defaults sem mudar comportamento / gates: owner existente, DAG acíclico, sem planner novo / ALLOWED: `interaction/argument_validation.py`, `orchestration.py` (remoção+imports), testes / FORBIDDEN: parser semântico, operationId hardcode, budget/policy, novo registry |
| FUNCTION_MAP / OWNER / REAL_CONSUMER / CONTRACT | ver matriz § Evidência específica R5 |
| EXISTING_EQUIVALENT / REUSE_DECISION / NEW_FILE_GATE | `YES_PARTIAL` / `EXTEND` (`interaction/argument_validation.py` — owner canônico de validação de argumentos) / `NEW_ABSTRACTIONS=0`, `NEW_FILES=1` (teste de paridade) |
| ACTUAL_FILES / SCOPED_DIFF / CONTRACT_COMPAT | `argument_validation.py` 314→500; `orchestration.py` 10979→10814; `test_stage04_completeness_resolution.py` (import repoint); `test_r5_argument_schema_parity.py` (novo) / diff apenas move + imports / contratos observáveis preservados |
| IMPORT_DAG_BEFORE_AFTER / DUPLICATE_CHECK / ARCH_TESTS | antes: `orchestration → argument_validation` (já existia) + `outcome_assessment → interaction.contracts`; depois: `orchestration → argument_validation → outcome_assessment` — acíclico (AST walk + import real); `argument_validation` NÃO importa orchestration / duplicate check AST: zero duplicado / audits guardrails+boundaries+phase3: 43 testes, 0 findings |
| LEGACY_CURRENT / DEPRECATED_ACTIVE / OBSOLETE_PROVEN / DELETED | símbolos removidos de `orchestration.py`; zero shim/alias; stage04 repontado ao owner canônico |
| BASELINE_TESTS / RED_GREEN / FULL_BACKEND / SECURITY / GENERALIZATION | baseline verde / 19 caracterizações literais criadas antes do move, verdes antes e depois; stage04 (36) + argument_validation (37) verdes / FULL_BACKEND exit 0 no SHA `efcee871b6` / SECURITY: `ORCHESTRATED_FIELDS` deny inalterado, `validate_arguments` intocado, defaults somente owner-publicados / GENERALIZATION: provider-neutral — semântica idêntica por move verbatim |
| D4/D5/D5-R/D5-schema/D8/D8-R/N1 / CRI_ON_OFF | caminhos cobertos deterministicamente (stage02–06, i02, q02c, referential, guided discovery) / `CRI_OFF_LIVE=TEST_NOT_RUN` (residual) |
| AI_EVAL_SHA_MODEL_CONFIG / BUSINESS_OUTCOME / POSTCONDITION | `LOCAL_MODEL_EVAL=NOT_RUN` — refatoração pura com paridade determinística; nenhum comportamento não-comprovável / outcome inalterado |
| AP01_AP20_EVIDENCE_WITH_STATUS / CI_VS_MANUAL | owner existente (PASS), DAG (PASS), sem validator duplicado (PASS), sem novo planner/registry (PASS), sem auth implícita (PASS), budget inalterado (PASS) / auditorias locais = scripts do CI |
| REGRESSION_DELTA / FIRST_DIVERGENT_STAGE / NO_REGRESSION_FOR_EVALUATED_SCOPE | zero / n/a / PASS no escopo deterministicamente testável |
| AUTO_REWORK_USED / REWORK_RED_GREEN / REWORK_FINAL_MATRIX | 0 / n/a / n/a |
| RESIDUAL_SEARCH / ROLLBACK / SECURITY_SECRETS | M09 KEEP com razão registrada; O2 residual mantido / rollback: SHA anterior + imagem `8a3fe498f488` / zero secrets |
| FINAL_HEAD / ORIGIN_MAIN_FINAL / PUSH_VERIFIED | `e1a57f915b` (impl, rebase de `efcee871b6` — delia-api byte-idêntica à árvore testada) + `bb3c9c44f5` (docs) → origin/main `bb3c9c44f5` / `YES` ff-only |
| README_LEDGER_UPDATED / DELETIONS_RATIONALE | README + ledger + plano 125 neste commit de docs / nenhuma deleção funcional |
| EXECUTION_DRIFT / RESIDUALS / STOP_REASON | `NONE` / residuais: O2 INCONCLUSIVE, CRI_OFF_LIVE TEST_NOT_RUN, tokens indisponíveis, D1 variabilidade, password-grant pendente / sem STOP |
| EXECUTOR_VERDICT / COORDINATION_REVIEW_REQUIRED | `IMPLEMENTED_STRUCTURE_ONLY — evidence ready for independent review` / `YES` |
| DEPLOY | `[1/1] delia-api` canonical `up-prod-sequential.sh --build delia-api`; nova imagem `dc9833166850`; rollback `8a3fe498f488` retida; health 200, unauth POST 401, 1 turno autenticado 200/GROUNDED; zero LLM-matrix em prod |

### Evidência específica da etapa R5

#### M08 — schema/completeness/defaults → `interaction/argument_validation.py` (owner existente, `REUSE_DECISION=EXTEND`)

| ORIGIN SYMBOL | NEW OWNER/FILE | CONTRACT/CONSUMERS | BEFORE/AFTER IMPORTS | TESTS | OLD SYMBOL REMOVED? | LEGACY/COMPAT DECISION |
|---|---|---|---|---|---|---|
| `MAX_ARGUMENT_KEYS` | `argument_validation.py` | bound de chaves em argumentos/defaults; consumers: orchestration + movers | orchestration passa a importar de av | stage04 + parity + full suite | sim | sem alias |
| `_schema_required_gaps` | `argument_validation.py` | required-gap walk JSON-Schema fragment; consumer: `_owner_entity_completeness_gaps` | +`_value_present`, `MAX_MISSING_INPUTS` de `outcome_assessment` | stage04 (nested gaps) + parity | sim | sem shim |
| `_apply_owner_declared_defaults` | `argument_validation.py` | defaults somente owner-publicados; consumers: entity completeness + `_apply_entity_defaults_to_arguments` | — | stage04 + parity | sim | sem shim |
| `_owner_entity_completeness_gaps` | `argument_validation.py` | gaps de entity_schemas do catálogo owner; consumer: `_argument_completeness_gaps` | +`_extract_owner_entity_schemas`, `_entity_payload_slot`, `_canonical_key` de `outcome_assessment` | stage04 + parity | sim | sem shim |
| `_apply_entity_defaults_to_arguments` | `argument_validation.py` | aplica defaults no payload declarado; consumers: orchestrator (3 sites) | idem | stage04 + parity | sim | sem shim |
| `_argument_completeness_gaps` | `argument_validation.py` | gate de completude argument×entity-schema; consumers: orchestrator (3 sites); `descriptor` aceito mas não usado | +`ProviderCapability` de `cp.contracts` (precedente: capability_attempt) | stage04 + parity | sim | sem shim |

**DAG após:** `orchestration → interaction/argument_validation → capability_provision/outcome_assessment` — acíclico; `outcome_assessment → interaction.contracts` pré-existente. Nenhum import de `orchestration` em `argument_validation`.

#### M09 — goal/model-stage — `KEEP` (decisão fundamentada no caller graph)

| SYMBOL | DECISION | RAZÃO |
|---|---|---|
| `_build_arguments` | `KEEP` | Flow de stage-3 do coordenador: schema keys, deterministic-schema gate, block assembly, model propose, validation — esperado KEEP pelo plano 125. |
| `_model_stage_proposal` | `KEEP` | Mechanics de invocação do modelo: deadline/budget, resume replay, timeout taxonomy, logging — boundary coordinator↔model, não validação pura. |
| `_propose` | `KEEP` | Idem — proposta semântica governada (lineage única). |
| `_repair_once` | `KEEP` | Rodada bounded de reparo: re-resolve grupo live, reseleção semântica, rebuild args — orquestração, PREPARE/ACT nunca alcançam. |
| `_turn_goal_from_proposal` | `KEEP` | Validação de payload de goal em `_TurnGoal` (tipo interno do orquestrador, `_GOAL_CLASSES`, logging por decisão) — acoplado ao estado do coordinator; extração exigiria exposição de contrato novo sem consumer. |

**Caso negativo adversarial executado:** extração de `_turn_goal_from_proposal` foi avaliada e descartada — retorna tipo privado do orquestrador (`_TurnGoal`) e emite logging de decisão por classe; um parser isolado forçaria duplicação do contrato de goal ou exposição de internals — `KEEP`, conforme gate de não forçar extrações por conveniência.

### Revisão independente (preencher SOMENTE pela coordenação)

`REVIEW_SHA=PENDING` · `REVIEW_VERDICT=PENDING` · `ACCEPTANCE_REASON=PENDING` · `NEXT_STAGE_AUTHORIZED=NO`.


### Complemento de gates de teste local e deploy — diretriz PO de 2026-10-23

**Norma executiva superior:** 16 + plano 125 + runbook 130. Para esta etapa, testes locais completos no SHA modificado passam a ser condição explícita de aceite técnico: focused, full backend, architecture/import DAG, security, provider-neutral generalization, CRI e outcomes aplicáveis; Ollama local quando comportamento de modelo/prompt for afetado. Registre `LOCAL_TEST_STATUS`, `TEST_SHA`, `MODEL_CONFIG` e evidências. O deploy em produção é **objetivo condicionado** a review independente e autorização operacional específica com rollback; não executá-lo apenas com o prompt de implementação. Após deploy autorizado, homologar caminhos reais e registrar `DEPLOY_AUTHORIZATION`, `DEPLOY_STATUS`, `IMAGE_DIGEST`, `PROD_SHA`, `PROD_AUTH_HOMOLOGATION`, `BUSINESS_OUTCOME_STATUS`. Se não houver acesso/autorização, `TEST_NOT_RUN` com motivo. Para R1/R2 históricos, isto é regra prospectiva: não transformar campos passados em PASS e criar release/homologação separados mediante autorização. A próxima etapa continua dependente de decisão explícita da coordenação/PO.


### Parecer independente da coordenação — 2026-10-24

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL (R5 estrutural)**; **R5_STRUCTURAL_SCOPE=ACCEPTED**; **R6_BOUNDED_PREPARATION=AUTHORIZED**; **R6_CODE_EXECUTION=REQUIRES_EXPLICIT_GATE**. Revisão no GitHub dos arquivos alterados no commit `e1a57f915b`, relatório e evidências. Não foram reexecutados a suíte, SSH ou smoke; os PASS e deploy são `EXECUTOR_REPORTED`.

**Escopo:** M08 cinco funções puras e `MAX_ARGUMENT_KEYS` transferidos para `interaction/argument_validation.py` sem novo owner; M09 `KEEP` fundamentado por dependências reais do coordenador. Snapshot/paridade literal 19, testes focados, full backend exit 0, 43 testes de arquitetura e imagem `dc9833166850` são resultados reportados pelo executor. O2 permanece residual externo a R5; `CRI_OFF_LIVE=TEST_NOT_RUN`.

**Incidente documental:** executor registrou corrupção transitória do ledger por shell heredoc não-quotado, com restauração posterior. `DOCUMENTATION_INCIDENT=RECORDED_AND_REPORTED_FIXED`; evidência de correção no HEAD, sem afirmação de ausência histórica de drift.

**Conflito de release a decidir:** seção 'Complemento de gates de teste local e deploy' deste documento exige **review independente e autorização operacional específica antes do deploy**. O executor executou deploy após testes e antes deste review, apoiado em autorização da task. As duas bases não são automaticamente equivalentes. `RELEASE_GOVERNANCE_CONFLICT=ARCHITECTURE_DECISION_REQUIRED`, `DEPLOY_PRE_REVIEW=EXECUTOR_REPORTED`, `SECURITY_OUTCOME=NO_NEW_FAILURE_REPORTED`. Não revogar silenciosamente o gate, não inventar aprovação retroativa e não ordenar rollback sem evidência de dano. Coordenação/owner deve confirmar precedência e remediar protocolo para próximas releases.

**Próximo passo:** R6 poderá iniciar **reancoragem/inventário e testes de caracterização** para o core, sem mudar state machine, policy, AuthZ, PREPARE/ACT ou semântica do planner. Alterações de código R6 e nova promoção produtiva aguardam decisão explícita sobre o conflito de release; R7 não autorizado. `REVIEW_SHA=e1a57f915b`; `R5_ACCEPTANCE_REASON=OWNER_REUSE_AND_PARITY`; `R6_READY=YES_WITH_GATE`; `R7_AUTHORIZED=NO`.
