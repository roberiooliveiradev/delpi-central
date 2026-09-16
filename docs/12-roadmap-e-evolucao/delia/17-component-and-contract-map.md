# DÉLIA — Mapa de Componentes, Contratos e Ownership

**Status:** arquitetura canônica de ownership
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)
**State:** [`21-data-and-state-model.md`](./21-data-and-state-model.md)
**Specs temáticas:** `53–66`

> Este documento define **ownership e contratos alvo**. Ele não prova que um runtime, serviço, tabela, adapter ou capability já exista. Existência e estado atual devem ser classificados por evidência como `PROVEN`, `TO_INVENTORY`, `PLANNED` ou `TARGET` conforme o caso.
> **C0.S2-T1 (histórico):** matriz de authorities/bounded contexts foi persistida como `FROZEN_CANDIDATE` / `CANDIDATE_FOR_ARCHITECTURE_REVIEW`.
> **C0.S2-T2:** `ARCHITECTURE_REVIEW_C0_S2` sobre `REVIEWED_HEAD=8bae12a250f2362603211a93c65bb098b8b1e9aa`, `VERDICT=ACCEPT_WITH_RESIDUAL`; `AUTHORITY_MAP=FROZEN_ACCEPTED`; `BOUNDED_CONTEXT_MAP=FROZEN_ACCEPTED`; `C0.S2=APPROVED`; `C0.S3_AUTHORIZED=YES`; `FOUNDATION_FREEZE=NOT APPROVED`; `DÉLIA_RUNTIME_DIFF=NONE`.

## 1. Owners canônicos

| Responsabilidade | Authority / owner | Proibido |
|---|---|---|
| corporate identity / SSO | Keycloak | shadow login/auth via biometric/device/memory |
| apps/routes/platform RBAC/governance | Core API | prompt/context/asset/provider scope granting platform permission |
| DELPI business rules/data/actions | Domain APIs/use cases | duplicar em DÉLIA/RPA/model |
| navigation/hosting/published host context | Portal | free URL/control from LLM; host context as permission authority |
| operational/intelligence context | DÉLIA over authorized refs/sources | second source of truth; context as authorization |
| DÉLIA UI | MFE próprio da DÉLIA; path `plugins/delia/` (`FROZEN_ACCEPTED` C0.S1) | Chat MFE as base |
| DÉLIA runtime/persistence | API própria da DÉLIA; path `delia-api/` (`FROZEN_ACCEPTED` C0.S1) | Chat API/tables/runtime authority |
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

`Automation Hub` acima é a authority **semântica alvo para execução técnica**. Runtime físico compartilhado permanece `NOT_PROVEN` / `TO_INVENTORY` / `DEFERRED` (C0.S0-D); falta de implementação comprovada **não** autoriza deslocar execução técnica para a DÉLIA.

O owner físico de timer/scheduler permanece `TO_INVENTORY`. A DÉLIA possuir `RecurringWorkDefinition` não significa possuir job runner/cron/lease/worker; inversamente, um scheduler existente não passa a possuir Work, Policy ou autorização.

## 2. Componentes físicos alvo

C0.S1 freeze aceito (`PLANNED / FROZEN_ACCEPTED`; autoridade de naming: `68`; review em `c822f0e72495256c3459a4b36b9c37a3bba95cbb`):

```text
Portal Shell
Core API
Keycloak
Gateway
plugins/plugin-ui
plugins/delia                 # MFE; container delpi-delia; /apps/delia
delia-api                     # API; container delpi-delia-api; /apps/delia-api/
Domain APIs / external providers / OT owners
Automation Hub                # technical execution boundary TARGET; physical runtime deferred
```

Histórico supersedido como target ativo: `plugins/minha-delpi-copilot`, `minha-delpi-copilot-api`.

### 2.1 Physical ownership freeze accepted (C0.S1)

```text
delia-api standalone boundary          = APPROVED
plugins/delia standalone boundary      = APPROVED
own migration ownership                = APPROVED (delia-api/migrations/; ns=delia)
separate DÉLIA admin service           = REJECTED (same API+MFE; conceptual /admin namespaces)
separate Control Tower service         = REJECTED (MODULE_IN_DELIA)
separate Process Intelligence service  = REJECTED (MODULE_IN_DELIA)
neutral shared Sandbox platform now    = REJECTED (DÉLIA analysis + isolated adapter deferred)
DÉLIA-owned Edge runtime               = REJECTED (ADAPTER_BOUNDARY + external/device owner)
Automation Hub inside DÉLIA            = REJECTED
Automation Hub external exec boundary  = APPROVED_TARGET (physical runtime deferred)
callbacks/webhooks ownership           = APPROVED_TARGET (/apps/delia-api/callbacks|webhooks/*; handlers deferred)

MODULE NAME != MICROSERVICE JUSTIFICATION
```

PostgreSQL cluster placement físico = `DEFERRED` (reuse de cluster ≠ ownership lógico).

### 2.2 Integration contract anchors (later C0 — no OpenAPI now)

| Boundary | OWNER | CONSUMER | DIRECTION | AUTHORITY | R/W character | TRUST BOUNDARY | CONTRACT_REQUIRED_LATER | CURRENT STATUS |
|---|---|---|---|---|---|---|---|---|
| DÉLIA ↔ Keycloak | Keycloak | DÉLIA API | AuthN inbound | identity/SSO | read identity | corporate IdP | YES | TARGET |
| DÉLIA ↔ Core | Core | DÉLIA API | AuthZ/apps/routes | platform RBAC/governance | read effective perms + app registry | Core SoT | YES | TARGET (semantics accepted) |
| Portal ↔ DÉLIA MFE | Portal host / DÉLIA MFE | Portal↔MFE | host mount + published context | Portal≠AuthZ/planner | context publish / UX | host boundary | YES | TARGET |
| DÉLIA ↔ Domain APIs | Domain API | DÉLIA API | HTTP/event/adapter | Domain business AuthZ + data | governed R/W | Domain SoT | YES | TARGET |
| DÉLIA ↔ Automation Hub | Hub (exec) / DÉLIA (orch) | both | orchestration→execution | Hub technical lifecycle | exec commands + status | exec trust | YES | TARGET; physical deferred |
| DÉLIA ↔ external providers | provider + DÉLIA adapter | DÉLIA API | outbound/inbound callbacks | provider scopes ≠ Core perms | governed R/W | egress/trust | YES | TARGET |
| DÉLIA ↔ OT / industrial | OT/safety owner | DÉLIA (adapter only) | never safety control | OT/safety independent | read/prepare bounded | safety airgap | YES | TARGET; Edge deferred |

### 2.3 C0.S2 — Authorities / bounded contexts freeze accepted

```text
STATUS = FROZEN_ACCEPTED
REVIEW = ARCHITECTURE_REVIEW_C0_S2
REVIEWED_HEAD = 8bae12a250f2362603211a93c65bb098b8b1e9aa
VERDICT = ACCEPT_WITH_RESIDUAL
C0.S0 = APPROVED
C0.S1 = APPROVED
C0.S2 = APPROVED
AUTHORITY_MAP = FROZEN_ACCEPTED
BOUNDED_CONTEXT_MAP = FROZEN_ACCEPTED
C0.S3_AUTHORIZED = YES
FOUNDATION_FREEZE = NOT APPROVED
NEW_RUNTIME_ABSTRACTIONS = NONE
SHARED_PRIMITIVES = DEFERRED_TO_C0_S3
DÉLIA_RUNTIME_DIFF = NONE
BLOCKERS = NONE
EXECUTION_DRIFT = NONE
```

C0.S2 congela **boundaries de responsabilidade**. Não inventa schemas/ports/adapters/engines/packages/shared primitives.

#### 2.3.1 Top-level authorities

```text
Keycloak          = identity / authentication / SSO
Core              = apps + routes + effective platform RBAC + governance
Domain APIs       = business data + business rules + final domain authorization + authoritative postconditions
Portal            = host + navigation + published bounded context
DÉLIA             = intelligence + Evidence coordination + Policy + Decision + Work + orchestration + Outcome coordination
Automation Hub    = technical execution lifecycle
External providers= external resources / provider-side authority
OT / Safety       = machine / industrial / safety authority
```

Nenhum colocation, token, provider scope, model output, memory, scheduler, Graph, Edge cache ou projection transfere essas authorities.

#### 2.3.2 Required invariants

```text
Keycloak != authorization authority
JWT != final permission
Core = effective platform RBAC
Domain APIs = final business authorization
Portal context != permission
DÉLIA != domain source of truth
Evidence != source of truth
DÉLIA Work/orchestration != Automation Hub technical execution
scheduler/timer != Work authority
schedule != permission
provider scope != Core/domain permission
Personal Memory != authority
prediction != FACT
recommendation != authorization
simulate != apply
PREPARE != ACT
technical execution success != business Outcome
Edge offline != expanded authority
biometric match != authentication
biometric match != authorization
DÉLIA != safety controller
Control Tower != second planner
Control Tower != permission authority
Business Graph != source of truth
Semantic Layer != source of truth
Process Intelligence != process business authority
```

#### 2.3.3 Bounded context matrix (36)

| # | RESPONSIBILITY | OWNER | CANONICAL SOURCE | CONSUMERS | AUTHORITY BOUNDARY | INTEGRATION | STATUS | CONTRACT_REQUIRED_LATER |
|---|---|---|---|---|---|---|---|---|
| 1 | Identity / Authentication | Keycloak | corporate identity / SSO | Core / Portal / DÉLIA / Domain APIs | identity only; JWT≠final permission | OIDC/JWT inbound | PROVEN platform; DÉLIA integration PLANNED | YES |
| 2 | Platform RBAC / Apps / Routes | Core | effective permission context + app registry | Portal / DÉLIA | no parallel RBAC in DÉLIA; `/me/apps`→`apps[].routes`; `/me/routes` NOT_CURRENT | Core HTTP | PROVEN platform; DÉLIA consumer PLANNED | YES |
| 3 | Domain business data / rules | each Domain API / business owner | authoritative Domain API | DÉLIA + authorized clients | final domain AuthZ in Domain; no Domain DB/imports | HTTP/event/adapter | PROVEN Domains; DÉLIA consumer PLANNED | YES |
| 4 | Portal hosting / nav / context | Portal | host + navigation + bounded published context | DÉLIA MFE | context=hint≠permission; Portal≠Work/planner/Evidence | federation/host contract | PROVEN host; DÉLIA mount PLANNED | YES |
| 5 | Conversation / Intelligence | DÉLIA | authorized sources + DÉLIA-owned interaction state | DÉLIA surfaces / Work / reasoning | conversation≠Domain SoT | internal DÉLIA modules | TARGET | YES (internal+source) |
| 6 | Evidence / Provenance | DÉLIA (coordination) | original authoritative source owner | analysis / Decision / Work / UX / audit | Evidence≠source authority; Evidence access≠source grant | refs + source contracts | TARGET | YES |
| 7 | Policy / Decision | DÉLIA | Core + Domain + source facts + approved policies | Work / UX / audit | Policy≠Core RBAC≠Domain AuthZ; rec≠AuthZ; Gate≠permission grant | Decision Gate contracts | TARGET | YES |
| 8 | Durable Work / Task / Case | DÉLIA | DÉLIA Work lifecycle | surfaces / Hub binding / Outcome | Work≠technical worker/executor state | Work lifecycle + adapters | TARGET | YES |
| 9 | Recurring Governed Work | DÉLIA (definition/lifecycle) | DÉLIA Work + Policy | scheduler adapter / occurrence / Decision | schedule≠permission; recurrence≠executor authority | definition + occurrence correlation | TARGET | YES |
| 10 | Physical scheduler / timer | TO_INVENTORY | technical occurrence / timer / trigger only | DÉLIA occurrence consumer | timer≠Work/Policy/permission/Decision | timer→signal only | TO_INVENTORY | YES |
| 11 | Automation / executor integration | DÉLIA (semantic orch/binding) | semantic capability → approved execution contract | Automation Hub / executors | semantic≠UI mechanics | capability→executor contract | TARGET | YES |
| 12 | Automation Hub technical execution | Automation Hub boundary | worker/executor/queue/technical lifecycle | DÉLIA (status/correlation) | Hub≠planner≠business AuthZ≠Work SoT; no copy of Hub tech state as DÉLIA truth | execution API/events | TARGET; physical TO_INVENTORY | YES |
| 13 | Outcome verification | DÉLIA (coordination); truth = Domain/provider/source | authoritative postcondition | Work / audit / UX | technical success≠business Outcome | postcondition verify | TARGET | YES |
| 14 | Business Graph | DÉLIA projection/intelligence | Domain/source owners | analysis / Decision / UX | Graph=relational projection≠master data/DW/SoT | projection refresh from owners | TARGET | YES |
| 15 | Semantic Business Layer | DÉLIA registry/projection/orch | metric/business owner + Domain/BI data authority | query / Decision / UX | DÉLIA≠KPI formula owner by default; Semantic≠SoT | MetricDefinition contracts (later) | TARGET | YES |
| 16 | Organizational Knowledge | DÉLIA knowledge governance | document/procedure/process owner | retrieval / Work / UX | indexing≠ownership transfer; Evidence→candidate→review→publish | Knowledge lifecycle | TARGET | YES |
| 17 | Personal Memory | DÉLIA user-scoped personalization | approved user-scoped memory candidates | UX / ranking | PM≠Org Knowledge≠business truth≠permission | memory lifecycle | TARGET | YES |
| 18 | Internet Research | DÉLIA orchestration | external source/site | Evidence / UX | external=untrusted; no policy/RBAC/Gate/system mutation | safe-fetch/search | TARGET | YES |
| 19 | External connections / providers | external provider + resource owner; DÉLIA=adapter/orch | provider resources/scopes | Evidence / Work / connectors | provider scope≠Core/Domain permission; secrets out of prompt/memory/MFE/logs | OAuth/connection lifecycle | TARGET; physical TO_INVENTORY | YES |
| 20 | Microsoft Teams | Microsoft 365; DÉLIA=adapter/orch | Teams/Graph resources | Meeting / Evidence / UX | Teams≠separate planner/product authority | M365 connector | TARGET | YES |
| 21 | Media | capture/source owner (raw); DÉLIA=intelligence/Evidence/media processing when approved | capture/source | Evidence / Meeting / Frontline | raw media≠Knowledge by default; storage owner TO_INVENTORY | media adapters | TARGET; storage TO_INVENTORY | YES |
| 22 | Biometric Identity | DÉLIA governed optional; corporate identity=Keycloak/Core UserRef | enrolled closed-set templates | Meeting / Frontline Evidence | match≠login≠AuthN≠AuthZ; unknown=unknown; template store TO_INVENTORY | biometric capability | TARGET | YES |
| 23 | Human Observation | DÉLIA Evidence/governance + process owner | observable process facts only | Evidence / Process | no personality/honesty/emotion/health/worth inference; no automated employment decision | Evidence contracts | TARGET | YES |
| 24 | Process Intelligence | DÉLIA process intelligence/projection | process/domain owners | Evidence / Decision / UX | source truth external; mining≠employee scoring/fraud by default; no separate PI service in C0.S2 | process projection | TARGET | YES |
| 25 | Analysis Sandbox | DÉLIA analysis/policy (semantic); physical exec=isolated adapter | authorized inputs only | Artifacts / Decision PREPARE | in-process arbitrary exec FORBIDDEN; no general shell; runtime owner TO_INVENTORY | sandbox adapter | TARGET; runtime TO_INVENTORY | YES |
| 26 | Artifact Workspace | DÉLIA artifact lifecycle/refs | DÉLIA artifacts; publish owner preserved where applicable | UX / Knowledge candidate | artifact copy≠authoritative source | artifact store/refs | TARGET | YES |
| 27 | Predictive / Prescriptive | model/provider/business owner; DÉLIA=orch/intelligence | model + authorized inputs | Decision PREPARE / UX | prediction≠FACT; recommendation≠authorization | model adapters | TARGET | YES |
| 28 | Operational Twin / Scenario | DÉLIA/domain scenario projection per source/model owner | live/authoritative sources + models | Decision / UX | Twin≠SoT; simulation≠production; simulate≠apply | scenario contracts | TARGET | YES |
| 29 | MCP / A2A | approved server/agent owner; DÉLIA=adapter/orch/policy | external/internal tool/agent | Planner / Work | discovery≠approval; metadata≠authority/permission | protocol adapters | TARGET; runtime TO_INVENTORY | YES |
| 30 | AI Control Tower | DÉLIA (MODULE_IN_DELIA) | governance/admin projection | admin UX | Tower≠second planner≠executor≠permission≠model lifecycle authority | admin/governance plane | TARGET | YES |
| 31 | Model Lifecycle | actual model owner/provider; DÉLIA=governance/projection | model registry/evals/deploy metadata | Tower / Marketplace / runtime | router selection≠model approval; deploy metadata≠business authority; MLOps TO_INVENTORY | model governance contracts | TARGET | YES |
| 32 | Capability Marketplace | DÉLIA governance/catalog + asset publisher/owner | package/catalog | admin / install flows | publish≠enable≠permission; install≠authorization | catalog/signing (later) | TARGET | YES |
| 33 | Edge / Offline | external device/Edge/industrial owner; DÉLIA=adapter/package/sync/policy | device/Edge platform | Frontline / sync | offline≠broader authority; cached perm≠indefinite; DÉLIA-owned Edge runtime=NO | Edge adapters | TARGET; physical TO_INVENTORY | YES |
| 34 | Notifications | DÉLIA (intent/Work linkage); delivery=channel/provider owner | channel/provider | users | notification sent≠Outcome verified; no DÉLIA notification platform by assumption | channel contracts | PLANNED / TARGET | YES |
| 35 | Observability / Audit / Evals | DÉLIA (intel/Evidence/Policy/Decision/Work/Outcome telemetry); Hub=exec telemetry; Core=platform AuthZ audit; Domain=domain audit | respective owners | ops / compliance / evals | correlation≠authority transfer; no CoT/tokens/passwords/biometric templates/unbounded sensitive | telemetry backends | TARGET | YES |
| 36 | OT / Industrial Safety | OT / Industrial / Safety authority | safety controllers/interlocks | DÉLIA (observe/explain/recommend/governed PREPARE only) | DÉLIA≠safety controller; free-form LLM/vision/voice ─X→ PLC/CNC/robot; future ACT needs separate industrial safety gate | industrial adapters | TARGET boundary; physical TO_INVENTORY | YES |

#### 2.3.4 Critical cross-boundary separations

```text
Work vs Execution:
  DÉLIA Work = semantic/business/intelligence orchestration lifecycle
  Automation Hub = technical execution lifecycle
  ExecutionRef in DÉLIA = correlation/projection only (not executor technical truth)

Recurring Work vs Scheduler:
  Recurring Work definition = DÉLIA
  physical timer = external technical mechanism (TO_INVENTORY)
  timer → signal; signal != authorization

Technical Result vs Outcome:
  technical result → authoritative postcondition → Outcome

Graph vs Semantic vs Process vs Twin:
  Business Graph = relationships
  Semantic Layer = business meaning / metrics
  Process Intelligence = observed process behavior
  Operational Twin / Scenario = simulated/projected state
  (not interchangeable; none = master data)

Personal vs Organizational Knowledge:
  Personal Memory != Organizational Knowledge
  Conversation history != Personal Memory
  Session context != Personal Memory
  Candidate knowledge != published organizational knowledge
```

#### 2.3.5 Boundary integration rule

Bounded contexts integram somente via:

```text
HTTP/API contract
OR real event with explicit owner/source/schema
OR approved provider/executor adapter
```

Proibido:

```text
internal imports across bounded contexts
foreign database reads/writes
shared tables as integration
duplicated authorization
implicit permission propagation
frontend permission enforcement as final authority
```

#### 2.3.6 Event rule

Não inventar broker. Não criar `EventEnvelope` implementation em C0.S2.

Event integration é permitida quando existir evento real com: source, owner, schema, timestamp, correlation, idempotency/dedup quando necessário, retention, consumer, contract.

Central event broker físico = `TO_INVENTORY` unless proven elsewhere.

#### 2.3.7 Abstraction Gate (C0.S2)

```text
NEW_RUNTIME_ABSTRACTIONS = NONE
```

C0.S2 **não** cria: service, microservice, port/adapter implementation, registry, repository, engine, shared package, schema, primitive, database, queue, worker, scheduler.

Physical names de C0.S1 permanecem aceitos. Shared primitives = C0.S3.

### 2.4 TO_INVENTORY (explicit — do not resolve by assumption)

```text
physical scheduler/timer owner
physical Automation Hub runtime
DÉLIA ↔ Core exact API contract
DÉLIA ↔ Portal exact context/host contract
event broker/transport (if any)
external OAuth connection lifecycle / secret owner mechanism
Teams registration/scopes/webhooks
media storage/capture/retention
biometric enrollment/template store
Process Mining runtime / event-log readiness
Sandbox isolated runtime
Artifact physical/object storage where needed
predictive/model inference runtimes
Twin/optimization runtime
MCP/A2A concrete implementations
model registry/MLOps platform
Marketplace distribution/signing runtime
Edge/MDM/offline sync
OT actuation/safety architecture
notification delivery contracts
observability/eval backend
physical Postgres placement (deferred by C0.S1)
```

### 2.5 PLANNED / TARGET (documentation ≠ runtime proof)

Capabilities abaixo permanecem `TARGET`/`PLANNED` — **nenhum runtime PASS** por esta documentação:

```text
Conversation/Intelligence, Evidence, Policy/Decision, Durable Work, Recurring Work,
Business Graph, Semantic Layer, Knowledge, Personal Memory, Internet Research,
External Connections, Teams, Media, Biometrics, Human Observation, Process Intelligence,
Sandbox, Artifacts, Predictive, Prescriptive, Twin, MCP/A2A, Control Tower,
Model governance, Marketplace, Edge, Notification orchestration, DÉLIA observability/evals
```

### 2.6 Contracts required later (C0.S5 detail; anchors only)

Expande §2.2. Cada linha: OWNER / CONSUMER / DIRECTION / AUTHORITY / R/W / TRUST / CONTRACT_REQUIRED_LATER=YES / STATUS.

| Boundary | OWNER | CONSUMER | DIRECTION | AUTHORITY | R/W | TRUST | STATUS |
|---|---|---|---|---|---|---|---|
| DÉLIA ↔ Keycloak | Keycloak | DÉLIA API | AuthN inbound | identity/SSO | R identity | IdP | TARGET |
| DÉLIA ↔ Core | Core | DÉLIA API | AuthZ/apps/routes | platform RBAC | R effective perms | Core SoT | TARGET |
| Portal ↔ DÉLIA | Portal / DÉLIA MFE | both | host+context | Portal≠AuthZ | context/UX | host | TARGET |
| DÉLIA ↔ Domain APIs | Domain API | DÉLIA API | HTTP/event/adapter | Domain AuthZ+data | governed R/W | Domain SoT | TARGET |
| DÉLIA ↔ physical scheduler | scheduler owner (TBD) | DÉLIA | timer→signal | timer≠AuthZ | signal only | exec trust | TO_INVENTORY |
| DÉLIA ↔ Automation Hub | Hub / DÉLIA orch | both | orch→exec | Hub technical | exec+status | exec trust | TARGET; physical TO_INVENTORY |
| DÉLIA ↔ internet/safe-fetch/search | DÉLIA orch + source | DÉLIA | egress read | untrusted content | R | egress | TARGET |
| DÉLIA ↔ providers/OAuth | provider + DÉLIA | DÉLIA | OAuth/API | scope≠Core perm | governed R/W | provider trust | TARGET; secrets TO_INVENTORY |
| DÉLIA ↔ Microsoft 365 / Teams | M365 | DÉLIA | Graph/Teams | Teams≠planner | governed R/W | tenant | TARGET |
| DÉLIA ↔ media/device sources | capture/source owner | DÉLIA | media ingest | raw≠Knowledge | R/process | device/consent | TARGET; storage TO_INVENTORY |
| DÉLIA ↔ biometric capability | DÉLIA + Keycloak/Core UserRef | DÉLIA | match evidence | match≠AuthN/Z | R evidence | enrollment trust | TARGET; template TO_INVENTORY |
| DÉLIA ↔ Process sources | process/domain owners | DÉLIA | event-log ingest | source truth external | R | source | TARGET |
| DÉLIA ↔ Sandbox runtime | isolated runtime owner (TBD) | DÉLIA | analysis exec | no general shell | bounded exec | isolation | TO_INVENTORY |
| DÉLIA ↔ Artifact store/publication | DÉLIA + publish owner | both | artifact lifecycle | copy≠SoT | R/W refs | storage ACL | TARGET |
| DÉLIA ↔ model/predictive runtimes | model owner/provider | DÉLIA | inference | pred≠FACT | R/invoke | model trust | TARGET |
| DÉLIA ↔ MCP/A2A | server/agent owner | DÉLIA | tool/agent call | discovery≠approval | governed | remote trust | TARGET; runtime TO_INVENTORY |
| DÉLIA ↔ Marketplace asset owners | publisher + DÉLIA gov | both | catalog/install | install≠AuthZ | R/W catalog | supply chain | TARGET |
| DÉLIA ↔ notification channels | channel/provider owner | DÉLIA | notify | sent≠Outcome | W notify | channel | PLANNED/TARGET |
| DÉLIA ↔ Edge | device/Edge owner | DÉLIA | sync/adapter | offline≠↑AuthZ | bounded | device | TARGET; physical TO_INVENTORY |
| DÉLIA ↔ OT/industrial | OT/safety owner | DÉLIA | observe/PREPARE only | DÉLIA≠safety ctrl | R/PREPARE | safety airgap | TARGET; physical TO_INVENTORY |
| DÉLIA ↔ observability/audit | respective owners | ops | telemetry | corr≠authority | W telemetry | redaction | TARGET |

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

## 3. Shared primitive registry — C0.S3 freeze candidate

> Canonical semantics: [`21-data-and-state-model.md`](./21-data-and-state-model.md) §4.
> Status: `FROZEN_CANDIDATE` / `CANDIDATE_FOR_ARCHITECTURE_REVIEW`. Não prova runtime. Não autoriza C0.S4.

```text
REUSED_EXISTING:
  CorrelationContext, EntityRef, UserRef, ServiceActorRef, DeviceRef,
  SourceRef, EvidenceRef, OutcomeRef, EventEnvelope
  (+ RelationshipRef, TaskRef/CaseRef, DecisionGate*, Workflow*, AuditEvent when already justified)

CapabilityProjection = PROJECTION_ONLY
  (≠ permission / business / executor-registry / provider-metadata / Hub SoT)

ACCEPTED_SHARED (refs only; no code/tables):
  MetricDefinitionRef, ArtifactRef, PredictionRef, ScenarioRef,
  AutomationExecutionRef, RecurringWorkRef, WorkOccurrenceRef, ModelRef

NOT_PROMOTED:
  ProcessTraceRef = REFERENCE_ONLY
  MemoryItemRef = DOMAIN_LOCAL_ONLY (Personal Memory)
  AnalysisRunRef = REJECT_ABSTRACTION (use CorrelationContext.analysisRunId + Source/Evidence/Artifact refs)
  ExecutorRef = DEFER_TO_CONTRACT (C0.S5); AutomationExecutionRef suffices now
  AIAssetRef = PROJECTION_ONLY + DEFER_BY_PHASE detail
  EdgeDeviceRef = REUSE DeviceRef

REJECTED_META:
  UniversalRef, GenericBusinessObjectRef, GenericExecutionObject,
  GenericAIObject, GenericAssetRef

WorkspaceContext shape = DEFER_TO_CONTRACT (C0.S5)
NEW_RUNTIME_ABSTRACTIONS = NONE
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

A scheduler implementation can be replaced by adapter/contract without changing Recurring Work domain semantics. C0 decide reuse versus adapter versus new implementation only after inventory and Abstraction Gate.

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