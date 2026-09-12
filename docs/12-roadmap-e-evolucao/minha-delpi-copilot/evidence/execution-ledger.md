# Minha DELPI Copilot — Execution Ledger

**Status:** `PLANNED / NOT_STARTED`  
**Product boundary:** standalone application  
**Plan:** [`../16-execution-master-plan.md`](../16-execution-master-plan.md)  
**Boundary:** [`../50-standalone-copilot-application-architecture.md`](../50-standalone-copilot-application-architecture.md)  
**Baseline:** [`../51-platform-integration-baseline.md`](../51-platform-integration-baseline.md)  
**Bootstrap:** [`../52-standalone-repository-and-bootstrap-plan.md`](../52-standalone-repository-and-bootstrap-plan.md)  
**Patterns:** [`../49-architecture-and-design-patterns-standard.md`](../49-architecture-and-design-patterns-standard.md)  
**Multimodal/Meeting/Frontline:** [`../53-multimodal-meeting-frontline-and-industrial-copilot.md`](../53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`../54-biometric-identity-and-human-observation-governance.md`](../54-biometric-identity-and-human-observation-governance.md)  
**Next:** **C0.S0 — Platform/Media/Device/Biometric/OT rebaseline**

## 1. Ledger rule

This file records execution/evidence only. It does not redefine architecture or sequence.

Documentation-only changes do not advance runtime phase status.

## 2. Canonical phase status

| Fase | Status | Próximo step | Dependência |
|---|---|---|---|
| C0 Platform + Architecture + Media/Privacy/Biometric/OT Foundations | **NOT_STARTED** | **C0.S0** | none |
| C1 Standalone Bootstrap | LOCKED | — | C0.S7 FOUNDATION_FREEZE |
| C2 Portal + Operational Context + Commands | LOCKED | — | C1 independence gate |
| C3 Intelligence + Multimodal/Biometric Foundations | LOCKED | — | C1+C2 foundations |
| C4 Business Reads + Graph | LOCKED | — | C3 action/capability/media foundation |
| C5 Writes + Durable Foundation | LOCKED | — | C4 reads/evidence |
| C6 Product Work + Meeting/Frontline + Proactivity | LOCKED | — | C5 durable/safety |
| C7 Advanced Realtime + Autonomy + Optimization | LOCKED | — | C0–C6 gates |

## 3. C0 sequence

```text
C0.S0 platform/monorepo/media/device/biometric/OT inventory
→ C0.S1 standalone boundary/names
→ C0.S2 authorities/bounded contexts
→ C0.S3 shared primitives/MediaRef/biometric-ref decisions
→ C0.S4 architecture/persistence/privacy/media/biometric boundaries
→ C0.S5 integration contracts
→ C0.S6 RED contract/conformance/privacy/device/biometric/OT harness
→ C0.S7 FOUNDATION_FREEZE
```

## 4. Current architectural decisions

```text
COPILOT_PRODUCT = STANDALONE_NEW_APPLICATION
COPILOT_API = NEW_OWN_SERVICE
COPILOT_MFE = NEW_OWN_MICROFRONTEND
COPILOT_SURFACES = GLOBAL | WORKSPACE | MEETING | FRONTLINE
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

MULTIMODAL_TARGET = TEXT | VOICE | IMAGE | DOCUMENT | VIDEO | SCREEN
MEDIA_REF = C0_DECISION_REQUIRED
MEDIA_RETENTION = CLASS_SPECIFIC_POLICY
RAW_MEDIA_PERSISTENCE = NOT_DEFAULT
CAPTURE_VISIBILITY = REQUIRED
SHARED_DEVICE_USER_ISOLATION = REQUIRED
DEVICE_IDENTITY_EQUALS_USER_IDENTITY = FORBIDDEN
OPERATIONAL_CONTEXT = WORKSPACE_CONTEXT_PLUS_ENTITY_REFS
MEETING_ACTION = CANDIDATE_UNTIL_GOVERNED
PROCESS_LEARNING = CANDIDATE_ONLY_UNTIL_REVIEW_EVAL_PUBLISH
BIOMETRIC_IDENTITY = GOVERNED_OPTIONAL_CAPABILITY
FACE_RECOGNITION = CLOSED_SET_ENROLLED_USERS_ONLY
SPEAKER_RECOGNITION = GOVERNED_OPTIONAL_CAPABILITY
BIOMETRIC_MATCH_EQUALS_AUTHORIZATION = FALSE
LOW_CONFIDENCE_IDENTITY = UNKNOWN_OR_CONFIRM
BIOMETRIC_TEMPLATE = PROTECTED_REVOCABLE_NO_LOGGING
HUMAN_OBSERVATION = OBSERVABLE_PROCESS_EVIDENCE_ONLY
EMOTION_PERSONALITY_CHARACTER_INFERENCE = FORBIDDEN_BY_DEFAULT
AUTOMATIC_EMPLOYMENT_DECISION_FROM_BIOMETRICS = FORBIDDEN
HIDDEN_WORKER_PROFILING = FORBIDDEN_BY_DEFAULT
VISUAL_FINDING_DEFAULT = EVIDENCE_OR_HYPOTHESIS
OT_ACTUATION = BLOCKED_BY_DEFAULT
COPILOT_IS_SAFETY_CONTROLLER = FALSE

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
Facial recognition universally out of scope   = SUPERSEDED_BY_GOVERNED_BIOMETRIC_CAPABILITY
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
| 2026-09-12 | standalone decision: own API + own MFE, Chat fully decoupled | PLAN_ONLY; docs only |
| 2026-09-12 | Portal/Core/Gateway/APIs/MFE factual baseline documented | PLAN_ONLY; docs only |
| 2026-09-12 | documentation consistency cleanup and phase remapping | PLAN_ONLY; docs only |
| 2026-09-12 | North Star expanded to Global/Workspace/Meeting/Frontline with voice/image/video, shared-device/privacy boundaries and default OT no-actuation | PLAN_ONLY; docs only |
| 2026-09-12 | `53` created; master plan/patterns/state/tests/requirements/prompt updated through `CP-181` | PLAN_ONLY; docs only |
| 2026-09-12 | **Biometric Identity + Human Observation added as governed capabilities; `54` created; requirements extended through `CP-193`** | PLAN_ONLY; docs only |

Actual `HEAD_BEFORE` for runtime is captured at C0.S0. Documentation-only commits do not advance execution status.

## 7. Canonical phase mapping

```text
C0 → platform/media/device/biometric/OT inventory + standalone/shared foundations
C1 → API/MFE/Manifest/Gateway/Compose/Portal bootstrap + Chat-offline independence
C2 → Workspace/Operational Context + Platform Commands + shared-device baseline
C3 → provider baseline + conversation + OpenAPI + capability + Expertise + Knowledge + multimodal/media/biometric foundations + Evidence + Planner
C4 → generic reads + Evidence normalization + Business Graph + operational context correlation
C5 → Decision Gates + writes + Outcome verification + Durable Workflow + modality-to-action governance
C6 → Task + Case + Room + Inbox + Watch + Meeting + Frontline + governed biometric identity + Human Observation + Organizational Knowledge/Learning + Expertise Studio
C7 → advanced realtime + autonomy + Watch ACT + Simulation + Model Router + scale/rollout
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
responsive/accessibility
browser media/capture patterns if any
```

### Core
```text
/me /me/apps /me/routes
RBAC/permission resolver
manifest/versioning
app/route models
notifications/audit/presence
corporate avatar/photo sources
device/session patterns if any
```

### Gateway/Infra
```text
MFE/API path conventions
dev/prod parity
Compose profiles/services
env/health/scripts
postgres/storage/network
object/media storage
encrypted sensitive storage/key management
SSE/WebSocket/WebRTC patterns
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
meeting/collaboration artifacts
procedures/training sources
```

### Media/Meeting/Frontline/Biometric
```text
speech/vision/media providers
recording/transcription patterns
privacy/consent/retention owners
shared devices/tablets/kiosks
production terminals
meeting room hardware/processes
network/noise/accessibility constraints
corporate photo/avatar sources
voice sample sources if any
biometric enrollment owner/process
biometric template storage/key management
face/speaker recognition providers if any
liveness/anti-spoof capability if any
participant lists/presence sources
Human Observation governance owner
```

### Operational/OT
```text
OP/operation/machine/product/lot/material/workstation IDs/owners
production/maintenance/quality source APIs
drawing/procedure/revision owners
OT telemetry/interfaces
machine command interfaces as factual inventory only
industrial safety/interlock owners
IT/OT segregation
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
- media/device/meeting/frontline/biometric inventory;
- privacy/consent/retention inventory;
- biometric enrollment/template/liveness decision;
- prohibited human-inference classes frozen;
- production/maintenance/quality context inventory;
- OT/industrial safety inventory;
- service/path/manifest/storage names frozen;
- MediaRef/biometric-ref decisions;
- architecture/pattern inventory/freeze;
- Copilot integration contracts;
- RED/conformance/privacy/device/biometric/OT harness;
- CP status update;
- ledger with actual HEAD/evidence.

No agent migration matrix is required.

## 10. Requirements authority

`25-requirements-traceability.md` is the single CP authority.

```text
CP-001–CP-193
```

`CP-155–CP-181` cover expanded access/multimodal/Meeting/Frontline/privacy/shared-device/industrial safety.  
`CP-182–CP-193` cover governed biometric identity and Human Observation.

Historical Chat migration requirements remain `OUT_OF_SCOPE_WITH_DECISION`.

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

When relevant:

```text
NO_HIDDEN_CAPTURE
RETENTION_POLICY_ENFORCED
MODALITY_RBAC_PARITY
SHARED_DEVICE_ISOLATION
BIOMETRIC_MATCH_NOT_AUTHORITY
UNKNOWN_IDENTITY_REMAINS_UNKNOWN
BIOMETRIC_TEMPLATE_PROTECTED
NO_SENSITIVE_PERSON_INFERENCE
NO_AUTOMATIC_EMPLOYMENT_DECISION_FROM_BIOMETRICS
VISUAL_EVIDENCE_SEMANTICS
NO_HIDDEN_WORKER_PROFILING
NO_ARBITRARY_OT_COMMAND
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
MEDIA_DEVICE_BIOMETRIC_OT_IMPACT:
EVIDENCE:
TESTS:
SECURITY_RBAC:
PRIVACY_RETENTION:
BIOMETRIC_HUMAN_OBSERVATION:
INDUSTRIAL_SAFETY:
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
HIDDEN_MEDIA_CAPTURE
UNDEFINED_MEDIA_RETENTION
SHARED_DEVICE_STATE_LEAK
VOICE_PERMISSION_BYPASS
VISUAL_FINDING_AS_UNVALIDATED_FACT
BIOMETRIC_PERMISSION_ELEVATION
LOW_CONFIDENCE_FORCED_IDENTITY
REVOKED_BIOMETRIC_STILL_ACTIVE
BIOMETRIC_TEMPLATE_LEAK
EMOTION_PERSONALITY_CHARACTER_INFERENCE
AUTOMATIC_EMPLOYMENT_DECISION_FROM_BIOMETRICS
HIDDEN_WORKER_PROFILING
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
```

## 15. First execution

Open `23-prompt-cursor-execucao.md` and execute **C0.S0 only**.

The first code after Foundation Freeze is the standalone Copilot API/MFE bootstrap, not intelligence/media/biometric/Meeting/Frontline features.
