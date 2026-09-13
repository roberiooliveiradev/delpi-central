# 13 — Catálogo funcional da DÉLIA

**Status:** `TARGET` — catálogo funcional temático  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Requirements:** [`25-requirements-traceability.md`](./25-requirements-traceability.md) — `CP-001…CP-310`

## 1. Objetivo

Descrever capabilities target sem duplicar a ordem C0–C7 e sem implicar implementação. Cada capability permanece `PLANNED/TARGET` até evidence provar runtime/contract.

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

Same DÉLIA product/policy/evidence/work semantics; physical API/MFE/runtime shape depends on C0/C1 evidence.

## 4. Portal / Context / Navigation

- open app/route/entity;
- deep links/view/filter/focus;
- WorkspaceContext + EntityRefs + SourceRefs when contracts are frozen;
- iframe bridge;
- operational context;
- shared-device/session hygiene.

Portal remains host/navigation/context publisher, not permission/business authority.

## 5. Expertise / Playbooks / Knowledge

- one DÉLIA identity;
- Expertise Packs/Domain Playbooks as governed target contracts;
- Reference/Decision/Experience/Solution Pattern Knowledge;
- cross-domain composition;
- version/review/eval/publish/rollback;
- expertise never grants permission.

## 6. Personal Memory / Personalization

- user preferences/continuity;
- followed topics/projects/metrics;
- personalized briefing;
- view/correct/delete/disable controls;
- no hidden sensitive/personality profile;
- memory never overrides live business truth/RBAC.

## 7. Multimodal / Voice / Biometrics

- PDF/image/drawing/photo/certificates/spreadsheets;
- STT/TTS/voice commands;
- camera/video/screen share;
- provenance;
- closed-set enrolled face/speaker recognition when governed;
- explicit capture/retention;
- Human Observation limited to observable process evidence;
- biometric match != authentication != authorization.

## 8. Internet Research

- current public research;
- safe search/fetch;
- source authority/freshness;
- conflict handling;
- provenance/citations;
- untrusted-content boundaries.

## 9. External Connectors

Potential approved provider families only after C0/provider contracts. `read != write`, `draft != send`, provider scope != Core permission.

## 10. Microsoft Teams

Future provider/surface integration under same DÉLIA semantics. No separate planner/runtime or automatic trust from Microsoft metadata.

## 11. Evidence / Epistemic UX

- Source/Evidence refs when frozen;
- freshness/confidence/limitations;
- FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION;
- conflicting evidence;
- source drill-down;
- outcome provenance.

## 12. Business Reads / Writes

Reads/writes use authorized Domain APIs/use cases whenever available. Material ACT requires live AuthZ + Policy/Decision + idempotency/audit + confirmation/approval as required + authoritative postcondition verification.

## 13. Business Graph

- relationship projection;
- cross-domain traversal;
- provenance/freshness;
- permission-aware fetch;
- no master-data replication;
- Graph != Semantic Layer.

## 14. Semantic Business Layer

- governed MetricDefinitions;
- glossary;
- dimensions/grain/units;
- formulas/owners/versions;
- conflict/deprecation handling;
- reproducible queries;
- source authority preserved.

## 15. Event-Driven Operational Intelligence

- real event ingestion;
- EventEnvelope when contract is frozen;
- authenticity/dedupe/order/correlation;
- polling as bounded fallback;
- `FAST|OPERATIONAL|REASONING`;
- not every event calls an LLM;
- event never grants permission.

## 16. Process Intelligence

- Process Discovery/Mining;
- Task Mining only when explicitly governed;
- conformance/variants/bottlenecks/waits/rework;
- automation opportunity candidates;
- before/after measurement;
- no hidden employee scoring.

## 17. Automation Hub / Technical Execution

Technical executor classes may include:

```text
official API
native integration
function/script
RPA
governed computer-use
Human Task
```

DÉLIA owns semantic capability/Policy/Decision/Work orchestration. Automation Hub or approved executor owner owns technical execution details, queues/workers/packages/credentials/session mechanics as applicable.

Outcome verification is coordinated by DÉLIA against authoritative business sources; Hub technical success is not business success.

## 18. Watch / Proactivity

```text
OBSERVE → detect/record
ADVISE  → analyze/notify
PREPARE → prepare draft/action/work plan, no material side effect
ACT     → governed ACT may exist from C5 for explicitly authorized capabilities
```

C6 Watch defaults to OBSERVE/ADVISE/PREPARE. C7 adds selected **autonomous Watch ACT / advanced autonomy**, not the first occurrence of ACT.

## 19. Durable Workflow / Work Management

- DAG/dependencies;
- safe parallel reads;
- wait_user/wait_approval/wait_event/wait_time;
- checkpoints/restart/resume;
- no duplicate write;
- Task/Case/Room/Inbox;
- human exceptions resume same Work;
- no technical executor duplication.

## 20. Decision Gates / Autonomy

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Autonomy is capability/identity/context/risk/sensitivity/materiality/environment/reversibility/policy scoped. L5 OFF by default.

## 21. Outcome Verification

```text
technical execution success
!= authoritative business outcome
```

Material ACT verifies postcondition at source authority before success claim.

## 22. Analysis Sandbox

Bounded isolated analysis for authorized data; read-only toward authoritative sources by default; no unrestricted host/private network; truthful failures.

## 23. Artifact Workspace

Versioned/provenanced work products with ACL/review/human edit preservation. External share/send is separate governed action.

## 24. Predictive Intelligence

Prediction carries model/version/horizon/freshness/limitations and is not FACT.

## 25. Prescriptive Intelligence

Recommendation/PREPARE only; `recommendation != authorization`.

## 26. Operational Twin / What-if

Scenario projection only; `SIMULATE != APPLY`; Twin is not source of truth.

## 27. MCP / A2A interoperability

Approved adapters/allowlists/scopes, least delegated context, cancellation/budget, normalized Evidence/Outcome, same write governance, discovery != approval.

## 28. AI Control Tower

Governance projection for AI/model/automation/connectors/tool-agent/Edge assets. Not a second planner/business authority.

## 29. AI Model Lifecycle / MLOps

Eval→approval→deployment→monitor/drift→rollback/revoke, with canonical owner. Router selects only approved assets.

## 30. Capability Marketplace

Governed catalog; package requirements never grant permissions; executable assets require supply-chain controls.

## 31. Edge / Offline

Governed local cache/inference/event buffering only when approved; offline never widens authority; Edge does not grant OT actuation.

## 32. Meeting Mode

Transcript/source/decision/candidate action/executed outcome remain distinct.

## 33. Frontline Mode

Large-touch/hands-free/current procedure/revision/operational context with governed media/Edge support. DÉLIA is not safety controller.

## 34. Organizational Learning

```text
Evidence
→ candidate
→ owner/review
→ eval
→ version
→ publish
```

No one-run auto-learning.

## 35. Iframe / AI-ready onboarding

Bridge for context/visual commands; Business Actions remain API/use-case based. UI state/bridge metadata never grants permission.

## 36. Model Router / Compute Policy

Select only approved model/deployment candidates. Router is not lifecycle/registry/permission authority.

## 37. Security / Privacy / Industrial Safety

- no secret/token leakage;
- source/user isolation;
- safe egress;
- no hidden biometric/task surveillance;
- sandbox bounded;
- external/tool/package content untrusted;
- Prediction != FACT;
- Twin != production;
- Edge offline != permission expansion;
- Marketplace install != permission;
- no arbitrary LLM/voice/vision/RPA/Edge→machine actuation.

## 38. Administração

Role-gated surfaces may include Connections, Automation governance projection, Process Intelligence, Control Tower, Semantic Catalog, Memory controls, Artifact Workspace, Model Governance, Marketplace and Edge Fleet. Admin access does not imply underlying business permission.

## 39. Final experience

DÉLIA should understand authorized context, find evidence, analyze/predict/simulate with epistemic clarity, prepare/execute governed work through canonical contracts, verify real outcomes, communicate status and learn only through explicit governance.
