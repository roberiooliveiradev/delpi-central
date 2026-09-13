# Minha DELPI Copilot — Padrão Normativo de Arquitetura e Design Patterns

**Status:** `CANONICAL_AUTHORITY` para arquitetura de código/patterns  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
**Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)

## 1. Objetivo

Fazer o Cursor classificar o problema e aplicar pattern já definido, em vez de inventar arquitetura por feature/provider/executor.

```text
problem
→ owner/boundary
→ layer
→ canonical pattern
→ Abstraction Gate
→ implement
→ contract/conformance tests
```

## 2. Product boundary primeiro

Copilot code pertence à nova Copilot API/MFE. Platform owners continuam Portal/Core/Keycloak/Gateway/plugin-ui/Domain APIs e infra neutra aprovada.

Chat internals não são shared library.

External provider SDK/API e RPA/computer-use runtime também não viram Domain authority; entram por adapters.

## 3. Architecture style

Obrigatório:

```text
Clean Architecture
+ Ports & Adapters / Hexagonal
+ Pragmatic DDD
+ Event-Driven only for real events
+ State Machines for nontrivial lifecycle
+ Policy/Specification for deterministic decisions
+ Light CQRS only when materially justified
```

Use o menor pattern que preserve ownership, testabilidade, segurança, privacidade, generalização, outcome truth e evolução.

## 4. Dependency rule

```text
Domain
↑
Application
↑
Interfaces / Adapters
↑
Infrastructure

Composition Root wires concrete implementations.
```

Domain/Application não importam Flask/SQLAlchemy/DB driver/HTTP client/LLM SDK/media SDK/OAuth SDK/search SDK/Graph SDK/Google SDK/WhatsApp SDK/RPA SDK/computer-use SDK/event broker/Chat modules/Portal source.

## 5. Backend layers

### Domain

Entities/Aggregates somente com identity/lifecycle real, Value Objects, invariants, pure Policies/Specifications e real Domain Events.

Sem DB/HTTP/provider/credential/framework/RPA/UI mechanics.

### Application

Use Cases/Application Services, Commands/Queries, ports, orchestration, policy invocation, transaction boundaries e lifecycle transitions.

Examples:

```text
ResearchExternalInformation
CreateExternalConnection
ReadExternalResource
SendExternalMessage
HandleProviderEvent
EvaluateOperationalCondition
SelectDecisionPath
PrepareAutomationAction
ExecuteAutomationCapability
VerifyAutomationOutcome
HandleAutomationExecutionResult
EscalateAutomationException
PromoteLearningCandidate
```

Sem provider URL, SDK, token, RPA selector ou concrete UI detail.

### Interfaces

Controllers/routes/DTOs/schema validation/event/webhook/RPA callback boundaries/mappers.

OAuth callback, provider webhook e executor callback são transport boundaries; business/policy logic não vive no controller.

### Infrastructure

- DB repositories;
- Core/Domain HTTP adapters;
- OpenAPI importer/executor;
- LLM/RAG/media/biometric adapters;
- Search/Safe Fetch adapters;
- OAuth/provider/secret/vault adapters;
- Microsoft/Google/WhatsApp/etc. connectors;
- event/webhook/subscription adapters;
- **API executor adapters**;
- **Function/Script executor adapters**;
- **RPA orchestrator/worker adapters**;
- **Computer-use adapters only when justified**;
- outcome-verification adapters;
- notification adapters;
- storage/cache/telemetry.

### Composition Root

Configura concrete adapters/repositories/policies/use cases/controllers. Feature use cases não criam SDK/provider/RPA clients diretamente.

## 6. Frontend architecture

```text
ui
state
data
```

UI apresenta connection state/source provenance/Decision UX e, quando Automation Hub existir, catalog/execution/worker/exception/outcome states.

State local não vira provider/RPA credential store nem workflow engine. Data layer usa Copilot API.

## 7. Pattern Decision Matrix

| Problema | Pattern padrão | Limite |
|---|---|---|
| external dependency | Port + Adapter | boundary real |
| application operation | Use Case/Application Service | one operational intent |
| owned persistent state | Repository | not HTTP/RPA proxy |
| complex lifecycle | State Machine | explicit transitions |
| deterministic rule/readiness | Policy / Specification | structured facts → deterministic result |
| incompatible provider/legacy shape | Adapter + ACL | protect canonical model |
| platform command | Command + Handler | typed generic target |
| reliable state+event | Transactional Outbox | only when required |
| retryable write | Idempotency | no blind retry |
| asynchronous event | Event-Driven | real source/owner/schema |
| event condition | Watch + Policy/Specification | OBSERVE/ADVISE/PREPARE/ACT lifecycle |
| decision path selection | Policy/Strategy justified by real paths | FAST/OPERATIONAL/REASONING |
| transport boundary | DTO + Mapper | no provider DTO leakage |
| concrete wiring | Composition Root DI | simple composition |
| media processing | bounded Pipeline | provenance/budgets |
| biometric provider | Port + Adapter | candidate identity only |
| public web fetch | Safe Fetch Port + Policy | egress boundary |
| OAuth connection | Use Cases + State Machine + Credential Port | provider details in adapter |
| connector capability | semantic capability + Adapter | planner provider-neutral |
| provider event | Adapter → EventEnvelope | authenticity/dedupe/reconciliation |
| automation capability mapping | Registry/Projection backed by contracts | no RPA mechanics in planner |
| automation execution | Command/Use Case + Executor Port | one semantic capability |
| RPA integration | Executor Port + Adapter/ACL | bot is replaceable executor |
| worker/queue lifecycle | State Machine + lease/idempotency | only if RPA infra requires it |
| outcome verification | Verifier Port + Specification | technical success != business success |
| background action | explicit Actor/Service Identity + Policy | event never grants authority |
| external/RPA write | Policy/Decision + Adapter | verify outcome/no blind retry |
| computer-use fallback | sandboxed Adapter | only if API/RPA unsuitable and justified |
| human exception | wait_user/wait_approval + same Workflow | no parallel manual process engine |
| OT actuation | separate industrial safety architecture | never generic LLM executor |

## 8. Use Case Pattern

```text
Controller/Event Handler
→ Use Case
→ Domain/Policy
→ Port
→ Adapter
```

Evitar `CopilotService`, `MultimodalService`, `ConnectorService`, `AutomationService`, `RpaManager` ou `AgentOrchestrator` god objects.

## 9. Ports & Adapters

Ports possíveis apenas quando o boundary real justificar:

```text
CoreApiPort
DomainActionPort
SearchProviderPort
SafeWebFetchPort
ExternalConnectionPort
ExternalCredentialPort
ExternalResourcePort
ExternalActionPort
ExternalSubscriptionPort
SecretStorePort
EventSourcePort
AutomationExecutorPort
AutomationRegistryPort
AutomationWorkerPort
OutcomeVerifierPort
NotificationPort
Media/Vision/Speech/Biometric ports
```

Não criar todos antecipadamente. Cada port passa pelo Abstraction Gate.

Concrete adapters podem incluir:

```text
MicrosoftGraphAdapter
GoogleWorkspaceAdapter
WhatsAppBusinessAdapter
DomainHttpExecutorAdapter
LegacyRpaAdapter
FunctionExecutorAdapter
ComputerUseAdapter
```

## 10. Repository Pattern

Repository somente para state/lifecycle que o Copilot/Hub realmente possui:

- Conversation;
- Expertise/Playbook;
- Workflow/Task/Case/Watch;
- ExternalConnection/Subscription;
- AutomationExecution metadata;
- Automation mapping/catalog quando owned;
- Meeting/Frontline metadata;
- Graph materialization quando provada.

Não criar `GmailRepository`, `OutlookRepository` ou `RpaRepository` apenas para encapsular remote calls.

## 11. Anti-Corruption Layer

Use para Core/domain/provider/RPA/legacy shapes incompatíveis. Normalize resources/capabilities/results para contracts Copilot.

Planner nunca conhece coordinate/selector/package-specific UI details.

## 12. State Machine

Exemplos:

```text
ExternalConnection:
PENDING_AUTH → ACTIVE → EXPIRED|REAUTH_REQUIRED|REVOKED|DISABLED|ERROR

ExternalSubscription:
CREATING → ACTIVE → RENEWING → ACTIVE|EXPIRED|REAUTH_REQUIRED|DISABLED|ERROR

AutomationExecution:
QUEUED → RUNNING → SUCCEEDED|FAILED|AMBIGUOUS|CANCELLED|TIMED_OUT

RPA Worker:
ONLINE ↔ BUSY → DRAINING|OFFLINE
```

Também aplica a Workflow/Decision/Case/Watch/Meeting/Media/Biometric quando lifecycle real exigir.

## 13. Policy / Specification

Policies possíveis:

```text
DecisionGatePolicy
AutonomyPolicy
DecisionPathPolicy
OperationalReadinessPolicy
AnomalyPolicy
RetryPolicy
IdempotencyPolicy
ExecutorSelectionPolicy
OutcomeVerificationPolicy
NotificationEscalationPolicy
RetentionPolicy
MediaCapturePolicy
BiometricIdentityPolicy
ExternalEgressPolicy
ExternalConnectionPolicy
ExternalActionPolicy
ExternalKnowledgePromotionPolicy
ComputePolicy
IndustrialSafetyBoundaryPolicy
```

Policy/Specification é structured deterministic decision, não prompt livre.

## 14. Internet Research Pattern

Search → Safe Fetch → extraction → Source/Evidence → freshness/relevance → synthesis. External content remains untrusted.

## 15. External Connection / OAuth Pattern

Connect use case → authorization adapter → callback validation → lifecycle → SecretStorePort → normalized capabilities. Token never crosses planner/LLM/MFE.

## 16. Semantic Capability Pattern

Planner trabalha com semantic capabilities, por exemplo:

```text
communication.email.send
maintenance.request.create
billing.invoice.issue
production.report.validate
inventory.read
```

Capability não codifica executor.

```text
billing.invoice.issue
→ Domain/API executor today
→ RPA executor tomorrow
→ another authoritative adapter later
```

Planner/workflow permanecem estáveis.

## 17. External Read Pattern

Capability → connection/scope validation → provider adapter → normalized result → Source/Evidence.

## 18. External Write Pattern

Intent → preview/Decision → revalidation → adapter → outcome verification → Outcome/Evidence/Audit.

## 19. Event / Signal Ingestion Pattern

```text
source event/webhook/push/telemetry
→ interface validation
→ source authenticity/trust validation
→ normalize EventEnvelope
→ dedupe/order/correlation
→ Watch/Workflow/Decision use case
```

Event payload never grants permission or ACT authority.

Polling fallback:

```text
scheduler
→ bounded query
→ synthetic normalized event/change
→ same dedupe/correlation path
```

Polling is fallback with explicit freshness/cost/interval semantics.

## 20. Decision Path Pattern

```text
event/user goal
→ DecisionPathPolicy
   ├─ FAST
   ├─ OPERATIONAL
   └─ REASONING
```

### FAST

Deterministic facts/rules/state machine. No LLM when unnecessary.

### OPERATIONAL

Bounded reads + rules + optional classifier/small model.

### REASONING

Graph + Knowledge + Expertise + LLM + structured decision candidate.

Do not create Strategy hierarchy until at least real paths/variation justify it; a simple Policy function may be enough initially.

## 21. Operational Readiness Pattern

```text
authoritative facts
→ Policy/Specification
→ READY | NOT_READY | INCONCLUSIVE
→ Evidence/Reason codes
```

LLM may explain/investigate but does not replace deterministic readiness when criteria exist.

Examples: invoice readiness, report plausibility, stock threshold, SLA breach.

## 22. Automation Capability Registry/Projection Pattern

Registry/projection maps semantic capability to executable contract:

```text
capabilityRef
→ executorRef/version/type
→ input/output schemas
→ pre/postconditions
→ timeout/retry/idempotency
→ owner/environment/status
```

This is not a manual business rule catalog. Capability authority still derives from Domain/OpenAPI/platform/external contracts and approved automation mappings.

## 23. Executor Selection Pattern

Default preference:

```text
API official
→ native supported integration
→ deterministic function/script
→ RPA
→ computer-use
→ human task
```

Selection considers availability, authority, reliability, policy, environment and capability mapping.

Choosing RPA despite a reliable authoritative API requires evidence/exception, not convenience.

## 24. Automation Execution Pattern

```text
intent/event
→ semantic capability
→ Policy/Decision
→ ExecutorSelection
→ AutomationExecution
→ ExecutorPort
→ concrete Adapter
→ technical result
→ OutcomeVerifier
→ OutcomeRef/Evidence/Audit
```

No parallel automation workflow engine; Durable Workflow remains orchestrator.

## 25. RPA Pattern

RPA belongs to Infrastructure/adapter boundary.

```text
AutomationExecutorPort
→ RpaExecutorAdapter
→ RPA orchestrator/worker
```

Requirements when real:

- package/version traceability;
- queue/lease/concurrency;
- worker health/heartbeat;
- environment isolation;
- credential injection through secret owner;
- selector/UI error translation;
- screenshot/artifact retention policy;
- idempotency/ambiguous outcome handling;
- audit/correlation.

Bot never owns business decision.

## 26. Computer-Use Pattern

Advanced fallback only:

- sandbox/session isolation;
- app/domain/network allowlists;
- protected credentials;
- bounded actions;
- same Policy/Decision semantics;
- takeover/stop;
- full audit;
- no arbitrary intranet access.

## 27. Outcome Verification Pattern

```text
technical executor result
→ expected postcondition
→ authoritative verifier/source
→ VERIFIED_SUCCESS | VERIFIED_FAILURE | PENDING | INCONCLUSIVE
```

Examples:

```text
HTTP 200 != invoice persisted
RPA Save click != committed transaction
provider accepted != final delivery if async
```

## 28. Background Identity Pattern

Autonomous/background actions require explicit actor context:

```text
USER_DELEGATED actor
or
SERVICE actor with explicit capability/policy scope
```

Event/worker/device identity never silently becomes permission authority.

## 29. Watch Pattern

```text
OBSERVE → record/detect
ADVISE  → analyze/notify
PREPARE → build candidate action/preview, no side effect
ACT     → execute only under C7 autonomy gate
```

PREPARE and ACT are distinct state transitions/capabilities.

## 30. Human Exception Pattern

```text
Workflow
→ wait_user / wait_approval
→ Inbox/Decision
→ human resolution
→ resume same Workflow
```

No separate “manual process” engine.

## 31. External Knowledge / Operational Learning Pattern

```text
Event + Context + Decision + Action + Outcome
→ Evidence
→ candidate pattern/optimization
→ review/eval
→ versioned publish
```

One successful automation run never changes policy automatically.

## 32. Resilience

Each adapter/executor defines timeout, retry eligibility, backoff, rate/concurrency, circuit breaker where useful, ambiguous outcome handling and degraded state.

Read retry != write retry. RPA timeout after possible click/save is potentially ambiguous, not automatically retryable.

## 33. Result/Error model

Canonical errors may include:

```text
EventSourceInvalid
EventDuplicate
EventStale
DecisionInconclusive
AutomationCapabilityUnavailable
AutomationExecutorUnavailable
AutomationExecutionTimedOut
AutomationExecutionAmbiguous
AutomationExecutionFailed
AutomationOutcomeNotVerified
AutomationPolicyBlocked
AutomationKillSwitchActive
AutomationWorkerUnavailable
ComputerUseBoundaryBlocked
```

Concrete provider/RPA exceptions do not leak directly to UI/LLM.

## 34. DTO + Mapper

SDK/RPA/provider DTOs are not public contracts. Map only application/domain refs/results.

## 35. Dependency Injection

Forbidden:

```text
UseCase creates RPA/Graph/Google client
Planner instantiates executor
UseCase reads worker credential directly
Controller owns retry/decision/business logic
RPA adapter calls planner
```

Concrete creation belongs to composition/infrastructure.

## 36. Bounded Contexts target

```text
Copilot Conversation/Intelligence
Capability & Action Integration
Expertise & Playbooks
Knowledge
Evidence & Provenance
Media & Interaction Sessions
External Information & Connections
Event & Operational Intelligence
Automation & Execution
Work Management
Policy & Decision
Platform Experience
Business Graph
Observability & Evals
```

`Automation & Execution` may remain module inside Copilot API or become neutral platform service only after C0 evidence/ADR. “Hub” does not imply microservice.

## 37. Patterns by component

| Componente | Preferred patterns |
|---|---|
| Internet Research | Use Case + Search Adapter + Safe Fetch + Evidence |
| External Connections | Use Case + State Machine + Repository + Secret Adapter |
| Provider Events | Adapter + EventEnvelope + dedupe/reconciliation |
| Event/Signal Plane | source adapters + EventEnvelope + correlation |
| Decision Intelligence | Policy/Specification + optional reasoning adapter |
| Operational Readiness | deterministic Specification + Evidence |
| Automation Capability | semantic projection/registry + contract versioning |
| Execution Hub | Use Cases + Executor Ports/Adapters + State Machine |
| RPA | Executor Adapter + worker/queue/idempotency |
| Computer Use | sandboxed Executor Adapter |
| Outcome Verification | Verifier Port + authoritative source |
| Watch | State Machine/Policy + same Workflow runtime |
| Human Exception | wait state + Inbox/Decision + resume |
| Workflow/Decision | State Machine + Policy + Idempotency |
| OT | separate safety architecture |

## 38. Abstraction Gate

Antes de criar interface/port/base/factory/strategy/registry/framework/repository/connector engine/event bus/RPA hub/executor registry/worker queue/computer-use adapter, provar:

1. real boundary?
2. real variation/consumer?
3. test double needed?
4. owned lifecycle/state?
5. reduces coupling?
6. equivalent already exists?
7. avoids Chat coupling?
8. shared refs sufficient?
9. persistence really needed?
10. provider/executor concern can stay in adapter?
11. credentials stay protected?
12. read/write and PREPARE/ACT remain distinct?
13. new provider/executor works without planner patch?
14. authoritative API exists, making RPA unnecessary?
15. technical success needs separate business verification?
16. background identity is explicit?
17. automation scope could be handled by existing Workflow/Watch instead of new engine?

“Might be useful later” is insufficient.

## 39. Anti-patterns

- Chat internals as Copilot library;
- god `AutomationService`/`RpaManager`/`AgentOrchestrator`;
- second Workflow engine inside Automation Hub;
- RPA bot as business-rule authority;
- planner with click/selector/coordenada;
- RPA chosen over supported authoritative API without evidence;
- one global unrestricted L5 flag;
- event payload executing write directly;
- worker identity treated as user permission;
- blind retry after ambiguous UI/API write;
- technical execution success treated as business completion;
- PREPARE silently becoming ACT;
- computer-use with unrestricted intranet/session access;
- secrets in prompt/log/MFE/screenshots;
- provider name branching in planner;
- external cache as truth;
- hidden worker/person profiling;
- free-form LLM to industrial machine.

## 40. Testing by layer

### Domain/Application

Pure Policy/Specification, decision-path, autonomy, lifecycle and use-case tests with port fakes.

### Infrastructure

Provider/executor contract tests, RPA worker/queue/package/version, token/credential isolation, timeout/ambiguous outcome, event verification, safe fetch.

### Interfaces

OAuth/webhook/event/executor callback/schema/auth/error tests.

### Frontend

Connection/source/Decision/Automation Admin/execution/outcome/exception UX without credential exposure.

### Standalone

```text
NO_CHAT_IMPORT
NO_CHAT_API_DEP
NO_CHAT_DB_AUTHORITY
CHAT_OFFLINE_INDEPENDENCE
```

Automation scope also requires event trust, duplicate prevention, executor substitution, worker isolation, outcome verification, PREPARE/ACT separation, autonomy scope and kill-switch tests from `20`.

## 41. Migration patterns

Copilot DB/contracts:

```text
EXPAND → compatible readers → writers → optional backfill → CUTOVER → CLEANUP
```

Provider/executor swaps use adapters/versioned mappings. Example RPA→API migration changes capability mapping and adapter, not planner/workflow/domain semantics.

## 42. ADR / Exception Gate

Any material deviation proves why, alternatives, trade-offs, no second authority, privacy/security impact, reliability/outcome semantics and exit/rollback.

## 43. FOUNDATION_FREEZE architecture gates

```text
ARCHITECTURE_STYLE
LAYER_RESPONSIBILITIES
DEPENDENCY_RULES
BOUNDED_CONTEXTS
PATTERN_DECISION_MATRIX
ERROR_MODEL
EVENT_MODEL
STATE_MACHINE_RULES
PERSISTENCE_RULES
FRONTEND_STATE_RULES
RESILIENCE_RULES
TESTING_PATTERN
MIGRATION_PATTERNS
ABSTRACTION_GATE
ARCHITECTURAL_EXCEPTION_PROCESS
SHARED_CODE_GATE
MEDIA_PROVIDER_BOUNDARIES
BIOMETRIC_BOUNDARIES
EXTERNAL_EGRESS_BOUNDARY
OAUTH_CONNECTION_BOUNDARY
PROVIDER_SECRET_BOUNDARY
EXTERNAL_EVENT_BOUNDARY
AUTOMATION_EXECUTION_BOUNDARY
EVENT_SIGNAL_BOUNDARY
BACKGROUND_IDENTITY_BOUNDARY
EXECUTOR_CONTRACT_BOUNDARY
OUTCOME_VERIFICATION_BOUNDARY
AUTONOMY_SCOPE_BOUNDARY
OT_SAFETY_BOUNDARY
CHAT_RUNTIME_DEPENDENCY=0
```

## 44. Regra final

```text
platform/product/privacy/security boundary first
→ factual event/executor inventory
→ proven repo convention
→ Pattern Decision Matrix
→ simplest solution preserving boundaries
→ verify business outcome
→ ADR only for material ambiguity
```

O objetivo é uma arquitetura previsível em que novos providers e executors possam ser adicionados sem refatorar planner, policy, Domain ou UX central.
