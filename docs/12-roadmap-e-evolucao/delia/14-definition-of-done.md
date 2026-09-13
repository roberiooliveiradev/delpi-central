# 14 — Definition of Done

**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Tests:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Requirements:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)  
**Specs temáticas:** `53–66`

## 1. Objetivo

Uma fase só fecha com comportamento, integração, segurança, privacidade, outcome truth, generalização, arquitetura e independência do Minha DELPI Chat provados no candidate vigente.

## 2. DoD global

```text
[ ] Copilot API/MFE/deploy/persistence próprios
[ ] zero runtime dependency no Chat
[ ] Core/Keycloak/Portal/Domain APIs mantêm authorities
[ ] external/OT owners mantêm source authority
[ ] shared primitives não duplicados
[ ] OpenAPI/semantic capabilities governam actions
[ ] planner provider/executor/model/tool-neutral
[ ] read != write; draft != send; PREPARE != ACT; simulate != apply
[ ] recommendation != authorization; prediction != FACT
[ ] event/tool/agent/model/package/device/biometric identity não concede permission
[ ] deterministic readiness usa Policy/Specification quando aplicável
[ ] not every event invokes LLM
[ ] technical executor success != verified business Outcome
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
[ ] process/memory/semantic/sandbox/twin/edge/model boundaries frozen
[ ] contract/conformance harness reproducible
[ ] CHAT_RUNTIME_DEPENDENCY=0
[ ] FOUNDATION_DUPLICATION=0 material
[ ] FOUNDATION_FREEZE=PASS
```

## 4. DoD C1 — Standalone Bootstrap

```text
[ ] API/MFE/manifest/Gateway/Compose próprios
[ ] JWT/Core integration
[ ] Module Federation/plugin-ui
[ ] full-page/global host contract
[ ] responsive/accessibility baseline
[ ] no thematic runtime feature activates implicitly
[ ] secrets absent from browser
[ ] Chat offline does not break Copilot
[ ] independent rollback/shutdown
```

## 5. DoD C2 — Context + Platform Commands

```text
[ ] WorkspaceContext bounded/sanitized
[ ] EntityRef/SourceRef without permission/credential truth
[ ] device/memory/model/execution refs do not grant authority
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
[ ] no material autonomous ACT
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

## 8. DoD C5 — Governed Writes + Durable Foundation

```text
[ ] Decision Gate/revalidation/idempotency
[ ] semantic capability→versioned executor mapping
[ ] API preferred over RPA when supported
[ ] executor adapters replaceable
[ ] AutomationExecution lifecycle valid
[ ] worker/session/credential isolation when RPA in scope
[ ] ambiguous write no blind retry
[ ] postcondition/Outcome verified where material
[ ] same Durable Workflow coordinates writes/tools/agents/executors
[ ] Process Intelligence opportunity remains candidate/PREPARE
[ ] MCP/A2A writes pass same governance
[ ] semantic definition/model/policy TOCTOU handled
[ ] Artifact version/provenance/ACL/human edits preserved
[ ] prescriptive output remains recommendation/PREPARE
[ ] SIMULATE != APPLY
```

## 9. DoD C6 — Product Work + Governance Experience

```text
[ ] Task/Case/Room/Inbox source ACL preserved
[ ] Watch OBSERVE/ADVISE/PREPARE works; ACT blocked
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
[ ] kill switch blocks new ACT independently of LLM
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
