# Minha DELPI Copilot — Execution Ledger

**Status:** `PLANNED / NOT_STARTED`  
**Product boundary:** standalone application  
**Plan:** [`../16-execution-master-plan.md`](../16-execution-master-plan.md)  
**Patterns:** [`../49-architecture-and-design-patterns-standard.md`](../49-architecture-and-design-patterns-standard.md)  
**Multimodal/Meeting/Frontline:** [`../53-multimodal-meeting-frontline-and-industrial-copilot.md`](../53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`../54-biometric-identity-and-human-observation-governance.md`](../54-biometric-identity-and-human-observation-governance.md)  
**Internet/External Connectors:** [`../55-internet-research-and-external-connectors.md`](../55-internet-research-and-external-connectors.md)  
**Microsoft Teams:** [`../56-microsoft-teams-connector-and-meeting-integration.md`](../56-microsoft-teams-connector-and-meeting-integration.md)  
**Autonomous Operations/Execution Hub:** [`../57-event-driven-autonomous-operations-and-automation-execution-hub.md`](../57-event-driven-autonomous-operations-and-automation-execution-hub.md)  
**Next:** **C0.S0 — Platform/Media/Device/Biometric/External/Automation/OT rebaseline**

## 1. Ledger rule

Este arquivo registra estado/evidence de execução. Mudanças somente documentais não avançam fase runtime.

## 2. Canonical phase status

| Fase | Status | Próximo step | Dependência |
|---|---|---|---|
| C0 Platform + Architecture + Media/Privacy/Biometric/External/Automation/OT Foundations | **NOT_STARTED** | **C0.S0** | none |
| C1 Standalone Bootstrap | LOCKED | — | C0.S7 FOUNDATION_FREEZE |
| C2 Portal + Operational Context + Commands | LOCKED | — | C1 independence gate |
| C3 Intelligence + Multimodal/Biometric/External/Decision Foundations | LOCKED | — | C1+C2 foundations |
| C4 Business + External Reads + Graph + Operational Read Intelligence | LOCKED | — | C3 foundations |
| C5 Governed Business/External/Automation Writes + Durable Foundation | LOCKED | — | C4 reads/evidence |
| C6 Product Work + Meeting/Frontline + Automation Hub + Events/Learning | LOCKED | — | C5 durable/executor foundation |
| C7 Autonomous Operations + Advanced Realtime/External Proactivity + Rollout | LOCKED | — | C0–C6 gates |

## 3. C0 sequence

```text
C0.S0 platform/monorepo/media/device/biometric/external/automation/OT inventory
→ C0.S1 standalone boundary/names
→ C0.S2 authorities/bounded contexts
→ C0.S3 shared primitives/ref decisions
→ C0.S4 architecture/persistence/privacy/external/automation boundaries
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
CORE_ROLE = APPS_ROUTES_RBAC_GOVERNANCE
KEYCLOAK_ROLE = IDENTITY_SSO
DOMAIN_APIS = BUSINESS_AUTHORITIES
PLUGIN_UI = SHARED_DESIGN_SYSTEM
OPENAPI_FIRST = NATIVE_COPILOT_FOUNDATION
BUSINESS_GRAPH = COPILOT_PROJECTION_NOT_MASTER_DATA
EVIDENCE_PROVENANCE = FOUNDATION_CONTRACT
DECISION_GATE = FOUNDATION_CONTRACT
DURABLE_WORKFLOW = SINGLE_CANONICAL_WORK_RUNTIME

COPILOT_SURFACES = GLOBAL | WORKSPACE | MEETING | FRONTLINE | FUTURE_TEAMS_SURFACE
BACKGROUND_OPERATION = WATCH_WORKFLOW_GOVERNED

MULTIMODAL_TARGET = TEXT | VOICE | IMAGE | DOCUMENT | VIDEO | SCREEN
BIOMETRIC_IDENTITY = GOVERNED_OPTIONAL_CAPABILITY
BIOMETRIC_MATCH_EQUALS_AUTHORIZATION = FALSE
HUMAN_OBSERVATION = OBSERVABLE_PROCESS_EVIDENCE_ONLY

INTERNET_RESEARCH = GOVERNED_CAPABILITY
EXTERNAL_CONNECTORS = PROVIDER_NEUTRAL
EXTERNAL_READ_WRITE_SEPARATION = REQUIRED
DRAFT_EQUALS_SEND = FALSE
PROVIDER_TOKEN_TO_LLM_MFE = FORBIDDEN
EXTERNAL_EVENTS = EVENT_ENVELOPE_NORMALIZED

TEAMS = MICROSOFT365_CAPABILITY_FAMILY
TEAMS_SEPARATE_COPILOT_RUNTIME = FORBIDDEN
TEAMS_SOURCE_ACL = PRESERVED
TEAMS_MEETING_ARTIFACTS = SOURCE_EVIDENCE_NOT_DECISION
TEAMS_RAW_REALTIME_MEDIA = C7_ADVANCED_ONLY_WITH_ADR

AUTONOMOUS_OPERATIONS = EVENT_DRIVEN_GOVERNED_TARGET
COPILOT_ROLE = INTELLIGENCE_CONTEXT_DECISION_ORCHESTRATION
AUTOMATION_EXECUTION_HUB_ROLE = EXECUTION
AUTOMATION_HUB_SEPARATE_MICROSERVICE = NOT_ASSUMED_BEFORE_C0
EXECUTOR_PREFERENCE = API | NATIVE_INTEGRATION | FUNCTION | RPA | COMPUTER_USE | HUMAN_TASK
RPA = REPLACEABLE_EXECUTOR_NOT_BUSINESS_AUTHORITY
PLANNER_RPA_UI_MECHANICS = FORBIDDEN
DECISION_PATHS = FAST | OPERATIONAL | REASONING
NOT_EVERY_EVENT_USES_LLM = TRUE
DETERMINISTIC_READINESS = REQUIRED_WHEN_RULES_FACTS_EXIST
EVENT_EQUALS_PERMISSION = FALSE
BACKGROUND_IDENTITY = EXPLICIT_USER_OR_SERVICE
TECHNICAL_EXECUTION_EQUALS_BUSINESS_OUTCOME = FALSE
OUTCOME_VERIFICATION = REQUIRED_WHEN_MATERIAL
WATCH_MODES_C6 = OBSERVE | ADVISE | PREPARE
WATCH_ACT = C7_ONLY
AUTONOMY_SCOPE = CAPABILITY_CONTEXT_RISK_SCOPED
GLOBAL_UNRESTRICTED_L5 = FORBIDDEN
L5_DEFAULT = OFF
AUTONOMY_KILL_SWITCHES = REQUIRED
COMPUTER_USE = ADVANCED_BOUNDED_FALLBACK

OT_ACTUATION = BLOCKED_BY_DEFAULT
COPILOT_IS_SAFETY_CONTROLLER = FALSE

ARCHITECTURE_STYLE = CLEAN_ARCHITECTURE_PORTS_ADAPTERS_PRAGMATIC_DDD
EVENT_DRIVEN = ONLY_WITH_REAL_EVENT_OWNER
STATE_MACHINE = NONTRIVIAL_LIFECYCLES
POLICY_SPECIFICATION = DETERMINISTIC_DECISION_RULES
ABSTRACTION_GATE = REQUIRED
```

All remain `PLAN_ONLY` until runtime evidence.

## 5. Superseded / rejected directions

```text
Copilot extends Minha DELPI Chat                = SUPERSEDED
Copilot depends on Chat/Onda J                  = SUPERSEDED
External knowledge limited to DELPI             = SUPERSEDED
Teams requires separate Copilot backend         = SUPERSEDED
Teams base connector requires raw media bot     = SUPERSEDED
Automation Hub means only RPA                   = SUPERSEDED_BY_EXECUTION_HUB
RPA bot owns business decision                  = FORBIDDEN
Planner emits clicks/selectors                  = FORBIDDEN
All events require LLM                          = FORBIDDEN_DESIGN
One global Copilot L5                           = FORBIDDEN
Technical executor success means process done   = FORBIDDEN
Event payload directly executes write           = FORBIDDEN
```

## 6. Planning history

| Data | Evento | Status |
|---|---|---|
| 2026-09-12 | initial standalone Copilot architecture | PLAN_ONLY |
| 2026-09-12 | Business Graph/Tasks/Cases/Rooms/Inbox/Watch/Evidence/Decision/Durable Work | PLAN_ONLY |
| 2026-09-12 | foundation-first + architecture/design patterns | PLAN_ONLY |
| 2026-09-12 | Global/Workspace/Meeting/Frontline + multimodal/OT boundaries (`53`) | PLAN_ONLY |
| 2026-09-12 | Biometric Identity + Human Observation (`54`, through CP-193) | PLAN_ONLY |
| 2026-09-13 | Internet Research + External Connectors (`55`, through CP-214) | PLAN_ONLY |
| 2026-09-13 | Microsoft Teams first-class capability family (`56`, through CP-225) | PLAN_ONLY |
| 2026-09-13 | **Event-Driven Autonomous Operations + Automation & Execution Hub (`57`, through CP-248)** | **PLAN_ONLY; docs only** |

Actual `HEAD_BEFORE` for runtime is captured at C0.S0. Documentation-only commits do not advance execution status.

## 7. Canonical phase mapping

```text
C0 → inventory/freeze platform + media + biometric + external + Teams + events + RPA/executors + service identity + outcome/autonomy + OT
C1 → standalone API/MFE/Manifest/Gateway/Compose/Portal bootstrap
C2 → Workspace/Operational Context + Platform Commands
C3 → Intelligence + OpenAPI + Expertise/Knowledge + multimodal + Internet/connectors + Event/Decision foundations
C4 → business/external reads + Graph + read-only readiness/anomaly intelligence
C5 → Decision Gates + governed writes + executor ports/adapters + AutomationExecution + Outcome verification + Durable Workflow
C6 → Task/Case/Room/Inbox + Watch OBSERVE/ADVISE/PREPARE + Meeting/Frontline + Automation Hub admin + events/notifications/learning
C7 → selected Watch ACT + capability-scoped L5 + autonomous operations + advanced computer-use/realtime + rollout
```

## 8. Required C0.S0 automation inventory

```text
RPA platforms/tools/licences/orchestrators
bots/robots/packages and owners
automation scripts/functions/jobs
queues/workers/worker pools/heartbeats
desktop/session/VDI execution infrastructure
event sources/buses/topics/webhooks
schedulers/polling jobs
service accounts/background identities
credential/secret owners and injection patterns
package/version/deploy/rollback patterns
retry/idempotency/lease/lock patterns
RPA screenshots/artifacts/logging/retention
existing rule/decision/BPM/workflow engines
business postcondition/outcome verification sources
notification/escalation channels
automation governance/SLA/support
kill switches/emergency stop patterns
```

Unknown = `NOT_PROVEN`.

## 9. Required C0 outputs

Além dos outputs existentes:

- automation/RPA/event/worker/service-identity inventory;
- Automation & Execution Hub ownership decision;
- executor preference/selection contract;
- semantic capability→executor contract decision;
- event source trust/dedupe/polling fallback decision;
- background identity decision;
- AutomationExecution lifecycle/idempotency decision;
- RPA worker/queue/credential/artifact boundary if RPA is real scope;
- outcome verification contract;
- Watch PREPARE vs ACT semantics;
- capability-scoped autonomy/kill-switch model;
- RED automation/event/autonomy conformance harness.

## 10. Requirements authority

`25-requirements-traceability.md` is the single CP authority.

```text
CP-001–CP-248
```

```text
CP-194–CP-214 = Internet/External Connectors
CP-215–CP-225 = Microsoft Teams
CP-226–CP-248 = Autonomous Operations / Automation & Execution Hub
```

Historical Chat migration requirements remain `OUT_OF_SCOPE_WITH_DECISION`.

## 11. Test authority

`20-testing-and-acceptance-matrix.md`.

Automation gates include:

```text
EVENT_SOURCE_AUTHENTICITY
EVENT_DEDUPE_NO_DUPLICATE_EXECUTION
EVENT_NOT_PERMISSION
FAST_PATH_NO_LLM_WHEN_DETERMINISTIC
DETERMINISTIC_READINESS_REPRODUCIBLE
PLANNER_NO_RPA_UI_MECHANICS
API_PREFERRED_OVER_RPA_WHEN_SUPPORTED
EXECUTOR_SUBSTITUTION_NO_PLANNER_PATCH
BACKGROUND_IDENTITY_EXPLICIT
AUTOMATION_EXECUTION_IDEMPOTENT
RPA_WORKER_SESSION_CREDENTIAL_ISOLATION
AMBIGUOUS_WRITE_NO_BLIND_RETRY
VERIFIED_BUSINESS_OUTCOME
PREPARE_NOT_ACT
CAPABILITY_SCOPED_AUTONOMY
L5_OFF_DEFAULT
AUTONOMY_KILL_SWITCH
COMPUTER_USE_BOUNDED
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
EVENT_AUTOMATION_RPA_IMPACT:
EVIDENCE:
TESTS:
SECURITY_RBAC:
PRIVACY_RETENTION:
BACKGROUND_IDENTITY:
EXECUTOR_OUTCOME_VERIFICATION:
AUTONOMY_POLICY:
EXTERNAL_CONNECTIONS_EGRESS:
TEAMS_INTEGRATION:
INDUSTRIAL_SAFETY:
CHAT_INDEPENDENCE:
ARCHITECTURAL_CONFORMANCE:
FOUNDATION_DRIFT:
COMPLETE_GATE:
NEXT_UNLOCKED:
NOTES:
```

## 13. COMPLETE_GATE blockers

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
PORTAL_AI_LOGIC_LEAK
DOMAIN_RULE_DUPLICATION
EVENT_PERMISSION_ELEVATION
DUPLICATE_EVENT_DUPLICATE_EXECUTION
PLANNER_RPA_UI_MECHANICS_LEAK
RPA_SELECTED_OVER_AUTHORITATIVE_API_WITHOUT_JUSTIFICATION
BACKGROUND_EXECUTION_WITHOUT_EXPLICIT_IDENTITY
AUTOMATION_EXECUTION_DUPLICATE
RPA_CREDENTIAL_OR_SESSION_LEAK
AMBIGUOUS_WRITE_BLIND_RETRY
EXECUTOR_TECHNICAL_SUCCESS_AS_BUSINESS_SUCCESS
PREPARE_BECOMES_ACT_IMPLICITLY
GLOBAL_UNSCOPED_L5
AUTONOMY_KILL_SWITCH_BYPASS
COMPUTER_USE_UNBOUNDED_ACCESS
ARBITRARY_LLM_OT_COMMAND
SAFETY_INTERLOCK_BYPASS
```

## 14. First execution

Open `23-prompt-cursor-execucao.md` and execute **C0.S0 only**.

The first runtime after Foundation Freeze is still the standalone Copilot API/MFE bootstrap — **not** RPA, Event engine, Automation Hub or autonomous ACT.
