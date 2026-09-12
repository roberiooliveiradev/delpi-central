# 15 — Mapa de integração com a Minha DELPI

**Status:** mapa canônico de integração  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Baseline factual:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)

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
- multimodal;
- Evidence/Provenance;
- policy/Decision Gates;
- generic execution;
- Business Graph projection;
- durable work;
- Task/Case/Watch/Inbox semantics;
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
full page
Portal global panel
```

Mesmo API/runtime em ambas.

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
- iframe bridge when needed.

Portal não implementa planner/RAG/actions/policy persistence.

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

## 8. Gateway

Novo paths próprios, conceitualmente:

```text
/apps/minha-delpi-copilot/
/apps/minha-delpi-copilot-api/
```

Dev/prod parity mandatory.

Streaming/SSE/socket tuning only if the chosen transport requires it.

## 9. Infra/Compose

Novos services próprios:

```text
minha-delpi-copilot-api
minha-delpi-copilot
```

No `depends_on` Chat.

Physical shared DB/network allowed only with logical ownership separation.

## 10. plugin-ui / federation

Copilot MFE reuses shared design system/federation.

Do not source-import Portal/Chat components.

Promote a Copilot component to `plugin-ui` only when truly transversal and consumers are proven.

## 11. Domain APIs

Remain business owners.

Copilot expects:

- OpenAPI quality;
- stable entity IDs;
- clear auth;
- idempotency where applicable;
- verified outcomes;
- timestamps/version/freshness when material;
- domain events where domain already supports them.

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

## 16. Multimodal

Copilot implements own adapters/runtime.

Existing Chat document-vision code = reference only.

Output normalizes to shared EvidenceRef.

## 17. Rooms

C0 inventories Portal Comercial Interaction Rooms and any other collaboration owner.

Decision:

```text
REUSE | EXTEND | ADAPTER | CREATE_REQUIRED
```

Target relation:

```text
CaseRef ↔ RoomRef
```

Do not duplicate room message/file storage when owner exists.

## 18. Notifications/Inbox

Copilot owns Inbox/work semantics.

Core/Portal may provide shared notification delivery/presentation via adapter.

```text
Copilot work/decision/watch state
→ notification adapter
→ Core/Portal delivery when appropriate
```

## 19. Events/jobs/workers

C0 inventories existing infrastructure first.

Copilot may reuse transport/worker infrastructure by neutral contract, but owns its own work/watch semantics.

No parallel event bus without proven gap.

## 20. Business Graph

```text
Domain Entity IDs/relationships
→ Copilot EntityRef/RelationshipRef projection
→ permission-aware traversal
→ Domain API source fetch
→ Evidence
```

Source data stays in domain owners.

## 21. Decision/Approval

Copilot owns DecisionGate semantics. Existing approval infrastructure may be adapted when compatible.

Final Domain API authorization remains required.

## 22. Durable Work

Copilot owns Workflow semantics/state.

Existing queues/schedulers/locks/event transport may be reused through adapters after C0 inventory.

## 23. Model/provider

Copilot owns provider ports/adapters and later Compute Policy.

Provider names/config do not leak into domain/application.

## 24. End-to-end integration

```text
Keycloak/Core
→ identity + platform authorization

Portal/MFE/Iframe
→ Workspace/Entity context

Domain OpenAPIs ─┐
Core apps/routes ├→ Copilot Capability View
Knowledge ───────┤
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
→ MFE/Inbox/Room/Watch presentation
→ Audit/Evals
```

## 25. Integration gate

Before a new component:

```text
Who owns this today?
Is it platform-shared or Copilot-owned?
Can an official contract be reused?
Would reuse couple Copilot to Chat product internals?
Would it duplicate Core/domain authority?
Can an Adapter preserve boundaries?
Would next phase force redesign?
```

A component is not created until those questions are answered with evidence.