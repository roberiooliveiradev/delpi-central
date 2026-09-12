# 15 — Mapa de integração com a Minha DELPI

**Status:** mapa canônico de integração  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Baseline factual:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Princípio

O Copilot é **novo produto**, mas integra as authorities atuais da plataforma.

```text
REUSE PLATFORM CONTRACT
→ ADAPT AT BOUNDARY
→ EXTEND PLATFORM CONTRACT if justified
→ CREATE COPILOT-OWNED COMPONENT when responsibility belongs to Copilot
```

Não aplicar `REUSE` a runtime interno do Minha DELPI Chat.

## 2. Copilot API

Novo owner: `minha-delpi-copilot-api`.

Responsável por:

- conversations/turns;
- understanding;
- OpenAPI ingestion/Action Catalog;
- capability retrieval;
- planner;
- Expertise/Playbooks;
- Knowledge/RAG;
- multimodal/media orchestration;
- speech/vision adapters;
- Evidence/Provenance;
- policy/Decision Gates;
- generic execution;
- Business Graph projection;
- durable work;
- Task/Case/Watch/Inbox semantics;
- Meeting session/artifact semantics;
- Frontline assistance semantics;
- model/provider abstraction;
- audit/evals/admin.

Não depende de `minha-delpi-ai-api`.

## 3. Copilot MFE

Novo owner: `plugins/minha-delpi-copilot`.

Reutiliza:

- React/Vite/Module Federation;
- `plugins/vite/federation.shared.ts`;
- `@delpi/plugin-ui`;
- Portal `getAccessToken` host contract.

Surfaces:

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
```

Mesmo API/runtime em todas.

## 4. Minha DELPI Chat

`minha-delpi-ai-api` e `plugins/minha-delpi-chat` são **sistemas vizinhos**.

Integração runtime:

```text
NONE required
```

Permitido apenas:

- leitura de código em C0 como benchmark interno;
- shared neutral platform library já existente;
- future extracted neutral package com 2+ consumers e owner próprio.

## 5. Portal Shell

Reutilizar:

- Router;
- AuthContext/Keycloak lifecycle;
- AppHost federated mode;
- AppLauncher/Core-driven apps;
- shared layout/theme;
- host token contract.

Adicionar/evoluir genericamente:

- global Copilot host/panel;
- Workspace Context Bridge;
- PlatformCommand execution;
- deep-link/entity resolver;
- iframe bridge when needed;
- host/device capability metadata bounded quando necessário.

Portal não implementa planner/RAG/actions/media intelligence/policy persistence.

## 6. Core API

Authority de:

- current user/platform context;
- apps/routes;
- permissions/RBAC;
- manifest registration/versioning;
- shared notifications/audit/presence when applicable.

Copilot API consumes official contracts; no local RBAC clone.

## 7. Keycloak

Identity/SSO owner.

```text
Portal → token
Copilot MFE → getAccessToken
Copilot API → validate JWT
Core/Domain APIs → authorization context/final rules
```

Shared device não muda essa regra: `device identity != user identity`.

## 8. Gateway

Novos paths próprios, conceitualmente:

```text
/apps/minha-delpi-copilot/
/apps/minha-delpi-copilot-api/
```

Dev/prod parity mandatory.

Streaming/SSE/WebSocket/WebRTC-related tuning only if the chosen transport requires it and C0/C3 evidence proves need.

## 9. Infra/Compose

Novos services próprios:

```text
minha-delpi-copilot-api
minha-delpi-copilot
```

No `depends_on` Chat.

Physical shared DB/network allowed only with logical ownership separation.

Media/object storage and realtime infra are reused/created only after C0 inventory.

## 10. plugin-ui / federation

Copilot MFE reuses shared design system/federation.

Do not source-import Portal/Chat components.

Promote a Copilot component to `plugin-ui` only when truly transversal and consumers are proven.

Frontline may require large-touch/accessibility components; promotion remains subject to the same shared-component gate.

## 11. Domain APIs

Remain business owners.

Copilot expects, where relevant:

- OpenAPI quality;
- stable entity IDs;
- clear auth;
- idempotency;
- verified outcomes;
- timestamps/version/freshness;
- domain events;
- production/maintenance/quality context sources.

No special “AI endpoint” if normal use case already exists.

## 12. api-delpi

`api-delpi` remains owner of exposed DELPI/TOTVS integrations.

Copilot calls it through authorized contracts. No TOTVS logic duplication inside Copilot.

## 13. MFEs

AI-ready integration can expose:

- WorkspaceContext;
- EntityRefs;
- deep links;
- visual commands;
- contextual Copilot entry;
- result/source presentation.

Business logic/RBAC stay server-side.

Industrial context should still use canonical EntityRefs rather than bespoke Copilot-only IDs.

## 14. Iframes

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

Portal/IframeBridge handles context/visual experience. Business Actions use APIs.

## 15. Knowledge

Copilot has own Knowledge runtime/index but source visibility remains with source ACL/owners.

Classes:

```text
Reference
Operational
Decision
Experience
Semantic
```

Meeting/process/frontline observations create candidates only; publishing remains governed.

## 16. Multimodal/media

Copilot implements own adapters/runtime.

Existing Chat document-vision code = reference only.

Target integrations, only as proven/needed:

```text
native document extraction
OCR/Vision
Speech-to-Text
Text-to-Speech
camera/image/video ingest
screen-share ingest
media storage
realtime transport
```

Output normalizes to EvidenceRef and optional MediaRef if C0 freezes that primitive.

Raw-media persistence is not default.

## 17. Meeting

Meeting Mode belongs to the Copilot product:

```text
Copilot MFE Meeting surface
→ Copilot API meeting/media use cases
→ authorized Core/Domain/Knowledge reads
→ Evidence/Decision candidate actions
→ Task/Case/Room/Workflow
```

No domain needs a “meeting API” merely for Copilot to query it.

Meeting transcript, summary, confirmed decision and executed action remain distinct.

## 18. Frontline

Frontline integration target:

```text
user
+ device/workstation
+ WorkspaceContext(EntityRefs)
+ voice/camera when allowed
→ Copilot
→ Domain APIs/Knowledge/Graph
→ Evidence/guidance
→ governed escalation/action
```

Relevant external owners can include production, maintenance, quality, procedures/training and device/platform infrastructure.

No `FrontlineContext` or frontline-specific action executor by default.

## 19. Shared devices

For tablet/kiosk/production terminal/meeting room device:

```text
user identity
≠ device identity
≠ operational context
```

Integration must support session switch/logout/cleanup and prevent previous-user state leakage.

Device metadata may describe capabilities but never grant business authorization.

## 20. Rooms

C0 inventories Portal Comercial Interaction Rooms and any other collaboration owner.

Decision:

```text
REUSE | EXTEND | ADAPTER | CREATE_REQUIRED
```

Target relation:

```text
CaseRef ↔ RoomRef
MeetingArtifactRef ↔ Case/Room when useful
```

Do not duplicate room message/file storage when owner exists.

## 21. Notifications/Inbox

Copilot owns Inbox/work semantics.

Core/Portal may provide shared notification delivery/presentation via adapter.

```text
Copilot work/decision/watch/meeting state
→ notification adapter
→ Core/Portal delivery when appropriate
```

## 22. Events/jobs/workers

C0 inventories existing infrastructure first.

Copilot may reuse transport/worker infrastructure by neutral contract, but owns its work/watch/media-job semantics.

Long media processing may use async jobs/workflows; do not create event bus/worker stack without proven gap.

## 23. Business Graph

```text
Domain Entity IDs/relationships
→ Copilot EntityRef/RelationshipRef projection
→ permission-aware traversal
→ Domain API source fetch
→ Evidence
```

Source data stays in domain owners.

Media/Meeting/Frontline references connect through canonical EntityRefs/Evidence rather than copying domain data.

## 24. Decision/Approval

Copilot owns DecisionGate semantics. Existing approval infrastructure may be adapted when compatible.

Final Domain API authorization remains required.

A meeting statement, voice command or visual finding is only input/candidate; it cannot bypass the Decision Gate.

## 25. Durable Work

Copilot owns Workflow semantics/state.

Existing queues/schedulers/locks/event transport may be reused through adapters after C0 inventory.

Meeting/Frontline use the same runtime for action follow-up.

## 26. Model/provider

Copilot owns provider ports/adapters and later Compute Policy.

Provider names/config do not leak into domain/application.

Media providers are subject to the same data policy and observability rules.

## 27. Privacy/consent/retention

C0 must identify real governance owners/contracts.

Copilot enforces policy for:

```text
transient capture
transcript
raw audio
raw video
screen capture
derived Evidence
meeting artifacts
frontline records
```

Do not assume a single retention period or that capture implies persistence.

## 28. Industrial/OT integration

Default integration is **read/observe**, when an approved owner contract exists:

```text
OT/domain telemetry
→ approved read adapter
→ EntityRef/Evidence
→ Copilot analysis/recommendation
```

Default prohibited:

```text
free-form LLM
→ generic action executor
→ PLC/CNC/robot/machine
```

Future actuation requires separate industrial safety architecture with deterministic command schema, allowlist, machine-state/preconditions, industrial owner, independent interlocks, authorization, test/simulation, fail-safe and audit.

Autonomy L5 does not grant OT permission.

## 29. Quality/computer vision

Visual finding integrates as Evidence/Hypothesis.

Official inspection/quality owner remains authority unless an automated inspection capability has been separately validated for that decision.

## 30. End-to-end integration

```text
Keycloak/Core
→ identity + platform authorization

Portal/MFE/Device/Iframe
→ Workspace/Entity context + modality capabilities

Domain OpenAPIs ─┐
Core apps/routes ├→ Copilot Capability View
Knowledge ───────┤
Media Evidence ──┤
Internal tools ──┘

Copilot goals/context
→ Expertise/Playbooks
→ Knowledge/Multimodal Evidence
→ Planner
→ Policy/Decision
→ Platform or Business Adapter
→ Portal / Domain API
→ Outcome/Evidence
→ Work state when durable
→ Global/Workspace/Meeting/Frontline presentation
→ Audit/Evals
```

## 31. Integration gate

Before a new component:

```text
Who owns this today?
Is it platform-shared, domain/industrial-owned or Copilot-owned?
Can an official contract be reused?
Would reuse couple Copilot to Chat internals?
Would it duplicate Core/domain/safety authority?
Can an Adapter preserve boundaries?
Can WorkspaceContext/EntityRef/EvidenceRef represent it?
Does media need persistence or only transient processing?
Who owns consent/retention?
Is the device shared?
Is this a Business Action or physical machine actuation?
Would next phase force redesign?
```

A component is not created until those questions are answered with evidence.