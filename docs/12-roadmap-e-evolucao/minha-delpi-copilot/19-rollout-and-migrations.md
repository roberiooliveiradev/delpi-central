# Minha DELPI Copilot — Rollout, Migrações e Implantação

**Status:** plano operacional  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Princípio:** incremental, reversível, observável e foundation-first. Sem big-bang.

## 1. Estratégia

Evoluir owners atuais antes de criar serviço novo:

```text
portal
minha-delpi-ai-api
plugins/minha-delpi-chat
Core API
APIs de domínio
MFEs/iframes
infra existente de events/jobs/rooms/notifications
```

Novo serviço/storage somente com gap provado em C0 e ADR quando material.

## 2. Releases alinhadas a C0–C7

### R0 — Foundation Freeze

Corresponde a C0.

Entrega:

- inventário/ownership;
- shared primitives/contracts;
- ports/persistence boundaries;
- versioning/correlation/error/idempotency semantics;
- contract harness;
- zero duplicate authority material.

Sem feature UX final necessária.

**Gate:** `FOUNDATION_FREEZE=PASS`.

### R1 — Platform/Context

Corresponde a C1.

Entrega:

- Platform Capability Projection;
- CopilotBridge;
- open app/route/entity;
- Workspace Context;
- MFE adapter;
- iframe base/handshake;
- contextual UX.

Rollout interno/canary.

### R2 — Intelligence Core

Corresponde a C2.

Entrega:

- single-Copilot session model;
- Expertise Catalog/retrieval;
- Domain Playbooks;
- Knowledge ACL integration;
- multimodal Evidence;
- epistemic synthesis;
- shadow agent migration com exit criteria.

Pode rodar sem Business Actions production-ready.

### R3 — Business Reads + Graph

Corresponde a C3.

Pré-condição: gates OpenAPI-first relevantes PASS.

Entrega:

- Business Capability Projection;
- generic reads;
- Outcome/Evidence normalization;
- Business Graph mínimo;
- cross-domain analysis.

Rollout read-only primeiro.

### R4 — Governed Writes

Corresponde a C4.

Entrega:

- Decision Gate Engine;
- impact preview;
- confirmations/approvals;
- idempotency/concurrency;
- generic writes;
- outcome verification;
- decoupling de agent activation/handoff.

Começar com write não destrutivo de baixo/médio risco.

### R5 — Durable Work

Corresponde a C5.

Entrega:

- workflow persistence/checkpoints;
- waits;
- DAG runner;
- Task;
- Case/Evidence Board;
- Room integration;
- Inbox;
- restart/resume safety.

### R6 — Proactivity/Ecosystem/Learning

Corresponde a C6.

Entrega:

- Watch OBSERVE/ADVISE;
- AI-ready SDK/templates;
- readiness scanner/waves;
- project preferences;
- Organizational Knowledge;
- Governed Learning;
- Expertise Studio;
- admin/coverage.

### R7 — Optimization/Autonomy/Rollout

Corresponde a C7.

Entrega gradual:

- L5 selected;
- Watch ACT selected;
- Simulation pilots;
- Model Router;
- agent-routing cleanup;
- progressive rollout/final verification.

L5/ACT não são default.

## 3. Feature flags

Flag = rollout tool, não arquitetura permanente.

Cada flag precisa:

```text
name
owner
scope
introducedAt
successCriteria
rollbackTrigger
exitCriteria
plannedRemoval
```

Nomes reais só após inventário de convenção atual.

Famílias conceituais possíveis:

```text
platform/context
single-copilot expertise
business reads/graph
governed writes
durable work
watch/proactivity
autonomy
simulation/model routing
```

Evitar flag por endpoint/app quando uma flag transversal/cohort resolve.

## 4. Migration policy

Preferir:

```text
EXPAND
→ compatible readers
→ writers
→ BACKFILL se necessário
→ CUTOVER
→ MONITOR
→ CONTRACT/CLEANUP posterior
```

Dual read/write somente se inevitável, com exit criteria.

## 5. Migration planning por fase

### C0

Não criar tabelas só porque o contrato existe. Definir boundaries e provar gaps.

### C2

Possível persistence de Expertise/Playbook catalog somente se current owner não atender.

### C3

Graph pode exigir relationship/index store; não armazenar domain objects completos.

### C4

Decision/approval persistence pode estender mecanismo existente.

### C5

Possíveis stores, se gaps provados:

- workflow instance/steps;
- checkpoints/waits;
- Task/Case refs/state;
- dedupe/idempotency coordination.

Room/Inbox devem preferir owners/views existentes.

### C6/C7

Watch/Experience/Compute policy persistence somente quando runtime correspondente for implementado.

## 6. Antes de qualquer migration

1. procurar owner/model/repository existente;
2. provar necessidade durável;
3. validar shared primitive C0;
4. definir retention/LGPD;
5. constraints/indexes;
6. concurrency/idempotency;
7. forward/backout path;
8. tests;
9. observability;
10. confirmar que fase seguinte conhecida não exigirá remodelagem previsível.

## 7. Ordem de experiência para usuários

Mesmo com foundations internas, percepção deve expandir com risco crescente:

```text
explain
→ navigation/context
→ specialized analysis/evidence
→ business reads
→ prepare/governed write
→ durable tasks/cases
→ advise/watch
→ selected automation
→ optimization
```

## 8. Cohorts

Conforme infraestrutura vigente:

- environment;
- internal users/groups;
- app/domain;
- capability family;
- feature family;
- autonomy level.

Cohort não concede business permission.

## 9. Rollback por camada

### Platform/Context
Desligar bridge/context integration; apps continuam manualmente utilizáveis.

### Expertise/Multimodal
Desabilitar candidate/version problemática; base conversational continua.

### Business Reads/Graph
Remover availability no Copilot; source APIs continuam normais.

### Writes
Read-only kill switch; preservar audit/outcomes.

### Durable Work
Bloquear novos workflows e preservar estado; definir tratamento seguro para running/waiting.

### Watch
Desabilitar triggers; não perder audit/history.

### Model Router
Voltar para policy/model baseline conhecido.

## 10. Stop-the-line

- unauthorized action/data exposure;
- duplicate authority/foundation drift;
- write sem required Decision Gate;
- duplicate write em retry/resume;
- graph/room/case vazando source data;
- Watch ACT sem policy;
- secret/token leak;
- arbitrary URL/action;
- model provider violando data policy;
- irreproducible evidence;
- migration sem rollback/mitigation em dado crítico.

## 11. Promotion criteria

- phase COMPLETE_GATE PASS;
- current SHA evidence;
- required tests PASS;
- RBAC/security negatives PASS;
- metrics/traces disponíveis;
- rollback testado;
- no material legacy fallback no objetivo da release;
- docs/ledger consistentes.

## 12. Produção

```text
internal canary
→ selected app/users
→ read scale
→ governed write canary
→ durable work selected
→ Watch advise selected
→ selected ACT/autonomy only after governance
→ metrics/incident review
→ progressive expansion
```

Nunca usar rollout para ocultar foundation incompleta.