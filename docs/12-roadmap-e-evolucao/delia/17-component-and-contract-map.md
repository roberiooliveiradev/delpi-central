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

## 3. Shared primitive registry — C0.S3 shared/reference semantics freeze accepted

> Canonical semantics: [`21-data-and-state-model.md`](./21-data-and-state-model.md) §4.
> Status: `FROZEN_ACCEPTED` / `APPROVED` via `ARCHITECTURE_REVIEW_C0_S3` (`REVIEWED_HEAD=641ffc07284b98ffbdb5e13217ce214c4ad8ebb0`; `VERDICT=ACCEPT_WITH_RESIDUAL`). Não prova runtime. `FOUNDATION_FREEZE=NOT APPROVED`.

```text
REVIEW = ARCHITECTURE_REVIEW_C0_S3
REVIEWED_HEAD = 641ffc07284b98ffbdb5e13217ce214c4ad8ebb0
VERDICT = ACCEPT_WITH_RESIDUAL
C0.S3 = APPROVED
SHARED_REFERENCE_SEMANTICS = FROZEN_ACCEPTED
C0.S4 = APPROVED
ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY = FROZEN_ACCEPTED
C0.S5 = APPROVED
INTEGRATION_CONTRACTS = FROZEN_ACCEPTED
C0.S6_AUTHORIZED = YES
FOUNDATION_FREEZE = NOT APPROVED
DÉLIA_RUNTIME_DIFF = NONE
NEW_RUNTIME_ABSTRACTIONS = NONE

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
  ExecutorRef = CLOSED_NONISSUE (C0.S5); contract-local executionOwnerRef/executorClass; AutomationExecutionRef suffices
  AIAssetRef = PROJECTION_ONLY + DEFER_BY_PHASE detail
  EdgeDeviceRef = REUSE DeviceRef

REJECTED_META:
  UniversalRef, GenericBusinessObjectRef, GenericExecutionObject,
  GenericAIObject, GenericAssetRef

WorkspaceContext shape = FROZEN_CANDIDATE (C0.S5 §22); ≠AuthZ/SoT/JWT/secret
```

## 3A. Architecture / persistence / privacy / safety — C0.S4 freeze accepted

> Canonical rules: [`21-data-and-state-model.md`](./21-data-and-state-model.md) §4A.
> Status: `FROZEN_ACCEPTED` / `APPROVED` via `ARCHITECTURE_REVIEW_C0_S4` (`REVIEWED_HEAD=7ac1fb930017bbabb05d8b1654941518f315c6a7`; `VERDICT=ACCEPT_WITH_RESIDUAL`). Não prova runtime. Autoriza C0.S5; **não** executa C0.S5; `FOUNDATION_FREEZE=NOT APPROVED`.

```text
REVIEW = ARCHITECTURE_REVIEW_C0_S4
REVIEWED_HEAD = 7ac1fb930017bbabb05d8b1654941518f315c6a7
VERDICT = ACCEPT_WITH_RESIDUAL
ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY = FROZEN_ACCEPTED
C0.S4 = APPROVED
C0.S5 = APPROVED
INTEGRATION_CONTRACTS = FROZEN_ACCEPTED (see §22)
C0.S6 = APPROVED
RED_CONTRACT_CONFORMANCE_PRIVACY_SECURITY_HARNESS = FROZEN_ACCEPTED (see 20)
C0.S7_AUTHORIZED = YES
C0.S7_EXECUTED = NO
PHYSICAL_POSTGRES_CLUSTER = DEFER_PHYSICAL_PLACEMENT / TO_INVENTORY
SecretRef = DEFER_TO_CONTRACT (no new shared primitive)
OT ACTUATION = BLOCKED_BY_DEFAULT
DÉLIA = NOT A SAFETY CONTROLLER
schedule != permission
Evidence != SoT
Prediction != FACT
Personal Memory != Organizational Knowledge
cache/projection != authority
NEW_RUNTIME_ABSTRACTIONS = NONE
FOUNDATION_FREEZE = NOT APPROVED
NEXT = C0.S7 — FOUNDATION_FREEZE review
```

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

## 22. Integration contracts — C0.S5 freeze accepted

> Status: `FROZEN_ACCEPTED` / `APPROVED` via `ARCHITECTURE_REVIEW_C0_S5` (`REVIEWED_HEAD=8d83383e9a9ff019132e7156d56e41643b168851`; `VERDICT=ACCEPT_WITH_RESIDUAL`). Não prova runtime. C0.S6 harness accepted em `20` (`FROZEN_ACCEPTED` via `ARCHITECTURE_REVIEW_C0_S6`); este §22 permanece contract authority; `FOUNDATION_FREEZE=NOT APPROVED`.
> Precedence: C0.S1–C0.S4 freezes are immutable input. Thematic specs cannot redefine owners/authorities.
> Residual: `DOCUMENTATION_CONTRACT_TAXONOMY_RESIDUAL` — only `READ|ADVISE|PREPARE|ACT|VERIFY|SIGNAL` are operation characters; `SIMULATE`/`analysis`/`ingress`/`tech` are semantic/technical qualifiers (not AuthZ modes).

```text
STATUS = FROZEN_ACCEPTED
REVIEW = ARCHITECTURE_REVIEW_C0_S5
REVIEWED_HEAD = 8d83383e9a9ff019132e7156d56e41643b168851
VERDICT = ACCEPT_WITH_RESIDUAL
INTEGRATION_CONTRACTS = FROZEN_ACCEPTED
C0.S0..C0.S5 = APPROVED
C0.S6_AUTHORIZED = YES
C0.S6 = APPROVED
RED_CONTRACT_CONFORMANCE_PRIVACY_SECURITY_HARNESS = FROZEN_ACCEPTED (authority: 20)
C0.S7_AUTHORIZED = YES
C0.S7_EXECUTED = NO
AUTHORITY_MAP = FROZEN_ACCEPTED
BOUNDED_CONTEXT_MAP = FROZEN_ACCEPTED
SHARED_REFERENCE_SEMANTICS = FROZEN_ACCEPTED
ARCHITECTURE_PERSISTENCE_PRIVACY_SAFETY = FROZEN_ACCEPTED
NEW_RUNTIME_ABSTRACTIONS = NONE
FOUNDATION_FREEZE = NOT APPROVED
PROGRAM = PLANNED / NOT_STARTED
C0 = NOT_STARTED
DÉLIA_RUNTIME_DIFF = NONE
RESIDUAL = DOCUMENTATION_CONTRACT_TAXONOMY_RESIDUAL
NEXT = C0.S7 — FOUNDATION_FREEZE review
HARNESS_POINTER = 20 §C0.S6 (does not redefine contracts)
```

C0.S5 congela **contratos tipados de integração** (boundaries, AuthZ, READ/ADVISE/PREPARE/ACT/VERIFY, erros, idempotência, Outcome). Não cria código, OpenAPI implementada, endpoints, SDKs, scheduler, Hub, broker, migrations ou services.

### 22.0 Operation character vocabulary

Canonical operation-character / authorization-mode vocabulary (**only**):

```text
READ | ADVISE | PREPARE | ACT | VERIFY | SIGNAL
```

```text
PREPARE = no side effect
ACT = side-effecting operation requiring fresh execution context; prepared intent alone does not authorize
VERIFY = authoritative postcondition/outcome verification
SIGNAL = occurrence/event stimulus only
PREPARE != ACT
SIMULATE != APPLY
ACT may not be inferred solely from HTTP verb / tool name / provider description / prompt / event / timer / scheduler / model output
```

Taxonomy residual (`DOCUMENTATION_CONTRACT_TAXONOMY_RESIDUAL` — documentation-only; no runtime enum/class):

```text
SIMULATE = semantic qualifier / behavior (not AuthZ mode); SIMULATE != APPLY
analysis = purpose/semantic qualifier (not AuthZ mode)
ingress = direction/purpose qualifier (not AuthZ mode)
tech / Hub tech lifecycle = technical qualifier (not AuthZ mode)
match = purpose qualifier for biometric READ (not AuthN/AuthZ)
```

### 22.1 Contract matrix

| CONTRACT_ID | OWNER | CONSUMERS | CHARACTER | STATUS |
|---|---|---|---|---|
| DELIA.AUTHN.IDENTITY | Keycloak | DÉLIA API | READ (AuthN context) | FROZEN_ACCEPTED |
| DELIA.CORE.EFFECTIVE_ACCESS | Core | DÉLIA API | READ | FROZEN_ACCEPTED |
| DELIA.PORTAL.HOST | Portal host + DÉLIA MFE | MFE/host | READ (UX host) | FROZEN_ACCEPTED |
| DELIA.DOMAIN.READ | Domain API (per op) | DÉLIA | READ | FROZEN_ACCEPTED |
| DELIA.DOMAIN.ACTION | Domain API (per op) | DÉLIA | ACT (+ PREPARE path) | FROZEN_ACCEPTED |
| DELIA.AUTOMATION.EXECUTION | Hub tech + DÉLIA orchestration | DÉLIA↔Hub | ACT \| SIGNAL (tech=Hub lifecycle qualifier) | FROZEN_ACCEPTED |
| DELIA.SCHEDULER.OCCURRENCE | Physical scheduler (TO_INVENTORY) | DÉLIA | SIGNAL | FROZEN_ACCEPTED |
| DELIA.EVENT.ENVELOPE | Source adapters → DÉLIA | Watch/Evidence/Work | SIGNAL | FROZEN_ACCEPTED |
| DELIA.EXTERNAL.CONNECTION | Provider + DÉLIA connection metadata | DÉLIA | READ | FROZEN_ACCEPTED |
| DELIA.EXTERNAL.RESOURCE | Provider | DÉLIA | READ | FROZEN_ACCEPTED |
| DELIA.EXTERNAL.ACTION | Provider | DÉLIA | ACT (typed ops) | FROZEN_ACCEPTED |
| DELIA.TEAMS | M365/Teams adapter under EXTERNAL | DÉLIA | READ \| ACT (split ops) | TARGET / FROZEN_ACCEPTED boundary |
| DELIA.MEDIA.INGRESS | Media owner + DÉLIA refs | DÉLIA | READ (ingress=direction/purpose) | FROZEN_ACCEPTED |
| DELIA.BIOMETRIC.MATCH | Biometric specialized store | DÉLIA | READ (match=purpose; ≠AuthN/AuthZ) | FROZEN_ACCEPTED |
| DELIA.PROCESS.EVENTLOG | Process source owners | Process Intelligence | READ | FROZEN_ACCEPTED |
| DELIA.ANALYSIS.EXECUTION | Sandbox boundary | DÉLIA analysis | READ (analysis=purpose) | FROZEN_ACCEPTED |
| DELIA.ARTIFACT | Artifact owner | DÉLIA/consumers | READ \| ACT (share=governed ACT) | FROZEN_ACCEPTED |
| DELIA.MODEL.INFERENCE | Model runtime (TO_INVENTORY) | DÉLIA | READ \| ADVISE | FROZEN_ACCEPTED |
| DELIA.SCENARIO.SIMULATE | Twin/scenario boundary | DÉLIA | ADVISE (SIMULATE=qualifier; ≠APPLY) | FROZEN_ACCEPTED |
| DELIA.MCP.INVOCATION | MCP host (TO_INVENTORY) | DÉLIA | READ \| ACT (bounded) | FROZEN_ACCEPTED |
| DELIA.A2A.DELEGATION | A2A host (TO_INVENTORY) | DÉLIA | READ \| ACT (bounded) | FROZEN_ACCEPTED |
| DELIA.MARKETPLACE.ASSET | Marketplace metadata | Tower/consumers | READ | FROZEN_ACCEPTED |
| DELIA.NOTIFICATION.REQUEST | Notification adapters | DÉLIA | ACT (delivery) | FROZEN_ACCEPTED |
| DELIA.EDGE.SYNC | Edge device/adapters | DÉLIA | SIGNAL (sync=purpose) | FROZEN_ACCEPTED |
| DELIA.OT.OBSERVE_PREPARE | OT/industrial owners | DÉLIA | READ \| ADVISE \| PREPARE (ACT forbidden) | FROZEN_ACCEPTED |
| DELIA.AUDIT.EVENT | Observability owner (TO_INVENTORY) | platform | SIGNAL (audit=purpose) | FROZEN_ACCEPTED |
| DELIA.OUTCOME.VERIFY | Domain/authoritative sources + DÉLIA | DÉLIA Work | VERIFY | FROZEN_ACCEPTED |

### 22.2 ExecutorRef / WorkspaceContext decisions

```text
ExecutorRef = DO NOT PROMOTE TO NEW SHARED PRIMITIVE = CLOSED_NONISSUE
Use contract-local: executionOwnerRef, executorClass, executionContractVersion, supportedCapability, timeout/cancel
Executor classes (semantic): DOMAIN_API | NATIVE_INTEGRATION | FUNCTION | RPA | COMPUTER_USE | HUMAN_TASK | OTHER_APPROVED

WorkspaceContext = FROZEN_CANDIDATE shape (below)
WorkspaceContext != authorization | SoT | JWT/secret carrier | Work/Decision/Evidence authority
```

### 22.3 High-risk sketches

#### DELIA.AUTHN.IDENTITY

```text
OWNER = Keycloak | CONSUMER = DÉLIA API | CHARACTER = READ / AuthN
INPUT = validated OIDC access token at interface boundary
OUTPUT AuthenticatedPrincipal {
  actorRef: UserRef | ServiceActorRef
  authenticationType
  authenticated
  tokenExpiresAt?
  issuerRef?
}
FORBIDDEN: JWT!=final permission; JWT!=Domain AuthZ; JWT!=prompt/Personal Memory;
           biometric candidate!=authenticated principal; DeviceRef!=UserRef
STATUS = FROZEN_CANDIDATE
```

#### DELIA.CORE.EFFECTIVE_ACCESS

```text
OWNER = Core | CONSUMER = DÉLIA API | CHARACTER = READ
FACTUAL_ANCHORS: GET /me ; GET /me/apps ; GET /me/access-profile
DO_NOT_RECREATE: /me/routes
OUTPUT CoreAccessContext {
  userRef
  effectivePermissionCodes[]
  isSuperadmin
  resolvedAt
  source = CORE
}
RULES: Core effective permission != JWT raw roles
       Portal permission props != backend authorization
       DÉLIA must not implement parallel RBAC
       /me/apps = application/navigation availability
       /me/access-profile = governance/introspection when needed
       material ops fail-closed if Core AuthZ cannot be established
ERRORS: UNAUTHENTICATED | AUTHORITY_UNAVAILABLE | AUTHORITY_CONTEXT_STALE
STATUS = FROZEN_CANDIDATE
```

#### DELIA.PORTAL.HOST + WorkspaceContext

```text
LIFECYCLE: mount(...) | unmount(...) | updateRoute?() | updateToken?()
PortalHostContext {
  basePath, pathname, search, routeId?, routeLabel?, locale?, timezoneHint?, workspaceContext?
}
WorkspaceContext {
  contextVersion, appId, routeId?, entityRefs[], sourceRefs[]?, deviceRef?,
  observedAt?, locale?, timezone?
}
Portal permissions / isSuperadmin props = UX hints only
FORBIDDEN: WorkspaceContext!=permission/JWT/secret/SoT;
           Portal context!=Work/Decision/Evidence authority
STATUS = FROZEN_CANDIDATE
```

#### DELIA.DOMAIN.READ

```text
NOT one generic endpoint — each Domain operation remains typed + owner-specific
REQUIRED eventually: stable operationId, capabilityId, typed request/response,
  identity context, Domain AuthZ, source revision/freshness when material,
  classification, errors, audit/correlation, contract version
MAY attach: EntityRef, SourceRef, freshness, revision/version, classification
NEVER rewrite Domain truth
FORBIDDEN: generic SQL; unrestricted proxy; foreign DB access;
           planner hardcoding URL/path/provider mechanics
STATUS = FROZEN_CANDIDATE
```

#### DELIA.DOMAIN.ACTION

```text
Every material write = distinct typed operation
REQUIRED: capabilityId, contractVersion, stable operationId, actorRef,
  target EntityRef(s), typed arguments, operationMode, workRef?, decisionRef?,
  correlationContext, idempotencyContext, concurrencyExpectation?, expectedPostcondition
AUTHZ_CHAIN:
  Keycloak AuthN → live Core effective RBAC → DÉLIA Policy/Decision
  → Domain final business AuthZ → Domain operation → authoritative Outcome verification
Domain MAY reject after DÉLIA Policy/Decision approves
Domain response != automatically verified Outcome
STATUS = FROZEN_CANDIDATE
```

#### Capability / Action descriptor (projection)

```text
Capability != Operation Contract != Decision != Work != AutomationExecution != Outcome
CapabilityProjection = PROJECTION_ONLY (C0.S3)
Descriptor may include: capabilityId, ownerRef, contractRef, operationId, contractVersion,
  allowedModes[], riskClass, requestSchemaRef, responseSchemaRef,
  idempotencySemantics, concurrencySemantics, postconditionRef, status
MUST_NOT_BECOME: permission | executor SoT | provider metadata authority
NO GenericActionPayload
```

#### DELIA.AUTOMATION.EXECUTION

```text
DÉLIA = semantic orchestration / Work / Decision / Outcome coordination
Hub = technical execution lifecycle
ExecutionRequest {
  requestId, capabilityId, contractVersion, actorRef, workRef, decisionRef?,
  correlationContext, typedInput, inputSchemaVersion, idempotencyContext, timeoutPolicyRef?
}
ExecutionAccepted { executionRef: AutomationExecutionRef, acceptedAt, technicalStatus }
ExecutionTechnicalResult {
  executionRef, technicalStatus, resultRef?, artifactRefs[]?, error?, observedAt
}
Work != AutomationExecution; Hub != planner/Policy/business AuthZ
technical SUCCEEDED != VERIFIED business Outcome
DÉLIA must not duplicate worker/queue/lease/package/credential/tech job lifecycle
Physical Hub runtime = TO_INVENTORY
STATUS = FROZEN_CANDIDATE
```

#### DELIA.SCHEDULER.OCCURRENCE

```text
Physical scheduler owner = TO_INVENTORY
OccurrenceSignal {
  recurringWorkRef, recurringWorkVersion, scheduledFor, actualTriggeredAt,
  schedulerTriggerRef?, correlationContext, signalVersion
}
LOGICAL_UNIQUENESS: RecurringWorkRef + recurringWorkVersion + scheduledFor
  → one logical Work occurrence; occurrenceId stable
UUID/hash algorithm = DEFER_TO_IMPLEMENTATION
Scheduler never = Work owner | actor | permission | Policy | Decision
After signal revalidate: definition active; not paused/cancelled/revoked;
  actor/delegation; Core; Domain; Policy/Decision; idempotency
STATUS = FROZEN_CANDIDATE
```

#### DELIA.EVENT.ENVELOPE

```text
EventEnvelope {
  eventId, eventType, schemaVersion, sourceRef, occurredAt, receivedAt,
  entityRefs[], correlationContext, classification,
  payloadRef? | boundedPayload?, sourceSequence?
}
sourceSequence only if source genuinely provides one
Auth/signature validation at adapter/trust boundary
Event != permission | Command | Work | Decision | ACT | Outcome
Transport = TO_INVENTORY where unproven
STATUS = FROZEN_CANDIDATE
```

#### DELIA.EXTERNAL.CONNECTION / RESOURCE / ACTION

```text
Classes: USER_DELEGATED | ORG_MANAGED | SHARED_RESOURCE | SERVICE_CONNECTION
Metadata: connectionId, ownerType, ownerRef, providerKey, resourceRef?,
  grantedScopes[], status, expiresAt?, revokedAt?, lastValidatedAt?, sharingClassification
Secret/token material NOT in semantic contract
Ops distinct: SEARCH | READ | DRAFT | SEND | WRITE ; DRAFT != SEND
provider scope != Core permission != Domain AuthZ
Webhook: raw callback → authenticity → dedupe/reconcile → EventEnvelope
Never: callback → direct ACT
Physical vault/token store = TO_INVENTORY
STATUS = FROZEN_CANDIDATE
```

#### DELIA.OUTCOME.VERIFY

```text
Request: workRef, executionRef?, capabilityId, targetRefs[], expectedPostconditionRef,
  authoritativeSourceRef, correlationContext
Response: verificationRef; status VERIFIED_SUCCESS|VERIFIED_FAILURE|PENDING|INCONCLUSIVE;
  observedOutcomeRef?, sourceRevision?, verifiedAt, failureReason?, evidenceRefs[]
technical result → verification input; technical result != Outcome; Notification != Outcome
STATUS = FROZEN_CANDIDATE
```

### 22.4 Additional contract notes (matrix-primary)

```text
DELIA.TEAMS: provider-specific adapter under EXTERNAL; Teams ACL authoritative;
  meeting artifact!=Decision; webhook!=ACT; registration/scopes/subscriptions=TO_INVENTORY

DELIA.MEDIA.INGRESS: operation character=READ; ingress=direction/purpose; MediaIngress{sourceRef, deviceRef?, sessionRef?, participantRefs[]?,
  capturedAt, endedAt?, modality, classification, consentNoticeState?, capturePurpose,
  storageRef, retentionPolicyRef?, correlationContext}
  raw media not in generic EventEnvelope; raw!=transcript!=summary!=Evidence!=Decision!=action!=Outcome
  physical store=TO_INVENTORY

DELIA.BIOMETRIC.MATCH: input refs only; output BiometricCandidate{candidateUserRef?,
  state MATCH|UNKNOWN|AMBIGUOUS, confidence, evidenceRef, modelVersion, correctionSupported}
  never expose template; MATCH!=AuthN/AuthZ; UNKNOWN remains UNKNOWN; template store=TO_INVENTORY

DELIA.PROCESS.EVENTLOG: processRef, caseKey, activity, occurredAt, sourceRef, entityRefs[],
  actorRef? if justified, businessStatus?, schemaVersion, classification, sourceRevision?
  output=projection/analysis ≠ business SoT/employee truth/AuthZ; engine=TO_INVENTORY

DELIA.ANALYSIS.EXECUTION: operation character=READ; analysis=purpose qualifier; sandbox isolated; budgets/timeout/network/package policies;
  no production DB credential / provider token / unrestricted host/private net / Domain mutation
  runtime=TO_INVENTORY

DELIA.ARTIFACT: artifactRef, ownerRef, version, classification, acl/policy, source/evidence refs,
  contentStorageRef, createdBy/editedBy, retention, provenance
  generation!=publication; ArtifactRef!=access grant; share/publish=separate governed ACT
  blob store=TO_INVENTORY

DELIA.MODEL.INFERENCE: Prediction!=FACT; ModelRef!=approval; output!=permission; router!=approval
DELIA.SCENARIO.SIMULATE: operation character=ADVISE; SIMULATE=semantic qualifier (≠APPLY); Scenario!=production; Twin!=SoT; Apply=new live ACT context

DELIA.MCP.INVOCATION / DELIA.A2A.DELEGATION: discovery!=approval; tool/agent metadata!=permission;
  never send CoT / whole conversation by default / ambient authority; runtime=TO_INVENTORY

DELIA.MARKETPLACE.ASSET: requiredPermissions!=granted; publish!=enable; enable!=authorization; install!=grant
DELIA.NOTIFICATION.REQUEST: DELIVERED!=business Outcome
DELIA.EDGE.SYNC: offline!=wider AuthZ; DeviceRef!=UserRef; cached permission!=eternal; buffered!=ACT
DELIA.OT.OBSERVE_PREPARE: READ|ADVISE|PREPARE only; ACT FORBIDDEN;
  generic DÉLIA→PLC/CNC/robot ACT = FORBIDDEN

DELIA.AUDIT.EVENT: material lineage allowed; never CoT/password/token/secret/biometric template/
  raw media by default/unbounded sensitive payload; Audit!=business authority; backend=TO_INVENTORY
```

### 22.5 Cross-cutting contract rules

#### Error model (semantic categories; not one universal wire DTO)

```text
UNAUTHENTICATED | FORBIDDEN_PLATFORM | FORBIDDEN_DOMAIN | POLICY_DENIED | DECISION_EXPIRED
INVALID_REQUEST | RESOURCE_NOT_FOUND | UNSUPPORTED_CAPABILITY
CONFLICT | STALE_STATE | IDEMPOTENCY_CONFLICT
AUTHORITY_UNAVAILABLE | SOURCE_UNAVAILABLE | PROVIDER_REVOKED | RATE_LIMITED | TIMEOUT
EXECUTION_REJECTED | EXECUTION_FAILED | AMBIGUOUS_RESULT
POSTCONDITION_FAILED
```

Normalized error may retain: semanticCategory, owner, ownerErrorCode, correlationId, retryable, safeDetails?
Do not erase Domain/provider native semantics. Raw SDK errors must not leak to UI/LLM.

#### Idempotency (material writes)

```text
clientOperationId = stable across retries of same intended operation
scope by: owner, capability, actor, target, operation context, request fingerprint, retention window
same identity + same fingerprint → same/reconciled result where owner supports
same identity + different fingerprint → IDEMPOTENCY_CONFLICT
if downstream lacks native idempotency: ambiguous → authoritative reconcile → retry only if safe
exactly-once NOT ASSUMED
```

#### Concurrency

```text
material stale-state mutation requires: expectedRevision | ETag/version | expectedState | owner equivalent
conflict = STALE_STATE or owner-native
recovery: re-read authoritative state → re-evaluate Policy/Decision → then decide new ACT
Do NOT force one global HTTP mechanism
```

#### Authorization contract rule

```text
Keycloak = AuthN
Core = effective platform RBAC
Domain API = final business authorization
Provider = external resource/provider authority
DÉLIA Policy/Decision = orchestration/business-intelligence gate
Automation Hub = technical execution acceptance
OT/Safety = independent industrial/safety authority
No authority is transitive
Portal hint != backend AuthZ; Core != provider scope; provider scope != Domain;
Decision != Domain permission; Hub acceptance != business AuthZ;
scheduler/event != authorization
```

#### Versioning / compatibility

```text
Every frozen contract: contractId + contractVersion
compatible: add optional field without semantic change
breaking: remove field; change meaning; optional→required; change authority;
  READ/PREPARE→ACT; change idempotency/postcondition semantics
Events: schemaVersion required | OpenAPI: stable operationId required
Breaking semantic op → new operationId or explicit major change
Deprecation: replacement + consumer migration plan + support window
```

#### Security / privacy

```text
Each contract states where applicable: dataClassification, PII/sensitive fields,
  source ACL, retention owner, logging/redaction, provider exposure, secret-bearing fields
Generic contracts must not carry secret material
If adapter needs credential reference: opaque adapter-local secure reference
  (NOT a new global SecretRef)
```

### 22.6 Abstraction Gate

```text
REJECTED: UniversalIntegrationRequest, GenericExternalCall, GenericActionPayload,
  GenericProviderObject, UniversalExecutionResult, UniversalAuthorizationContext,
  UniversalBusinessResponse
NOT_REQUIRED: new shared ExecutorRef; new shared SecretRef
DO_NOT_CREATE: new service, event bus, scheduler, Hub runtime, provider SDK framework,
  action gateway, policy engine, generic integration engine
NEW_RUNTIME_ABSTRACTIONS = NONE
```

### 22.7 Residuals

```text
TO_INVENTORY:
  physical Hub/scheduler/event broker/PG/vault-KMS;
  per-Domain op inventory + Domain idempotency/concurrency/postcondition sources;
  Teams registration/scopes/subscriptions; media/biometric/Sandbox/Artifact/model/Twin/
  MCP-A2A/Marketplace/Edge/notification/observability backends;
  service/delegation credential mechanism; legal retention durations;
  future OT actuation architecture

DEFER_TO_IMPLEMENTATION:
  HTTP DTO class names; idempotency header name; ETag vs revision transport;
  WorkOccurrence ID algorithm; provider SDK structures; scheduler registration;
  Hub transport; broker topics; telemetry vendor fields

DEFER_BY_PHASE:
  Marketplace enable/install; Control Tower runtime; advanced Watch ACT;
  Meeting/Frontline; Process Mining runtime; Twin optimization; Edge autonomy;
  physical OT actuation; L5 autonomous workflows
```
