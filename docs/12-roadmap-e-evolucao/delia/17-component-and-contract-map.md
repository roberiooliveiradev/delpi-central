# DÉLIA — Mapa de Componentes, Contratos e Ownership

**Status:** arquitetura canônica de ownership  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Specs temáticas:** `53–66`

> Este documento define **ownership e contratos alvo**. Ele não prova que um runtime, serviço, tabela, adapter ou capability já exista. Existência e estado atual devem ser classificados por evidência em `C0.S0` como `PROVEN`, `TO_INVENTORY`, `PLANNED` ou `TARGET` conforme o caso.

## 1. Owners canônicos

| Responsabilidade | Authority / owner | Proibido |
|---|---|---|
| corporate identity / SSO | Keycloak | shadow login/auth via biometric/device/memory |
| apps/routes/platform RBAC/governance | Core API | prompt/context/asset/provider scope granting platform permission |
| DELPI business rules/data/actions | Domain APIs/use cases | duplicar em DÉLIA/RPA/model |
| navigation/hosting/published host context | Portal | free URL/control from LLM; host context as permission authority |
| operational/intelligence context | DÉLIA over authorized refs/sources | second source of truth; context as authorization |
| DÉLIA UI | MFE próprio da DÉLIA; namespace técnico temporário `plugins/minha-delpi-copilot` | Chat MFE as base |
| DÉLIA runtime/persistence | API própria da DÉLIA; namespace técnico temporário `minha-delpi-copilot-api` | Chat API/tables/runtime authority |
| Business Action discovery | Domain OpenAPI + Action Catalog derivado pela DÉLIA | manual endpoint authority |
| Evidence/Source/Outcome | DÉLIA contracts + source authority | feature-specific duplicate truth |
| Business Graph | DÉLIA projection + domain source owners | graph as master database |
| Semantic Business Layer | DÉLIA semantic registry + metric business owners | LLM-invented KPI formula |
| Organizational Knowledge | DÉLIA Knowledge governance + source owners | auto-publish from memory/web/process |
| Personal Memory | user-owned DÉLIA memory context | memory as organizational truth/RBAC |
| Internet Research | DÉLIA orchestration + public source authority | unrestricted HTTP / cache truth |
| External resources/scopes | provider + connection owner | provider scope as Core/domain permission |
| Teams | Microsoft 365 source owner + DÉLIA adapter | Teams-specific DÉLIA runtime |
| biometrics | DÉLIA biometric boundary + Keycloak/Core `UserRef`, quando aprovado | match as login/permission |
| Human Observation | DÉLIA Evidence/governance + process owner | psychological/employee scoring |
| Event/Signal ingestion | source owner + DÉLIA adapter/EventEnvelope | event payload as permission/action |
| Decision Intelligence | DÉLIA Application/Policy + authoritative facts | LLM/RPA as sole formal rule when deterministic criteria exist |
| Process Intelligence | DÉLIA process projection + process/source owners | Process Mining as employee surveillance |
| Recurring Governed Work definition/lifecycle | DÉLIA Work/Policy | physical scheduler job state or schedule metadata as permission authority |
| Physical timer/scheduler trigger | platform/scheduler/execution owner proven in C0 | becoming DÉLIA Work/Policy/business authority |
| Automation capability mapping | DÉLIA Capability/Action projection + contrato semântico do executor | UI mechanics in planner |
| Automation decision/work orchestration | DÉLIA Policy/Decision/Work | second planner/workflow engine in executor |
| Automation technical execution | Automation Hub | DÉLIA, provider or bot becoming business/permission authority |
| RPA mechanics | Automation Hub / approved RPA adapter | bot as business authority |
| Computer-use mechanics | Automation Hub / sandboxed governed executor | unrestricted desktop/network |
| Outcome verification | authoritative Domain/provider/source + DÉLIA orchestration | technical success as business completion |
| Analysis Sandbox | DÉLIA analysis boundary or neutral execution platform if proven | general-purpose corporate shell |
| Artifact Workspace | DÉLIA artifact lifecycle/storage refs + collaboration owner | generated blob without lineage/ACL |
| Predictive models | model owner/provider + DÉLIA model adapters | prediction as fact/permission |
| Operational Twin | DÉLIA/domain scenario projection + authoritative sources | twin as source of truth |
| MCP tools | approved server owner + DÉLIA adapter/policy | discovery as approval |
| A2A agents | approved external agent owner + DÉLIA delegation policy | external agent as superior authority |
| AI Control Tower | DÉLIA governance/admin plane | admin role as business permission |
| Model lifecycle | model owner + DÉLIA governance/Control Tower | unversioned/unreviewed production model |
| Capability Marketplace | DÉLIA governance/catalog + asset publisher/owner | install as permission grant |
| Edge runtime | device/Edge platform owner + DÉLIA package/sync policy | offline as wider authority |
| OT/machine safety | industrial/safety owners | DÉLIA/Edge/RPA as safety controller |
| notifications | shared channel owner + DÉLIA orchestration | notification as proof of outcome |
| audit/evals | DÉLIA observability + platform audit | CoT/secrets/raw surveillance telemetry |

`Automation Hub` acima é a authority **semântica alvo para execução técnica**. `C0.S0/C0.S1` deve provar runtime existente, owner físico, contracts e gaps; falta de implementação comprovada vira `TO_INVENTORY/PLANNED`, não permissão para deslocar execução técnica para a DÉLIA.

O owner físico de timer/scheduler também é `TO_INVENTORY` até C0. A DÉLIA possuir `RecurringWorkDefinition` não significa possuir job runner/cron/lease/worker; inversamente, um scheduler existente não passa a possuir Work, Policy ou autorização.

## 2. Componentes físicos alvo

Namespaces técnicos planejados permanecem temporários até C0.S1:

```text
Portal Shell
Core API
Keycloak
Gateway
plugins/plugin-ui
plugins/minha-delpi-copilot
minha-delpi-copilot-api
Domain APIs / external providers / OT owners
Automation Hub
```

Dentro da API da DÉLIA, bounded modules podem incluir:

```text
Conversation / Understanding / Planner
Action Catalog / Capability Projection
Expertise / Playbooks / Knowledge
Personal Memory
Evidence / Policy / Decision
Durable Work / Task / Case / Watch
Recurring Governed Work / Scheduling definition & occurrence correlation
Event & Operational Intelligence
Process Intelligence
Business Graph
Semantic Business Layer
Internet Research / External Connections / Teams
Automation orchestration / executor integration
Analysis / Artifacts
Predictive / Prescriptive / Scenario/Twin
Agent/Tool Interoperability
AI Asset / Model Governance / Marketplace
Edge integration
Media / Biometric / Meeting / Frontline
Observability / Evals
```

**Module name does not imply microservice.** C0 decide physical split only from real ownership/consumers/scale/isolation needs. Um module de integração com automação ou scheduling não transforma a DÉLIA em owner da execução técnica do Automation Hub/scheduler.

## 3. Shared primitive registry

Preferir estas foundations canônicas como contratos alvo quando suficientes:

```text
CorrelationContext
EntityRef
RelationshipRef
SourceRef
EvidenceRef
OutcomeRef
WorkspaceContext
CapabilityProjection
DecisionGateRequest/Decision
WorkflowPlan/WorkflowStep
TaskRef/CaseRef
EventEnvelope/AuditEvent
```

A presença nesta lista **não prova implementação atual**. C0.S0 deve localizar definição, owner, consumers e evidência antes de reutilizar ou criar qualquer type.

Candidate refs somente se C0 provar necessidade transversal:

```text
MediaRef
Biometric refs
ExternalConnectionRef
AutomationExecutionRef / ExecutorRef
RecurringWorkRef / WorkOccurrenceRef
ProcessTraceRef
MetricDefinitionRef
MemoryItemRef
AnalysisRunRef
ArtifactRef
PredictionRef
ScenarioRef
AIAssetRef / ModelRef
EdgeDeviceRef
```

Do not create feature-specific duplicate Evidence/Event/Outcome/Workflow models.

## 4. Core producer → consumer graph

```text
Keycloak
→ authenticated identity / SSO context

Core API
→ apps/routes/platform permissions/governance context

Portal
→ bounded host/navigation/workspace context

Authorized Domain/External/Operational sources
→ DÉLIA operational/intelligence context

Domain/OpenAPI
→ Action Catalog / Capability Projection
→ Planner/Policy

Public/External/Domain/Edge Events
→ source adapters
→ SourceRef/EventEnvelope
→ Evidence/Watch/Workflow/Decision

RecurringWorkDefinition
→ approved physical scheduler/timer adapter
→ time occurrence signal
→ DÉLIA occurrence correlation/idempotency
→ live identity + Core/domain AuthZ + Policy/Decision
→ Durable Workflow

Business/Process data
→ Graph + Semantic Layer + Process Intelligence
→ grounded analysis

Decision
→ semantic capability
→ Durable Workflow
→ Automation Hub / approved executor adapter
→ technical result
→ authoritative Outcome verification
→ Evidence/Audit/Notification

Authorized data
→ Sandbox / Predictive / Scenario
→ Artifact/Prediction/Recommendation
→ PREPARE or governed Decision/ACT according to phase/capability
```

## 5. Semantic distinctions

```text
Graph = entity relations
Semantic Layer = metric/concept meaning
Process Intelligence = observed process behavior
Personal Memory = user-private continuity/preferences
Knowledge = governed reusable organizational/user knowledge
Recurring Governed Work = persistent bounded Work intent/lifecycle triggered by recurrence
Physical scheduler = technical timer/job trigger mechanism
Watch = condition/event observation product with phase-bounded modes
Operational Twin = scenario projection
Control Tower = governance projection
Marketplace = governed asset catalog
```

None substitutes source systems or each other.

## 6. Connection / source ownership

```text
USER_DELEGATED
ORG_MANAGED
SHARED_RESOURCE
SERVICE_CONNECTION
```

Personal/restricted source remains bounded. Provider scope does not mutate Core/domain permission.

## 7. Semantic capability graph

Examples:

```text
communication.email.send
billing.invoice.issue
maintenance.request.create
inventory.read
metric.query
process.mine
analysis.run
artifact.create
prediction.run
scenario.simulate
```

Planner asks for capability; approved adapters resolve provider/executor/model/tool without exposing UI mechanics.

Scheduling lifecycle (`create/list/pause/resume/cancel`) belongs ao Work product/use cases and must not be confused with business action authorization. Um timer fire não é semantic business capability permission.

## 8. Event / Decision ownership

```text
source event
→ authenticity/trust
→ EventEnvelope
→ dedupe/order/correlation
→ FAST|OPERATIONAL|REASONING
→ structured finding/decision candidate
```

Source event proves only its factual event, not authorization.

Time/schedule trigger is treated with the same authority discipline: it proves that an occurrence time was reached under the scheduler contract, **not** that ACT is authorized.

## 9. Process Intelligence ownership

```text
authoritative event logs
→ process projection/traces
→ variants/conformance/bottlenecks
→ Evidence
→ opportunity candidate
```

Process owner owns intended process and interpretation. DÉLIA does not infer employee fault/intent from deviation.

## 10. Semantic Business Layer ownership

Metric business owner approves definition. Data source owner remains authority for rows/entities.

```text
MetricDefinition
→ source query/calculation
→ value + definition version + Evidence
```

Metadata does not grant data access.

## 11. Personal Memory ownership

Memory belongs to user by default. DÉLIA manages lifecycle/retention/user controls. Memory influences relevance/presentation but never business truth, RBAC or Organizational Knowledge automatically.

## 12. Automation/executor ownership

Default executor preference:

```text
official API
→ native integration
→ deterministic function/script
→ RPA
→ governed computer-use
→ Human Task
```

DÉLIA works with semantic capabilities and governed Work/Decision. Automation Hub owns technical execution mechanics for executors under its boundary. A capability can migrate RPA→API without planner/workflow redesign.

Planner never receives clicks/selectors/package internals.

### 12.1 Recurring Work / scheduler ownership

Target contract:

```text
DÉLIA Work
owns:
- recurring definition intent/version/lifecycle
- owner/scope/capability/target refs
- occurrence correlation/idempotency refs
- Policy/Decision coordination
- Outcome/Evidence/Audit linkage

Physical scheduler/timer owner
owns:
- timer/job runtime
- trigger materialization mechanics
- job leases/heartbeats/technical retry state when applicable
- scheduler-specific HA/operational state
```

Boundary invariants:

```text
schedule != permission
stored intent != eternal authorization
scheduler identity != business actor
scheduler success != business Outcome
Recurring Work != Watch autonomous ACT
```

A material occurrence must re-resolve current user/service identity and revalidate live Core/domain AuthZ, Policy/Decision, provider/connection and source scope before ACT.

A scheduler implementation can be replaced by adapter/contract without changing Recurring Work domain semantics. C0 decides reuse versus adapter versus new implementation only after inventory and Abstraction Gate.

## 13. Outcome ownership

```text
technical result
→ OutcomeVerifier
→ authoritative source
→ VERIFIED_SUCCESS|VERIFIED_FAILURE|PENDING|INCONCLUSIVE
```

Notification does not prove completion.

## 14. Analysis / Artifact ownership

Sandbox executes bounded analysis over authorized inputs. Artifact Workspace owns artifact metadata/version/provenance/ACL and storage refs. Source data remains with source owner.

## 15. Predictive / Twin ownership

Model owner/provider owns model lifecycle facts; DÉLIA stores bounded `ModelRef`/Prediction lineage.

Operational Twin is a projection of authoritative live state. Scenario never becomes production state. Apply is new business action.

## 16. MCP/A2A ownership

MCP server/A2A agent remains external integration authority only for capabilities it exposes. DÉLIA owns allowlist/policy/delegation orchestration. Discovery/metadata/result cannot grant authority.

## 17. Control Tower / Model / Marketplace ownership

Control Tower aggregates governed projections and admin controls over assets; no second business planner.

Model lifecycle owns approval/eval/deployment/rollback/revoke metadata.

Marketplace owns package/catalog lifecycle. Manifest permissions/scopes are requirements, never grants.

## 18. Edge ownership

Device/Edge platform owns device runtime/health. DÉLIA owns approved package/content/model projection/sync semantics when applicable. User identity/permissions remain Keycloak/Core/domain authorities; offline cache cannot create indefinite authority.

## 19. Independence graph

Must remain true:

```text
DÉLIA ─X→ Chat runtime/API/tables
DÉLIA ─X→ Automation Hub technical internals as business authority
DÉLIA ─X→ physical scheduler technical internals as Work/permission authority
Automation Hub ─X→ business decision/permission authority
Scheduler/timer ─X→ business decision/permission/ACT authority
Timer tick ─X→ implicit ACT authority
Control Tower ─X→ domain permission authority
Process Mining ─X→ employee scoring authority
Memory ─X→ RBAC/business truth
Semantic Layer ─X→ source data authority
Sandbox ─X→ production DB credentials/unrestricted network
Twin ─X→ production state mutation
MCP/A2A ─X→ implicit trust
Marketplace ─X→ permission grant
Edge ─X→ offline authority expansion
RPA ─X→ business-rule authority
```

## 20. C0 ownership questions

Before any new component/schema/service:

```text
Who owns source truth?
Who approves meaning/rule/model/process?
Does canonical ref already represent it?
Is persistence content or only ref/projection?
Who owns credential/key/package?
Who owns recurring definition versus physical scheduler/job state?
What are timezone/DST/misfire/overlap semantics?
How is per-occurrence idempotency derived and persisted?
How are background identity and revocation revalidated at occurrence time?
Is this read, prepare, simulate or write?
What verifies the business outcome?
Does this create a new permission authority?
Can implementation be swapped by adapter?
What is the revoke/rollback/kill-switch path?
What happens when source/model/network/scheduler is stale/unavailable?
Could personal/employee data leak or become a score?
Could offline/simulation/tool/scheduler metadata widen authority?
```

Unknown = `TO_INVENTORY`; never infer implementation or readiness from a document/filename.

## 21. Stabilization order

```text
factual inventory
→ standalone boundary
→ authorities/bounded contexts
→ shared primitives
→ privacy/data/trust/state contracts
→ recurring Work/scheduler boundary freeze
→ architecture/test freeze
→ standalone bootstrap
→ capability foundations
→ read-only analysis/discovery
→ governed ACT/executors/recurring Work/artifacts
→ product governance/experience
→ selected advanced autonomy/Edge/Marketplace
```

No thematic capability may silently redefine frozen authorities.
