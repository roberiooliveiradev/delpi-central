# Minha DELPI Copilot — Mapa de Componentes, Contratos e Ownership

**Status:** arquitetura canônica de ownership  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Microsoft Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)  
**Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Owners canônicos

| Responsabilidade | Authority / owner | Proibido |
|---|---|---|
| identidade corporativa | Keycloak + Core integration | biometric/external/worker shadow identity |
| permissões apps/rotas | Core API/RBAC | permission por prompt/context/provider/event/worker |
| negócio DELPI | Domain APIs/use cases | duplicar regra no Copilot/RPA |
| navegação | Portal | URL livre do LLM |
| Copilot UI | `plugins/minha-delpi-copilot` | usar Chat MFE como base |
| Copilot runtime/persistence | `minha-delpi-copilot-api` | Chat API/tables/runtime como authority |
| OpenAPI Business Actions | Domain OpenAPI + Copilot derived catalog | endpoint catalog manual |
| Workspace Context | Portal/MFE/iframe/device adapters | context como authorization |
| Evidence/Source/Outcome | Copilot contracts + source authority | feature-specific evidence schema |
| biometria | Copilot biometric subsystem + Core userRef | biometric match como login/RBAC |
| industrial safety | OT/safety owner | Copilot/LLM/RPA como safety controller |
| Internet Research semantics | Copilot API | browser/web provider como policy authority |
| public search/fetch source truth | source website/provider | Copilot cache como authority |
| egress/safe fetch controls | approved infra/security owner + Copilot policy enforcement | unrestricted HTTP from LLM |
| external connection lifecycle | Copilot API | provider token as conversation state |
| provider authorization/scopes | external provider contract + connection owner | scope treated as Core permission |
| provider credential material | approved secret/vault owner | token in DB plain field/MFE/log/LLM |
| external resources | provider account/service | mailbox/Drive/etc. replicated as Copilot master |
| external connector mapping | provider adapter | provider branch in planner |
| Teams source/resource truth | Microsoft 365/Teams resource owner | Teams transcript/message as automatic corporate truth |
| external source privacy/sharing | connection/source owner + security/privacy policy | personal/restricted source auto-shared |
| external write governance | Copilot Policy/Decision + provider final validation | generated draft auto-sent |
| provider/domain events | source owner + Copilot event adapter | event payload bypassing policy |
| Event/Signal correlation semantics | Copilot Watch/Work runtime | new event authority without source owner |
| Decision Intelligence | Copilot Policy/Application + Domain/source facts | RPA/LLM textual output as sole business authority when deterministic rules exist |
| Automation Capability mapping | Copilot Automation/Capability projection or neutral platform owner if proven in C0 | clicks/selectors as planner contract |
| Automation execution lifecycle | Automation & Execution bounded context/owner decided in C0 | second planner/second workflow engine |
| RPA execution mechanics | RPA adapter/orchestrator/worker owner | RPA bot as business-rule authority |
| function/script execution | approved executor adapter/owner | unversioned arbitrary code execution |
| computer-use execution | bounded/sandboxed executor adapter | unrestricted desktop/network access |
| background actor/service identity | Keycloak/Core/service identity owner + Copilot Policy | worker/device/event identity as permission |
| outcome verification | Domain/provider/source authority + Copilot verifier orchestration | technical success treated as business completion |
| autonomy policy | Copilot Policy/Admin | global unrestricted L5 |
| workflow/task/case/watch | Copilot API | parallel provider/RPA workflow engine |
| room/collaboration | existing owner if reusable | membership granting source ACL |
| notifications | Core/Portal/shared channel owner + Copilot orchestration | notification used as proof of successful business outcome |
| audit/evals | Copilot observability + platform audit | secrets/raw sensitive payload/CoT in logs |
| external Knowledge promotion | Copilot Knowledge governance + source owner | web/email/message/automation run auto-truth |

## 2. Componentes físicos alvo

```text
Portal Shell
Core API
Keycloak
Gateway
plugins/plugin-ui
plugins/minha-delpi-copilot
minha-delpi-copilot-api

Copilot API internal bounded components:
- OpenAPI importer / Action Catalog
- Capability Projection
- Planner / Expertise / Playbooks / Knowledge
- Evidence / Policy / Decision
- Durable Work / Task / Case / Watch
- Event / Operational Intelligence
- Automation Capability Projection
- Automation Execution orchestration
- Outcome Verification
- Notification/Escalation orchestration
- Media / Biometric adapters
- Internet Research / Safe Web Fetch
- External Connection / Provider adapters
- External subscription/event adapters
- Business Graph projection
- Observability/Evals
```

Concrete executors/providers may include Domain HTTP APIs, functions/scripts, Microsoft Graph, Google Workspace, WhatsApp Business, RPA orchestrator/workers and computer-use adapters when approved.

**Automation & Execution Hub does not imply a separate microservice.** C0 decides whether this bounded context stays inside Copilot API or becomes a neutral platform service based on real ownership/consumers/infrastructure.

## 3. Primitive registry — frozen in C0

Canonical/candidate concepts:

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
Biometric refs? when proven
ExternalConnectionRef? / ExternalResourceRef? when needed
AutomationExecutionRef? / ExecutorRef? only when C0 proves transversal need
```

Do not create a second Event/Evidence/Outcome/Workflow model for RPA/automation.

## 4. Producer → consumer graph

```text
Keycloak/Core
→ authenticated user/service identity + platform authorization

Domain OpenAPI
→ Action Catalog
→ Capability Projection
→ Planner/Policy

Public Internet / External Providers / Domain events
→ source adapters
→ SourceRef/EventEnvelope
→ Evidence/Watch/Workflow/Decision

Operational decision
→ DecisionPathPolicy
   FAST | OPERATIONAL | REASONING
→ deterministic Policy and/or AI reasoning
→ candidate semantic capability

Semantic capability
→ Decision/AutonomyPolicy
→ Durable Workflow
→ Automation Capability mapping
→ Executor Port
→ API | Function | RPA | Computer-Use | Human Task
→ technical execution result
→ Outcome Verifier
→ authoritative business Outcome
→ Evidence/Audit/Notification

WorkflowPlan
→ Durable Runtime
→ Task/Case/Watch/Inbox
```

## 5. Connection ownership

```text
USER_DELEGATED
ORG_MANAGED
SHARED_RESOURCE
SERVICE_CONNECTION
```

Provider scope never mutates Core permission model. Personal/restricted sources do not become organization-wide by convenience.

## 6. Semantic capability graph

Planner works with semantic capabilities, for example:

```text
communication.email.search/read/draft/send
calendar.events.read/create/update
files.search/read/create/update
messaging.message.send
billing.invoice.issue
maintenance.request.create
production.report.validate
inventory.read
```

Provider/executor adapters resolve concrete implementation.

## 7. Executor ownership graph

Default preference:

```text
API official
→ native supported integration
→ deterministic function/script
→ RPA
→ computer-use
→ Human Task
```

A capability can migrate:

```text
billing.invoice.issue
RPA v1
→ API v2
```

without planner/workflow redesign.

Planner never receives:

```text
click coordinates
CSS/XPath selector
screen-specific sequence
RPA package internals
```

## 8. Event / Signal graph

```text
source event
→ authenticity/trust validation
→ EventEnvelope
→ dedupe/order/correlation
→ Watch/Workflow/Decision
```

Polling/scheduler is bounded fallback only when no supported event contract exists.

Event source is not permission authority.

## 9. Decision Intelligence graph

```text
Event / User Intent
→ DecisionPathPolicy
   ├─ FAST        deterministic rules/state machine
   ├─ OPERATIONAL bounded reads + rules + optional classifier
   └─ REASONING   Graph/Knowledge/Expertise/LLM
```

Known readiness criteria use Policy/Specification over authoritative facts.

## 10. Automation execution contract

Candidate contract:

```text
capabilityRef
executorRef/version/type
input/output schema
preconditions
postconditions
actor/service identity
idempotency semantics
timeout/retry semantics
environment
owner/status
```

Execution lifecycle:

```text
QUEUED → RUNNING → SUCCEEDED|FAILED|AMBIGUOUS|CANCELLED|TIMED_OUT
```

Technical `SUCCEEDED` does not automatically mean business Outcome `VERIFIED_SUCCESS`.

## 11. RPA / worker ownership

If RPA is real scope after C0:

```text
RPA adapter
→ orchestrator/queue
→ worker/session
→ legacy UI
```

RPA infrastructure owns worker/session/package mechanics; Copilot owns semantic orchestration only when its bounded context is owner of execution request/correlation.

Requirements include worker health, lease/concurrency, environment/package version, protected credentials, session isolation, artifact retention and idempotency.

## 12. Outcome ownership

```text
technical result
→ OutcomeVerifier
→ authoritative Domain/provider/source
→ VERIFIED_SUCCESS | VERIFIED_FAILURE | PENDING | INCONCLUSIVE
```

Notification happens from truthful outcome state; notification itself never becomes evidence that the operation succeeded.

## 13. Autonomy ownership

Autonomy is capability/context/risk scoped:

```text
capability + actor/service + context + risk + limits + environment + policy
```

```text
L5_DEFAULT = OFF
GLOBAL_UNRESTRICTED_L5 = FORBIDDEN
```

C6 Watch supports `OBSERVE|ADVISE|PREPARE`; `ACT` is C7 only.

## 14. External/Teams/Knowledge graphs

Internet/connector/Teams flows preserve SourceRef/Evidence/freshness/source ACL. Restricted source never auto-promotes to shared Knowledge.

External event adapters normalize into the same EventEnvelope used by operational events.

## 15. Independence graph

Must remain true:

```text
Copilot MFE ─X→ Chat source
Copilot API ─X→ Chat runtime/API/tables
Automation Hub ─X→ second Copilot planner
RPA bot ─X→ business authority
Executor ─X→ Core permission authority
```

Shared dependencies must be platform-neutral.

## 16. Anti-duplication rules

Do not create:

- second Core/RBAC/user model;
- manual app URL registry;
- manual business endpoint authority;
- provider/executor-specific planner router;
- second Evidence/Decision/Event model;
- external source master copies;
- second Workflow engine inside Automation Hub;
- provider/RPA credential store inside conversation state;
- `FrontlineContext` parallel to WorkspaceContext;
- RPA UI mechanics in planner/domain/application;
- global autonomy flag as single authority;
- machine state/safety authority inside Copilot.

## 17. C0 ownership questions

Before creating component/schema/service:

```text
Who owns source truth?
Who owns business rule?
Who owns event authenticity?
Is this Copilot-owned, neutral platform-shared, provider/domain/RPA-owned?
Does a canonical contract already exist?
Can existing refs represent it?
Does persistence need content or only refs/metadata?
Who owns credential/key material?
Who is the explicit background actor/service identity?
Is this read, prepare or material write?
Is an authoritative API available before choosing RPA?
Can executor swap without planner patch?
How are retries/idempotency/ambiguous outcomes handled?
What source verifies the business postcondition?
Could duplicate events produce duplicate effects?
Could PREPARE silently become ACT?
Is autonomy scoped by capability/context/risk?
Could computer-use reach outside its allowlist?
Could any path bypass OT safety?
```

Unknown = `NOT_PROVEN`.

## 18. Stabilization order

```text
platform/media/device/biometric/external/automation/OT inventory
→ standalone boundaries
→ authorities
→ primitives
→ event/executor/background-identity/outcome/autonomy contracts
→ architecture conformance
→ FOUNDATION_FREEZE
→ standalone bootstrap
→ intelligence + Event/Decision foundations
→ read-only operational intelligence
→ governed executor foundation
→ Automation Hub + PREPARE
→ selected autonomous ACT
```

No feature/provider/executor may silently redefine frozen authorities/primitives.
