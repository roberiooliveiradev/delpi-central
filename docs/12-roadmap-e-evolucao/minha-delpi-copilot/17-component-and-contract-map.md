# Minha DELPI Copilot — Mapa de Componentes, Contratos e Ownership

**Status:** arquitetura canônica de ownership  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

## 1. Owners canônicos

| Responsabilidade | Authority / owner | Proibido |
|---|---|---|
| identidade corporativa | Keycloak + Core integration | biometric/external shadow identity |
| permissões apps/rotas | Core API/RBAC | permission por prompt/context/provider scope |
| negócio DELPI | Domain APIs/use cases | duplicar regra no Copilot |
| navegação | Portal | URL livre do LLM |
| Copilot UI | `plugins/minha-delpi-copilot` | usar Chat MFE como base |
| Copilot runtime/persistence | `minha-delpi-copilot-api` | Chat API/tables/runtime como authority |
| OpenAPI Business Actions | Domain OpenAPI + Copilot derived catalog | endpoint catalog manual |
| Workspace Context | Portal/MFE/iframe/device adapters | context como authorization |
| Evidence/Source/Outcome | Copilot contracts + source authority | feature-specific evidence schema |
| biometria | Copilot biometric subsystem + Core userRef | biometric match como login/RBAC |
| industrial safety | OT/safety owner | Copilot/LLM como safety controller |
| Internet Research semantics | Copilot API | browser/web provider como policy authority |
| public search/fetch source truth | source website/provider | Copilot cache como authority |
| egress/safe fetch controls | approved infra/security owner + Copilot policy enforcement | unrestricted HTTP from LLM |
| external connection lifecycle | Copilot API | provider token as conversation state |
| provider authorization/scopes | external provider contract + connection owner | scope treated as Core permission |
| provider credential material | approved secret/vault owner | token in DB plain field/MFE/log/LLM |
| external resources | provider account/service | mailbox/Drive/etc. replicated as Copilot master |
| external connector mapping | provider adapter | provider branch in planner |
| external source privacy/sharing | connection owner + security/privacy policy | personal source auto-shared |
| external write governance | Copilot Policy/Decision + provider final validation | generated draft auto-sent |
| provider events | provider + Copilot event adapter | webhook payload bypassing policy |
| external Knowledge promotion | Copilot Knowledge governance + source owner | web/email/message auto-truth |
| workflow/task/case/watch | Copilot API | parallel provider workflow engine |
| room/collaboration | existing owner if reusable | membership granting source ACL |
| notifications | Core/Portal shared owner when applicable | duplicate channel without gap |
| audit/evals | Copilot observability + platform audit | secrets/raw sensitive payload/CoT in logs |

## 2. Componentes físicos alvo

```text
Portal Shell
Core API
Keycloak
Gateway
plugins/plugin-ui
plugins/minha-delpi-copilot
minha-delpi-copilot-api

Copilot API internal components:
- OpenAPI importer / Action Catalog
- Capability Projection
- Planner / Expertise / Playbooks / Knowledge
- Evidence / Policy / Decision
- Durable Work / Task / Case / Watch
- Media / Biometric adapters
- Internet Research module
- Safe Web Fetch adapter
- External Connection module
- SecretStore adapter
- Provider adapters
- External subscription/event adapters
- Business Graph projection
- Observability/Evals
```

Concrete provider adapters may include Microsoft Graph, Google Workspace and WhatsApp Business when approved. They are not separate Copilot runtimes.

## 3. Primitive registry — frozen in C0

Already canonical/candidate concepts:

```text
CorrelationContext
EntityRef
RelationshipRef
SourceRef
EvidenceRef
OutcomeRef
PlatformCommand / PlatformCommandResult
WorkspaceContext
CapabilityProjection
ExpertisePack / Selection / Context
DomainPlaybook
DecisionGateRequest / Decision
WorkflowPlan / WorkflowStep
TaskRef / CaseRef
EventEnvelope / AuditEvent
MediaRef? when proven
BiometricEnrollmentRef? / BiometricIdentityCandidate? / PersonObservationRef? when proven
ExternalConnectionRef? / ExternalResourceRef? when SourceRef alone is insufficient
```

### ExternalConnectionRef candidate

```text
connectionId
ownerType
ownerRef
providerKey
status
scope summary bounded
policyRef
```

Nunca contém token/secret.

### External SourceRef usage

```text
sourceType
providerRef
resourceRef
connectionRef? opaque
observedAt/freshness/version?
```

## 4. Producer → consumer graph

```text
Keycloak/Core
→ authenticated user + platform authorization

Domain OpenAPI
→ Copilot Action Catalog
→ Capability Projection
→ Planner/Policy
→ Domain API
→ Outcome/Evidence

Public Internet
→ Search Adapter
→ Safe Web Fetch
→ SourceRef/Evidence
→ Synthesis/Knowledge candidate

External Provider OAuth/API
→ ExternalConnection
→ protected secretRef
→ Provider Adapter
→ normalized connector capabilities
→ Planner/Policy
→ read/write outcome
→ SourceRef/Evidence/Outcome

Provider webhook/subscription
→ provider event adapter
→ EventEnvelope
→ dedupe/reconciliation
→ Watch/Inbox/Workflow

Portal/MFE/Device
→ WorkspaceContext
→ Copilot

Media/Biometric
→ candidate identity/Evidence
→ Copilot context

WorkflowPlan
→ Durable Runtime
→ Task/Case/Watch
→ Inbox/Room/notifications
```

## 5. Connection ownership

Canonical semantic classes:

```text
USER_DELEGATED
ORG_MANAGED
SHARED_RESOURCE
SERVICE_CONNECTION
```

Rules:

- owner/scope explicit;
- one user connection does not become organization-wide;
- shared/org connection still requires Copilot policy/RBAC;
- connection revoke/expiry immediately affects capability availability;
- provider scope never mutates Core permission model.

## 6. Provider-neutral capability graph

```text
communication.email.search/read/draft/send
calendar.events.read/create/update
files.search/read/create/update
messaging.conversations.read
messaging.message.send
```

Planner works with semantic capability; provider adapter resolves concrete API.

## 7. Internet research graph

```text
research goal
→ SearchProviderPort
→ candidates
→ SafeWebFetchPort
→ extraction
→ SourceRef/EvidenceRef
→ freshness/authority classification
→ grounded synthesis
```

No arbitrary LLM URL → unrestricted HTTP path.

## 8. External event graph

```text
provider event
→ authenticity validation
→ normalize EventEnvelope
→ dedupe/order handling
→ Watch/Workflow/Inbox
→ permission/connection revalidation
```

Renewal/reconciliation lifecycle is separate from event semantics.

## 9. External learning graph

```text
web/email/message/file Evidence
→ transient use OR candidate
→ privacy/freshness/licensing check
→ owner/review/eval
→ versioned Knowledge publish
```

Personal source never auto-promotes to shared organizational Knowledge.

## 10. Independence graph

Must remain true:

```text
Copilot MFE ─X→ Chat source
Copilot API ─X→ Chat runtime/API/tables
Copilot Provider Adapter ─X→ Chat tool runtime
Copilot External Connection ─X→ Chat credential storage
```

Shared dependencies must be platform-neutral.

## 11. Anti-duplication rules

Do not create:

- second Core/RBAC/user model;
- manual app URL registry;
- manual business endpoint authority;
- provider-specific planner router;
- Gmail/Outlook/WhatsApp-specific domain models when semantic contracts suffice;
- second Evidence/Decision/Event model;
- external source master copies;
- separate connector workflow engine;
- provider token store inside conversation state;
- `FrontlineContext` parallel to WorkspaceContext;
- machine state authority inside Copilot.

## 12. C0 ownership questions

Before creating component/schema:

```text
Who owns source truth?
Is this Copilot-owned, platform-shared, provider-owned or domain-owned?
Does a canonical contract already exist?
Can SourceRef/EntityRef/EvidenceRef represent it?
Does persistence need content or only refs/metadata?
Who owns secret/key material?
Is connection personal/shared/org/service?
Which scopes are truly required?
Is this read or write?
Can new provider work by adapter without planner patch?
How are webhook renewal/reconciliation handled?
Could personal data leak into org knowledge/cache?
Does external content remain untrusted?
```

Unknown = `NOT_PROVEN`.

## 13. Stabilization order

```text
platform/media/device/biometric/external/OT inventory
→ standalone boundaries
→ authorities
→ primitives
→ egress/OAuth/secret/provider/privacy contracts
→ architecture conformance
→ FOUNDATION_FREEZE
→ standalone bootstrap
→ intelligence + Internet/connector foundations
→ external reads
→ governed external writes
→ external events/learning
→ advanced proactivity
```

No feature/provider may redefine frozen primitives silently.
