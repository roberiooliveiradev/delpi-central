# 14 — Definition of Done

**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Tests:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Requirements:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)  
**Specs temáticas:** `53–66`

## 1. Objetivo

Uma fase só fecha com comportamento, integração, segurança, privacidade, outcome truth, generalização, arquitetura e independência do Minha DELPI Chat provados no candidate vigente.

## 2. DoD global

```text
[ ] DÉLIA API/MFE/deploy/persistence próprios
[ ] zero runtime dependency no Chat
[ ] Keycloak = identity/SSO authority
[ ] Core = apps/routes/RBAC/governance authority
[ ] Portal = host/navigation/published-context authority
[ ] Domain APIs mantêm business authority
[ ] Automation Hub mantém technical-execution authority
[ ] physical scheduler/timer, if used, remains technical trigger owner only
[ ] external/OT owners mantêm source/safety authority
[ ] shared primitives não duplicados
[ ] OpenAPI/semantic capabilities governam actions
[ ] planner provider/executor/model/tool/scheduler-neutral
[ ] read != write; draft != send; PREPARE != ACT; simulate != apply
[ ] schedule != permission; stored schedule intent != eternal authorization
[ ] Recurring Governed Work != Watch autonomous ACT
[ ] recommendation != authorization; prediction != FACT
[ ] event/tool/agent/model/package/device/biometric/scheduler identity não concede permission
[ ] deterministic readiness usa Policy/Specification quando aplicável
[ ] not every event invokes LLM
[ ] technical executor/scheduler success != verified business Outcome
[ ] no blind retry after ambiguous material write
[ ] autonomy capability/context/risk-scoped; L5 OFF default
[ ] kill switches/rollback/revoke paths independem de prompt
[ ] provider/RPA/tool/model secrets ficam fora de LLM/MFE/logs comuns
[ ] Process Mining não vira worker surveillance
[ ] Personal Memory != Organizational Knowledge != live business truth
[ ] Semantic Layer != Business Graph
[ ] Sandbox isolated/read-only by default
[ ] Artifact has provenance/version/ACL
[ ] Twin/scenario state != production state
[ ] Edge/offline never widens authority
[ ] Marketplace/model/tool install != permission grant
[ ] media/biometric/privacy boundaries pass
[ ] OT safety boundary intact
```

## 3. DoD C0 — Foundation Freeze

```text
[ ] platform/API/MFE/infra inventory with evidence
[ ] media/device/biometric/OT inventory
[ ] Internet/OAuth/connector/Teams inventory
[ ] event/RPA/automation/queue/worker/service-identity inventory
[ ] scheduler/timer/cron/polling/recurring-job inventory
[ ] Recurring Work definition owner vs physical scheduler owner frozen
[ ] recurrence/IANA timezone/DST/misfire/overlap/idempotency semantics frozen
[ ] background identity/AuthZ/revoke semantics per occurrence frozen
[ ] Automation Hub physical owner/runtime/contract status classified
[ ] outcome/postcondition/notification owners inventory
[ ] event logs/process owners/case keys/task-mining inventory
[ ] AI/model/automation assets/evals/cost/incidents/kill switches inventory
[ ] MCP/A2A/tool/agent/trust/delegation inventory
[ ] personal preference/memory/privacy/delete/export inventory
[ ] semantic KPI/glossary/BI model/metric owner inventory
[ ] sandbox/query/file/artifact infrastructure inventory
[ ] predictive/optimization/simulation/twin inventory
[ ] Edge/network/device/MDM/offline/local-inference inventory
[ ] model registry/MLOps/catalog/signing/supply-chain inventory
[ ] standalone ownership/names/storage boundaries frozen
[ ] shared primitive decisions frozen
[ ] recurring Work/process/memory/semantic/sandbox/twin/edge/model boundaries frozen
[ ] contract/conformance harness reproducible
[ ] CHAT_RUNTIME_DEPENDENCY=0
[ ] FOUNDATION_DUPLICATION=0 material
[ ] FOUNDATION_FREEZE=PASS
```

## 4. DoD C1 — Standalone Bootstrap

```text
[ ] API/MFE/manifest/Gateway/Compose próprios
[ ] JWT/Core integration
[ ] Keycloak identity/SSO contract preserved
[ ] Module Federation/plugin-ui
[ ] full-page/global host contract
[ ] responsive/accessibility baseline
[ ] no thematic runtime feature activates implicitly
[ ] no recurring material ACT before C5 gates
[ ] secrets absent from browser
[ ] Chat offline does not break DÉLIA
[ ] independent rollback/shutdown
```

## 5. DoD C2 — Context + Platform Commands

```text
[ ] WorkspaceContext bounded/sanitized
[ ] EntityRef/SourceRef without permission/credential truth
[ ] device/memory/model/execution/schedule refs do not grant authority
[ ] shared-device user switch clears local personalized/media/source state
[ ] typed authorized navigation/actions
[ ] iframe bridge safe
```

## 6. DoD C3 — Intelligence + Foundations

```text
[ ] own conversation/runtime
[ ] own OpenAPI Action Catalog/Capability Projection
[ ] provider/executor/model/tool-neutral planner
[ ] FAST/OPERATIONAL/REASONING semantics tested
[ ] EventLog/ProcessTrace contracts valid
[ ] AI Asset Registry projection valid
[ ] MCP/A2A allowlist/trust boundary valid
[ ] Personal Memory lifecycle/privacy boundary valid
[ ] MetricDefinition/Glossary versioned
[ ] Sandbox isolated/quota-bounded
[ ] Prediction/Twin contracts preserve epistemic semantics
[ ] Edge device/package/cache contracts versioned
[ ] Model Registry/eval lineage valid
[ ] existing media/biometric/external gates pass
[ ] no material ACT in C3
```

## 7. DoD C4 — Governed Reads + Analysis

```text
[ ] business/external reads authorized/provenanced
[ ] Graph does not replicate masters
[ ] Process Mining variants/conformance/bottlenecks grounded in real logs
[ ] process deviations do not become person accusations
[ ] Semantic Query uses governed metric formula/version
[ ] Analysis Sandbox read-only result reproducible or truthfully marked otherwise
[ ] predictive results carry model/version/horizon/freshness/limitations
[ ] Personal Memory only affects relevance/presentation, not live truth
[ ] MCP/A2A read-only delegation bounded and provenanced
[ ] Edge read-only cache freshness/revision enforced
[ ] no side effect implicit
```

## 8. DoD C5 — Governed ACT + Durable/Recurring Foundation

```text
[ ] Decision Gate/revalidation/AuthZ/idempotency/audit
[ ] L4 governed execute only for explicitly enabled capability/context
[ ] semantic capability→versioned executor mapping
[ ] API preferred over RPA when supported
[ ] Automation Hub contract used for technical execution under its boundary
[ ] executor adapters replaceable
[ ] AutomationExecution technical state not duplicated as DÉLIA source of truth
[ ] worker/session/credential isolation when RPA in scope
[ ] ambiguous write no blind retry
[ ] postcondition/Outcome verified where material
[ ] same DÉLIA Durable Workflow coordinates writes/tools/agents/execution requests
[ ] Recurring Work create/inspect/list/pause/resume/cancel lifecycle works
[ ] recurring definition survives chat/session/restart independently
[ ] recurrence uses explicit IANA timezone/start/end and deterministic calendar semantics
[ ] DST/misfire/missed-run/overlap semantics are explicit and tested when applicable
[ ] duplicate timer/retry/restart/reconciliation does not duplicate a material occurrence/effect
[ ] paused/cancelled/expired/disabled schedule does not create future material ACT
[ ] each material occurrence revalidates current identity + Core/domain AuthZ + Policy/Decision + provider/source permission
[ ] revoked creator/connection/capability cannot continue on stale authorization
[ ] occurrence links Work/Decision/Execution/Outcome/Evidence/Audit
[ ] recurring report→email anchor works without open chat session and without duplicate send
[ ] report generated != send authorized; provider accepted != verified final Outcome automatically
[ ] Process Intelligence opportunity remains candidate/PREPARE
[ ] MCP/A2A writes pass same governance
[ ] semantic definition/model/policy TOCTOU handled
[ ] Artifact version/provenance/ACL/human edits preserved
[ ] prescriptive output remains recommendation/PREPARE until separately authorized Apply
[ ] SIMULATE != APPLY
```

## 9. DoD C6 — Product Work + Governance Experience

```text
[ ] Task/Case/Room/Inbox source ACL preserved
[ ] Watch OBSERVE/ADVISE/PREPARE works
[ ] Watch does not autonomously trigger ACT in C6
[ ] C5 governed ACT remains available only through explicitly authorized/confirmed flows
[ ] Recurring Work UX shows status/recurrence/timezone/next occurrence when derivable/last outcome/history
[ ] recurring pause/resume/cancel actions are RBAC-governed and audited
[ ] schedule admin does not grant underlying domain/provider write permission
[ ] C5 recurring Work remains distinct from C6 Watch autonomous behavior
[ ] Automation Hub admin shows truthful technical vs verified outcome states
[ ] Process Intelligence UX provides maps/variants/bottlenecks/conformance/backlog
[ ] before/after process metrics reproducible
[ ] AI Control Tower exposes owner/risk/health/eval/cost/value/incidents/dependencies/kill switch
[ ] Control Tower admin does not imply business permission
[ ] MCP/A2A lifecycle/disable/revoke works
[ ] Personal Memory user view/correct/delete/disable works
[ ] personalized briefing grounded in live authorities
[ ] Semantic catalog handles lineage/conflicts/deprecation
[ ] Artifact Workspace preserves human edits/version history
[ ] Operational Twin scenario isolated from production
[ ] Edge offline modes/sync/cache health work when in scope
[ ] Model drift/health views and Marketplace lifecycle work
[ ] Meeting/Frontline/external learning governance remains valid
```

## 10. DoD C7 — Advanced Autonomy + Scale

```text
[ ] no global unrestricted L4/L5 switch
[ ] L5 OFF default
[ ] capability/actor/context/risk/amount/environment/budget limits
[ ] selected Watch ACT has explicit allowlist/policy/identity/limits
[ ] recurring governed L4 does not require or imply L5
[ ] kill switch blocks new autonomous ACT independently of LLM
[ ] autonomous action produces verified Outcome
[ ] closed-loop process optimization is measured/reversible/governed
[ ] autonomous A2A delegation bounded/approved/cancellable
[ ] advanced personalization does not create hidden employee profile
[ ] semantic federation/materialization preserves source authority/freshness
[ ] scaled sandbox maintains isolation/quotas/cleanup
[ ] predictive/prescriptive ACT passes live policy/revalidation
[ ] Operational Twin Apply re-reads live production state
[ ] Edge rollout package/model health/rollback/revoke works
[ ] bounded offline actions, if any, expire/reconcile and never widen authority
[ ] model deployment/drift/rollback/kill switch works
[ ] Marketplace publish/enable uses security/supply-chain gates
[ ] revoked model/server/package no longer selectable
[ ] progressive rollout/canary/rollback
[ ] final Chat-offline independence
[ ] OT physical actuation remains separate safety initiative
```

## 11. Transversal required tests

```text
positive/sibling/negative
unauthorized/TOCTOU
unknown/metamorphic
injection from every untrusted source
Decision Gate
idempotency/replay
partial/ambiguous outcome
persist/reload/restart
SCHEDULE_NOT_PERMISSION
SCHEDULE_LIVE_AUTHZ_REVALIDATION
SCHEDULE_OCCURRENCE_IDEMPOTENT
SCHEDULE_PAUSE_CANCEL_ENFORCED
SCHEDULE_TIMEZONE_EXPLICIT
SCHEDULE_MISFIRE_OVERLAP_EXPLICIT
SCHEDULE_RETRY_RESTART_NO_DUPLICATE_ACT
layer/dependency conformance
CHAT_OFFLINE_INDEPENDENCE
PROCESS_LOG_PROVENANCE
NO_WORKER_SURVEILLANCE
CONTROL_TOWER_NOT_BUSINESS_AUTHORITY
MCP_A2A_NO_AUTO_TRUST
TOOL_AGENT_INJECTION_RESISTANCE
PERSONAL_MEMORY_ISOLATION
MEMORY_NOT_BUSINESS_TRUTH
GOVERNED_METRIC_REPRODUCIBILITY
SANDBOX_ISOLATION
SANDBOX_READ_ONLY_SOURCE
ARTIFACT_PROVENANCE_AND_HUMAN_EDIT_PRESERVATION
PREDICTION_NOT_FACT
SIMULATE_NOT_APPLY
EDGE_OFFLINE_NO_PERMISSION_EXPANSION
MODEL_REVOKE_ENFORCED
MARKETPLACE_INSTALL_NOT_PERMISSION
AI_SUPPLY_CHAIN_CONTROLS
OT_COMMAND_BLOCK
```

## 12. Blockers

Qualquer release blocker de `20` bloqueia a fase. Em especial:

```text
FOUNDATION_DRIFT
DUPLICATE_AUTHORITY
CHAT_RUNTIME_IMPORT
ACT_WITHOUT_LIVE_AUTHZ
ACT_WITHOUT_IDEMPOTENCY_OR_AUDIT
SCHEDULE_PERMISSION_ELEVATION
SCHEDULE_WITHOUT_LIVE_AUTHZ
DUPLICATE_SCHEDULE_OCCURRENCE_SIDE_EFFECT
PAUSED_OR_CANCELLED_SCHEDULE_EXECUTES
SCHEDULE_MISFIRE_POLICY_UNDEFINED
SCHEDULE_TIMEZONE_IMPLICIT
SCHEDULE_RETRY_DUPLICATE_ACT
WATCH_AUTONOMOUS_ACT_BEFORE_C7
EXECUTOR_TECHNICAL_SUCCESS_AS_BUSINESS_SUCCESS
PROCESS_MINING_WORKER_PROFILING
MCP_A2A_AUTO_TRUST
TOOL_AGENT_POLICY_INJECTION
CROSS_USER_PERSONAL_MEMORY_LEAK
MEMORY_OVERRIDES_LIVE_AUTHORITY
UNGOVERNED_METRIC_FORMULA
SANDBOX_ESCAPE_OR_UNGOVERNED_WRITE
ARTIFACT_PROVENANCE_LOSS
PREDICTION_PRESENTED_AS_FACT
SIMULATION_MUTATES_PRODUCTION
EDGE_OFFLINE_PERMISSION_EXPANSION
REVOKED_AI_ASSET_STILL_ACTIVE
MARKETPLACE_PERMISSION_ELEVATION
AI_PACKAGE_SUPPLY_CHAIN_BYPASS
ARBITRARY_LLM_OT_COMMAND
```

Nenhuma fase fecha com blocker material aberto.
