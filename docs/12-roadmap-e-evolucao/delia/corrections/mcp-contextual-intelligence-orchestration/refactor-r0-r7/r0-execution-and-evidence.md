# R0 — Baseline, inventário finito e contrato de saída: prompt e registro de evidências

**PLANO:** [125](../125-orchestration-complete-refactoring-finite-plan.md) · **RUNBOOK:** [130](../130-orchestration-refactor-r0-r7-execution-playbook.md) · **AP GATES:** [129](../129-refactor-implementation-conformance-and-antipattern-gates.md)  
**TASK_ID:** `DELIA-ORCH-REFAC-R0-BOUNDED-01` · **LOTES:** M01–M10 · **ESTADO DO DOCUMENTO:** TEMPLATE_NOT_EXECUTED / NOT_AUTHORIZED.  
**NÃO É autorização nem evidência de execução.** Ler 16→50→17→49→51→52→21→20→25 + 03/24/60, ADR58, roadmap59, 113,117, 125,128–130, .cursor e ledger no HEAD.

## Prompt pronto para Devin — executar SOMENTE quando gate liberado

> Execute integralmente `DELIA-ORCH-REFAC-R0-BOUNDED-01` conforme o plano 125, protocolo 129 e runbook 130 §4. Sem pedir microconfirmações; STOP quando não existir autorização/contrato/owner, não por conveniência. Reancore HEAD/origin/main/status/authorities, confirme que a etapa anterior recebeu parecer independente e congele o BASE_SHA. Faça o menor diff possível dentro da whitelist. Execute baseline/RED→GREEN/paridade, suíte backend completa e provas de arquitetura, segurança, generalização e outcomes impactados. Se detectar regressão reparável dentro do contrato, execute automaticamente UM rework bounded com novo RED, reaplique toda a matriz e remova código legado obsoleto; se ainda falhar, STOP. Preencha este documento com evidências reais, registre README/ledger no final e envie report à coordenação. Não se autoaceite, não execute deploy ou próxima etapa sem gate.

**Objetivo:** Congelar baseline funcional pós-estabilização, mapear todas as funções e consumidores, demonstrar equivalentes e destinos possíveis sem tocar runtime.

**Arquivos permitidos no contrato preliminar (R0 deve reduzir a ALLOWED_FILES precisa):** Documentação R0, matrizes e scripts read-only previamente existentes; nenhum arquivo runtime.

**Arquivos/mudanças proibidos:** Alterar orchestration.py, imports, prompts, schemas, CI, providers, deployment ou autorizar NEW.

**Passos específicos obrigatórios:** Revalidar latest 16/ledger/HEAD e aceite independente da estabilização; extrair AST/call graph/import DAG, revisar F01–F42 e G-SA; inventariar cada função, ativo legado e dependência, com prova de consumidores reais e custo de acoplamento; marcar KEEP/EXTEND/EXTRACT/SKIP e CURRENT/DEPRECATED/OBSOLETE/TO_INVENTORY; definir contratos e ALLOWED_FILES precisos para R1–R6.

**Provas de não regressão específicas:** Sem regressão de runtime porque CODE_CHANGED=NO, comparar baselines versionados e status dos outcomes D4/D5/D5-R/D5-schema/D8/D8-R/N1; NÃO declarar teste executado nesta etapa se não foi.

**Gate de saída:** Mapa M01–M10 completo, sem funções sem classificação; DAG de dependências, arquivos planejados condicionais, backlog de legado e baseline funcional com SHA/model/config, tudo revisável.

**STOP material:** Se não houver aceite independente da estabilização ou a autoridade 16/ledger bloquear a fase, STOP R0 sem código.

## Documento obrigatório a preencher pelo executor após execução

**STATUS:** `NOT_STARTED` — substituir por `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW|IMPLEMENTATION_FAILED|IMPLEMENTATION_INCONCLUSIVE|EXECUTION_DRIFT|SKIP_WITH_DECISION` somente com fatos.

| Campo | Evidência a preencher (não presumir PASS) |
|---|---|
| PLAN_ID / STEP / TASK_ID | DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01 / R0 / task concreta |
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

### Evidência específica da etapa R0

Tabela obrigatória por cada função/arquivo afetado: SYMBOL | LINE/HEAD | OWNER | CURRENT CONTRACT | CONSUMERS | IMPORTS | STATUS KEEP/EXTEND/EXTRACT/SKIP | EQUIVALENT | TARGET FILE | CP/RQ | TEST | LEGACY CLASS. Identificar no mínimo M01–M10 e fechar o inventário do arquivo sem criar runtime.

### Revisão independente (preencher SOMENTE pela coordenação)

`REVIEW_SHA=PENDING` · `REVIEW_VERDICT=PENDING` · `ACCEPTANCE_REASON=PENDING` · `NEXT_STAGE_AUTHORIZED=NO`.
