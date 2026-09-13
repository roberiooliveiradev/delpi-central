# 12 — Roadmap macro do Minha DELPI Copilot

> **Status:** planejamento canônico  
> **Produto:** aplicação standalone nova  
> **Autoridade de execução:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
> **Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
> **Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
> **Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
> **Microsoft Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)  
> **Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)  
> **Próxima etapa:** `C0.S0`

Este roadmap apresenta evolução macro. A ordem atômica/dependências/gates vive somente em `16`.

## Visão geral

```text
C0 — Platform + Architecture + Media/Privacy/Biometric/External/Automation/OT Foundation Freeze
C1 — Standalone Application Bootstrap
C2 — Portal Context + Operational Context + Platform Commands
C3 — Intelligence + Multimodal/Biometric/Internet/Connector/Decision Foundations
C4 — Business + External Reads + Business Graph + Operational Read Intelligence
C5 — Governed Business/External/Automation Writes + Durable Work Foundation
C6 — Tasks/Cases/Rooms/Inbox/Watch + Meeting/Frontline + Automation Hub + Events/Learning
C7 — Autonomous Operations + Advanced Realtime/External Proactivity + Simulation/Model Routing/Rollout
```

## C0 — Foundation Freeze

Entregas principais:

- inventário Portal/Core/Gateway/Infra/MFEs/APIs/OpenAPIs;
- auth/RBAC/manifest/federation/contracts;
- media/devices/shared terminals/biometric/privacy;
- production/maintenance/quality/OT boundaries;
- Internet/egress/search/safe-fetch;
- OAuth/secrets/external connectors/Teams;
- rooms/events/notifications/jobs/workers/schedulers existentes;
- **RPA tools/orchestrators/licences/bots/packages existentes**;
- **automations/scripts/functions/jobs existentes**;
- **queues/workers/desktop execution infrastructure existente**;
- **service accounts/background identities**;
- **business postcondition/outcome sources**;
- **automation governance/kill switches/emergency stop**;
- ownership do futuro Automation & Execution Hub;
- executor preference/contract;
- event trust/dedupe/correlation;
- background identity;
- Outcome verification;
- capability-scoped autonomy;
- RED/conformance harness;
- `CHAT_RUNTIME_DEPENDENCY=0`;
- `FOUNDATION_FREEZE=PASS`.

Nenhuma ferramenta RPA, fila, event bus ou novo serviço é assumido como existente sem evidence.

## C1 — Standalone Bootstrap

- own Copilot API/MFE;
- JWT/Core;
- Module Federation/plugin-ui;
- own manifest/Gateway/Compose;
- full-page + global host;
- responsive/accessibility baseline;
- Chat-offline independence.

Não implementar Automation Hub/RPA/event engine apenas porque seus contracts já foram congelados.

## C2 — Portal + Operational Context + Commands

- WorkspaceContext;
- Global Bridge;
- platform capability projection;
- open app/route/entity;
- EntityRefs operacionais;
- SourceRefs externos bounded;
- shared-device baseline;
- iframe baseline;
- execution/watch refs apenas como contexto, nunca execution authority.

## C3 — Intelligence + Decision Foundations

- model/provider abstraction;
- conversation/turn state;
- OpenAPI ingestion/Action Catalog;
- capability retrieval/planner;
- Expertise/Playbooks/Knowledge;
- multimodal/speech/vision/biometric;
- Internet Research + ExternalConnection;
- Microsoft 365/Teams foundation;
- Evidence/provenance;
- **EventEnvelope ingestion semantics**;
- **DecisionPathPolicy `FAST | OPERATIONAL | REASONING`**;
- deterministic Policy/Specification for material readiness where criteria exist;
- no material autonomous ACT.

Nem todo evento chama LLM.

## C4 — Reads + Graph + Operational Read Intelligence

- generic business reads;
- external/Teams reads;
- Evidence/freshness normalization;
- DELPI Business Graph;
- internal/external correlation;
- read-only operational intelligence, e.g.:

```text
invoice readiness
production report plausibility
stock/shortage risk
supplier delay risk
machine downtime context
```

No side effect in these read-only evaluations.

## C5 — Governed Writes + Automation Execution Foundation

- Decision Gate;
- business/external writes;
- `draft != send`;
- Durable Workflow/checkpoints/waits;
- semantic Automation Capability Registry/Projection;
- executor ports/adapters as prioritized:

```text
API
Function/Script
RPA
Computer-Use only when justified
Notification
Human Task
```

- AutomationExecution lifecycle;
- RPA worker/queue integration only if C0 proves it belongs in scope;
- idempotency/retry/ambiguous outcome handling;
- **verified business Outcome/postcondition**.

Default executor preference:

```text
API official
→ native integration
→ deterministic function/script
→ RPA
→ computer-use
→ human
```

## C6 — Product Work + Automation Hub + Proactivity

- Task/Case/Evidence Board;
- Interaction Rooms;
- Inbox;
- provider/domain events;
- Meeting/Frontline;
- Knowledge/Learning;
- Expertise Studio;
- Automation & Execution Hub administration;
- executions/workers/exceptions/outcomes visibility;
- notification/escalation orchestration;
- Watch modes:

```text
OBSERVE
ADVISE
PREPARE
```

`ACT` remains locked.

Manual exception resumes the same Durable Workflow.

## C7 — Autonomous Operations + Advanced Rollout

- Watch `ACT` for selected capabilities;
- capability/context/risk-scoped autonomy;
- L5 OFF by default;
- allowlists/budgets/limits/kill switches;
- autonomous end-to-end workflows with Outcome verification;
- external proactivity;
- advanced realtime;
- computer-use only as bounded fallback;
- Simulation;
- Model Router/Compute Policy;
- scale/cost/performance;
- canary/rollback.

Anchor when in declared scope:

```text
ready-to-invoice
→ deterministic readiness
→ autonomy policy
→ billing.invoice.issue
→ API/RPA executor
→ verify authoritative invoice outcome
→ notify affected people/channels
```

OT actuation remains a separate industrial-safety initiative.

## Dependência entre fases

```text
foundation C0
↓
standalone app C1
↓
context C2
↓
intelligence/event/decision foundations C3
↓
read-only operational intelligence C4
↓
governed execution foundation C5
↓
Automation Hub + PREPARE proactivity C6
↓
selected autonomous ACT C7
```

## Regras anti-refatoração

- C0 inventaria antes de escolher RPA platform/event bus/queue architecture;
- Copilot intelligence and Automation Hub execution remain separate concerns;
- API is preferred over RPA when an authoritative supported contract exists;
- planner works with semantic capability, never RPA clicks/selectors;
- EventEnvelope precedes source-specific automation logic;
- deterministic Policy/Specification precedes prompt-only readiness decisions;
- AutomationExecution/idempotency precedes autonomous retry;
- technical execution success never replaces verified business outcome;
- `PREPARE != ACT`;
- autonomy is capability/context/risk scoped; no global L5;
- background actor/service identity is explicit;
- computer-use remains sandboxed fallback;
- OT safety remains external authority;
- Chat does not need migration/refactor to progress.

## Releases de produto

```text
Foundation Release                         → C0
Standalone Bootstrap Release               → C1
Contextual Platform Release                → C2
Intelligence/Event Decision Foundation     → C3
Connected Operational Read Copilot         → C4
Governed Execution Foundation              → C5
Automation Hub + Work/Meeting/Frontline    → C6
Autonomous Operations Release              → C7
```

## Primeira execução

```text
C0.S0 platform/media/device/biometric/external/automation/OT inventory
→ C0.S1 boundary/names
→ C0.S2 authorities
→ C0.S3 primitives/refs
→ C0.S4 architecture/privacy/event/executor/outcome/autonomy boundaries
→ C0.S5 integration contracts
→ C0.S6 RED harness
→ C0.S7 FOUNDATION_FREEZE
→ C1.S1 API skeleton
```

Estado executável: [`evidence/execution-ledger.md`](./evidence/execution-ledger.md).
