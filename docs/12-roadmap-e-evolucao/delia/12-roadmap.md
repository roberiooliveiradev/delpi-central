# 12 — Roadmap macro da DÉLIA

> **Status:** planejamento canônico  
> **Produto:** aplicação standalone nova de Continuous Operational Intelligence  
> **Autoridade de execução:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Requirements:** `CP-001…CP-316`  
> **Próxima etapa:** `ARCHITECTURE_REVIEW_C0_S5`

Este documento mostra a evolução macro. Ordem atômica, dependências e gates vivem somente em `16`. Nada neste roadmap prova runtime implementado ou fase concluída.

## Visão geral

```text
C0 — Enterprise AI/Platform Foundation Freeze
C1 — Standalone Application Bootstrap
C2 — Portal Context + Platform Commands
C3 — Intelligence Core + Capability Foundations
C4 — Governed Reads + Graph/Semantics/Analysis/Predictive Discovery
C5 — Governed ACT + Durable/Recurring Work + Approved Execution Contracts
C6 — Product Work + Process/Control/Meeting/Frontline/Ecosystem
C7 — Advanced Autonomy + Twin/Edge/Marketplace/Optimization + Rollout
```

## C0 — Foundation Freeze

Inventariar e congelar, sem runtime diff:

- Portal/Core/Keycloak/Gateway/Infra/MFEs/APIs;
- media/devices/biometric/privacy/OT;
- Internet/OAuth/connectors/Teams;
- events/RPA/automation/queues/workers/service identities/outcome sources;
- schedulers/timers/cron/polling, recurring job/work definitions e owners;
- timezone/DST/calendar, misfire/missed-run/reconciliation, overlap/concurrency e occurrence idempotency;
- background identity/AuthZ/revoke semantics para execução temporal;
- process logs/process owners/task mining;
- AI/model/automation assets/evals/cost/incidents/kill switches;
- MCP/A2A/tool/agent infrastructure;
- Personal Memory/profile/preferences/privacy;
- semantic KPIs/glossary/BI models;
- sandbox/query/file/artifact infrastructure;
- predictive/optimization/simulation/twin;
- Edge/offline/network/device/MDM/local inference;
- model registry/MLOps/Marketplace/supply-chain;
- ownership/primitives/state/security/tests.

C0 separa `RecurringWorkDefinition`/Work ownership do owner físico do scheduler/timer. `schedule != permission`; scheduler existente não vira Work/Policy authority e ausência de scheduler provado não autoriza criar um novo sem Abstraction Gate.

Output só pode ser `FOUNDATION_FREEZE=PASS` quando `20` e o ledger tiverem evidence válida no SHA/config avaliado. Até lá, programa permanece `PLANNED / NOT_STARTED`.

## C1 — Standalone Bootstrap

Own API/MFE/manifest/Gateway/Compose/JWT-Core/federation/plugin-ui/full-page/global panel/accessibility/rollback, conforme contracts/evidence C0. No thematic runtime auto-enabled.

Os namespaces planejados `minha-delpi-copilot-*` permanecem técnicos e temporários até C0.S1; o produto é DÉLIA.

## C2 — Portal Context + Commands

WorkspaceContext, EntityRefs/SourceRefs, typed navigation/platform commands, iframe bridge, shared-device baseline e operational context, somente conforme contracts congelados. Context never grants authority.

## C3 — Intelligence + Capability Foundations

Targets condicionados a C0/Abstraction Gate:

- model/provider abstraction mínima;
- conversation/understanding/planner;
- OpenAPI-derived Capability Projection;
- Expertise/Playbooks/Knowledge;
- multimodal/biometric/media;
- Internet/External/Teams foundations;
- Event/Decision `FAST|OPERATIONAL|REASONING`;
- ProcessTrace/EventLog semantics;
- AI asset governance projection;
- MCP/A2A trust/adapters;
- Personal Memory lifecycle;
- Semantic Metric/Glossary contracts;
- isolated Analysis Sandbox foundation;
- Prediction/Prescription/Twin contracts;
- Edge device/package/cache contracts;
- model/eval lineage.

No material ACT in C3. `PREPARE != ACT`.

## C4 — Governed Reads + Analysis

- business/external/Teams reads;
- Business Graph target;
- governed semantic metric queries;
- Process Mining/conformance/variants/bottlenecks read-only;
- Analysis Sandbox read-only/reproducible;
- predictive read-only pilots;
- MCP/A2A read-only delegation;
- Personal Memory-driven relevance over live facts;
- Edge read-only cached knowledge/telemetry;
- source/model/metric provenance.

## C5 — Governed ACT + Durable/Recurring Foundation

C5 é o primeiro gate que pode liberar material `ACT` governado para capabilities explicitamente autorizadas. Na taxonomia de autonomia de `08`, isso corresponde a `L4 governed execute`; não equivale a L5/autonomous execution.

- live AuthZ + Policy/Decision/revalidation/idempotency/audit;
- business/external/Teams writes quando autorizados;
- semantic capability projection + versioned mapping para execution contract aprovado;
- direct Domain API path quando apropriado;
- Automation Hub/approved executor adapters para technical execution quando aplicável;
- DÉLIA Work/execution correlation sem duplicar technical worker state;
- authoritative Outcome Verification;
- Durable Workflow/waits/resume;
- Recurring Governed Work persisted independently of chat session;
- create/inspect/list/pause/resume/cancel recurring Work;
- explicit IANA timezone/start/end/DST/misfire/overlap semantics;
- one correlated/idempotent occurrence across duplicate tick/retry/restart/reconciliation;
- live identity/Core/domain AuthZ + Policy/Decision/provider/source revalidation per material occurrence;
- canonical recurring report→Artifact→`communication.email.send` anchor with verified Outcome;
- Process opportunity → candidate/PREPARE;
- MCP/A2A writes sob mesmos gates;
- Artifact lifecycle/version/provenance/ACL;
- Prescriptive recommendation → PREPARE, never implicit Apply;
- material ACT → authoritative postcondition verification quando required.

```text
L3 = PREPARE
L4 = GOVERNED EXECUTE
L5 = AUTONOMOUS EXECUTE WITH EXPLICIT LIMITS
```

Recurring Work temporal bounded pode usar L4 em C5 quando todos os live gates passarem. Isso não é Watch autonomous ACT e não exige C7/L5.

## C6 — Product Work + Governance Experience

- Task/Case/Room/Inbox/Watch `OBSERVE|ADVISE|PREPARE` by default;
- Recurring Work admin/history UX: status/recurrence/timezone/next occurrence quando derivável/last outcome/pause/resume/cancel;
- Meeting/Frontline;
- external/provider events;
- Automation Hub governance/projection UX sem tomar technical ownership;
- Process Intelligence UX + before/after measurement;
- AI Control Tower;
- MCP/A2A lifecycle/health;
- Personal Memory controls + personalized briefing;
- Semantic Layer catalog/lineage/conflicts;
- Artifact Workspace collaboration/templates;
- Operational Twin scenario workspace;
- Edge offline pilot/sync/admin;
- model drift views;
- Capability Marketplace draft/review/catalog;
- Organizational Knowledge/Governed Learning/Expertise Studio.

Watch não dispara ACT autonomamente em C6. Capabilities de L4/governed ACT liberadas em C5, incluindo Recurring Governed Work bounded, continuam sujeitas aos mesmos gates. Schedule admin não concede domain/provider permission.

## C7 — Advanced Autonomy + Scale

C7 adiciona autonomia avançada; não inaugura ACT.

- capability-scoped autonomy, L5 OFF default;
- selected Watch autonomous ACT/autonomous workflows;
- closed-loop Process Intelligence sob explicit policy;
- mature Control Tower budgets/cohorts/incidents/kill switches;
- autonomous A2A delegation;
- advanced personalization privacy-safe;
- semantic federation/materialization scale;
- scaled sandbox/artifacts;
- Predictive/Prescriptive autonomous ACT with verified Outcome;
- advanced Operational Twin + `SIMULATE != APPLY`;
- Edge rollout/offline bounded actions only if separately approved;
- production model deployment/drift/rollback/revoke;
- Marketplace publish/enable/supply-chain controls;
- Model Router/Compute Policy optimization;
- advanced realtime/media/Teams when justified;
- computer-use advanced only sandboxed;
- canary/rollback/performance/cost;
- OT actuation remains separate industrial-safety initiative.

Recurring Governed Work C5 não precisa de L5/C7 quando a recorrência é bounded e cada ocorrência revalida autorização. C7 não transforma schedule em permission authority.

## Releases conceituais

```text
Foundation Release               → C0
Standalone Bootstrap             → C1
Contextual Platform              → C2
Intelligence Foundations         → C3
Connected Analytical DÉLIA       → C4
Governed Action / Durable Work    → C5
Enterprise Intelligence Platform → C6
Governed Autonomous Enterprise   → C7
```

## Anti-refactor rules

```text
boundary before provider code
Abstraction Gate before interface/registry/engine/scheduler
Graph != Semantic Layer
Memory != Knowledge
Process Mining != surveillance
Control Tower != business authority
MCP/A2A discovery != approval
Sandbox != unrestricted shell
Prediction != fact
Twin simulation != production
Edge offline != wider authority
Model/Marketplace install != permission
API before RPA where authoritative contract exists
DÉLIA Work != Automation Hub technical execution
DÉLIA RecurringWork definition != physical scheduler technical state
schedule != permission
technical success != verified Outcome
PREPARE != ACT
C5 governed ACT != C7 autonomous ACT
L5 default OFF
```

## Primeira execução

```text
C0.S0 factual inventory only
→ C0.S1–S7 foundation freeze
→ C1.S1 standalone API skeleton
```

Estado real: [`evidence/execution-ledger.md`](./evidence/execution-ledger.md).
