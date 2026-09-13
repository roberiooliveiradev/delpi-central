# 13 — Catálogo funcional do Minha DELPI Copilot

**Status:** catálogo funcional temático  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Requirements:** [`25-requirements-traceability.md`](./25-requirements-traceability.md) — `CP-001…CP-310`

## 1. Objetivo

Descrever o que o produto pode evoluir para fazer, sem duplicar a ordem C0–C7.

## 2. Conversation / Understanding

- natural PT-BR;
- multi-intent/follow-up;
- structured goals;
- entity resolution;
- text/voice/media;
- contextual clarification only when needed;
- no chain-of-thought persistence.

## 3. Surfaces

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
TEAMS future surface
BACKGROUND Watches/Workflows
ADMIN governance surfaces
```

Same Copilot API/product/policy/evidence/work runtime.

## 4. Portal / Context / Navigation

- open app/route/entity;
- deep links/view/filter/focus;
- WorkspaceContext + EntityRefs + SourceRefs;
- iframe bridge;
- operational context OP/machine/product/operation/workstation/lot/material;
- shared-device/session hygiene.

## 5. Expertise / Playbooks / Knowledge

- one Copilot identity;
- Expertise Packs;
- Domain Playbooks;
- Reference/Decision/Experience/Solution Pattern Knowledge;
- cross-domain composition;
- version/review/eval/publish/rollback;
- expertise never grants permission.

## 6. Personal Memory / Personalization

- user preferences;
- confirmed personal work facts;
- followed topics/projects/metrics;
- work continuity refs;
- personalized briefing;
- view/correct/delete/disable controls;
- no hidden sensitive/personality profile;
- memory never overrides live business truth/RBAC.

## 7. Multimodal / Voice / Biometrics

- PDF/image/drawing/photo/certificates/spreadsheets;
- STT/TTS/voice commands;
- camera/video/screen share;
- page/region/frame/time provenance;
- closed-set enrolled face/speaker recognition when governed;
- explicit capture/retention;
- Human Observation limited to observable process evidence.

## 8. Internet Research

- current public research;
- safe search/fetch;
- source authority/freshness;
- conflict handling;
- provenance/citations;
- untrusted-content boundaries.

## 9. External Connectors

Potential approved connectors:

- Microsoft 365 / Outlook / Teams / OneDrive / SharePoint;
- Google Workspace / Gmail / Drive / Calendar;
- WhatsApp Business;
- Slack/GitHub/CRMs/service desks/future providers.

Capabilities include search/read/draft/send/create/update according to scopes/policy. `read != write`, `draft != send`.

## 10. Microsoft Teams

- teams/channels/chats/messages/replies;
- meeting metadata/transcripts/recordings when authorized;
- change notifications;
- meeting artifacts to Evidence/Task/Case/Watch;
- future app/tab/bot as same Copilot runtime;
- live raw media advanced/optional only.

## 11. Evidence / Epistemic UX

- SourceRef/EvidenceRef;
- freshness/confidence/limitations;
- FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION;
- conflicting evidence;
- source drill-down;
- outcome provenance.

## 12. Business Reads / Writes

Read/compare/analyze data from onboarded domain APIs. Writes create/edit/approve/reject/assign/comment/cancel/initiate domain processes only through authorized Business Actions, Policy/Decision and final domain validation.

## 13. Business Graph

- canonical entity relationships;
- cross-domain traversal;
- provenance/freshness;
- permission-aware fetch;
- no master-data replication.

## 14. Semantic Business Layer

- governed MetricDefinitions;
- business glossary;
- dimensions/grain/units;
- official formulas/owners/versions;
- conflict/deprecation handling;
- reproducible semantic queries;
- zero-copy/federated source preference.

Graph relates entities; Semantic Layer defines business meaning.

## 15. Event-Driven Operational Intelligence

- real event ingestion;
- EventEnvelope;
- authenticity/dedupe/order/correlation;
- polling only as bounded fallback;
- `FAST|OPERATIONAL|REASONING` paths;
- deterministic readiness/anomaly policies;
- proactive Watches.

## 16. Process Intelligence

- Process Discovery;
- Process Mining;
- Task Mining only when explicitly governed;
- conformance checking;
- variants;
- bottlenecks/waits/rework;
- process KPI mining;
- automation opportunity detection;
- before/after measurement;
- BPMN/process-map artifacts.

No hidden employee productivity/person score.

## 17. Automation & Execution Hub

Executor types:

```text
API
native integration
function/script
RPA
computer-use
Human Task
```

Functions:

- semantic capability→executor mapping;
- execution queues/state;
- RPA worker visibility when applicable;
- idempotency/retry/cancel;
- exception handling;
- outcome verification;
- notification/escalation;
- kill switches.

API is preferred when supported/authoritative.

## 18. Watch / Proactivity

```text
OBSERVE → detect/record
ADVISE  → analyze/notify
PREPARE → prepare draft/action/work plan, no side effect
ACT     → C7 only under explicit autonomy
```

## 19. Durable Workflow / Work Management

- DAG/dependencies;
- safe parallel reads;
- wait_user/wait_approval/wait_event/wait_time;
- checkpoints/restart/resume;
- no duplicate write;
- Task/Case/Room/Inbox;
- human exceptions resume same Workflow.

## 20. Decision Gates / Autonomy

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Autonomy L0–L5 is capability/context/risk scoped; L5 OFF by default. No global unrestricted autonomy.

## 21. Outcome Verification

Material actions distinguish technical execution from authoritative business completion:

```text
EXECUTED?
AND
EXPECTED POSTCONDITION VERIFIED?
```

No false “success” notifications.

## 22. Analysis Sandbox

- bounded Python/SQL/DataFrame/statistics/forecast/optimization/chart workloads;
- isolated runtime;
- authorized read inputs;
- quotas/timeouts;
- no unrestricted host/private network;
- reproducibility metadata;
- truthful failure.

## 23. Artifact Workspace

Generate/manage:

```text
reports/documents
spreadsheets
presentations
PDFs
charts
process maps/BPMN
A3/8D/FMEA candidates
checklists/procedure drafts
project plans
meeting minutes
analysis packages
```

With version/provenance/ACL/review/human edit preservation/export/share governance.

## 24. Predictive Intelligence

Potential use cases:

- demand/stockout risk;
- supplier delay;
- machine failure/maintenance;
- quality/scrap risk;
- production delay/capacity;
- SLA/financial risks where approved.

Prediction carries model/version/horizon/confidence/freshness/limitations and is not FACT.

## 25. Prescriptive Intelligence

- objectives/constraints;
- alternative actions;
- predicted outcomes;
- trade-offs/risk;
- recommendation/PREPARE;
- never implicit authorization.

## 26. Operational Twin / What-if

- dynamic source-state projection;
- scenario branches;
- simulation/compare;
- impact on OP/capacity/inventory/customer/etc.;
- `SIMULATE != APPLY`;
- scenario never writes production directly.

## 27. MCP / A2A interoperability

- approved MCP tool/resource integrations;
- approved A2A external-agent delegation;
- lifecycle/allowlists/scopes;
- minimal delegated context;
- cancellation/budget;
- normalized Evidence/Outcome;
- same write governance;
- discovery != approval.

## 28. AI Control Tower

Central Digital Workforce governance:

- AI asset/model/automation/connectors/tool-agent/Edge inventory;
- owner/version/risk/data scope;
- eval freshness/health;
- cost and verified value;
- incidents/dependencies;
- rollout/cohorts;
- kill switches/rollback.

Admin does not inherit business action permissions.

## 29. AI Model Lifecycle / MLOps

- LLM/embedding/vision/speech/classifier/forecast/anomaly/optimization models;
- eval/approval/deployment;
- drift/latency/cost/availability;
- datasets/eval governance;
- rollback/revoke;
- cloud/provider/batch/Edge deployments.

## 30. Capability Marketplace

Governed lifecycle for:

- Expertise/Playbooks;
- Watches;
- automations;
- connector packs;
- MCP/A2A integrations;
- analysis/artifact templates;
- semantic metric packs;
- Frontline skills;
- approved models.

Package requirements never grant permissions. Executable assets pass supply-chain controls.

## 31. Edge / Offline Industrial Copilot

- current procedure/drawing cache;
- bounded local search/STT/vision/model inference;
- telemetry reads;
- FAST path;
- offline Frontline assistance;
- event buffering/store-and-forward;
- device/package/model management;
- explicit online/degraded/offline modes;
- no authority widening offline.

## 32. Meeting Mode

- explicit session/capture;
- transcript + authorized business/external queries;
- participant/speaker association when governed;
- facts/decisions/pending topics;
- candidate actions;
- ata viva;
- Task/Case/Room follow-up.

Transcript != decision != executed action.

## 33. Frontline Mode

- large touch/hands-free;
- camera/image;
- current procedure/drawing/revision;
- OP/machine/product context;
- maintenance/quality support;
- occurrence/help request;
- training assistance;
- governed biometric identity assistance;
- Edge/offline support when available.

## 34. Organizational Learning

```text
source/experience/process/execution
→ Evidence
→ candidate
→ review/eval/freshness/privacy/licensing
→ versioned publish
```

No one-run auto-learning into production policy.

## 35. Iframe / AI-ready onboarding

Secure bridge for context/visual commands; Business Actions remain API-based. Apps onboard through shared contracts/readiness without central planner hardcode.

## 36. Model Router / Compute Policy

Choose only approved models based on capability, quality, latency, cost, data policy and deployment availability. Revoked model unavailable.

## 37. Security / Privacy / Industrial Safety

- no secret/token leakage;
- source/user isolation;
- safe egress;
- no hidden capture/biometric surveillance;
- Process Mining not employee scoring;
- sandbox bounded;
- tool/agent/package untrusted;
- Prediction not fact;
- Twin not production;
- Edge offline not permission expansion;
- Marketplace install not permission;
- no arbitrary LLM/RPA/Edge→machine actuation.

## 38. Administração

Role-gated surfaces may include:

```text
Connections
Automation Hub
Process Intelligence
AI Control Tower
Semantic Catalog
Memory controls
Artifact Workspace
Model Governance
Marketplace
Edge Fleet
```

## 39. Final experience

The user should feel that the Copilot:

```text
understands where I am and what matters to me
knows business meaning and process reality
finds internal/external evidence
can perform reproducible analysis
anticipates risks and simulates alternatives
produces usable artifacts
prepares/executes governed work
coordinates APIs/RPAs/tools/agents/people
verifies what really happened
keeps me informed
works in meeting and shopfloor contexts
can remain useful in bounded offline scenarios
governs models/assets safely
learns only through explicit governance
```
