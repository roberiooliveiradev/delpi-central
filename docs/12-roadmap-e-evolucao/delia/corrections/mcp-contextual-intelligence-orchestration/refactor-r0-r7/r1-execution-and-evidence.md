# R1 — Instruções LLM e recursos declarativos: prompt e registro de evidências

**PLANO:** [125](../125-orchestration-complete-refactoring-finite-plan.md) · **RUNBOOK:** [130](../130-orchestration-refactor-r0-r7-execution-playbook.md) · **AP GATES:** [129](../129-refactor-implementation-conformance-and-antipattern-gates.md)  
**TASK_ID:** `DELIA-ORCH-REFAC-R1-BOUNDED-01` · **LOTES:** M01 · **ESTADO DO DOCUMENTO:** TEMPLATE_NOT_EXECUTED / NOT_AUTHORIZED.  
**NÃO É autorização nem evidência de execução.** Ler 16→50→17→49→51→52→21→20→25 + 03/24/60, ADR58, roadmap59, 113,117, 125,128–130, .cursor e ledger no HEAD.

## Prompt pronto para Devin — executar SOMENTE quando gate liberado

> Execute integralmente `DELIA-ORCH-REFAC-R1-BOUNDED-01` conforme o plano 125, protocolo 129 e runbook 130 §4. Sem pedir microconfirmações; STOP quando não existir autorização/contrato/owner, não por conveniência. Reancore HEAD/origin/main/status/authorities, confirme que a etapa anterior recebeu parecer independente e congele o BASE_SHA. Faça o menor diff possível dentro da whitelist. Execute baseline/RED→GREEN/paridade, suíte backend completa e provas de arquitetura, segurança, generalização e outcomes impactados. Se detectar regressão reparável dentro do contrato, execute automaticamente UM rework bounded com novo RED, reaplique toda a matriz e remova código legado obsoleto; se ainda falhar, STOP. Preencha este documento com evidências reais, registre README/ledger no final e envie report à coordenação. Não se autoaceite, não execute deploy ou próxima etapa sem gate.

**Objetivo:** Separar apenas conteúdo declarativo de instruções onde recurso/loader legítimo já existe, preservando lineage e contrato das propostas.

**Arquivos permitidos no contrato preliminar (R0 deve reduzir a ALLOWED_FILES precisa):** Blocos de instrução e wiring estritamente autorizados em orchestration.py, recurso/loader versionado existente, testes focados e documentação.

**Arquivos/mudanças proibidos:** Novo prompt registry, alteração de seleção/Policy, duplicação de instruções, migração em massa, troca de modelo, budget ou configuração.

**Passos específicos obrigatórios:** Inventariar instruction-id/version/hash/purpose/consumers; distinguir schema e lógica de strings; reutilizar loader e validar compatibilidade; criar RED/snapshot antes, fazer menor migração, eliminar string duplicada antiga e imports mortos; declarar SKIP se hash/contrato não puder ser preservado sem ADR.

**Provas de não regressão específicas:** Snapshot de prompts/lineage, recurso ausente/corrompido fail-closed, R0 goldens, backend completo, testes de modelo quando proposta semântica material, AP-01…20 e grafo de imports.

**Gate de saída:** Texto migrado tem owner e versão; comportamento tipado/prompt invariantes ou mudança explicitamente autorizada; nenhum texto legado duplicado.

**STOP material:** Qualquer violação AP/autoridade, ausência de owner/contrato ou segunda falha do mesmo pacote exige STOP e revisão independente.

## Documento obrigatório a preencher pelo executor após execução

**STATUS:** `NOT_STARTED` — substituir por `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW|IMPLEMENTATION_FAILED|IMPLEMENTATION_INCONCLUSIVE|EXECUTION_DRIFT|SKIP_WITH_DECISION` somente com fatos.

| Campo | Evidência a preencher (não presumir PASS) |
|---|---|
| PLAN_ID / STEP / TASK_ID | DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01 / R1 / task concreta |
| AUTHORIZATION_REF / PHASE_FROM_16_LEDGER | PENDING |
| HEAD_BEFORE / ORIGIN_MAIN / GIT_STATUS / BASE_SHA | PENDING |
| AUTHORITIES_READ / CP_RQ / FROZEN_DECISIONS | PENDING |
| GOAL / ENTRY_GATES / ALLOWED_FILES / FORBIDDEN_FILES | PENDING |
| FUNCTION_MAP / OWNER / REAL_CONSUMER / CONTRACT | TO_INVENTORY |
| EXISTING_EQUIVALENT / REUSE_DECISION / NEW_FILE_GATE | TO_INVENTORY |
| ACTUAL_FILES / SCOPED_DIFF / CONTRACT_COMPAT | PENDING |
| IMPORT_DAG_BEFORE_AFTER / DUPLICATE_CHECK / ARCH_TESTS | TEST_NOT_RUN |
| LEGACY_CURRENT / DEPRECATED_ACTIVE / OBSOLETE_PROVEN / DELETED | TO_INVENTORY |
| BASELINE_TESTS / RED_GREEN / FULL_BACKEND / SECURITY / GENERALIZATION | TEST_NOT_RUN |
| D4/D5/D5-R/D5-schema/D8/D8-R/N1 / CRI_ON_OFF | TEST_NOT_RUN |
| AI_EVAL_SHA_MODEL_CONFIG / BUSINESS_OUTCOME / POSTCONDITION | TEST_NOT_RUN |
| AP01_AP20_EVIDENCE_WITH_STATUS / CI_VS_MANUAL | PENDING |
| REGRESSION_DELTA / FIRST_DIVERGENT_STAGE / NO_REGRESSION_FOR_EVALUATED_SCOPE | INCONCLUSIVE |
| AUTO_REWORK_USED (0/1) / REWORK_RED_GREEN / REWORK_FINAL_MATRIX | 0 / TEST_NOT_RUN |
| RESIDUAL_SEARCH / ROLLBACK / SECURITY_SECRETS | PENDING |
| FINAL_HEAD / ORIGIN_MAIN_FINAL / PUSH_VERIFIED | PENDING |
| README_LEDGER_UPDATED / DELETIONS_RATIONALE | PENDING |
| EXECUTION_DRIFT / RESIDUALS / STOP_REASON | PENDING |
| EXECUTOR_VERDICT / COORDINATION_REVIEW_REQUIRED | PENDING / YES |

### Evidência específica da etapa R1

Tabela obrigatória por função migrada: ORIGIN SYMBOL | NEW OWNER/FILE | CONTRACT/CONSUMERS | BEFORE/AFTER IMPORTS | TESTS | OLD SYMBOL REMOVED? | LEGACY/COMPAT DECISION. Incluir ao menos 1 caso negativo adversarial, se runtime mudou.

### Revisão independente (preencher SOMENTE pela coordenação)

`REVIEW_SHA=PENDING` · `REVIEW_VERDICT=PENDING` · `ACCEPTANCE_REASON=PENDING` · `NEXT_STAGE_AUTHORIZED=NO`.
