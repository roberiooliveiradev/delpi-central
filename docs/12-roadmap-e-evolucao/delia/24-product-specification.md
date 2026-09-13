# Minha DELPI Copilot — Especificação Funcional e Técnica Completa

**Status:** especificação canônica de produto  
**Produto:** aplicação standalone nova  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Rastreabilidade:** [`25-requirements-traceability.md`](./25-requirements-traceability.md) — `CP-001…CP-310`  
**Specs temáticas:** `53–66`

## 1. Definição

O Minha DELPI Copilot é a **camada inteligente entre pessoas, sistemas, processos, dados e operação da DELPI e fontes externas autorizadas**.

Não é apenas Chat+RAG. O target é:

```text
Continuous Operational Intelligence
+ Enterprise Copilot
+ Decision Intelligence
+ Governed Automation Orchestration
+ Process Intelligence
+ Analytical / Predictive / Scenario Intelligence
+ AI Governance
```

Possui API/MFE/persistence/manifest/deploy próprios e não depende do Minha DELPI Chat.

## 2. North Star

> Entender contexto interno e externo, perceber mudanças, explicar processos, pesquisar, analisar, prever, simular, decidir dentro de políticas, coordenar trabalho e automações, verificar resultados, produzir artefatos e transformar experiência validada em conhecimento — preservando autoridades, privacidade, segurança e controle humano.

## 3. Information/operational spaces

```text
MINHA DELPI
→ Core + Domain APIs + apps + Knowledge + operational events

PUBLIC INTERNET
→ search/safe fetch

CONNECTED SOURCES
→ Microsoft 365/Teams, Google, WhatsApp Business, etc.

PROCESS / EVENT SPACE
→ event logs, Watches, Process Intelligence

ANALYTICAL / MODEL SPACE
→ Semantic Layer, Sandbox, Predictive/Twin

EDGE / FRONTLINE SPACE
→ governed local cache/inference/sync
```

Nenhum espaço herda automaticamente authority do outro.

## 4. Surfaces

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
TEAMS future surface
BACKGROUND Watches/Workflows
ADMIN governance surfaces
```

Same Copilot API/product identity/policy/evidence/work runtime.

## 5. Copilot único

One Copilot dynamically specialized by Expertise Packs, Playbooks, Knowledge, Personal Memory, current context and authorized capabilities. No departmental-agent runtime.

External A2A agents are integrations, not alternative user-facing Copilots.

## 6. Conversation / Context / Memory

- PT-BR natural;
- multi-intent/follow-up;
- text/voice/media;
- WorkspaceContext + EntityRef + SourceRef;
- no CoT persistence;
- Personal Memory for user preferences/continuity with inspect/correct/delete/disable controls;
- memory never grants permission or overrides live business truth.

## 7. Business capabilities

```text
Domain OpenAPI
→ Action Catalog
→ authorized Capability Projection
→ planner
→ validation
→ Policy/Decision
→ executor
→ verified Outcome/Evidence
```

No manual endpoint authority or provider/executor hardcode.

## 8. Internet Research / External Connectors / Teams

Research uses Search + Safe Fetch + provenance/freshness. Connections use official OAuth/API contracts, least privilege, protected credentials and source ownership.

Targets include Microsoft 365/Outlook/Teams/OneDrive/SharePoint, Google Workspace/Gmail/Drive/Calendar, WhatsApp Business, Slack, GitHub and future approved providers.

```text
read != write
draft != send
external content = untrusted
```

Teams remains Microsoft 365 capability family and future surface of same Copilot runtime.

## 9. Multimodal / Biometrics / Human Observation

PDF/image/drawing/spreadsheet/voice/camera/video/screen can feed Evidence under explicit media policy.

Closed-set biometric recognition of enrolled users may assist identity association but never replace login/RBAC.

Human Observation is limited to observable process evidence, not personality/emotion/trust/sensitive profiling or autonomous employment decisions.

## 10. Event-Driven Operational Intelligence

The user is not the only trigger.

```text
EVENT/SIGNAL
→ validate/normalize EventEnvelope
→ dedupe/correlate
→ context
→ FAST | OPERATIONAL | REASONING decision path
→ OBSERVE/ADVISE/PREPARE/ACT according to phase/policy
```

Not every event calls an LLM. Deterministic readiness uses structured rules when criteria exist.

## 11. Automation & Execution Hub

Copilot is intelligence/orchestration; Hub is execution boundary.

Executor preference:

```text
official API
→ native integration
→ deterministic function/script
→ RPA
→ computer-use
→ Human Task
```

Planner works with semantic capabilities such as `billing.invoice.issue`, never clicks/selectors.

Technical executor success is separated from verified business Outcome.

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

Process Mining understands the real process from authorized event logs. It does not become employee surveillance or automatic RPA deployment.

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

The Copilot produces editable/versioned/provenanced work objects:

```text
report/document
spreadsheet
a presentation
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
Copilot
models
Watches
workflows
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

## 23. Edge / Offline Industrial Copilot

Cloud Copilot + governed Edge runtime for approved use cases:

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
ACT only in C7 under explicit autonomy
```

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
permission elevation from prompt/event/tool/agent/model/package/memory
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
free-form LLM/RPA/Edge→machine actuation
```

## 28. Administration

Role-gated product surfaces can include:

```text
Connections
Automation & Execution Hub
Process Intelligence
AI Control Tower
Semantic Catalog
Memory controls
Artifact Workspace
Model Governance
Marketplace
Edge Fleet
```

Admin access respects separation of duties.

## 29. Non-functionals

- standalone deployment/rollback;
- security/privacy/data minimization;
- provider/executor/model/tool neutrality;
- reproducible evidence/analysis;
- source freshness/provenance;
- idempotency/outcome verification;
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
→ governed deployment
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

Release complete for declared scope requires CP coverage through current authority, standalone independence, correct owners, tests/gates, safe data/model/tool lifecycle, verified outcomes, privacy/security/safety, observability/rollback and no material unresolved drift.

Estado real vive no execution ledger.
