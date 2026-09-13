# Minha DELPI Copilot — Mapa de Componentes, Contratos e Ownership

**Status:** arquitetura canônica de ownership  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)  
**Specs temáticas:** `53–66`

## 1. Owners canônicos

| Responsabilidade | Authority / owner | Proibido |
|---|---|---|
| corporate identity | Keycloak + Core | shadow user via biometric/device/memory |
| platform permissions/apps/routes | Core API/RBAC | prompt/context/asset granting permission |
| DELPI business rules/data/actions | Domain APIs/use cases | duplicar em Copilot/RPA/model |
| navigation/hosting | Portal | free URL/control from LLM |
| Copilot UI | `plugins/minha-delpi-copilot` | Chat MFE as base |
| Copilot runtime/persistence | `minha-delpi-copilot-api` | Chat API/tables/runtime authority |
| Business Action discovery | Domain OpenAPI + Copilot derived Action Catalog | manual endpoint authority |
| Workspace Context | Portal/MFE/adapters | context as authorization |
| Evidence/Source/Outcome | Copilot contracts + source authority | feature-specific duplicate truth |
| Business Graph | Copilot projection + domain source owners | graph as master database |
| Semantic Business Layer | Copilot semantic registry + metric business owners | LLM-invented KPI formula |
| Organizational Knowledge | Copilot Knowledge governance + source owners | auto-publish from memory/web/process |
| Personal Memory | user-owned Copilot memory context | memory as organizational truth/RBAC |
| Internet Research | Copilot orchestration + public source authority | unrestricted HTTP / cache truth |
| External resources/scopes | provider + connection owner | provider scope as Core permission |
| Teams | Microsoft 365 source owner + Copilot adapter | Teams-specific Copilot runtime |
| biometrics | Copilot biometric subsystem + Core userRef | match as login/permission |
| Human Observation | Copilot Evidence/governance + process owner | psychological/employee scoring |
| Event/Signal ingestion | source owner + Copilot adapter/EventEnvelope | event payload as permission/action |
| Decision Intelligence | Copilot Application/Policy + authoritative facts | LLM/RPA as sole formal rule when deterministic criteria exist |
| Process Intelligence | Copilot process projection + process/source owners | Process Mining as employee surveillance |
| Automation capability mapping | Copilot/neutral platform owner decided in C0 | UI mechanics in planner |
| Automation execution | Automation bounded context/owner decided in C0 | second planner/workflow engine |
| RPA mechanics | RPA orchestrator/worker adapter owner | bot as business authority |
| Computer-use | sandboxed executor owner | unrestricted desktop/network |
| Outcome verification | authoritative Domain/provider/source + Copilot orchestration | technical success as business completion |
| Analysis Sandbox | Copilot analysis boundary or neutral execution platform if proven | general-purpose corporate shell |
| Artifact Workspace | Copilot artifact lifecycle/storage refs + collaboration owner | generated blob without lineage/ACL |
| Predictive models | model owner/provider + Copilot model adapters | prediction as fact/permission |
| Operational Twin | Copilot/domain scenario projection + authoritative sources | twin as source of truth |
| MCP tools | approved server owner + Copilot adapter/policy | discovery as approval |
| A2A agents | approved external agent owner + Copilot delegation policy | external agent as superior authority |
| AI Control Tower | Copilot governance/admin plane | admin role as business permission |
| Model lifecycle | model owner + Copilot governance/Control Tower | unversioned/unreviewed production model |
| Capability Marketplace | Copilot governance/catalog + asset publisher/owner | install as permission grant |
| Edge runtime | device/Edge platform owner + Copilot package/sync policy | offline as wider authority |
| OT/machine safety | industrial/safety owners | Copilot/Edge/RPA as safety controller |
| notifications | shared channel owner + Copilot orchestration | notification as proof of outcome |
| audit/evals | Copilot observability + platform audit | CoT/secrets/raw surveillance telemetry |

## 2. Componentes físicos alvo

Default owners remain:

```text
Portal Shell
Core API
Keycloak
Gateway
plugins/plugin-ui
plugins/minha-delpi-copilot
minha-delpi-copilot-api
Domain APIs / external providers / OT owners
```

Inside Copilot API, bounded modules may include:

```text
Conversation / Understanding / Planner
Action Catalog / Capability Projection
Expertise / Playbooks / Knowledge
Personal Memory
Evidence / Policy / Decision
Durable Work / Task / Case / Watch
Event & Operational Intelligence
Process Intelligence
Business Graph
Semantic Business Layer
Internet Research / External Connections / Teams
Automation & Execution orchestration
Analysis / Artifacts
Predictive / Prescriptive / Scenario/Twin
Agent/Tool Interoperability
AI Asset / Model Governance / Marketplace
Edge integration
Media / Biometric / Meeting / Frontline
Observability / Evals
```

**Module name does not imply microservice.** C0 decides physical split only from real ownership/consumers/scale/isolation needs.

## 3. Shared primitive registry

Prefer existing foundations:

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

Candidate refs only if C0 proves transversal need:

```text
MediaRef
Biometric refs
ExternalConnectionRef
AutomationExecutionRef / ExecutorRef
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
Keycloak/Core
→ authenticated user/service + platform authorization

Domain/OpenAPI
→ Action Catalog / Capability Projection
→ Planner/Policy

Public/External/Domain/Edge Events
→ source adapters
→ SourceRef/EventEnvelope
→ Evidence/Watch/Workflow/Decision

Business/Process data
→ Graph + Semantic Layer + Process Intelligence
→ grounded analysis

Decision
→ semantic capability
→ Durable Workflow
→ executor/tool/agent/model adapter
→ technical result
→ authoritative Outcome verification
→ Evidence/Audit/Notification

Authorized data
→ Sandbox / Predictive / Scenario
→ Artifact/Prediction/Recommendation
→ PREPARE/Decision only until governed ACT
```

## 5. Semantic distinctions

```text
Graph = entity relations
Semantic Layer = metric/concept meaning
Process Intelligence = observed process behavior
Personal Memory = user-private continuity/preferences
Knowledge = governed reusable organizational/user knowledge
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

Personal/restricted source remains bounded. Provider scope does not mutate Core permission.

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

Planner asks for capability; adapters resolve provider/executor/model/tool.

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

## 9. Process Intelligence ownership

```text
authoritative event logs
→ process projection/traces
→ variants/conformance/bottlenecks
→ Evidence
→ opportunity candidate
```

Process owner owns intended process and interpretation. Copilot does not infer employee fault/intent from deviation.

## 10. Semantic Business Layer ownership

Metric business owner approves definition. Data source owner remains authority for rows/entities.

```text
MetricDefinition
→ source query/calculation
→ value + definition version + Evidence
```

Metadata does not grant data access.

## 11. Personal Memory ownership

Memory belongs to user by default. Copilot manages lifecycle/retention/user controls. Memory influences relevance/presentation but never business truth, RBAC or Organizational Knowledge automatically.

## 12. Automation/executor ownership

Default executor preference:

```text
official API
→ native integration
→ deterministic function/script
→ RPA
→ computer-use
→ Human Task
```

Capability can migrate RPA→API without planner/workflow redesign.

Planner never receives clicks/selectors/package internals.

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

Model owner/provider owns model lifecycle facts; Copilot stores bounded `ModelRef`/Prediction lineage.

Operational Twin is a projection of authoritative live state. Scenario never becomes production state. Apply is new business action.

## 16. MCP/A2A ownership

MCP server/A2A agent remains external integration authority only for capabilities it exposes. Copilot owns allowlist/policy/delegation orchestration. Discovery/metadata/result cannot grant authority.

## 17. Control Tower / Model / Marketplace ownership

Control Tower aggregates governed projections and admin controls over assets; no second business planner.

Model lifecycle owns approval/eval/deployment/rollback/revoke metadata.

Marketplace owns package/catalog lifecycle. Manifest permissions/scopes are requirements, never grants.

## 18. Edge ownership

Device/Edge platform owns device runtime/health. Copilot owns approved package/content/model projection/sync semantics when applicable. User identity/permissions remain central/domain authorities; offline cache cannot create indefinite authority.

## 19. Independence graph

Must remain true:

```text
Copilot ─X→ Chat runtime/API/tables
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
Is this read, prepare, simulate or write?
What verifies the business outcome?
Does this create a new permission authority?
Can implementation be swapped by adapter?
What is the revoke/rollback/kill-switch path?
What happens when source/model/network is stale/unavailable?
Could personal/employee data leak or become a score?
Could offline/simulation/tool metadata widen authority?
```

Unknown = `NOT_PROVEN`.

## 21. Stabilization order

```text
factual inventory
→ standalone boundary
→ authorities/bounded contexts
→ shared primitives
→ privacy/data/trust/state contracts
→ architecture/test freeze
→ standalone bootstrap
→ capability foundations
→ read-only analysis/discovery
→ governed writes/executors/artifacts
→ product governance/experience
→ selected advanced autonomy/Edge/Marketplace
```

No thematic capability may silently redefine frozen authorities.
