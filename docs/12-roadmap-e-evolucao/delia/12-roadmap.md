# 12 — Roadmap macro da DÉLIA

> **Status:** planejamento canônico  
> **Produto:** aplicação standalone nova de Continuous Operational Intelligence  
> **Autoridade de execução:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Requirements:** `CP-001…CP-310`  
> **Próxima etapa:** `C0.S0`

Este documento mostra a evolução macro. Ordem atômica, dependências e gates vivem somente em `16`.

## Visão geral

```text
C0 — Enterprise AI/Platform Foundation Freeze
C1 — Standalone Application Bootstrap
C2 — Portal Context + Platform Commands
C3 — Intelligence Core + Capability Foundations
C4 — Governed Reads + Graph/Semantics/Analysis/Predictive Discovery
C5 — Governed ACT + Executors + Durable Work
C6 — Product Work + Process/Control/Meeting/Frontline/Ecosystem
C7 — Advanced Autonomy + Twin/Edge/Marketplace/Optimization + Rollout
```

## C0 — Foundation Freeze

Inventariar e congelar, sem runtime diff:

- Portal/Core/Gateway/Infra/MFEs/APIs;
- media/devices/biometric/privacy/OT;
- Internet/OAuth/connectors/Teams;
- events/RPA/automation/queues/workers/service identities/outcome sources;
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

Output: `FOUNDATION_FREEZE=PASS` and `CHAT_RUNTIME_DEPENDENCY=0`.

## C1 — Standalone Bootstrap

Own API/MFE/manifest/Gateway/Compose/JWT-Core/federation/plugin-ui/full-page/global panel/accessibility/rollback. No thematic runtime auto-enabled.

Os namespaces planejados `minha-delpi-copilot-*` permanecem técnicos e temporários até C0.S1; o produto é DÉLIA.

## C2 — Portal Context + Commands

WorkspaceContext, EntityRefs/SourceRefs, typed navigation/platform commands, iframe bridge, shared-device baseline e operational context. Context never grants authority.

## C3 — Intelligence + Capability Foundations

- model/provider abstraction;
- conversation/understanding/planner;
- OpenAPI Action Catalog/Capability Projection;
- Expertise/Playbooks/Knowledge;
- multimodal/biometric/media;
- Internet/External/Teams foundations;
- Event/Decision `FAST|OPERATIONAL|REASONING`;
- ProcessTrace/EventLog contracts;
- AI Asset Registry projection;
- MCP/A2A trust/adapters;
- Personal Memory lifecycle;
- Semantic Metric/Glossary registry;
- isolated Analysis Sandbox foundation;
- Prediction/Prescription/Twin contracts;
- Edge device/package/cache contracts;
- Model Registry/eval lineage.

No material ACT in C3. `PREPARE != ACT`.

## C4 — Governed Reads + Analysis

- business/external/Teams reads;
- Business Graph;
- governed semantic metric queries;
- Process Mining/conformance/variants/bottlenecks read-only;
- Analysis Sandbox read-only/reproducible;
- predictive read-only pilots;
- MCP/A2A read-only delegation;
- Personal Memory-driven relevance over live facts;
- Edge read-only cached knowledge/telemetry;
- source/model/metric provenance.

## C5 — Governed ACT + Durable Foundation

C5 é o primeiro gate que pode liberar `ACT` material governado para capabilities explicitamente autorizadas. Na taxonomia de autonomia de `08`, isso corresponde a `L4 governed execute`; não equivale a L5/autonomous execution.

- Decision Gate/revalidation/live AuthZ/idempotency/audit;
- business/external/Teams writes;
- Automation Capability Registry + executor adapters;
- API/function/RPA/computer-use only when justified;
- AutomationExecution + Outcome Verification;
- Durable Workflow/waits/resume;
- Process opportunity → candidate/PREPARE;
- MCP/A2A writes under same gates;
- Artifact lifecycle/version/provenance/ACL;
- Prescriptive recommendation → PREPARE, never implicit Apply;
- material ACT → authoritative postcondition verification when required.

```text
L3 = PREPARE
L4 = GOVERNED EXECUTE
L5 = AUTONOMOUS EXECUTE WITH EXPLICIT LIMITS
```

## C6 — Product Work + Governance Experience

- Task/Case/Room/Inbox/Watch `OBSERVE|ADVISE|PREPARE`;
- Meeting/Frontline;
- external/provider events;
- Automation Hub admin;
- Process Intelligence UX + before/after measurement;
- AI Control Tower;
- MCP/A2A lifecycle/health;
- Personal Memory controls + personalized briefing;
- Semantic Layer catalog/lineage/conflicts;
- Artifact Workspace collaboration/templates;
- Operational Twin scenario workspace;
- Edge offline pilot/sync/admin;
- Model drift views;
- Capability Marketplace draft/review/catalog;
- Organizational Knowledge/Governed Learning/Expertise Studio.

Watch não dispara ACT autonomamente em C6. Capabilities de L4/governed ACT já liberadas em C5 continuam sujeitas a live AuthZ, Policy/Decision, idempotência, audit e Outcome verification.

## C7 — Advanced Autonomy + Scale

C7 adiciona autonomia avançada; não inaugura o conceito de ACT.

- capability-scoped autonomy, com L5 OFF default;
- selected Watch autonomous ACT/autonomous workflows;
- closed-loop Process Intelligence under explicit policy;
- mature AI Control Tower budgets/cohorts/incidents/kill switches;
- autonomous A2A delegation;
- advanced personalization privacy-safe;
- semantic federation/materialization scale;
- scaled sandbox/artifacts;
- Predictive/Prescriptive autonomous ACT with verified Outcome;
- advanced Operational Twin + `SIMULATE != APPLY`;
- Edge rollout/offline bounded actions only if separately approved;
- production model deployment/drift/rollback/revoke;
- Marketplace publish/enable/supply-chain controls;
- Model Router/Compute Policy;
- advanced realtime/media/Teams when justified;
- computer-use advanced only sandboxed;
- canary/rollback/performance/cost;
- OT actuation remains separate industrial-safety initiative.

## Releases conceituais

```text
Foundation Release                  → C0
Standalone Bootstrap                → C1
Contextual Platform                 → C2
Intelligence Foundations            → C3
Connected Analytical DÉLIA          → C4
Governed Action / Durable Work       → C5
Enterprise Intelligence Platform    → C6
Governed Autonomous Enterprise      → C7
```

## Anti-refactor rules

```text
boundary before provider code
shared primitive before feature type
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
