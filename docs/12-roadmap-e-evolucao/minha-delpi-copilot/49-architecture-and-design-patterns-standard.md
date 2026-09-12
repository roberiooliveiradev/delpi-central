# Minha DELPI Copilot — Padrão Normativo de Arquitetura e Design Patterns

**Status:** `CANONICAL_AUTHORITY` para arquitetura de código/patterns  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)

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
- approved neutral shared packages
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

> use o menor pattern que preserve ownership, testabilidade, segurança, generalização e evolução.

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

Não acessa DB/HTTP/LLM/env/framework.

### Application

- Use Cases/Application Services;
- orchestration;
- ports;
- Commands/Queries;
- state transition use cases;
- policy invocation;
- transaction boundary abstractions.

Sem SQL, URLs, provider names or transport concerns.

### Interfaces

- Flask controllers/routes;
- request/response DTOs;
- event/stream transport boundaries;
- schema validation;
- transport mappers.

### Infrastructure

- SQLAlchemy/PostgreSQL adapters;
- Core/Domain HTTP adapters;
- OpenAPI importer/executor;
- LLM/embedding adapters;
- RAG/vector adapters;
- OCR/Vision adapters;
- event broker/outbox;
- file/object storage;
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
Rendering/accessibility/user events/presentation only.

### State
Local/conversation/workspace UI state. No durable business authority.

### Data
Typed Copilot API clients, adapters, cache/query integration, contracts.

State ownership:

```text
Server State          → query/cache layer
Workspace State       → Portal/Copilot context adapter
Conversation UI State → MFE + server refs
Local UI State        → component/hook
Durable Work State    → Copilot API
```

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
- CreateWatch.

Avoid one monolithic `CopilotService`.

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
Business Graph source adapters
```

## 11. Repository Pattern

Use only for Copilot-owned lifecycle/persistent authority, e.g. when proven:

- Conversation;
- Expertise/Playbook catalogs;
- Workflow;
- Task/Case;
- Watch;
- Graph relationship materialization.

Wrong:

```text
PurchaseOrderRepository that merely calls purchase API
```

Correct:

```text
DomainApiAdapter / generic Business Action executor
```

## 12. Adapter / Anti-Corruption Layer

Use for:

- Core contract → Copilot canonical context;
- MFE/Portal host contract;
- iframe messages;
- Domain API/provider variations;
- existing room/notification infrastructure;
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
```

Do not scatter lifecycle rules across `if status` branches.

## 14. Policy / Specification

Policies:

```text
DecisionGatePolicy
AutonomyPolicy
RetryPolicy
RetentionPolicy
CapabilityAvailabilityPolicy
ComputePolicy
```

Form:

```text
structured input → structured decision
```

Policy is not a free-form prompt.

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

## 16. Event-Driven

Use when reacting asynchronously to a fact.

Distinguish:

```text
Domain Event
Integration Event
EventEnvelope used by Copilot boundary
```

Do not convert simple synchronous call into event without reason.

Watch/wait_event share the canonical event semantics.

## 17. Transactional Outbox

Use only when we need atomic:

```text
state persisted + integration event eventually published
```

If platform owner already guarantees equivalent semantics, use its contract.

## 18. Idempotency

Preference:

1. Domain API native idempotency;
2. domain use-case key;
3. Copilot orchestration guard only when necessary.

Write timeout ambiguity requires outcome verification before retry.

## 19. Saga

Only when:

- multiple writes across systems;
- process consistency matters;
- real compensation operations exist.

Never for read-only analysis or because “workflow is multi-step”.

## 20. Resilience

Every external adapter defines as appropriate:

```text
timeout
retry eligibility/backoff
circuit breaker
bulkhead/concurrency limit
ambiguous outcome handling
```

Read retry != write retry.

## 21. Result/Error model

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
Internal
```

Infra exceptions do not leak directly to MFE/LLM.

## 22. DTO + Mapper

Do not expose persistence ORM models as public transport contracts.

```text
Transport DTO
↕
Application/Domain model
↕ when needed
Persistence model
```

Avoid ceremonial mapping when no semantic boundary exists.

## 23. Dependency Injection

Use simple composition.

Forbidden:

```text
UseCase creates PostgresRepository()
DomainService creates HttpClient()
```

Concrete construction belongs to composition/startup.

## 24. Factory / Builder / Strategy

- Factory: config/runtime-dependent construction;
- Builder: truly complex/invariant-heavy object creation;
- Strategy: real interchangeable behavior.

One implementation plus hypothetical future variation is not enough for an internal Strategy.

## 25. CQRS

Light CQRS only if separate read/write models materially simplify performance/security/shape.

No Event Sourcing or duplicate stores by default.

## 26. Bounded Contexts target

C0 finalizes names/owners:

```text
Copilot Conversation/Intelligence
Capability & Action Integration
Expertise & Playbooks
Knowledge
Evidence & Provenance
Work Management
Policy & Decision
Platform Experience
Business Graph
Observability & Evals
```

These live within the standalone Copilot product while respecting external platform/domain boundaries.

## 27. Patterns by Copilot component

| Componente | Preferred patterns |
|---|---|
| Core integration | Port + Adapter + bounded DTO |
| Domain Actions | OpenAPI adapter + generic executor + Policy |
| Platform Actions | Command + Handler + Adapter |
| Workspace Context | Adapter + bounded contract |
| Iframe Bridge | Adapter + ACL + typed messages |
| Expertise | versioned catalog; Repository if persisted; retrieval policy |
| Playbooks | versioned content + repository/port |
| Multimodal | Pipeline + adapters; Strategy only if needed |
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

## 28. Abstraction Gate

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
```

Answer:

1. Is there a real boundary?
2. Is there real variation or multiple consumers?
3. Do we need a test double for an external boundary?
4. Does the concept own lifecycle/state?
5. Does abstraction reduce coupling rather than add indirection?
6. Does repo already contain an equivalent abstraction?
7. Would the abstraction couple Copilot to Chat internals?

If justification is “maybe later”, do not create it.

External boundaries may justify a Port from first implementation.

## 29. Anti-patterns

- Chat internals used as Copilot library;
- `Manager/Helper/Utils/Service` god objects;
- repository for every HTTP resource;
- deep base-class inheritance;
- global mutable service locator/singleton state;
- framework types in Domain/Application;
- ORM model as external contract;
- event bus without schema/owner;
- Strategy/Factory without variation;
- Saga without compensation;
- CQRS/Event Sourcing by fashion;
- feature-specific Entity/Evidence/Decision/Event model;
- second Core/RBAC/domain authority;
- Portal containing planner/RAG/action logic;
- fallback to Chat runtime.

## 30. Testing by layer

### Domain
Pure units/invariants/value objects/state/policy.

### Application
Use cases with port fakes/stubs; no Flask/provider required.

### Infrastructure
Contract/integration tests, mapping, timeout/error translation.

### Interfaces
Schema/auth/error/transport tests.

### Frontend
Components/hooks/adapters/integration/accessibility.

### Standalone boundary

Required checks:

```text
NO_CHAT_IMPORT
NO_CHAT_API_DEP
NO_CHAT_DB_AUTHORITY
CHAT_OFFLINE_INDEPENDENCE
```

## 31. Migration patterns

### Copilot DB/contracts

```text
EXPAND → compatible readers → writers → optional backfill → CUTOVER → CLEANUP
```

### External legacy integration actually being replaced

```text
Adapter/ACL → telemetry → canary → cutover → residual scan → remove adapter
```

Again: Minha DELPI Chat is not being migrated into Copilot.

## 32. ADR / Exception Gate

If canonical pattern cannot satisfy a real requirement:

1. prove why;
2. list alternatives;
3. document trade-offs;
4. prove no second authority/product coupling;
5. register ADR/decision;
6. update this standard if exception becomes standard.

## 33. FOUNDATION_FREEZE architecture gates

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
CHAT_RUNTIME_DEPENDENCY=0
```

All required = PASS before runtime feature work.

## 34. Checklist per step

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
[ ] tests match layer/contract
[ ] sibling/unknown no hardcode
[ ] no predictable next-phase redesign
```

## 35. Regra final

Quando houver dúvida:

```text
platform/product boundary first
→ proven repo convention
→ Pattern Decision Matrix
→ simplest solution preserving boundaries
→ ADR only for material ambiguity
```

O objetivo não é usar muitos patterns; é obter código previsível, consistente, testável e evolutivo sem refatoração estrutural desnecessária.