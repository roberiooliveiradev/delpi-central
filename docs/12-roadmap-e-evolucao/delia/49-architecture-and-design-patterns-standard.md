# DÉLIA — Padrão Normativo de Arquitetura e Design Patterns

**Status:** `CANONICAL_AUTHORITY` para arquitetura de código/patterns  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Tests:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Specs temáticas:** `53–66`

> Este documento define padrões e constraints alvo. Ele **não prova implementação** de ports, repositories, registries, engines, runtimes, services, schemas ou capabilities. Criação/reuso exige evidência e passagem pelo Abstraction Gate.

## 1. Objetivo

Evitar arquitetura inventada por feature/provider. Sempre:

```text
problem
→ responsibility/owner/source of truth
→ consumers
→ contract
→ boundary
→ layer
→ simplest canonical pattern
→ Abstraction Gate
→ implementation
→ contract/conformance tests
```

## 2. Product boundary primeiro

Código da DÉLIA pertence à nova API/MFE da DÉLIA. Portal/Core/Keycloak/Gateway/plugin-ui/Domain APIs/External providers/Automation Hub/OT owners preservam authorities.

Chat internals não são shared library.

Provider SDK, RPA runtime, MCP server, A2A agent, model runtime, sandbox engine e Edge runtime entram por boundaries/adapters; nenhum vira Domain authority.

Automation Hub é owner semântico da **execução técnica** de automações. DÉLIA é owner de inteligência, contexto, Evidence, Policy, Decision, Work/orquestração e verificação de Outcome. C0 deve provar o runtime físico e contratos existentes; ausência de prova não transfere ownership.

## 3. Architecture style

```text
Clean Architecture
+ Ports & Adapters / Hexagonal
+ Pragmatic DDD
+ Event-Driven only for real events
+ State Machines for nontrivial lifecycle
+ Policy/Specification for deterministic decisions
+ Light CQRS only when materially justified
```

Use o menor pattern que preserve ownership, testability, security, privacy, generalization, evidence/outcome truth e evolution.

## 4. Dependency rule

```text
Domain
↑
Application
↑
Interfaces / Adapters
↑
Infrastructure

Composition Root wires concretes.
```

Domain/Application não importam Flask/SQLAlchemy/HTTP/DB driver/LLM SDK/media SDK/OAuth SDK/provider SDK/RPA SDK/MCP SDK/A2A SDK/sandbox runtime/model-serving SDK/event broker/Portal/Chat source/Automation Hub internals.

Bounded contexts integram por contrato HTTP/evento/port adapter apropriado; nunca por import de domain/use case ou banco alheio.

## 5. Layer responsibilities

### Domain

- real entities/aggregates only;
- value objects/invariants;
- pure Policy/Specification;
- real Domain Events.

Sem provider/executor/model/UI mechanics.

### Application

Use Cases/Application Services, Commands/Queries, ports aprovados pelo Abstraction Gate, orchestration, lifecycle transitions, transaction boundaries.

Examples target — não criar sem necessidade comprovada:

```text
ResearchExternalInformation
EvaluateOperationalCondition
MineProcessVariants
QueryGovernedMetric
RunAnalysis
CreateArtifact
CreateOrUpdateMemoryItem
DelegateExternalAgentTask
PrepareAutomationAction
ExecuteAutomationCapability
VerifyAutomationOutcome
CreateScenario
RunPrediction
PublishMarketplaceAsset
HandleEdgeSync
```

### Interfaces

Controllers/routes/DTOs/schema validation/webhook/event/callback boundaries/mappers. Business/policy logic never lives in controller.

### Infrastructure

Concrete adapters for DB/Core/Domain/OpenAPI/LLM/media/biometric/search/fetch/OAuth/connectors/events/Automation Hub/RPA/computer-use/MCP/A2A/sandbox/model runtime/Edge/storage/cache/telemetry.

### Composition Root

Creates/configures concrete implementations. Feature use cases never instantiate SDKs directly.

## 6. Frontend architecture

```text
ui
state
data
features/contracts/adapters only when responsibility is real
```

Durable business/memory/artifact/process/model/automation state is backend-owned. Browser never becomes secret/token/model-registry store.

## 7. Pattern Decision Matrix

| Problem | Default pattern | Boundary |
|---|---|---|
| external dependency | Port + Adapter | real external boundary |
| application operation | Use Case/Application Service | one intent |
| owned persistent lifecycle | Repository | not remote proxy |
| complex lifecycle | State Machine | explicit transitions |
| deterministic rule/readiness | Policy / Specification | structured facts → result |
| incompatible provider/legacy shape | Adapter + ACL | protect canonical model |
| platform command | Command + Handler | typed target |
| state + event atomicity | Transactional Outbox | only if required |
| retryable write | Idempotency | no blind retry |
| asynchronous event | Event Adapter → EventEnvelope | source/auth/dedupe |
| event condition | Watch + Specification | OBSERVE/ADVISE/PREPARE/ACT |
| decision path | Policy; Strategy only if real variation | FAST/OPERATIONAL/REASONING |
| semantic business metric | Definition/Registry + Query Use Case | owner/version/formula |
| process mining | Event-log projection + Process Mining Use Case | process, not person score |
| analysis execution | Sandbox Port + isolated runtime Adapter | bounded/quota/read default |
| artifact generation | Artifact Use Case + Repository/Storage Adapter | lineage/version/ACL |
| prediction/model inference | Model Port + Adapter + PredictionRef | model/version/horizon |
| simulation/twin | Scenario/Projection + Simulation Port | simulated != production |
| personal memory | Memory Use Cases + Repository + Policy | user-owned/private |
| MCP tool | Tool Port/Adapter + allowlist | untrusted tool metadata |
| A2A agent | Delegation Port/Adapter + bounded task | external agent not authority |
| automation capability | semantic Registry/Projection | no UI mechanics in planner |
| automation orchestration | Use Case/Workflow + Policy/Decision | DÉLIA owns semantic Work |
| technical executor | Automation Hub contract + adapter | no executor internals in planner |
| RPA | Automation Hub/RPA Executor Adapter + ACL | replaceable legacy executor |
| computer-use | Automation Hub/sandboxed Executor Adapter | advanced fallback |
| outcome verification | Verifier Port + Specification | technical != business success |
| Control Tower | Registry projections + Admin Queries/Commands | governance plane |
| model lifecycle | Registry + State Machine + Eval/Deployment adapters | governed model asset |
| marketplace | Package manifest + lifecycle + supply-chain gates | install != permission |
| Edge/offline | Device/Package/Sync adapters + bounded state | offline != wider authority |
| OT actuation | separate industrial safety architecture | never generic LLM executor |

Patterns nesta matriz são **defaults condicionais**, não instrução para criar todas as abstrações.

## 8. Use Case Pattern

```text
Controller/Event Handler
→ Use Case
→ Domain/Policy
→ approved Port
→ Adapter
```

Avoid god objects: `DeliaService`, `CopilotService`, `ConnectorService`, `AutomationService`, `RpaManager`, `AgentOrchestrator`, `SemanticService`, `ProcessMiningService`, `TwinService`, `ControlTowerService` with mixed responsibilities.

## 9. Ports & Adapters

Possible ports only when a real boundary is proven:

```text
CoreApiPort
DomainActionPort
SearchProviderPort
SafeWebFetchPort
ExternalConnection/Resource/Action/Subscription ports
SecretStorePort
EventSourcePort
AutomationHubPort
OutcomeVerifierPort
NotificationPort
ProcessEventSourcePort
SemanticMetricSourcePort
AnalysisSandboxPort
ArtifactStoragePort
ModelInferencePort
SimulationPort
ExternalToolPort
AgentDelegationPort
EdgeDevice/Sync ports
ModelRegistry/Deployment ports
```

Do not create them all upfront. Every abstraction passes the gate and must have real owner/consumer/variation/lifecycle or test-double justification.

## 10. Repository Pattern

Repository only for owned lifecycle/state:

```text
Conversation
PersonalMemory
Expertise/Playbook
Workflow/Task/Case/Watch
ExternalConnection/Subscription
AutomationExecution projection/catalog only when DÉLIA owns that lifecycle state
Artifact metadata/version
AIAsset/Model/Marketplace metadata when owned
Meeting/Frontline metadata
Graph/Semantic/Process derived registry/materialization when justified
```

Do not create `GmailRepository`, `RpaRepository`, `McpRepository` merely to wrap remote calls.

Automation Hub execution state is not automatically DÉLIA-owned persistence; C0 must define contract/projection needs without duplicating executor truth.

## 11. Anti-Corruption Layer

Normalize Core/domain/provider/Automation Hub/RPA/MCP/A2A/model/legacy shapes into DÉLIA contracts. SDK/provider/executor types never leak to Domain/Application/public API.

## 12. State Machines

Use only for real lifecycles, e.g.:

```text
ExternalConnection
DÉLIA Work/Decision lifecycle
AutomationExecution projection only if owned/required
MCP/A2A integration approval lifecycle
MemoryItem
Artifact
Model deployment lifecycle
Marketplace asset lifecycle
Worker/Edge device operational state where durable
```

No random `if status` spread across controllers.

## 13. Policy / Specification

Typical policies — candidates, not mandatory class names:

```text
DecisionGatePolicy
AutonomyPolicy
DecisionPathPolicy
OperationalReadinessPolicy
AnomalyPolicy
Retry/IdempotencyPolicy
ExecutorSelectionPolicy
OutcomeVerificationPolicy
RetentionPolicy
MemoryWritePolicy
SemanticMetricPolicy
SandboxPolicy
ExternalEgressPolicy
ExternalActionPolicy
ToolAgentTrustPolicy
ModelApprovalPolicy
MarketplaceEnablePolicy
EdgeOfflinePolicy
IndustrialSafetyBoundaryPolicy
```

Policy is structured decision, not free-form prompt.

## 14. Semantic Capability Pattern

Planner works with semantic capabilities independent from technical executor/provider:

```text
billing.invoice.issue
maintenance.request.create
communication.email.send
inventory.read
analysis.run
artifact.create
process.mine
metric.query
```

Mapping can change RPA→API/provider A→B without planner rewrite.

## 15. Internet / External Connector Patterns

Target canonical flow:

```text
Search → Safe Fetch → Source/Evidence
OAuth → ExternalConnection → SecretRef → Provider Adapter
Provider event → validation → EventEnvelope → Watch/Workflow
Intent → preview/Decision → write adapter → verified Outcome
```

External content remains untrusted; `draft != send`.

## 16. Event / Decision Intelligence Pattern

```text
event/user goal
→ EventEnvelope / context
→ DecisionPathPolicy
   FAST | OPERATIONAL | REASONING
→ structured result/decision candidate
```

FAST uses deterministic rules; OPERATIONAL uses bounded reads/rules + optional small model; REASONING uses Graph/APIs/Knowledge/Expertise/docs/external sources/LLM conforme necessidade.

Never call LLM merely because an event occurred.

## 17. Operational Readiness Pattern

```text
authoritative facts
→ Specification
→ READY | NOT_READY | INCONCLUSIVE
→ reason codes + Evidence
```

LLM can investigate/explain, not replace formal criteria.

## 18. Automation / Executor Pattern

```text
intent/event
→ semantic capability
→ DÉLIA Policy/Decision
→ DÉLIA Work/Workflow
→ executor selection under policy
→ Automation Hub contract
→ technical executor/adapter
→ technical result
→ authoritative OutcomeVerifier/source
→ Outcome/Evidence/Audit
```

Default preference:

```text
official API
→ supported native integration
→ deterministic function/script
→ RPA
→ computer-use
→ human task
```

DÉLIA Work remains the canonical intelligence/orchestration lifecycle. Automation Hub may have its own technical execution lifecycle but must not become a second business planner or permission authority.

## 19. RPA / Computer-Use Pattern

RPA sits behind the Automation Hub/executor boundary. Worker/queue/lease/package/credential/session isolation belongs to the technical execution owner when RPA is real scope.

Computer-use is advanced fallback with sandbox/session/app/network allowlist, takeover/stop and full audit.

Planner never sees click/selector/coordinate mechanics.

## 20. Outcome Verification Pattern

```text
technical result
→ expected postcondition
→ authoritative verifier/source
→ VERIFIED_SUCCESS|VERIFIED_FAILURE|PENDING|INCONCLUSIVE
```

No notification/message may convert an unverified action into “success”. Automation Hub technical success alone is insufficient.

## 21. Process Intelligence Pattern

```text
authorized event logs
→ normalized process events
→ case traces
→ variants/conformance/bottlenecks
→ Evidence
→ opportunity candidate
```

Rules:

- missing event stays missing;
- task mining requires privacy boundary;
- actor-level data minimized;
- deviation != employee fault/fraud;
- opportunity != automatic automation deployment;
- process KPIs use governed semantic definitions where available.

## 22. Semantic Business Layer Pattern

```text
user intent
→ resolve MetricDefinition/Glossary concept
→ permission-aware source plan
→ deterministic query/calculation
→ Evidence + definition version
→ explanation
```

Graph = relationships; Semantic Layer = meaning/formula/grain/dimensions. Do not collapse them into one generic graph model.

## 23. Personal Memory Pattern

```text
candidate memory
→ MemoryWritePolicy
→ save/confirm/ignore
→ versioned MemoryItem
→ retrieval for relevance/presentation
```

Memory cannot grant permission or override live business truth. Personal Memory and Organizational Knowledge have different ownership/lifecycles.

## 24. MCP / A2A Pattern

### MCP

```text
semantic capability
→ Tool Adapter
→ approved server
→ schema-validated invocation
→ normalized Source/Evidence/Outcome
```

### A2A

```text
bounded subtask
→ AgentDelegationPolicy
→ approved agent adapter
→ status/result/artifact
→ normalized Evidence/Outcome
→ Workflow continues
```

Discovery ≠ approval. Tool descriptions/messages/artifacts are untrusted. Delegation sends minimum context and no CoT dump.

## 25. Analysis Sandbox Pattern

```text
authorized read/data export
→ isolated sandbox
→ bounded code/query
→ analysis result
→ Evidence/Artifact
```

Default: read-only source access; quotas/timeout/storage/network/egress/package policy; no broad DB/host credentials.

## 26. Artifact Workspace Pattern

```text
CreateArtifact Use Case
→ Artifact lifecycle/version
→ Storage Adapter
→ provenance/ACL
→ review/edit/attach/export
```

Human edits form new versions or explicit patches; regeneration must not silently overwrite them. External sharing remains separate action.

## 27. Predictive / Prescriptive Pattern

### Prediction

```text
features/source refs
→ ModelInferencePort
→ model adapter
→ PredictionRef(model/version/horizon/confidence/limitations)
```

Prediction ≠ FACT.

### Prescription

```text
objectives + constraints + candidate scenarios
→ optimizer/model/simulation adapter
→ trade-offs
→ recommendation/PREPARE
```

Recommendation ≠ authorization.

## 28. Operational Twin / Simulation Pattern

```text
live authoritative state refs
→ bounded twin projection
→ scenario branch
→ simulation
→ compare
```

`SIMULATED_STATE != PRODUCTION_STATE`. Apply always starts a new live read/revalidation/Decision/action context.

## 29. Edge / Offline Pattern

```text
central approved package/model/content
→ versioned deployment adapter
→ Edge device
→ bounded local inference/cache/event buffer
→ sync/reconcile
```

Offline modes explicit. Cache has revision/freshness. Loss of cloud never widens authority. Device identity != user identity. No free-form machine actuation.

## 30. AI Control Tower Pattern

Control Tower is a governance/query/command plane over asset projections:

```text
AIAsset registry projections
+ health/evals/cost/value/incidents/dependencies
+ rollout/kill-switch commands
```

It does not execute business actions merely because admin controls an asset and is not a second planner.

## 31. Model Lifecycle Pattern

```text
experiment/draft
→ eval
→ approval
→ deployment
→ monitor/drift
→ rollback/deprecate/revoke
```

Model Router only chooses approved/available models compatible with Compute Policy.

## 32. Capability Marketplace Pattern

```text
package manifest
→ review/security/evals
→ approved
→ publish
→ local enable/config/authorization
```

Install/enable never grants RBAC/provider scope. Executable packages require supply-chain controls.

## 33. Resilience

Each adapter defines timeout/retry/rate/concurrency/circuit breaker only where the boundary and failure semantics justify them.

Special cases:

- write retry != read retry;
- Edge sync handles clock/order/dedupe;
- A2A task handles timeout/cancel/duplicate;
- sandbox kills runaway workload;
- model unavailable/OOD degrades truthfully;
- RPA timeout after possible side effect is AMBIGUOUS until verified.

## 34. Result/Error Model

Canonical families are candidates to stabilize by contract when consumers exist; não criar catálogo especulativo apenas porque o nome aparece aqui.

```text
External*
EventSourceInvalid|Duplicate|Stale
DecisionInconclusive
Automation* errors
ProcessDataIncomplete
SemanticMetricUnknown|Conflict|Stale
MemoryDisabled|MemoryNotFound
SandboxBlocked|SandboxTimedOut|AnalysisFailed
ArtifactConflict|ArtifactUnauthorized
ModelUnavailable|ModelRevoked|PredictionOutOfDistribution
AgentNotApproved|ToolNotApproved|DelegationFailed
EdgeOffline|EdgeCacheStale|EdgePackageRevoked
MarketplaceAssetUnapproved|PackageIntegrityFailed
```

Provider-specific errors never leak raw SDK detail to UI/LLM.

## 35. Dependency Injection

Forbidden:

```text
UseCase creates SDK/client/worker directly
Planner instantiates executor/model/server
Controller owns business/retry/approval logic
MCP/RPA adapter calls planner
Sandbox receives production DB credentials
Edge device invents business permissions
DÉLIA bypasses Automation Hub technical boundary with ad hoc executor implementation
```

## 36. Bounded Contexts target

Candidates de bounded contexts, a congelar em C0 conforme owner/consumers/contracts reais:

```text
Conversation & Intelligence
Capability & Action Integration
Expertise & Playbooks
Knowledge
Personal Memory
Evidence & Provenance
Media & Interaction Sessions
External Information & Connections
Event & Operational Intelligence
Process Intelligence
Business Graph
Semantic Business Layer
Analysis & Artifacts
Predictive/Prescriptive & Scenario/Twin
Automation Integration & Orchestration
Work Management
Policy & Decision
Agent/Tool Interoperability
AI Asset/Model Governance
Edge/Offline Runtime Integration
Platform Experience
Observability & Evals
```

A bounded context name does not imply separate microservice. O Automation Hub permanece boundary de execução técnica, não bounded context interno da DÉLIA por default.

## 37. Abstraction Gate

**Obrigatório antes de criar qualquer interface/port/base/factory/strategy/registry/framework/repository/engine/service/shared module.**

Perguntar, nesta ordem:

1. existe boundary/owner/source of truth real?
2. existe consumer/variação real que justifique abstração?
3. existe lifecycle próprio ou test double necessário?
4. equivalente já existe no owner correto?
5. reduz coupling em vez de apenas esconder complexidade?
6. shared primitive/contrato mais simples já resolve?
7. provider/executor detail pode permanecer no adapter?
8. persistence é realmente necessária e owned pela DÉLIA?
9. credentials/data/identity permanecem bounded?
10. read/write, PREPARE/ACT e simulate/apply continuam separados?
11. sibling provider/executor/model funciona sem planner patch?
12. novo state duplica Domain/provider/Automation Hub truth?
13. um padrão mais simples resolve?
14. rollback/revoke/disable path existe?
15. cria permission authority acidentalmente?
16. depende de Chat ou internals de outro bounded context?
17. C0/phase atual permite criar essa abstração agora?

Se qualquer resposta material for negativa ou desconhecida, **não criar ainda**; classificar `TO_INVENTORY`, `PLANNED` ou exigir ADR conforme o caso.

“Might be useful later” is insufficient.

## 38. Anti-patterns

- Chat internals as DÉLIA library;
- god services/orchestrators;
- second business workflow/planner engine in Automation Hub/Control Tower/Marketplace;
- DÉLIA implementing ad hoc technical executor that bypasses Automation Hub ownership;
- Process Mining as hidden employee leaderboard;
- Graph as universal semantic model;
- Semantic Layer copying all data;
- Personal Memory as permission/business truth;
- MCP/A2A auto-trust;
- tool/agent prompt injection changing policy;
- sandbox as unrestricted corporate shell;
- artifact without lineage/version;
- model prediction as fact;
- twin scenario as production state;
- Edge offline broad permission cache;
- model/package install as authorization;
- RPA bot as business authority;
- planner with click/selector;
- one global L5 flag;
- free-form LLM→industrial machine.

## 39. Testing by layer

### Domain/Application

Pure Policy/Specification/lifecycle/use-case tests with fake ports only for abstractions that passaram pelo gate.

### Infrastructure

Contract/security tests for providers/executors/tools/agents/sandbox/models/Edge/storage, including timeout/error translation.

### Interfaces

Schema/auth/webhook/event/callback/upload/download/admin tests.

### Frontend

Source/Decision/Memory/Semantic/Artifact/Process/Control-Tower/Automation/Twin/Edge UX without credential leakage.

### Standalone

```text
NO_CHAT_IMPORT
NO_CHAT_API_DEP
NO_CHAT_DB_AUTHORITY
CHAT_OFFLINE_INDEPENDENCE
```

## 40. Migration Patterns

```text
EXPAND → compatible readers → writers → optional backfill → CUTOVER → CLEANUP
```

Adapters/versioned mappings handle provider/executor/model swaps. Definitions/models/packages are versioned; no silent mutation.

## 41. ADR / Exception Gate

Material deviation documents problem, evidence, alternatives, trade-offs, authority/privacy/security/reliability impact, migration/rollback and exit strategy.

## 42. FOUNDATION_FREEZE gates

At minimum:

```text
ARCHITECTURE_STYLE
DEPENDENCY_RULES
BOUNDED_CONTEXTS
PATTERN_DECISION_MATRIX
STATE/PERSISTENCE/ERROR/EVENT/RESILIENCE RULES
ABSTRACTION_GATE
MEDIA/BIOMETRIC/EXTERNAL BOUNDARIES
AUTOMATION/OUTCOME/AUTONOMY BOUNDARIES
PROCESS_INTELLIGENCE_BOUNDARY
AI_ASSET_GOVERNANCE_BOUNDARY
MCP_A2A_TRUST_BOUNDARY
PERSONAL_MEMORY_BOUNDARY
SEMANTIC_LAYER_BOUNDARY
SANDBOX_ARTIFACT_BOUNDARY
PREDICTIVE_TWIN_BOUNDARY
EDGE_OFFLINE_BOUNDARY
MODEL_MARKETPLACE_BOUNDARY
OT_SAFETY_BOUNDARY
CHAT_RUNTIME_DEPENDENCY=0
```

## 43. Regra final

```text
responsibility/owner/source first
→ consumers
→ contract
→ factual inventory
→ simplest canonical pattern
→ Abstraction Gate
→ adapter at volatile boundary
→ evidence/outcome truth
→ security/privacy/rollback
→ ADR only when materially needed
```

O objetivo é adicionar novos domínios, providers, tools, agents, models, executors e Edge targets sem reescrever planner, policy, core domain semantics ou UX foundation — e sem criar abstrações especulativas ou autoridades paralelas.
