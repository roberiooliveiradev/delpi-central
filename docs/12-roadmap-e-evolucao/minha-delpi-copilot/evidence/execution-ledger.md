# Minha DELPI Copilot — Execution Ledger

**Status:** `PLANNED / NOT_STARTED`  
**Product boundary:** standalone application  
**Plan:** [`../16-execution-master-plan.md`](../16-execution-master-plan.md)  
**Boundary:** [`../50-standalone-copilot-application-architecture.md`](../50-standalone-copilot-application-architecture.md)  
**Baseline:** [`../51-platform-integration-baseline.md`](../51-platform-integration-baseline.md)  
**Bootstrap:** [`../52-standalone-repository-and-bootstrap-plan.md`](../52-standalone-repository-and-bootstrap-plan.md)  
**Patterns:** [`../49-architecture-and-design-patterns-standard.md`](../49-architecture-and-design-patterns-standard.md)  
**Next:** **C0.S0 — Platform/monorepo rebaseline**

## 1. Ledger rule

This file records execution/evidence only. It does not redefine architecture or sequence.

## 2. Canonical phase status

| Fase | Status | Próximo step | Dependência |
|---|---|---|---|
| C0 Platform + Architecture Foundations | **NOT_STARTED** | **C0.S0** | none |
| C1 Standalone Bootstrap | LOCKED | — | C0.S7 FOUNDATION_FREEZE |
| C2 Portal Context + Commands | LOCKED | — | C1 independence gate |
| C3 Intelligence Core | LOCKED | — | C1+C2 foundations |
| C4 Business Reads + Graph | LOCKED | — | C3 action/capability foundation |
| C5 Writes + Durable Foundation | LOCKED | — | C4 reads/evidence |
| C6 Product Work + Proactivity | LOCKED | — | C5 durable/safety |
| C7 Autonomy + Optimization | LOCKED | — | C0–C6 gates |

## 3. C0 sequence

```text
C0.S0 platform/monorepo inventory
→ C0.S1 standalone boundary/names
→ C0.S2 authorities/bounded contexts
→ C0.S3 shared primitives
→ C0.S4 architecture/persistence boundaries
→ C0.S5 integration contracts
→ C0.S6 RED contract/conformance harness
→ C0.S7 FOUNDATION_FREEZE
```

## 4. Current architectural decisions

```text
COPILOT_PRODUCT = STANDALONE_NEW_APPLICATION
COPILOT_API = NEW_OWN_SERVICE
COPILOT_MFE = NEW_OWN_MICROFRONTEND
CHAT_RUNTIME_DEPENDENCY = FORBIDDEN
CHAT_DATABASE_AUTHORITY = FORBIDDEN
CHAT_API_PROXY_DEPENDENCY = FORBIDDEN
CHAT_AGENT_MIGRATION = OUT_OF_SCOPE
OPENAPI_FIRST = NATIVE_COPILOT_FOUNDATION
PORTAL_ROLE = HOST_CONTEXT_NAVIGATION
CORE_ROLE = APPS_ROUTES_RBAC_GOVERNANCE
KEYCLOAK_ROLE = IDENTITY_SSO
DOMAIN_APIS = BUSINESS_AUTHORITIES
PLUGIN_UI = SHARED_DESIGN_SYSTEM
BUSINESS_GRAPH = COPILOT_PROJECTION_NOT_MASTER_DATA
SINGLE_COPILOT_IDENTITY = TARGET
EXPERTISE_PACKS = PLANNED
DOMAIN_PLAYBOOKS = PLANNED
EVIDENCE_PROVENANCE = FOUNDATION_CONTRACT
DECISION_GATE = FOUNDATION_CONTRACT
DURABLE_WORKFLOW = PLANNED
TASK_CASE_WATCH_INBOX = PLANNED
SIMULATION = C7
MODEL_ROUTER = C7

ARCHITECTURE_STYLE = CLEAN_ARCHITECTURE_PORTS_ADAPTERS_PRAGMATIC_DDD
EVENT_DRIVEN = ONLY_WITH_REAL_EVENT_OWNER
STATE_MACHINE = NONTRIVIAL_LIFECYCLES
CQRS = LIGHT_JUSTIFIED_ONLY
COMPOSITION_ROOT_DI = REQUIRED
ABSTRACTION_GATE = REQUIRED
```

All remain `PLAN_ONLY` until runtime evidence.

## 5. Superseded decisions

```text
Copilot extends minha-delpi-ai-api            = SUPERSEDED
Copilot extends plugins/minha-delpi-chat      = SUPERSEDED
Copilot blocked by Chat llm-json/Onda J       = SUPERSEDED
Copilot migrates AgentSpecializationService   = OUT_OF_SCOPE
Copilot removes userActivatedAgent in Chat    = OUT_OF_SCOPE
Copilot removes Chat soft handoff              = OUT_OF_SCOPE
Copilot migrates Chat agent_id/chat_mode       = OUT_OF_SCOPE
```

## 6. Planning history

| Data | Evento | Status |
|---|---|---|
| 2026-09-12 | initial Copilot architecture | PLAN_ONLY |
| 2026-09-12 | iframe bridge incorporated | PLAN_ONLY |
| 2026-09-12 | single Copilot + expertise/playbooks | PLAN_ONLY |
| 2026-09-12 | Business Graph/Tasks/Cases/Rooms/Inbox/Watch/Evidence/Decision | PLAN_ONLY |
| 2026-09-12 | foundation-first reordering | PLAN_ONLY |
| 2026-09-12 | normative architecture/design patterns | PLAN_ONLY |
| 2026-09-12 | **standalone decision: own API + own MFE, Chat fully decoupled** | PLAN_ONLY; docs only |
| 2026-09-12 | Portal/Core/Gateway/APIs/MFE factual baseline documented | PLAN_ONLY; docs only |
| 2026-09-12 | **documentation consistency cleanup:** phase drift removed from Decision/Durable/Knowledge/Studio/Model Router/Operational map/UX/Observability/Benchmark; `32` and `44` restored as active thematic specs; `31` and `45–47` remain superseded | PLAN_ONLY; docs only; audited through `4ba3ac8cd2928429901b22600a3a074257883a0a` before this ledger commit |

Actual `HEAD_BEFORE` for runtime is captured at C0.S0. Documentation-only commits do not advance execution status.

## 7. Canonical phase mapping after cleanup

```text
C0 → platform inventory + standalone boundary + shared foundations
C1 → API/MFE/Manifest/Gateway/Compose/Portal bootstrap + Chat-offline independence
C2 → Workspace Context + Platform Commands
C3 → provider baseline + conversation + OpenAPI ingestion + capability retrieval + Expertise + Playbooks + Knowledge + Multimodal + Evidence + Planner
C4 → generic business reads + Evidence normalization + Business Graph + cross-domain analysis
C5 → Decision Gates + writes + Outcome verification + Durable Workflow/checkpoints/waits
C6 → Task + Case + Room + Inbox + Watch OBSERVE/ADVISE + Organizational Knowledge/Learning + Expertise Studio + AI-ready ecosystem
C7 → autonomy + Watch ACT + Simulation + Model Router + scale/rollout
```

Any thematic document diverging from this mapping is documentation drift and must be corrected against `16`.

## 8. Required C0.S0 inventory

### Portal
```text
AuthContext/Keycloak
AppHost federated lifecycle
AppLauncher/Router
panel/drawer/global host infrastructure
getAccessToken/host props
federation share scope
notifications/socket/context
```

### Core
```text
/me /me/apps /me/routes
RBAC/permission resolver
manifest/versioning
app/route models
notifications/audit/presence
```

### Gateway/Infra
```text
MFE/API path conventions
dev/prod parity
Compose profiles/services
env/health/scripts
postgres/storage/network
```

### Apps/MFEs/APIs
```text
manifests
mount/unmount/federation/plugin-ui
HTTP/auth clients
Workspace/deep-link contracts
Domain APIs/OpenAPIs
auth/permissions/errors/pagination
entity IDs
idempotency/events/websockets
```

### Collaboration/work
```text
interaction rooms
requests/cases
notifications/inbox-like concepts
approvals
workers/jobs/schedulers/events
```

### Chat reference only
```text
architecture/providers/RAG/multimodal/actions
lessons/anti-patterns
neutral shared-library candidates only
```

Finding classification:

```text
PLATFORM_REUSE
NEUTRAL_SHARED_REUSE
COPILOT_IMPLEMENT_NEW
EXTEND_PLATFORM_CONTRACT
ADAPTER_REQUIRED
ADR_REQUIRED
NOT_PROVEN
OUT_OF_SCOPE
```

## 9. Required C0 outputs

- revalidated `51` baseline;
- owners/contracts map;
- app/API/OpenAPI inventory;
- manifest/federation inventory;
- entity/deep-link/event/room/notification inventory;
- service/path/manifest/storage names frozen;
- architecture/pattern inventory/freeze;
- Copilot integration contracts;
- RED/conformance harness;
- CP status update;
- ledger with actual HEAD/evidence.

No agent migration matrix is required.

## 10. Requirements authority

`25-requirements-traceability.md` is the single CP authority.

```text
CP-001–CP-154
```

Standalone additions are `CP-141–CP-154`. Historical Chat migration requirements remain `OUT_OF_SCOPE_WITH_DECISION`.

## 11. Test authority

`20-testing-and-acceptance-matrix.md`.

Required standalone gates include:

```text
NO_CHAT_IMPORT
NO_CHAT_API_DEP
NO_CHAT_DB_AUTHORITY
CHAT_OFFLINE_INDEPENDENCE
INDEPENDENT_DEPLOY_ROLLBACK
```

## 12. Event template

```text
DATE:
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
DEPENDENCY_GATE:
CP_REQUIREMENTS:
CANONICAL_OWNERS:
LAYER/PATTERNS:
PLATFORM_REUSE:
COPILOT_NEW_CODE:
CHAT_DEPENDENCIES:
EVIDENCE:
TESTS:
CHAT_INDEPENDENCE:
ARCHITECTURAL_CONFORMANCE:
FOUNDATION_DRIFT:
COMPLETE_GATE:
NEXT_UNLOCKED:
NOTES:
```

## 13. Allowed states

```text
NOT_STARTED
READY_TO_EXECUTE
IN_PROGRESS
BLOCKED_WITH_EVIDENCE
EXECUTION_DRIFT
FAIL
PASS
LOCKED
```

## 14. COMPLETE_GATE blockers

```text
PARTIAL
INCONCLUSIVE
PENDING
TEST_NOT_RUN
STALE_EVIDENCE
DUPLICATE_AUTHORITY
FOUNDATION_DRIFT
ARCHITECTURE_PATTERN_DRIFT
UNJUSTIFIED_ABSTRACTION
CHAT_RUNTIME_IMPORT
CHAT_API_REQUIRED
CHAT_DATABASE_AUTHORITY
CHAT_MIGRATION_DEPENDENCY
PORTAL_AI_LOGIC_LEAK
DOMAIN_RULE_DUPLICATION
```

## 15. First execution

Open `23-prompt-cursor-execucao.md` and execute **C0.S0 only**.

The first code after Foundation Freeze is the standalone Copilot API/MFE bootstrap, not intelligence features.