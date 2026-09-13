# Minha DELPI Copilot — Padrão Normativo de Arquitetura e Design Patterns

**Status:** `CANONICAL_AUTHORITY` para arquitetura de código/patterns  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)

## 1. Objetivo

Fazer o Cursor classificar o problema e aplicar pattern já definido, em vez de inventar arquitetura por feature/provider.

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

External provider SDK/API também não vira Domain authority; ele entra por adapter.

## 3. Architecture style

Obrigatório:

```text
Clean Architecture
+ Ports & Adapters / Hexagonal
+ Pragmatic DDD
+ Event-Driven only for real events
+ State Machines for nontrivial lifecycle
+ Light CQRS only when materially justified
```

Use o menor pattern que preserve ownership, testabilidade, segurança, privacidade, generalização e evolução.

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

Domain/Application não importam Flask/SQLAlchemy/DB driver/HTTP client/LLM SDK/media SDK/OAuth provider SDK/search SDK/Microsoft Graph SDK/Google SDK/WhatsApp SDK/event broker/Chat modules/Portal source.

## 5. Backend layers

### Domain

Entities/Aggregates somente com identity/lifecycle real, Value Objects, invariants, pure Policies/Specifications e real Domain Events.

Sem DB/HTTP/provider/credential/framework.

### Application

Use Cases/Application Services, Commands/Queries, ports, orchestration, policy invocation, transaction boundaries e lifecycle transitions.

Examples:

```text
ResearchExternalInformation
CreateExternalConnection
RefreshExternalConnection
ReadExternalResource
DraftExternalMessage
SendExternalMessage
HandleProviderEvent
ReconcileExternalSubscription
PromoteExternalKnowledgeCandidate
```

Sem provider URL, SDK, token ou concrete API detail.

### Interfaces

Controllers/routes/DTOs/schema validation/event/webhook boundaries/mappers.

OAuth callback e webhook são transport boundaries; business/policy logic não vive no controller.

### Infrastructure

- DB repositories;
- Core/Domain HTTP adapters;
- OpenAPI importer/executor;
- LLM/RAG/media/biometric adapters;
- Search provider adapters;
- Safe Web Fetch adapter;
- OAuth/provider adapters;
- secret/vault adapter;
- Microsoft/Google/WhatsApp/other concrete connectors;
- event/webhook/subscription adapters;
- storage/cache/telemetry.

### Composition Root

Configura concrete adapters/repositories/policies/use cases/controllers. Feature use cases não criam provider SDK diretamente.

## 6. Frontend architecture

```text
ui
state
data
```

UI apresenta connection state/scopes/source provenance/draft/send/Decision UX. State local não vira provider credential store. Data layer usa Copilot API; browser não recebe refresh token de provider.

Durable ExternalConnection/Subscription state vive no backend/secret owner.

## 7. Pattern Decision Matrix

| Problema | Pattern padrão | Limite |
|---|---|---|
| external dependency | Port + Adapter | boundary real |
| application operation | Use Case/Application Service | one operational intent |
| owned persistent state | Repository | not HTTP proxy |
| complex lifecycle | State Machine | explicit transitions |
| deterministic rule | Policy | structured input/output |
| incompatible provider shape | Adapter + ACL | protect canonical model |
| platform command | Command + Handler | typed generic target |
| reliable state+event | Transactional Outbox | only when required |
| retryable write | Idempotency | no blind retry |
| asynchronous provider event | Event-Driven | real event owner/schema |
| transport boundary | DTO + Mapper | no provider DTO leakage |
| concrete wiring | Composition Root DI | simple composition |
| media processing | bounded Pipeline | provenance/budgets |
| realtime media | Session + transport adapter | explicit limits |
| biometric provider | Port + Adapter | candidate identity only |
| public web search | Search Port + Adapter | provider-neutral results |
| public web fetch | Safe Fetch Port + Policy | egress boundary required |
| OAuth connection | Use Cases + State Machine + Credential Port | provider adapter owns details |
| provider credential | Secret/Vault Adapter | never normal domain field |
| connector capability | semantic capability + Adapter | planner provider-neutral |
| provider event | Webhook/Subscription Adapter → EventEnvelope | authenticity/dedupe/reconciliation |
| external cache | bounded cache/materialization | scoped, TTL, never authority |
| external communication write | Use Case + Policy/Decision + Adapter | `draft != send` |
| browser fallback | sandboxed adapter | only if justified; not default |
| OT actuation | separate industrial safety architecture | never generic LLM executor |

## 8. Use Case Pattern

```text
Controller/Event Handler
→ Use Case
→ Domain/Policy
→ Port
→ Adapter
```

Evitar `CopilotService`, `MultimodalService` ou `ConnectorService` god objects.

## 9. Ports & Adapters

External boundaries que podem justificar ports quando implementadas:

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
Media/Vision/Speech/Biometric ports
```

Não criar todos antecipadamente. Cada port passa pelo Abstraction Gate.

Provider-specific adapters:

```text
MicrosoftGraphAdapter
GoogleWorkspaceAdapter
WhatsAppBusinessAdapter
...
```

não contaminam planner/domain/application com provider semantics.

## 10. Repository Pattern

Repository somente para state/lifecycle que o Copilot possui:

- Conversation;
- Expertise/Playbook;
- Workflow/Task/Case/Watch;
- ExternalConnection metadata se Copilot-owned;
- ExternalSubscription state;
- Meeting/Frontline metadata quando durable;
- Graph materialization quando provada.

Não criar `GmailRepository` ou `OutlookRepository` apenas para encapsular HTTP. Use provider adapter.

## 11. Anti-Corruption Layer

Use para Core/domain/provider/legacy shapes incompatíveis. Normalize provider resources/capabilities para contratos Copilot sem espalhar Graph/Gmail/WhatsApp vocabulary no core.

Chat não é legacy sendo migrado para Copilot; não usar Strangler entre Chat e Copilot.

## 12. State Machine

Required para lifecycle real, por exemplo:

```text
ExternalConnection:
PENDING_AUTH → ACTIVE → EXPIRED|REAUTH_REQUIRED|REVOKED|DISABLED|ERROR

ExternalSubscription:
CREATING → ACTIVE → RENEWING → ACTIVE|EXPIRED|REAUTH_REQUIRED|DISABLED|ERROR
```

Também aplica a Workflow/Decision/Case/Watch/Meeting/Media/Biometric quando persistence/lifecycle forem reais.

Não espalhar state transition em `if status` aleatórios.

## 13. Policy

Policies possíveis quando justificadas:

```text
DecisionGatePolicy
AutonomyPolicy
RetryPolicy
RetentionPolicy
MediaCapturePolicy
BiometricIdentityPolicy
ExternalEgressPolicy
ExternalConnectionPolicy
ExternalDataSharingPolicy
ExternalActionPolicy
ExternalKnowledgePromotionPolicy
ComputePolicy
IndustrialSafetyBoundaryPolicy
```

Policy é deterministic structured decision, não prompt livre.

## 14. Internet Research Pattern

```text
Research Use Case
→ SearchProviderPort
→ candidate sources
→ SafeWebFetchPort
→ extraction/normalization
→ SourceRef/EvidenceRef
→ freshness/relevance
→ synthesis
```

Rules:

- no LLM-created URL directly into unrestricted HTTP client;
- egress validation before and after redirect;
- bounded type/size/time/concurrency;
- protected/internal destinations blocked according to policy;
- external content treated as untrusted;
- sensitive internal context minimized before external query;
- provenance/freshness preserved.

Search and fetch are different responsibilities.

## 15. External Connection / OAuth Pattern

```text
ConnectExternalSource Use Case
→ provider authorization adapter
→ callback DTO validation
→ connection lifecycle
→ SecretStorePort
→ ExternalConnection repository
→ normalized capability projection
```

Application owns connection intent/state transition; provider adapter owns concrete auth endpoints/scopes/token protocol details.

Provider token never crosses into planner/LLM/MFE.

Connection ownership is explicit:

```text
USER_DELEGATED
ORG_MANAGED
SHARED_RESOURCE
SERVICE_CONNECTION
```

## 16. Semantic Connector Capability Pattern

Planner sees semantic capabilities such as:

```text
communication.email.search
communication.email.read
communication.email.draft
communication.email.send
calendar.events.read
calendar.events.create
files.search
files.read
messaging.message.send
```

Adapter maps those to real provider contracts. Do not branch planner by provider name.

When provider publishes usable OpenAPI/schema, prefer contract-driven normalization where appropriate.

## 17. External Read Pattern

```text
authorized semantic capability
→ connection/scope validation
→ provider adapter
→ normalized resource/result
→ SourceRef/EvidenceRef
→ presentation/correlation
```

Do not copy mailbox/file store as Copilot master data.

## 18. External Write Pattern

```text
intent
→ draft/preview when applicable
→ ExternalActionPolicy/Decision Gate
→ connection/scope revalidation
→ provider adapter
→ outcome verification
→ OutcomeRef/Evidence/Audit
```

Rules:

- `draft != send`;
- no blind retry;
- ambiguous timeout requires outcome verification;
- target/recipient constraints may be policy inputs;
- connection revoked after preview blocks execution.

## 19. Provider Event Pattern

```text
webhook/push/subscription
→ interface validation
→ provider adapter authenticity validation
→ normalize EventEnvelope
→ dedupe/correlation
→ Watch/Workflow/Inbox
```

Subscription lifecycle separately handles renewal, expiry and reconciliation. Event payload never grants permission or bypasses Decision Gate.

## 20. External Knowledge Promotion Pattern

```text
external SourceRef/Evidence
→ transient use OR candidate
→ owner/review
→ freshness/privacy/licensing/eval
→ versioned publish
```

Personal source cannot auto-promote to organizational Knowledge.

## 21. Media/Biometric Pipelines

Continue usando bounded pipeline/adapters/provenance/retention. External attachments entram no mesmo safe ingest boundary after provider download validation.

## 22. Resilience

Cada external adapter define conforme aplicável:

```text
timeout
retry eligibility/backoff
rate-limit handling
circuit breaker
concurrency limit
ambiguous outcome handling
re-auth/degraded state
```

Read retry != write retry. Provider subscription failure requires truthful stale/degraded state and reconciliation path.

## 23. Result/Error model

Canonical semantics devem cobrir também:

```text
ExternalNotConnected
ExternalConsentRequired
ExternalScopeMissing
ExternalConnectionExpired
ExternalPermissionRevoked
ExternalProviderUnavailable
ExternalRateLimited
ExternalResourceNotFound
ExternalEgressBlocked
ExternalEventInvalid
ExternalSyncStale
```

Provider exceptions não vazam diretamente à UI/LLM.

## 24. DTO + Mapper

Provider SDK DTOs não são contracts públicos. Mapear somente o necessário para application/domain refs/outcomes.

## 25. Dependency Injection

Forbidden:

```text
UseCase creates Google/Microsoft/WhatsApp client
UseCase reads provider token directly
Planner instantiates HTTP client
Controller owns refresh token lifecycle
```

Concrete creation belongs to composition/infrastructure.

## 26. Browser automation

Não é default. Só após provar que API/connector/structured fetch não atende.

Quando existir:

- sandbox/domain/session bounds;
- protected credential injection;
- same Policy/Decision semantics;
- no arbitrary internal-network reach;
- kill switch;
- telemetry.

## 27. Bounded Contexts target

```text
Copilot Conversation/Intelligence
Capability & Action Integration
Expertise & Playbooks
Knowledge
Evidence & Provenance
Media & Interaction Sessions
External Information & Connections
Work Management
Policy & Decision
Platform Experience
Business Graph
Observability & Evals
```

Meeting/Frontline remain product modules over shared contexts. Industrial OT/safety remains external authority.

## 28. Patterns by component

| Componente | Preferred patterns |
|---|---|
| Internet Research | Use Case + Search Adapter + Safe Fetch Adapter + Evidence |
| External Connections | Use Case + State Machine + Repository + Secret Adapter |
| Microsoft/Google/WhatsApp/etc. | Provider Adapter + ACL |
| External Reads | Capability + Adapter + Evidence normalization |
| External Writes | Policy/Decision + Adapter + verified Outcome |
| Provider Events | Webhook Adapter + EventEnvelope + dedupe/reconciliation |
| External Knowledge | candidate lifecycle + review/eval/publish |
| Core/Domain Actions | Port/Adapter + canonical contracts |
| Workspace | bounded contract |
| Multimodal/Biometric | Pipeline + adapters |
| Workflow/Decision | State Machine + Policy + Idempotency |
| OT | separate safety architecture |

## 29. Abstraction Gate

Antes de criar interface/port/base/factory/strategy/registry/framework/repository/connector engine/web fetcher/browser automation, provar:

1. real boundary?
2. real variation/consumer?
3. test double needed for external boundary?
4. owned lifecycle/state?
5. reduces coupling?
6. equivalent already exists?
7. avoids Chat product coupling?
8. existing SourceRef/EntityRef/EvidenceRef sufficient?
9. persistence really needed?
10. provider-specific concern can stay in adapter?
11. token/secret remains inside protected boundary?
12. read/write semantics remain distinct?
13. new provider works without planner patch?

“Might be useful later” is insufficient.

## 30. Anti-patterns

- Chat internals as Copilot library;
- god `ConnectorService`;
- repository for every external HTTP resource;
- provider SDK types in Domain/Application;
- provider name branching in planner;
- manual provider endpoint catalog as authority;
- OAuth token in conversation/context/log/MFE;
- one shared connection silently used by all users;
- personal mailbox/file copied to organizational Knowledge automatically;
- browser automation before official API/connector without evidence;
- unrestricted web fetch;
- implicit `draft → send`;
- webhook payload executing write directly;
- external cache as source of truth;
- raw media/biometric persistence by default;
- hidden worker profiling;
- free-form LLM to industrial machine.

## 31. Testing by layer

### Domain/Application
Pure policy/lifecycle/use-case tests with port fakes.

### Infrastructure
Provider contract tests, token refresh/revoke, mapping, limits, event verification, timeout/error translation, safe fetch/egress tests.

### Interfaces
OAuth callback/webhook/schema/auth/error tests.

### Frontend
Connection/source/draft/send/Decision/accessibility UX without credential exposure.

### Standalone

```text
NO_CHAT_IMPORT
NO_CHAT_API_DEP
NO_CHAT_DB_AUTHORITY
CHAT_OFFLINE_INDEPENDENCE
```

External scope also requires connector generalization, credential isolation, safe egress, read/write separation, event reliability and privacy tests from `20`.

## 32. Migration patterns

Copilot DB/contracts:

```text
EXPAND → compatible readers → writers → optional backfill → CUTOVER → CLEANUP
```

Provider swaps use adapters/versioned connection policy. Do not rewrite application/domain for a provider migration.

## 33. ADR / Exception Gate

Any material deviation proves why, alternatives, trade-offs, no second authority, privacy/security impact and exit/rollback.

## 34. FOUNDATION_FREEZE architecture gates

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
EXTERNAL_LEARNING_BOUNDARY
OT_SAFETY_BOUNDARY
CHAT_RUNTIME_DEPENDENCY=0
```

## 35. Regra final

```text
platform/product/privacy/security boundary first
→ proven repo convention
→ Pattern Decision Matrix
→ simplest solution preserving boundaries
→ ADR only for material ambiguity
```

O objetivo é uma arquitetura previsível que permita adicionar novos providers sem refatorar planner, policy, Domain ou UX central.
