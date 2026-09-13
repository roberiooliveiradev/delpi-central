# 12 — Roadmap macro do Minha DELPI Copilot

> **Status:** planejamento canônico  
> **Produto:** aplicação standalone nova  
> **Autoridade de execução:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
> **Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
> **Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
> **Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
> **Próxima etapa:** `C0.S0`

Este roadmap apresenta evolução macro. A ordem atômica/dependências/gates vive somente em `16`.

## Visão geral

```text
C0 — Platform + Architecture + Media/Privacy/Biometric/External/OT Foundation Freeze
C1 — Standalone Application Bootstrap
C2 — Portal Context + Platform Commands
C3 — Intelligence Core + Multimodal/Biometric/Internet/Connector Foundations
C4 — Business + External Reads + DELPI Business Graph
C5 — Governed Business/External Writes + Durable Work Foundation
C6 — Tasks/Cases/Rooms/Inbox/Watch + Meeting/Frontline + External Events/Ecosystem/Learning
C7 — External Proactivity + Advanced Realtime + Autonomy + Simulation + Model Routing + Rollout
```

## C0 — Foundation Freeze

Entregas:

- inventário Portal/Core/Gateway/Infra/MFEs/APIs;
- OpenAPI/auth/entity/event/rooms/notifications;
- media/devices/shared terminals;
- biometric sources/enrollment/storage/liveness;
- production/maintenance/quality/OT boundaries;
- outbound web/egress/search/fetch infrastructure;
- OAuth/callback/secret-store patterns;
- Microsoft 365/Google Workspace/WhatsApp Business/other connector inventory;
- personal vs organizational external-source ownership;
- webhook/subscription/scheduler/reconciliation patterns;
- privacy/retention/compliance owners;
- names/paths/DB ownership;
- shared primitives/refs;
- Clean Architecture/pattern freeze;
- RED/conformance harness;
- `CHAT_RUNTIME_DEPENDENCY=0`;
- `FOUNDATION_FREEZE=PASS`.

## C1 — Standalone Bootstrap

- own API/MFE;
- JWT/Core;
- Module Federation/plugin-ui;
- own manifest/Gateway/Compose;
- full-page + global host;
- responsive/accessibility baseline;
- capability/config foundations only;
- Chat-offline independence.

No Internet/connector runtime feature is implemented merely because callback/config paths exist.

## C2 — Portal Context + Commands

- WorkspaceContext;
- Global Bridge;
- platform capability projection;
- open app/route/entity;
- operational EntityRefs;
- bounded SourceRefs for current external resources when material;
- shared-device baseline;
- iframe baseline;
- security/generalization.

No provider token/permission truth in context.

## C3 — Intelligence + Multimodal/Biometric/Internet/Connector Foundations

- model/provider abstraction;
- own conversation/turn state;
- OpenAPI ingestion/action catalog;
- capability retrieval/planner;
- Expertise/Playbooks/Knowledge;
- multimodal/speech/vision/biometric foundations;
- Internet Research search + safe fetch + SourceRef/Evidence;
- ExternalConnection lifecycle;
- provider-neutral connector capability model;
- least-privilege OAuth/secret boundary implementation as scoped;
- Evidence/provenance;
- unknown/metamorphic/generalization evals.

## C4 — Business + External Reads + Graph

- generic business reads;
- external reads from authorized connections;
- mail/calendar/file/message retrieval capabilities as providers are onboarded;
- source/freshness/evidence normalization;
- DELPI Business Graph;
- internal/external correlation through refs, not copied masters;
- cross-domain + external analysis;
- unknown provider/connector gates.

Example:

```text
item/fornecedor interno
+ authorized Outlook/Gmail correspondence
+ public research
→ Evidence-backed analysis
```

## C5 — Governed Business/External Writes + Durable Foundation

- Decision Gate;
- generic business write executor;
- external draft/send/create/update capabilities;
- `draft != send`;
- provider connection/scope revalidation;
- verified external outcome;
- idempotency/ambiguous-outcome handling;
- WorkflowPlan/checkpoints/waits/resume;
- no duplicate business/external write.

## C6 — Product Work + External Events + Meeting/Frontline + Ecosystem

- Task/Case/Evidence Board;
- Interaction Rooms;
- Inbox;
- Watch OBSERVE/ADVISE;
- provider webhook/subscription/push → EventEnvelope;
- renewal/reconciliation/stale state;
- Meeting Mode/ata viva;
- Frontline Mode/training/process observation;
- Organizational Knowledge/Governed Learning;
- external source → candidate → review/eval/publish;
- Expertise Studio;
- AI-ready app/connector readiness.

## C7 — External Proactivity + Advanced Realtime + Autonomy/Rollout

- autonomy L0–L5, L5 OFF default;
- Watch ACT;
- selected proactive external actions with connection/action allowlists;
- background research within budgets/privacy policy;
- browser automation only as justified sandboxed fallback;
- What-if/Simulation;
- Model Router/Compute Policy;
- advanced realtime/media;
- performance/cost/scaling;
- canary/rollback;
- final Product Complete.

OT actuation remains a separate industrial-safety initiative.

## Dependência entre fases

```text
foundation C0
↓
standalone app C1
↓
portal/context C2
↓
intelligence + external foundations C3
↓
business/external reads C4
↓
governed business/external writes C5
↓
work + events + meeting/frontline + learning C6
↓
selected external proactivity + advanced autonomy C7
```

## Regras anti-refatoração

- egress/OAuth/secret/privacy boundaries precedem provider code;
- planner is provider-neutral;
- SourceRef/EvidenceRef precede external feature-specific models;
- external read/write split precedes messaging automation;
- EventEnvelope precede provider-specific Watch logic;
- ExternalConnection lifecycle precede token-handling feature code;
- personal vs organizational privacy precede Knowledge promotion;
- Chat does not need migration/refactor to progress.

## Releases de produto

```text
Foundation Release                       → C0
Standalone Bootstrap Release             → C1
Contextual Platform Release              → C2
Intelligent Multimodal/Research Release  → C3
Connected Read Copilot Release           → C4
Operational + External Action Release    → C5
Work/Meeting/Frontline/Events Release    → C6
Mature Proactive Connected Copilot       → C7
```

## Primeira execução

```text
C0.S0 platform/media/device/biometric/external/OT inventory
→ C0.S1 boundary/names
→ C0.S2 authorities
→ C0.S3 primitives/refs
→ C0.S4 architecture/privacy/egress/OAuth/secrets
→ C0.S5 integration contracts
→ C0.S6 RED harness
→ C0.S7 FOUNDATION_FREEZE
→ C1.S1 API skeleton
```

Estado executável: [`evidence/execution-ledger.md`](./evidence/execution-ledger.md).
