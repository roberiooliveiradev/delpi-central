# Minha DELPI Copilot — Padrão Normativo de Arquitetura e Design Patterns

**Status:** `CANONICAL_AUTHORITY` para arquitetura de código/patterns  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Objetivo

Fazer o Cursor classificar o problema e aplicar um padrão já definido, em vez de inventar arquitetura por feature e refatorar depois.

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

Patterns nunca podem violar o boundary standalone.

```text
Copilot code belongs to:
- minha-delpi-copilot-api
- plugins/minha-delpi-copilot

Platform shared owners:
- Portal
- Core API
- Keycloak
- Gateway
- plugin-ui
- federation shared config
- Domain APIs
- approved neutral shared packages/infrastructure
```

`minha-delpi-ai-api` e `plugins/minha-delpi-chat` **não são shared libraries**.

Copiar/importar internals do Chat não é reuse; é product coupling e deve falhar.

## 3. Architecture style

Obrigatório:

```text
Clean Architecture
+
Ports & Adapters / Hexagonal
+
Pragmatic DDD
+
Event-Driven only for real events
+
State Machines for nontrivial lifecycle
+
Light CQRS only when read/write asymmetry is material
```

Princípio:

> use o menor pattern que preserve ownership, testabilidade, segurança, privacidade, generalização e evolução.

Sem DDD cerimonial, CQRS total, Event Sourcing, Saga/Factory/Strategy “por moda”.

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

Domain/Application não importam:

- Flask;
- SQLAlchemy;
- PostgreSQL driver;
- HTTP client concreto;
- LLM/provider SDK concreto;
- speech/vision/media SDK concreto;
- WebRTC/browser concrete transport;
- vector DB concreto;
- event broker concreto;
- Chat modules;
- Portal React source.

## 5. Backend layers

### Domain

Pode conter:

- Entity/Aggregate quando há identity/lifecycle próprio;
- Value Objects;
- invariants;
- pure Domain Policies;
- Specification when genuinely combinable;
- Domain Events as domain facts.

Não acessa DB/HTTP/LLM/media SDK/env/framework.

### Application

- Use Cases/Application Services;
- orchestration;
- ports;
- Commands/Queries;
- state transition use cases;
- policy invocation;
- transaction boundary abstractions;
- media/session orchestration only through ports;
- Meeting/Frontline use cases without provider details.

Sem SQL, URLs, provider names or transport concerns.

### Interfaces

- Flask controllers/routes;
- request/response DTOs;
- event/stream/media transport boundaries;
- schema validation;
- transport mappers.

### Infrastructure

- SQLAlchemy/PostgreSQL adapters;
- Core/Domain HTTP adapters;
- OpenAPI importer/executor;
- LLM/embedding adapters;
- RAG/vector adapters;
- OCR/Vision adapters;
- STT/TTS adapters;
- realtime media transport adapters;
- media/file/object storage adapters;
- device-context adapters;
- event broker/outbox;
- telemetry/cache/materializers.

### Composition Root

Normal place for:

```text
config
→ create adapters/repositories
→ create policies/use cases
→ register controllers/handlers
```

## 6. Frontend architecture

Base:

```text
ui
state
data
```

Copilot MFE may organize feature folders inside those responsibilities.

### UI
Rendering/accessibility/user events/presentation/media controls only.

### State
Local/conversation/workspace/media-session UI state. No durable business authority.

### Data
Typed Copilot API clients, adapters, cache/query integration, contracts.

State ownership:

```text
Server State          → query/cache layer
Workspace State       → Portal/Copilot context adapter
Conversation UI State → MFE + server refs
Media UI State        → MFE/browser session state; durable refs in API if needed
Local UI State        → component/hook
Durable Work State    → Copilot API
```

Browser camera/mic permission state is UI/platform state, not authorization truth for business actions.

## 7. Shared-code gate

Before extracting/reusing code across products:

```text
1. Is the contract product-neutral?
2. Are there 2+ real consumers?
3. Is there a neutral owner/location?
4. Can it version/test independently?
5. Does reuse avoid importing Chat product internals?
```

If not, implement inside Copilot.

Do not transform Chat into a library.

## 8. Pattern Decision Matrix

| Problema | Pattern padrão | Limite |
|---|---|---|
| external dependency | Port + Adapter | default at external boundary |
| application operation | Use Case / Application Service | one operational intent |
| owned persistent aggregate/state | Repository | not for simple HTTP proxy |
| complex lifecycle | State Machine | explicit transitions/invariants |
| deterministic decision rules | Policy | structured input/output |
| combinable reusable predicates | Specification | only when composition helps |
| real interchangeable algorithms | Strategy | only with actual variation |
| incompatible external/legacy shape | Adapter + Anti-Corruption Layer | protect canonical model |
| gradual replacement of a real legacy integration | Strangler Fig | temporary + exit criteria |
| visual/platform command | Command + Handler | generic by command type |
| state + event atomicity | Transactional Outbox | only when required |
| retry/replayable write | Idempotency | prefer domain-native support |
| asynchronous reaction | Event-Driven | real event owner/schema required |
| distributed transaction with compensation | Saga | real writes + real compensation |
| unstable external integration | Timeout/Retry/Circuit Breaker | writes never blind-retry |
| HTTP/event boundary | DTO + Mapper | no ORM contract leakage |
| concrete wiring | Composition Root DI | simple composition |
| config-dependent construction | Factory | only when construction varies |
| complex invariant-heavy creation | Builder/Factory Method | simple constructor first |
| materially different read/write models | light CQRS | no default duplication |
| speech/vision/provider integration | Port + Adapter | provider SDK stays infrastructure |
| media ingestion | Pipeline + bounded stages | no unbounded in-request processing |
| large/long media | Async Job/Workflow when required | avoid blocking synchronous request |
| realtime media | Session + bounded transport adapter | explicit limits/backpressure |
| meeting lifecycle | Use Cases + State Machine if persisted | no second backend/runtime |
| frontline lifecycle | Use Cases + State Machine if persisted | same Copilot runtime |
| shared-device context | Adapter + bounded session contract | device != user identity |
| media retention/consent | Policy + lifecycle metadata | not free-form prompt |
| industrial telemetry | Read Adapter + Entity/Evidence mapping | source remains OT/domain owner |
| machine actuation | separate industrial safety architecture | never generic LLM executor by default |

## 9. Use Case Pattern

```text
Controller/Event Handler
→ Use Case
→ Domain/Policy
→ Port
→ Adapter
```

Examples:

- ResolveWorkspaceContext;
- ImportOpenApiProvider;
- RetrieveCapabilities;
- TraverseBusinessGraph;
- EvaluateDecisionGate;
- ExecuteBusinessAction;
- ResumeWorkflow;
- CreateCopilotCase;
- CreateWatch;
- StartMeetingSession;
- StopMeetingSession;
- CreateMeetingArtifact;
- StartFrontlineSession;
- IngestMedia;
- CreateKnowledgeCandidate.

Avoid one monolithic `CopilotService` or `MultimodalService` god object.

## 10. Ports & Adapters

Especially for:

```text
Core API
Domain APIs
OpenAPI
LLM/providers
Knowledge/vector store
Database
Event transport
Notifications
Storage
OCR/Vision
Speech-to-Text
Text-to-Speech
Realtime media transport
Device context
Business Graph source adapters
Industrial telemetry/read sources
```

Potential media ports (`SpeechToTextPort`, `MediaIngestPort`, etc.) are **candidates**, not mandatory boilerplate. Each must pass Abstraction Gate.

## 11. Repository Pattern

Use only for Copilot-owned lifecycle/persistent authority, e.g. when proven:

- Conversation;
- Expertise/Playbook catalogs;
- Workflow;
- Task/Case;
- Watch;
- Meeting session/artifact metadata if durable;
- Frontline session metadata if durable;
- Graph relationship materialization.

Wrong:

```text
PurchaseOrderRepository that merely calls purchase API
RawVideoRepository created only because video exists
```

Correct:

```text
DomainApiAdapter / generic Business Action executor
MediaStoragePort only when durable media storage is actually required
```

## 12. Adapter / Anti-Corruption Layer

Use for:

- Core contract → Copilot canonical context;
- MFE/Portal host contract;
- iframe messages;
- Domain API/provider variations;
- media/speech/vision providers;
- device/workstation context;
- existing room/notification infrastructure;
- industrial telemetry sources;
- any actual legacy system that exposes incompatible shape.

**Not used to migrate the Minha DELPI Chat into Copilot.** Chat is separate product, not a legacy implementation being strangled by this roadmap.

## 13. State Machine

Required for lifecycle with transition rules/waits/expiry/reopen.

Examples:

```text
Workflow: PLANNED → RUNNING → WAITING_* → RUNNING → terminal
Decision: REQUESTED → PENDING → APPROVED|REJECTED|EXPIRED|INVALIDATED
Case: OPEN → INVESTIGATING/WAITING/ACTIONING → RESOLVED/CLOSED/REOPENED
Expertise content: DRAFT → REVIEW → TESTING → PUBLISHED → DEPRECATED
Watch: ACTIVE → TRIGGERED/COOLDOWN → ACTIVE | EXPIRED | DISABLED
Meeting: DRAFT → ACTIVE → ENDING → COMPLETED|FAILED|CANCELLED when persistence justified
MediaSession: CREATED → CAPTURING → PROCESSING → STOPPED/terminal when lifecycle justified
FrontlineSession: READY → ACTIVE → WAITING_HELP/ESCALATED → terminal when durable state justified
```

Do not create tables/state machines solely because these examples exist; prove lifecycle/persistence need first.

Do not scatter lifecycle rules across `if status` branches.

## 14. Policy / Specification

Policies:

```text
DecisionGatePolicy
AutonomyPolicy
RetryPolicy
RetentionPolicy
MediaCapturePolicy
ConsentPolicy
CapabilityAvailabilityPolicy
ComputePolicy
IndustrialSafetyBoundaryPolicy
```

Form:

```text
structured input → structured decision
```

Policy is not a free-form prompt.

Industrial safety authority remains with industrial owner; Copilot policy can only further restrict, never relax that owner.

## 15. Command + Handler

Platform actions:

```text
PlatformCommand
→ validator/authorized target resolver
→ generic handler registry
→ handler by command type
```

Allowed:
- OpenAppCommandHandler;
- OpenRouteCommandHandler;
- SetViewCommandHandler.

Forbidden:
- OpenCommercialPortalHandler;
- handler per app/customer/provider.

Do not reuse generic PlatformCommand handlers for physical machine actuation.

## 16. Media Pipeline Pattern

Media processing follows bounded stages, not a monolithic provider call:

```text
capture/reference
→ validate type/size/policy
→ transient or persisted ingest
→ extraction/transcription/perception
→ normalize Evidence
→ optional async enrichment
→ synthesis/presentation
→ retention/delete lifecycle
```

Rules:

- validate before provider call;
- preserve provenance;
- explicit resource budgets;
- raw media persistence optional, not default;
- large/long video may become async job/workflow;
- provider failure produces degraded mode, not fabricated result.

## 17. Realtime Session Pattern

Use only for genuine realtime requirements.

Session boundary should define:

```text
start/stop
active modalities
user/device/session refs
budgets
backpressure
network loss behavior
provider lifecycle
consent/retention policy
observability
cleanup
```

Realtime is not a global singleton and does not auto-resume mic/camera after reload without explicit policy/user state.

## 18. Event-Driven

Use when reacting asynchronously to a fact.

Distinguish:

```text
Domain Event
Integration Event
EventEnvelope used by Copilot boundary
```

Do not convert simple synchronous call into event without reason.

Watch/wait_event share the canonical event semantics.

Media frame streams are not automatically domain events.

## 19. Transactional Outbox

Use only when we need atomic:

```text
state persisted + integration event eventually published
```

If platform owner already guarantees equivalent semantics, use its contract.

## 20. Idempotency

Preference:

1. Domain API native idempotency;
2. domain use-case key;
3. Copilot orchestration guard only when necessary.

Write timeout ambiguity requires outcome verification before retry.

Repeated voice utterance, duplicated transcript event or meeting replay cannot duplicate write.

## 21. Saga

Only when:

- multiple writes across systems;
- process consistency matters;
- real compensation operations exist.

Never for read-only analysis, Meeting transcription or because “workflow is multi-step”.

## 22. Resilience

Every external adapter defines as appropriate:

```text
timeout
retry eligibility/backoff
circuit breaker
bulkhead/concurrency limit
ambiguous outcome handling
```

Media/realtime adds when needed:

```text
size/duration limit
backpressure
concurrent-session limit
network-loss fallback
async/degraded fallback
cost budget
```

Read retry != write retry.

## 23. Result/Error model

Canonical semantics should cover:

```text
Validation
Unauthorized
Forbidden
NotFound
Conflict
PolicyBlocked
DecisionRequired
ProviderUnavailable
Timeout
BusinessRuleViolation
MediaPermissionDenied
MediaPolicyBlocked
MediaTooLarge
RealtimeUnavailable
SharedDeviceSessionInvalid
IndustrialSafetyBlocked
Internal
```

Infra exceptions do not leak directly to MFE/LLM.

## 24. DTO + Mapper

Do not expose persistence ORM models as public transport contracts.

```text
Transport DTO
↕
Application/Domain model
↕ when needed
Persistence model
```

Media provider DTOs do not leak into Evidence/domain contracts.

Avoid ceremonial mapping when no semantic boundary exists.

## 25. Dependency Injection

Use simple composition.

Forbidden:

```text
UseCase creates PostgresRepository()
DomainService creates HttpClient()
MeetingUseCase creates SpeechProviderSDK()
FrontlineUseCase creates CameraProvider()
```

Concrete construction belongs to composition/startup.

## 26. Factory / Builder / Strategy

- Factory: config/runtime-dependent construction;
- Builder: truly complex/invariant-heavy object creation;
- Strategy: real interchangeable behavior.

One implementation plus hypothetical future variation is not enough for an internal Strategy.

Model/STT/Vision provider selection belongs to adapters/compute policy, not arbitrary feature branches.

## 27. CQRS

Light CQRS only if separate read/write models materially simplify performance/security/shape.

No Event Sourcing or duplicate stores by default.

## 28. Bounded Contexts target

C0 finalizes names/owners:

```text
Copilot Conversation/Intelligence
Capability & Action Integration
Expertise & Playbooks
Knowledge
Evidence & Provenance
Media & Interaction Sessions
Work Management
Policy & Decision
Platform Experience
Business Graph
Observability & Evals
```

Meeting/Frontline are product/application modules over these bounded responsibilities, not necessarily new bounded contexts.

Industrial OT/safety remains external authority/boundary unless a separate approved initiative defines otherwise.

## 29. Patterns by Copilot component

| Componente | Preferred patterns |
|---|---|
| Core integration | Port + Adapter + bounded DTO |
| Domain Actions | OpenAPI adapter + generic executor + Policy |
| Platform Actions | Command + Handler + Adapter |
| Workspace Context | Adapter + bounded contract |
| Shared Device Context | Adapter + bounded session metadata |
| Iframe Bridge | Adapter + ACL + typed messages |
| Expertise | versioned catalog; Repository if persisted; retrieval policy |
| Playbooks | versioned content + repository/port |
| Multimodal | Pipeline + adapters; Strategy only if needed |
| Speech | Port + Adapter; realtime session only when necessary |
| Image/Video | Media Pipeline + Evidence normalization |
| Media persistence | Storage Adapter + Retention Policy only when needed |
| Meeting | Application Use Cases + shared Media/Evidence/Work contracts |
| Frontline | Application Use Cases + WorkspaceContext + Media/Evidence adapters |
| Evidence | Value Object/validated factory + provenance |
| Graph | Ports/Adapters + permission policy; repository only if materialized |
| Decision | Policy + State Machine |
| Workflow | Application orchestration + State Machine + Idempotency |
| Task/Case | Aggregate/lifecycle if proven + Workflow refs |
| Room/Notification | Adapter to existing owner when viable |
| Inbox | materialized projection/surface |
| Watch | Event-driven + State Machine + dedupe |
| Organizational Knowledge | versioned lifecycle + review policy |
| Expertise Studio | Use Cases + State Machine + admin RBAC |
| Model Router | Strategy/Compute Policy after C7 baseline |
| Industrial telemetry | Read Adapter + canonical Entity/Evidence mapping |
| Industrial actuation | separate deterministic safety architecture, not generic Copilot executor |

## 30. Abstraction Gate

Before creating:

```text
interface/port
base class
factory
strategy
registry
framework
generic engine
repository
media service
realtime gateway
meeting backend
frontline backend
OT adapter
```

Answer:

1. Is there a real boundary?
2. Is there real variation or multiple consumers?
3. Do we need a test double for an external boundary?
4. Does the concept own lifecycle/state?
5. Does abstraction reduce coupling rather than add indirection?
6. Does repo already contain an equivalent abstraction?
7. Would the abstraction couple Copilot to Chat internals?
8. Can existing WorkspaceContext/EntityRef/EvidenceRef model it?
9. Does raw media really need persistence?
10. Is this business automation or physical actuation?
11. Who owns privacy/retention/safety?

If justification is “maybe later”, do not create it.

External boundaries may justify a Port from first implementation.

## 31. Anti-patterns

- Chat internals used as Copilot library;
- `Manager/Helper/Utils/Service` god objects;
- repository for every HTTP resource;
- deep base-class inheritance;
- global mutable service locator/singleton state;
- framework/provider/media SDK types in Domain/Application;
- ORM model as external contract;
- event bus without schema/owner;
- Strategy/Factory without variation;
- Saga without compensation;
- CQRS/Event Sourcing by fashion;
- feature-specific Entity/Evidence/Decision/Event model;
- `FrontlineContext` duplicating WorkspaceContext;
- second Core/RBAC/domain authority;
- Portal containing planner/RAG/action/media intelligence;
- fallback to Chat runtime;
- one `MultimodalService` owning every provider/workflow/policy;
- raw-media persistence by default;
- hidden camera/mic capture;
- media retention without class/policy;
- meeting-specific action executor;
- voice-specific RBAC;
- device identity as user identity;
- hidden employee surveillance;
- free-form LLM output sent to PLC/CNC/robot;
- Copilot replacing safety interlocks.

## 32. Testing by layer

### Domain
Pure units/invariants/value objects/state/policy.

### Application
Use cases with port fakes/stubs; no Flask/provider/media SDK required.

### Infrastructure
Contract/integration tests, provider mapping, timeout/error translation, media lifecycle, cleanup/backpressure when applicable.

### Interfaces
Schema/auth/error/transport/media-session tests.

### Frontend
Components/hooks/adapters/integration/accessibility/media permission/shared-device UX.

### Standalone boundary

Required checks:

```text
NO_CHAT_IMPORT
NO_CHAT_API_DEP
NO_CHAT_DB_AUTHORITY
CHAT_OFFLINE_INDEPENDENCE
```

When Meeting/Frontline/media are in scope:

```text
NO_HIDDEN_CAPTURE
RETENTION_POLICY_ENFORCED
SHARED_DEVICE_ISOLATION
MODALITY_RBAC_PARITY
NO_ARBITRARY_OT_COMMAND
```

## 33. Migration patterns

### Copilot DB/contracts

```text
EXPAND → compatible readers → writers → optional backfill → CUTOVER → CLEANUP
```

### External legacy integration actually being replaced

```text
Adapter/ACL → telemetry → canary → cutover → residual scan → remove adapter
```

Again: Minha DELPI Chat is not being migrated into Copilot.

Media provider migration follows adapters/versioned policy; do not rewrite business/application layers for provider swaps.

## 34. ADR / Exception Gate

If canonical pattern cannot satisfy a real requirement:

1. prove why;
2. list alternatives;
3. document trade-offs;
4. prove no second authority/product coupling;
5. include privacy/retention/safety impact when applicable;
6. register ADR/decision;
7. update this standard if exception becomes standard.

## 35. FOUNDATION_FREEZE architecture gates

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
MEDIA_RETENTION_POLICY
SHARED_DEVICE_BOUNDARY
OT_SAFETY_BOUNDARY
CHAT_RUNTIME_DEPENDENCY=0
```

All required = PASS before runtime feature work that depends on them.

## 36. Checklist per step

```text
[ ] owner/product boundary clear
[ ] correct layer
[ ] canonical pattern selected
[ ] shared primitive reused
[ ] port/abstraction justified
[ ] state machine if lifecycle requires
[ ] external dependency behind adapter
[ ] composition root wiring
[ ] error/resilience semantics preserved
[ ] frontend has no durable business authority
[ ] no Chat product coupling
[ ] media privacy/retention considered when applicable
[ ] shared-device isolation considered when applicable
[ ] no modality RBAC bypass
[ ] OT physical actuation separated from generic action runtime
[ ] tests match layer/contract
[ ] sibling/unknown no hardcode
[ ] no predictable next-phase redesign
```

## 37. Regra final

Quando houver dúvida:

```text
platform/product/privacy/safety boundary first
→ proven repo convention
→ Pattern Decision Matrix
→ simplest solution preserving boundaries
→ ADR only for material ambiguity
```

O objetivo não é usar muitos patterns; é obter código previsível, consistente, testável e evolutivo sem refatoração estrutural desnecessária — inclusive quando o Copilot evoluir de texto administrativo para voz, vídeo, Meeting e Frontline.