# Minha DELPI Copilot — Mapa de Componentes, Contratos e Ownership

**Status:** arquitetura canônica de ownership  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## 1. Owners canônicos

| Responsabilidade | Authority / owner | Consumidores | Proibido |
|---|---|---|---|
| identidade | Keycloak + Core integration | Portal, Copilot API, Domain APIs | identity própria/superuser do Copilot |
| permissões efetivas da plataforma | Core API/RBAC | Portal, Copilot API | permission derivada de prompt/context/pack |
| apps/rotas | Core API | Portal, Copilot | catálogo manual app→URL |
| navegação | Portal Router/AppHost | Copilot MFE/commands | URL livre do LLM |
| Copilot UI | `plugins/minha-delpi-copilot` | usuário/Portal | implementar Copilot no Chat MFE |
| Copilot runtime | `minha-delpi-copilot-api` | Copilot MFE/Portal adapters | usar `minha-delpi-ai-api` como runtime |
| Copilot persistence | Copilot API migration chain | Copilot runtime | Chat tables/sessions/agents como authority |
| negócio | Domain APIs/use cases | UI/Copilot | duplicar regra na Copilot API/LLM |
| integrações DELPI/TOTVS | `api-delpi` quando owner | Copilot/other apps | copiar integração para Copilot |
| technical Business Action contract | OpenAPI da Domain API | Copilot Action Catalog/executor | endpoint catalog manual |
| workspace visual | Portal + MFE/iframe adapters | Copilot API | contexto como authorization |
| entity identity | domain owner + Copilot `EntityRef` projection | Context/Graph/Case/Evidence | IDs paralelos |
| relationships | domain owner + Copilot Graph projection | traversal/analysis | replicar datasets masters |
| capability projection | Copilot API derivada de authorities | retrieval/planner/UX | virar source técnica independente |
| expertise | Copilot Expertise Catalog | runtime/admin | permission/tool grant |
| playbook | Copilot Playbook Catalog | planner/workflows | endpoint como authority |
| knowledge visibility | source ACL + Copilot policy adapter | RAG | projeto/pack ampliar ACL |
| multimodal perception | Copilot extractor adapters | Evidence | OCR/VLM como conclusão |
| evidence/provenance | Copilot Evidence contract + source authority | synthesis/Case/audit | claim material sem source quando disponível |
| policy/decision | Copilot Policy/Decision owner + final Domain API auth | writes/workflows | LLM relaxar policy |
| workflow/task/case/watch | Copilot API | MFE/Portal surfaces | engines paralelos |
| room/collaboration | existing owner if reusable; adapter from Copilot | Case/Room UX | membership conceder source ACL |
| inbox semantics | Copilot API | Copilot MFE/Portal | Portal virar workflow engine |
| notification delivery | Core/Portal shared owner quando aplicável | usuário | duplicar canal sem gap |
| model/compute policy | Copilot API infrastructure/policy | runtime | model selection espalhada em features |
| audit/evals | Copilot observability + platform audit where required | admin/security | CoT/secrets/JWT |

## 2. Componentes físicos alvo

| Componente | Responsabilidade |
|---|---|
| Portal Shell | host global, Router, current workspace, Copilot panel host |
| Core API | apps/routes/RBAC/governance/shared notifications |
| Keycloak | SSO/identity |
| Gateway | single public entry/routing |
| `plugins/plugin-ui` | shared UI components/design system |
| `plugins/minha-delpi-copilot` | full-page + panel Copilot UX |
| `minha-delpi-copilot-api` | complete Copilot intelligence/work runtime |
| Copilot OpenAPI importer/index | derive action contracts from Domain APIs |
| Copilot Action Catalog | operational action representation derived from OpenAPI |
| Capability Projection | authorized semantic index |
| Expertise/Playbook Catalogs | dynamic specialization/methodology |
| Knowledge/RAG adapters | authorized knowledge retrieval |
| Multimodal adapters | perception of documents/images/drawings |
| Policy/Decision subsystem | allow/deny/gates/autonomy |
| Durable Workflow Runtime | steps/checkpoints/waits/resume |
| DELPI Business Graph projection | permission-aware references/relations |
| Task/Case/Watch services | persistent Copilot work semantics |
| Domain APIs | actual business data/rules/actions |
| Observability | Copilot traces/metrics/audit/evals |

`minha-delpi-ai-api` and `plugins/minha-delpi-chat` are **not components of this runtime graph**.

## 3. Primitive registry — frozen in C0

Names below are conceptual until C0 confirms final schemas.

### `CorrelationContext`
```text
requestId
conversationId
turnId
workflowId?
taskId?
caseId?
traceId?
```

### `EntityRef`
```json
{
  "entityType": "product",
  "entityId": "90264238",
  "sourceSystem": "api-delpi",
  "label": "90264238"
}
```

### `RelationshipRef`
```text
from EntityRef
relationshipType
to EntityRef
authority/sourceRef
confidence/provenance
```

### `SourceRef`
```text
sourceType
sourceId/provider
entityRef?
action/result/document ref?
timestamp/freshness
```

### `EvidenceRef`
```text
evidenceId
sourceRef
kind
value/ref
location?
observedAt
freshness
confidence?
limitations[]
```

Epistemic classification:
```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

### `OutcomeRef`
Actual capability/action outcome reference with status/result/entity/evidence refs.

### Platform contracts
- `PlatformCommand`
- `PlatformCommandResult`
- `WorkspaceContext`
- `IframeBridgeEnvelope`

Targets are logical IDs/refs, never arbitrary URLs.

### Capability/specialization
- `CapabilityProjection`
- `ExpertisePack`
- `ExpertiseSelection`
- `ExpertiseContext`
- `DomainPlaybook`
- `MultimodalEvidenceRef`

### Decision
- `DecisionGateRequest`
- `DecisionGateDecision`

Levels:
```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

### Durable work
- `WorkflowPlan`
- `WorkflowStep`
- `TaskRef`
- `CaseRef`
- checkpoint/wait state contracts

### Events/Audit
- `EventEnvelope`
- canonical AuditEvent/equivalent

## 4. Producer → consumer graph

```text
Keycloak
→ Portal/Core/Copilot API identity validation

Core /me/apps/routes
→ Platform Capability Projection
→ Copilot planner
→ PlatformCommand
→ Portal validator/Router/MFE/Iframe

Domain OpenAPI
→ Copilot OpenAPI importer/index
→ Copilot Action Catalog
→ authorized Capability Projection
→ retrieval/planner
→ Policy/Decision Gate
→ generic executor
→ Domain API
→ OutcomeRef/EvidenceRef

Portal/MFE/Iframe
→ WorkspaceContext
→ Copilot API understanding/retrieval

Attachments
→ Copilot multimodal adapters
→ EvidenceRef
→ expertise/playbook/analysis

EntityRefs + RelationshipRefs
→ Copilot Business Graph traversal
→ Domain API source fetch
→ EvidenceRef

WorkflowPlan
→ Copilot Durable Runtime
→ Task/Case/Watch
→ Inbox/Room/notification adapters
```

## 5. Independence graph

Must remain true:

```text
Copilot MFE ─X→ minha-delpi-chat source
Copilot API ─X→ minha-delpi-ai-api modules/endpoints as required runtime
Copilot DB  ─X→ Chat tables as authority
```

Shared dependencies must be neutral platform components:

```text
Portal
Core
Keycloak
Gateway
plugin-ui
shared federation config
Domain APIs
approved shared libraries
```

## 6. Anti-duplication rules

Do not create:

- another Core/RBAC model;
- manual app→URL registry;
- manual endpoint/action authority;
- `CaseEntityRef` incompatible with `EntityRef`;
- feature-specific Evidence model;
- confirmation model parallel to Decision Gate;
- Task engine parallel to Workflow runtime;
- Watch-specific event envelope;
- Graph master copies of Domain API objects;
- Chat compatibility layer inside Copilot;
- departmental agent tool registries.

## 7. C0 ownership inventory questions

Before creating a component/schema:

```text
Who owns the source truth today?
Is this platform-shared or Copilot-owned?
Does an official contract already exist?
Would reuse introduce Chat product coupling?
Who produces and consumes it?
Does it need persistence/versioning?
Can the Domain API remain owner while Copilot stores only refs/projections?
Is a new shared package justified by 2+ real consumers?
```

Unknown = `NOT_PROVEN`, not assumption.

## 8. Stabilization order

```text
platform inventory
→ standalone boundaries
→ authorities
→ primitives
→ ports/persistence/integration contracts
→ architecture conformance
→ FOUNDATION_FREEZE
→ standalone bootstrap
→ intelligence/features
```

No feature may redefine a frozen primitive silently.