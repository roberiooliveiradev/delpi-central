# Minha DELPI Copilot — Rollout, Migrações e Implantação

**Status:** plano operacional standalone  
**Autoridade de ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)

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

## 2. Releases C0–C7

### R0 — Foundation Freeze / C0

- platform inventory;
- standalone boundary;
- service/path/manifest/storage naming;
- authorities/primitives;
- architecture/pattern freeze;
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
- own manifest;
- Gateway routes;
- Compose services;
- Portal full-page mount;
- global host/panel contract;
- independent rollback;
- Chat-offline independence test.

### R2 — Portal Context / C2

- Workspace Context;
- Global Bridge;
- Platform Capability Projection;
- open app/route/entity;
- MFE context/deep-link helper;
- iframe integration baseline.

### R3 — Intelligence Core / C3

- Copilot-owned conversation/turn model;
- provider abstraction;
- OpenAPI ingestion + Action Catalog;
- capability retrieval;
- planner;
- expertise/playbooks;
- Knowledge/RAG;
- multimodal/evidence;
- eval/observability.

No Chat agent/session/action migration.

### R4 — Business Reads + Graph / C4

- generic reads;
- normalized outcomes/evidence;
- Business Graph;
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
- restart/replay safety.

Start with low/medium-risk non-destructive writes.

### R6 — Product Work + Proactivity / C6

- Tasks;
- Cases/Evidence Board;
- Room integration;
- Inbox;
- Watch OBSERVE/ADVISE;
- Organizational Knowledge;
- Governed Learning;
- Expertise Studio;
- AI-ready onboarding/admin.

### R7 — Autonomy + Optimization / C7

- L0–L5 final policy;
- Watch ACT selected;
- Simulation;
- Model Router;
- performance/cost/scaling;
- progressive rollout;
- Product Complete verification.

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

Existing platform integration requiring adaptation may use:

```text
existing platform/domain owner
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
- create storage only after C0 proves durable need.

## 5. Infra rollout

Dev/prod must evolve together for:

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

No `depends_on` Chat.

## 6. Portal rollout

Order:

```text
full-page federated app
→ internal users
→ global side-panel host
→ broader groups
```

Both surfaces use the same MFE/runtime. The Portal host remains thin.

## 7. Business capability rollout

```text
OpenAPI ingestion
→ read-only capabilities
→ cross-domain reads
→ low-risk governed writes
→ durable workflows
→ Watch advice
→ selected ACT/autonomy
```

No action goes production because a model can “probably call it”; schema/RBAC/policy/evals must pass.

## 8. Feature flags

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
business-reads
business-graph
governed-writes
durable-work
watch
selected-autonomy
model-routing
```

Flags do not authorize permanent duplicate architectures.

## 9. Cohorts

- environment;
- user/group;
- app/domain;
- capability family;
- autonomy level.

Cohort never grants business permission.

## 10. Rollback

### Bootstrap
Disable Copilot routes/services/manifest version; Portal and Chat continue normally.

### Context/Platform
Disable bridge/panel; full Portal remains functional.

### Intelligence
Disable candidate provider/feature; Copilot may degrade to explicit unavailable mode, never silently delegate to Chat.

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

## 11. Before any migration/new abstraction

1. prove owner/boundary;
2. prove durable need;
3. ensure no Chat coupling;
4. reuse C0 primitives;
5. apply Pattern Decision Matrix;
6. pass Abstraction Gate;
7. define retention/LGPD;
8. concurrency/idempotency;
9. forward/backout path;
10. tests/observability;
11. check known next-phase impact;
12. ADR for material exception.

## 12. Stop-the-line

- Chat runtime/API/table dependency;
- unauthorized data/action;
- duplicate authority;
- architecture/pattern drift;
- framework/provider leak into inner layers;
- Portal AI logic leak;
- domain business-rule duplication;
- write without required Decision Gate;
- duplicate write after retry/resume;
- Graph/Case/Room permission leakage;
- Watch ACT without policy;
- secret/token leak;
- migration without safe rollback;
- stale/non-reproducible evidence.

## 13. Promotion criteria

- phase COMPLETE_GATE PASS;
- current SHA evidence;
- required tests PASS;
- architecture conformance PASS;
- security/RBAC negatives PASS;
- Chat-independence PASS;
- metrics/traces available;
- rollback tested;
- docs/ledger consistent.

## 14. Production progression

```text
standalone bootstrap internal
→ contextual platform internal
→ intelligence/read canary
→ read scale
→ governed write canary
→ durable work selected
→ Watch advise selected
→ selected ACT/autonomy
→ metrics/incident review
→ progressive expansion
```

The Copilot must remain deployable, operable and reversible independently of the Minha DELPI Chat throughout this progression.