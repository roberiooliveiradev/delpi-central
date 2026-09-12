# Minha DELPI Copilot — Rollout, Migrações e Implantação

**Status:** plano operacional standalone  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Estratégia

O Copilot nasce como **novo par de aplicação** dentro da plataforma:

```text
minha-delpi-copilot-api
plugins/minha-delpi-copilot
```

Ele reutiliza as foundations corporativas:

```text
Portal
Core API
Keycloak
Gateway
plugin-ui
Module Federation
Domain APIs
infra compartilhada aprovada
```

Ele **não migra runtime do Minha DELPI Chat**.

As surfaces Global/Workspace/Meeting/Frontline são liberadas progressivamente sobre o mesmo runtime.

## 2. Releases C0–C7

### R0 — Foundation Freeze / C0

- platform inventory;
- media/device/privacy/OT inventory;
- standalone boundary;
- service/path/manifest/storage naming;
- authorities/primitives;
- MediaRef decision;
- architecture/pattern freeze;
- privacy/retention/shared-device boundaries;
- industrial safety non-authority;
- integration contracts;
- RED conformance harness;
- `CHAT_RUNTIME_DEPENDENCY=0`.

No runtime code yet.

### R1 — Standalone Bootstrap / C1

- Copilot API skeleton;
- health/config/logging;
- JWT + Core integration;
- Copilot MFE skeleton;
- federation/plugin-ui;
- responsive/accessibility baseline;
- media-permission baseline without capture;
- own manifest;
- Gateway routes;
- Compose services;
- Portal full-page mount;
- global host/panel contract;
- independent rollback;
- Chat-offline independence test.

### R2 — Portal + Operational Context / C2

- Workspace Context;
- Global Bridge;
- Platform Capability Projection;
- open app/route/entity;
- MFE context/deep-link helper;
- OP/machine/product/operation EntityRefs where proven;
- shared-device/session context baseline;
- iframe integration baseline.

### R3 — Intelligence + Multimodal Foundations / C3

- Copilot-owned conversation/turn model;
- provider abstraction;
- OpenAPI ingestion + Action Catalog;
- capability retrieval;
- planner;
- expertise/playbooks;
- Knowledge/RAG;
- document/image multimodal;
- speech baseline when prioritized;
- short-video/screen ingestion when prioritized;
- Evidence/media provenance;
- media retention/policy enforcement;
- eval/observability.

No Chat agent/session/action/media migration.

### R4 — Business Reads + Graph / C4

- generic reads;
- normalized outcomes/evidence;
- Business Graph;
- operational-context correlation;
- cross-domain analysis;
- unknown/metamorphic provider gates.

Rollout read-only first.

### R5 — Governed Writes + Durable Foundation / C5

- Decision Gates;
- impact preview;
- generic writes;
- idempotency/concurrency;
- outcome verification;
- WorkflowPlan/checkpoints/waits;
- modality-to-action governance;
- restart/replay safety.

Start with low/medium-risk non-destructive writes.

### R6 — Product Work + Meeting/Frontline + Proactivity / C6

- Tasks;
- Cases/Evidence Board;
- Room integration;
- Inbox;
- Watch OBSERVE/ADVISE;
- Meeting Mode;
- ata viva;
- Frontline Mode;
- hands-free/operator assistance;
- training assistance;
- process-observation knowledge candidates;
- Organizational Knowledge;
- Governed Learning;
- Expertise Studio;
- AI-ready onboarding/admin.

Meeting/Frontline are piloted by cohort/device/process, not enabled company-wide by default on first release.

### R7 — Advanced Realtime + Autonomy + Optimization / C7

- L0–L5 final policy;
- Watch ACT selected;
- Simulation;
- Model Router;
- advanced realtime media when justified;
- edge/device optimization when justified;
- performance/cost/scaling;
- progressive rollout;
- Product Complete verification.

OT physical actuation remains blocked unless a **separate industrial safety initiative/gate** authorizes a deterministic integration.

## 3. Migration policy

There is **no Chat→Copilot migration** required for this initiative.

Copilot schema/contract changes follow:

```text
EXPAND
→ compatible readers
→ writers
→ BACKFILL if necessary
→ CUTOVER
→ MONITOR
→ CLEANUP
```

Existing platform/domain/media integration requiring adaptation may use:

```text
existing owner
→ Adapter / Anti-Corruption Layer
→ Copilot canonical contract
```

Strangler applies only where an actual legacy integration is being replaced; it does not imply migrating the Chat into the Copilot.

## 4. Storage rollout

- Copilot has its own migration chain;
- physical PostgreSQL may be shared if approved;
- logical table/schema ownership remains separate;
- no Chat table edits;
- no Chat foreign keys as Copilot authority;
- create storage only after C0 proves durable need;
- raw media persistence is opt-in by purpose/policy;
- media metadata and artifacts use lifecycle/retention classes.

## 5. Infra rollout

Dev/prod evolve together for:

```text
Copilot API Dockerfile/service
Copilot MFE Dockerfile/service
Gateway API route
Gateway MFE route
Compose service/profile
health checks
env examples
sequential scripts
volumes/storage
manifest registration
```

Streaming/media infra is added only when actual transport/provider requires it.

No `depends_on` Chat.

## 6. Portal rollout

Order:

```text
full-page federated app
→ internal users
→ global side-panel host
→ broader authorized groups
```

Both use the same MFE/runtime.

Meeting/Frontline surfaces are enabled later by capability/feature policy and appropriate devices/cohorts, not by creating separate Portal apps unless a real UX/deployment need is proven.

## 7. Business capability rollout

```text
OpenAPI ingestion
→ read-only capabilities
→ cross-domain reads
→ low-risk governed writes
→ durable workflows
→ Watch advice
→ Meeting action follow-up
→ Frontline issue/escalation actions
→ selected ACT/autonomy
```

No action goes production because a model can “probably call it”; schema/RBAC/policy/evals must pass.

## 8. Multimodal rollout

Prefer progressive value/risk:

```text
documents/images
→ voice input/output
→ camera snapshots
→ short video/screen share
→ Meeting pilot
→ Frontline pilot
→ sampled/continuous realtime only if evidence justifies
```

Each step requires privacy/retention/provider/latency/cost evidence.

Do not jump directly to continuous video.

## 9. Meeting rollout

Recommended progression:

```text
internal meeting transcript/summary pilot
→ grounded live business queries
→ decision/pending-action extraction
→ ata viva
→ Task/Case/Room linkage
→ selected departments
→ broader authorized availability
```

Gates before expansion:

- capture indicators/consent;
- summary/action accuracy;
- source/RBAC compliance;
- retention/deletion;
- action governance;
- cost/latency;
- clear stop/rollback.

## 10. Frontline rollout

Do not infer first factory pilot from administrative Wave 1.

Select after C0 evidence based on:

- device availability;
- browser/network reliability;
- process owner;
- procedure/drawing source quality;
- production context/API readiness;
- safety/privacy complexity;
- operator value;
- low initial actuation risk.

Recommended progression:

```text
read-only/context help
→ procedure/drawing assistance
→ voice hands-free
→ camera/image assistance
→ governed issue/escalation
→ Task/Case linkage
→ training assistance
→ knowledge candidate capture
```

No machine actuation in default Frontline rollout.

## 11. Process-learning rollout

```text
candidate creation only
→ domain expert review
→ eval
→ versioned Knowledge/Playbook update
→ canary
→ broader publish
```

Do not score operators or auto-change standard work from raw observation.

## 12. Feature flags

Each flag requires:

```text
name
owner
scope
introducedAt
successCriteria
rollbackTrigger
exitCriteria
plannedRemoval
```

Useful families:

```text
copilot-app-bootstrap
global-panel
workspace-context
platform-commands
intelligence-core
multimodal-document-image
voice
camera-video
meeting-mode
frontline-mode
business-reads
business-graph
governed-writes
durable-work
watch
selected-autonomy
model-routing
advanced-realtime
```

Flags do not authorize permanent duplicate architectures or business permission.

## 13. Cohorts

- environment;
- user/group;
- app/domain;
- capability family;
- surface;
- device/workstation class;
- production area/process when applicable;
- autonomy level.

Cohort never grants business permission.

## 14. Privacy/media rollout gate

Before enabling media capture for a cohort:

```text
purpose defined
capture indicator verified
retention class defined
raw persistence yes/no explicit
provider/data policy approved
access/delete path known
shared-device cleanup tested
incident disable/kill switch ready
```

## 15. Industrial/OT rollout gate

Default rollout contains **no free-form physical actuation**.

If a future initiative proposes OT actuation, it is not a normal Copilot flag. It requires separate approval/evidence for:

- industrial owner;
- risk assessment;
- deterministic typed command schema;
- allowlist;
- machine state/preconditions;
- independent safety PLC/interlocks;
- authorization;
- simulation/test environment;
- fail-safe/kill switch;
- audit.

## 16. Rollback

### Bootstrap
Disable Copilot routes/services/manifest version; Portal and Chat continue normally.

### Context/Platform
Disable bridge/panel; full Portal remains functional.

### Intelligence
Disable candidate provider/feature; Copilot may degrade to explicit unavailable mode, never silently delegate to Chat.

### Media
Disable modality/provider; stop new sessions; preserve/delete retained data according to policy. Do not silently switch to unapproved provider.

### Meeting
Disable new Meeting sessions; existing artifacts remain governed/accessible per policy.

### Frontline
Disable Frontline surface/capabilities and fall back to existing operational process, not to unsafe automation.

### Reads/Graph
Remove capability availability; Domain APIs continue normally.

### Writes
Switch Copilot to read-only; preserve audit/outcomes.

### Durable Work
Block new workflows and preserve running/waiting state safely.

### Watch
Disable triggers while preserving history.

### Model Router
Return to known baseline Compute Policy.

**Rollback must never mean “fallback to Minha DELPI Chat runtime”.**

## 17. Before any migration/new abstraction

1. prove owner/boundary;
2. prove durable need;
3. ensure no Chat coupling;
4. reuse C0 primitives;
5. apply Pattern Decision Matrix;
6. pass Abstraction Gate;
7. define privacy/retention/LGPD when applicable;
8. concurrency/idempotency;
9. forward/backout path;
10. tests/observability;
11. shared-device impact;
12. industrial safety impact;
13. check known next-phase impact;
14. ADR for material exception.

## 18. Stop-the-line

- Chat runtime/API/table dependency;
- unauthorized data/action;
- duplicate authority;
- architecture/pattern drift;
- framework/provider leak into inner layers;
- Portal AI/media logic leak;
- domain business-rule duplication;
- write without required Decision Gate;
- duplicate write after retry/resume/voice repeat;
- Graph/Case/Room permission leakage;
- Watch ACT without policy;
- secret/token leak;
- hidden media capture;
- undefined/violated media retention;
- shared-device user-state leak;
- hidden worker surveillance;
- visual finding promoted to official fact without owner;
- arbitrary LLM→machine command;
- safety interlock bypass;
- migration without safe rollback;
- stale/non-reproducible evidence.

## 19. Promotion criteria

- phase COMPLETE_GATE PASS;
- current SHA evidence;
- required tests PASS;
- architecture conformance PASS;
- security/RBAC negatives PASS;
- privacy/shared-device/OT gates PASS when applicable;
- Chat-independence PASS;
- metrics/traces available;
- rollback tested;
- docs/ledger consistent.

## 20. Production progression

```text
standalone bootstrap internal
→ contextual platform internal
→ intelligence/read canary
→ read scale
→ governed write canary
→ durable work selected
→ Meeting pilot
→ Frontline read/help pilot
→ Watch advise selected
→ broader Meeting/Frontline after evidence
→ selected ACT/autonomy
→ advanced realtime only after value/cost/privacy proof
→ metrics/incident review
→ progressive expansion
```

The Copilot must remain deployable, operable and reversible independently of the Minha DELPI Chat throughout this progression.