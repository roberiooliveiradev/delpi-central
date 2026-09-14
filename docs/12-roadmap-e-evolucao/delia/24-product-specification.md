# DÉLIA — Especificação Funcional e Técnica Completa

**Status:** especificação canônica de produto  
**Produto:** aplicação standalone nova  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Rastreabilidade:** [`25-requirements-traceability.md`](./25-requirements-traceability.md) — `CP-001…CP-316`  
**Specs temáticas:** `53–66`

## 1. Definição

A **DÉLIA — DELPI · Ecossistema de Ligações, Inteligência e Automação** é a inteligência operacional entre pessoas, sistemas, processos, dados e operação da DELPI e fontes externas autorizadas.

Não é Chat+RAG. O target é:

```text
Continuous Operational Intelligence
+ Decision Intelligence
+ Governed Automation Orchestration
+ Durable / Recurring Governed Work
+ Process Intelligence
+ Analytical / Predictive / Scenario Intelligence
+ AI Governance
```

Possui API/MFE/persistence/manifest/deploy próprios e não depende do Minha DELPI Chat.

## 2. North Star

> Entender contexto interno e externo, perceber mudanças e tempo, explicar processos, pesquisar, analisar, prever, simular, decidir dentro de políticas, coordenar trabalho pontual ou recorrente e automações, verificar resultados, produzir artefatos e transformar experiência validada em conhecimento — preservando authorities, privacidade, segurança e controle humano.

## 3. Information/operational spaces

```text
MINHA DELPI
→ Keycloak + Core + Domain APIs + apps + Knowledge + operational events

PUBLIC INTERNET
→ search/safe fetch

CONNECTED SOURCES
→ Microsoft 365/Teams, Google, WhatsApp Business, etc.

PROCESS / EVENT / TIME SPACE
→ event logs, Watches, Recurring Governed Work, Process Intelligence

ANALYTICAL / MODEL SPACE
→ Semantic Layer, Sandbox, Predictive/Twin

EDGE / FRONTLINE SPACE
→ governed local cache/inference/sync
```

Nenhum espaço herda automaticamente authority do outro.

Authorities fundamentais:

```text
Keycloak       = identity/SSO
Core API       = apps/routes/RBAC/governance
Portal         = host/navigation/published context
Domain APIs    = business data/rules/actions
Providers      = external resources/scopes
DÉLIA          = intelligence/context/Evidence/Policy/Decision/Work/RecurringWork/orchestration/outcome coordination
Automation Hub = technical execution
Scheduler      = technical time-trigger materialization; physical owner TO_INVENTORY until C0
OT/Safety      = machine/safety authority
```

Scheduler/timer nunca se torna business/permission authority por materializar horário.

## 4. Surfaces

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
TEAMS future surface
BACKGROUND Watches/Workflows/Recurring Work
ADMIN governance surfaces
```

Same DÉLIA API/product identity/policy/evidence/work runtime.

## 5. DÉLIA única

Uma DÉLIA dinamicamente especializada por Expertise Packs, Playbooks, Knowledge, Personal Memory, contexto atual e capabilities autorizadas. Sem runtime de agentes departamentais.

External A2A agents são integrações, não alternativas user-facing à DÉLIA.

## 6. Conversation / Context / Memory

- PT-BR natural;
- multi-intent/follow-up;
- text/voice/media;
- WorkspaceContext + EntityRef + SourceRef;
- no CoT persistence;
- Personal Memory for user preferences/continuity with inspect/correct/delete/disable controls;
- memory never grants permission or overrides live business truth.

Conversation pode originar Recurring Work por use case autorizado, mas o Work recorrente não depende da sessão permanecer aberta.

## 7. Business capabilities

```text
Domain OpenAPI
→ Action Catalog
→ authorized Capability Projection
→ planner
→ validation
→ Policy/Decision
→ DÉLIA Work/orchestration
→ direct Domain API or Automation Hub execution contract as applicable
→ verified Outcome/Evidence
```

No manual endpoint authority or provider/executor hardcode. Direct Domain API execution is valid when it is the approved authoritative contract; technical automation execution belongs to the Automation Hub boundary.

## 8. Internet Research / External Connectors / Teams

Research uses Search + Safe Fetch + provenance/freshness. Connections use official OAuth/API contracts, least privilege, protected credentials and source ownership.

Targets include Microsoft 365/Outlook/Teams/OneDrive/SharePoint, Google Workspace/Gmail/Drive/Calendar, WhatsApp Business, Slack, GitHub and future approved providers.

```text
read != write
draft != send
external content = untrusted
```

Teams remains Microsoft 365 capability family and future surface of same DÉLIA runtime.

## 9. Multimodal / Biometrics / Human Observation

PDF/image/drawing/spreadsheet/voice/camera/video/screen can feed Evidence under explicit media policy.

Closed-set biometric recognition of enrolled users may assist identity association but never replace login/RBAC.

Human Observation is limited to observable process evidence, not personality/emotion/trust/sensitive profiling or autonomous employment decisions.

## 10. Event-Driven Operational Intelligence

The user is not the only trigger. Time can also be a deterministic trigger under a frozen scheduling contract.

```text
EVENT / SIGNAL / TIME OCCURRENCE
→ validate/normalize
→ dedupe/correlate
→ context
→ FAST | OPERATIONAL | REASONING decision path
→ OBSERVE/ADVISE/PREPARE/ACT according to phase/policy
```

Not every event calls an LLM. Deterministic readiness uses structured rules when criteria exist.

```text
event payload != permission
timer tick != permission
schedule != permission
```

C5 may allow governed ACT for explicit capabilities. C6 keeps Watch autonomous ACT disabled by default. C7 adds selected advanced autonomy/Watch ACT; L5 remains OFF by default.

## 11. Automation Hub

DÉLIA is intelligence/Policy/Decision/Work/orchestration; Automation Hub is the technical-execution boundary.

Executor preference:

```text
official API
→ native integration
→ deterministic function/script
→ RPA
→ governed computer-use
→ Human Task
```

Planner works with semantic capabilities such as `billing.invoice.issue`, never clicks/selectors.

Technical executor success is separated from verified business Outcome. Automation Hub never becomes business/permission authority or a second DÉLIA planner/workflow authority.

### 11.1 Recurring Governed Work / Scheduling

Recurring Governed Work is a first-class `TARGET` capability, traced by `CP-311–CP-316`.

A user/owner authorized to do so can define persistent bounded Work such as:

> “Todos os dias às 09:00 gere o relatório de produção do dia anterior e envie por email para a diretoria.”

This is **not** “the LLM remembering to wake up”. The recurrence is persistent and deterministic and survives the initiating chat/session.

Minimum product lifecycle target:

```text
CREATE
INSPECT / LIST
PAUSE
RESUME
CANCEL
```

Definition semantics include, when applicable:

```text
owner/creator refs
versioned Work template/definition
recurrence/calendar expression
IANA timezone
startAt/endAt
capability/scope/target refs
policy ref
misfire/missed-run policy
overlap/concurrency policy
failure/retry policy
lifecycle status
```

DÉLIA owns the governed Work definition/lifecycle/correlation when C0 confirms the state boundary. The physical timer/scheduler owner is independently inventoried in C0 and owns timer/job runtime mechanics. It may be platform reuse, a neutral shared capability or a new adapter/implementation only after the Abstraction Gate.

Each temporal occurrence is a distinct correlated/idempotent execution opportunity. Duplicate tick, retry, process restart or reconciliation must not duplicate a material effect.

Authorization invariants:

```text
schedule != permission
stored intent != eternal authorization
timer/scheduler identity != business actor
physical scheduler success != business Outcome
```

Every material occurrence re-resolves the current user/service actor and revalidates live Core/domain AuthZ, Policy/Decision, connection/provider status, current source permissions and capability limits before ACT.

If the creator loses access, leaves the organization, a connection is revoked, recipients/scope become invalid or policy changes, future occurrences block/degrade/pause truthfully rather than reusing stale authorization.

Phase semantics:

```text
C0 = inventory/freeze scheduler owner + recurrence/timezone/misfire/overlap/idempotency/AuthZ contract
C5 = Recurring Governed Work runtime; bounded L4 ACT may execute under live gates
C6 = schedule/admin/history UX; Watch still has no autonomous ACT by default
C7 = not required for bounded C5 recurring L4; only advanced autonomy/L5 remains C7
```

Recurring Work is therefore distinct from Watch autonomous ACT.

Canonical report/email flow:

```text
RecurringWorkDefinition
→ deterministic time occurrence
→ one correlated occurrence/idempotency key
→ current user/service identity
→ live AuthZ + Policy/Decision
→ authorized previous-period reads
→ grounded/versioned report Artifact
→ PREPARE communication send intent
→ revalidate recipient/connection/write capability
→ communication.email.send
→ provider/executor technical result
→ authoritative/contractual Outcome verification when available
→ Evidence + Audit + Outcome
```

```text
report generated != email authorized
provider accepted != verified final outcome automatically
```

## 12. Process Intelligence

Capabilities:

```text
Process Discovery
Process Mining
Task Mining when explicitly governed
Conformance Checking
Variant/Bottleneck/Wait/Rework Analysis
Automation Opportunity Detection
Before/After Measurement
```

Process Mining understands the real process from authorized event logs. It does not become employee surveillance or automatic automation deployment.

## 13. Business Graph

EntityRef/RelationshipRef connect business entities and source refs without copying masters. Graph answers relationships/context, not metric semantics.

## 14. Semantic Business Layer

Defines official business meaning of metrics/concepts:

```text
MetricDefinition
→ owner
→ formula
→ grain/dimensions
→ unit
→ source
→ freshness
→ version
```

LLM interprets intent; structured definition drives material calculation. Graph != Semantic Layer.

## 15. Analysis Sandbox

Isolated, quota-bounded analysis environment for authorized data:

```text
Python / bounded SQL / DataFrames / statistics / forecasting / optimization / charts
```

Read-only toward authoritative sources by default, no unrestricted host/private network or broad credentials, reproducibility metadata required when material.

## 16. Artifact Workspace

A DÉLIA produces editable/versioned/provenanced work objects:

```text
report/document
spreadsheet
presentation
PDF/export
chart
dashboard snapshot
process map/BPMN
A3/8D/FMEA candidate
checklist/procedure draft
project plan
meeting minutes
analysis package
```

Human edits are preserved. Share/send/publish remains governed.

## 17. Predictive / Prescriptive Intelligence

```text
DESCRIPTIVE
DIAGNOSTIC
PREDICTIVE
PRESCRIPTIVE
```

Prediction includes model/version/horizon/confidence/freshness/limitations and is never presented as FACT.

Prescription compares objectives/constraints/alternatives/trade-offs and produces recommendation/PREPARE, not automatic authorization.

## 18. Operational Twin / Scenario Workspace

A bounded live-state projection for what-if analysis:

```text
live authoritative state refs
→ scenario branch
→ simulate
→ compare impacts
```

`SIMULATED_STATE != PRODUCTION_STATE`. Apply starts a new live Decision/action path.

## 19. MCP / A2A interoperability

MCP-compatible tools/resources and A2A-compatible external agents can extend capabilities through approved adapters/allowlists.

```text
discovery != approval
external agent/tool result != authority
```

Minimum context, scoped credentials, timeout/cancel/budget and same write governance apply.

## 20. AI Control Tower

Central governance plane for Digital Workforce/AI assets:

```text
DÉLIA runtime
models
Watches
workflows
recurring Work definitions/outcomes projection
automations/RPAs
connectors
MCP/A2A
Edge deployments
semantic assets
Marketplace assets
```

Tracks owner/version/risk/data scope/evals/health/cost/verified value/incidents/dependencies/kill switches. Control Tower admin != business permission.

## 21. AI Model Lifecycle

Govern all relevant model families: LLM, embedding, vision, speech, classifier, forecast, anomaly, optimization, quality models.

Lifecycle covers eval→approval→deployment→monitor/drift→rollback/revoke. Model Router only selects approved models.

## 22. Capability Marketplace

Governed catalog for Expertise, Playbooks, Watches, Automations, Connectors, MCP/A2A packs, analysis/artifact templates, semantic metric packs, Frontline skills and approved models.

Manifest declares dependencies/scopes/permissions as requirements, not grants. Executable assets pass supply-chain controls.

## 23. Edge / Offline Industrial

Cloud DÉLIA + governed Edge runtime for approved use cases:

- cached current procedure/drawing;
- local bounded search/STT/vision/model inference;
- telemetry reads;
- FAST path;
- event buffering/store-and-forward;
- Frontline continuity.

Modes are explicit (`ONLINE/DEGRADED/OFFLINE_READ_ONLY/SYNCING` etc.). Offline never widens authority. OT safety remains independent.

## 24. Meeting / Frontline

Meeting combines authorized transcript/data/sources/decisions/actions into ata viva. Frontline prioritizes large-touch/hands-free/current procedure/revision/operational context.

Both use same policy/evidence/work runtime and can consume Semantic/Process/Predictive/Edge capabilities where appropriate.

## 25. Task / Case / Room / Inbox / Watch

Durable collaboration/work objects relate internal/external/process/artifact Evidence without granting source access.

Watch modes:

```text
OBSERVE
ADVISE
PREPARE
ACT — only when the Watch itself is explicitly approved for autonomous ACT under C7 gates
```

This does **not** mean all ACT is deferred to C7. Governed L4 execution of explicit capabilities may exist from C5 through authorized/confirmed flows. Watch in C6 remains `OBSERVE|ADVISE|PREPARE` by default.

Recurring Governed Work is not represented by enabling `Watch ACT`: a recurring time trigger is a previously defined bounded Work recurrence whose material occurrences still pass C5 live gates.

## 26. Organizational Knowledge / Governed Learning

```text
experience/source/process/execution
→ Evidence
→ candidate
→ owner/review/eval/freshness/privacy/licensing
→ versioned publish
```

Personal Memory, one successful automation run or public webpage never auto-publishes corporate truth.

## 27. Security / Privacy / Safety

Fundamental negatives:

```text
permission elevation from prompt/event/timer/tool/agent/model/package/memory
secret/token exposure
cross-user external/memory leak
Process Mining employee scoring
open-world biometric surveillance
sandbox escape/unrestricted source write
prediction presented as fact
simulation writing production
Edge offline authority expansion
Marketplace install granting permission
implicit send/write/ACT
schedule/timer as permission authority
stale creator authorization reused for future scheduled ACT
duplicate timer/retry/restart causing duplicate material ACT
paused/cancelled schedule still firing
undefined/implicit timezone/misfire/overlap semantics
Automation Hub becoming business permission/planner authority
DÉLIA bypassing technical execution boundary with ad hoc executor internals
free-form LLM/RPA/Edge→machine actuation
```

## 28. Administration

Role-gated product surfaces can include:

```text
Connections
Recurring Work / Schedule management
Automation Hub observability/admin projection
Process Intelligence
AI Control Tower
Semantic Catalog
Memory controls
Artifact Workspace
Model Governance
Marketplace
Edge Fleet
```

Admin access respects separation of duties. Recurring Work admin can inspect/pause/resume/cancel within its own authorization but never grants underlying domain/provider write permission. DÉLIA admin UI may project Automation Hub/scheduler state/contracts but does not become their technical runtime.

## 29. Non-functionals

- standalone deployment/rollback;
- security/privacy/data minimization;
- provider/executor/model/tool/scheduler neutrality;
- reproducible evidence/analysis;
- source freshness/provenance;
- idempotency/outcome verification;
- deterministic recurrence/timezone semantics;
- restart/retry/misfire safety for recurring occurrences;
- cost/rate/resource budgets;
- model/process/data quality monitoring;
- accessibility;
- generalization/metamorphic tests;
- no duplicate authorities;
- no Chat dependency;
- industrial safety boundary.

## 30. Reference scenarios

### Process improvement

```text
real event logs
→ process variants/bottleneck
→ automation opportunity candidate
→ owner review
→ PREPARE automation
→ governed deployment/execution through approved boundary
→ before/after measurement
```

### Predictive operation

```text
stock/production/supplier data
→ governed metric/features
→ prediction
→ scenario alternatives
→ prescription
→ PREPARE
→ Decision/ACT if allowed
→ verified Outcome
```

### Recurring daily production report

```text
authorized user creates “daily 09:00 <IANA timezone>” recurring Work
→ persisted definition independent of chat
→ deterministic occurrence
→ live identity/AuthZ/Policy
→ previous-day production reads
→ grounded/versioned report
→ separate governed email.send
→ no duplicate send on duplicate/retry/restart
→ verified Outcome/Evidence/Audit
```

### Personal daily briefing

```text
Personal Memory preferences
+ Tasks/Cases/Watches
+ authorized live sources
→ prioritized briefing
```

### Factory offline

```text
Edge cached current procedure/model
→ offline read-only assistance
→ buffered event
→ sync/reconcile
```

## 31. Product Complete

Release complete for declared scope requires CP coverage through current authority (`CP-001…CP-316`), standalone independence, correct owners, tests/gates, safe data/model/tool/scheduler lifecycle, verified outcomes, privacy/security/safety, observability/rollback and no material unresolved drift.

Estado real vive no execution ledger. Documentation alone does not prove runtime implementation or advance phase.
