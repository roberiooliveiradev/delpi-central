# Minha DELPI Copilot — Rollout, Migrações e Implantação

**Status:** plano operacional  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Arquitetura/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
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

Architecture style/pattern não muda por release. O que foi congelado em C0 permanece authority; exceção exige decisão arquitetural explícita.

## 2. Releases alinhadas a C0–C7

### R0 — Foundation Freeze

Corresponde a C0.

Entrega:

- inventário/ownership;
- inventário dos patterns/layers/DI/error/event/state/resilience/migration atuais;
- shared primitives/contracts;
- ports/persistence boundaries;
- architecture style validado;
- layer/dependency rules;
- bounded contexts;
- Pattern Decision Matrix;
- Abstraction Gate;
- error/result model;
- event/state-machine rules;
- frontend state ownership;
- resilience/idempotency;
- migration/Strangler/ACL rules;
- architectural exception/ADR process;
- versioning/correlation/error/idempotency semantics;
- contract + architecture conformance harness;
- zero duplicate authority/foundation material.

Sem feature UX final necessária.

**Gate:** `FOUNDATION_FREEZE=PASS` com os gates arquiteturais do `16/49`.

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

Padrões: Command + Handler + Adapter; sem handler específico por app no core.

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

Migração legada usa Adapter/Anti-Corruption Layer/Strangler. Strategy só quando variação real justificar.

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

Graph segue Ports & Adapters; storage/index novo somente com gap comprovado.

Rollout read-only primeiro.

### R4 — Governed Writes

Corresponde a C4.

Entrega:

- Decision Gate Engine;
- impact preview;
- confirmations/approvals como estados do mesmo lifecycle;
- idempotency/concurrency;
- generic writes;
- outcome verification;
- decoupling de agent activation/handoff.

Padrões: Policy + State Machine + Idempotency. Retry cego de write é proibido.

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

Padrões: Application orchestration + State Machine + Idempotency. Saga somente se houver múltiplos writes distribuídos e compensações reais.

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

Watch usa event semantics canônicas; Expertise Studio usa use cases/lifecycle canônico.

### R7 — Optimization/Autonomy/Rollout

Corresponde a C7.

Entrega gradual:

- L5 selected;
- Watch ACT selected;
- Simulation pilots;
- Model Router;
- agent-routing cleanup;
- progressive rollout/final verification.

Model Router só introduz Strategy/Policy após baseline. L5/ACT não são default.

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

Feature flag não autoriza manter duas architectures/authorities indefinidamente.

## 4. Migration policy

Preferir para schema/contrato:

```text
EXPAND
→ compatible readers
→ writers
→ BACKFILL se necessário
→ CUTOVER
→ MONITOR
→ CONTRACT/CLEANUP posterior
```

Para runtime/legado:

```text
Legacy
→ Adapter / Anti-Corruption Layer
→ canonical model
→ telemetry/evals
→ canary
→ cutover
→ residual scan
→ remove legacy adapter
```

Isso implementa Strangler Fig quando aplicável.

Dual read/write somente se inevitável, com owner + exit criteria + planned removal.

## 5. Migration planning por fase

### C0

Não criar tabelas, repositories ou generic engines só porque o contrato existe. Definir boundaries, patterns e provar gaps.

### C2

Possível persistence de Expertise/Playbook catalog somente se current owner não atender. Legacy agent compatibility permanece atrás de ACL/adapter temporário.

### C3

Graph pode exigir relationship/index store; não armazenar domain objects completos. Repository só se o Graph possuir estado/materialização própria.

### C4

Decision/approval persistence pode estender mecanismo existente. Idempotência prefere owner da domain API.

### C5

Possíveis stores, se gaps provados:

- workflow instance/steps;
- checkpoints/waits;
- Task/Case refs/state;
- dedupe/idempotency coordination.

Room/Inbox devem preferir owners/views existentes.

### C6/C7

Watch/Experience/Compute policy persistence somente quando runtime correspondente for implementado.

## 6. Antes de qualquer migration ou nova abstração

1. procurar owner/model/repository/adapter existente;
2. provar necessidade durável ou boundary real;
3. validar shared primitive C0;
4. consultar Pattern Decision Matrix do `49`;
5. passar pelo Abstraction Gate;
6. definir retention/LGPD;
7. constraints/indexes;
8. concurrency/idempotency;
9. forward/backout path;
10. tests;
11. observability;
12. confirmar que fase seguinte conhecida não exigirá remodelagem previsível;
13. se houver desvio do padrão canônico, registrar ADR/decisão antes de implementar.

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

Cohort não concede business permission nem flexibiliza architecture/security gates.

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

### Legacy migration
Rollback pode reativar caminho compatível somente enquanto sua janela/exit criteria estiverem ativos; não reintroduzir legacy como fallback permanente.

## 10. Stop-the-line

- unauthorized action/data exposure;
- duplicate authority/foundation drift;
- architecture/pattern drift material;
- dependency rule violation;
- unjustified abstraction;
- architectural exception sem ADR/decisão;
- framework/provider concreto vazando para Domain/Application;
- durable business authority no frontend;
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
- architecture conformance PASS;
- RBAC/security negatives PASS;
- metrics/traces disponíveis;
- rollback testado;
- Abstraction Gate/evidence registrado para abstrações novas materiais;
- ADR presente para exceções materiais;
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

Nunca usar rollout para ocultar foundation incompleta ou architecture drift.