# Minha DELPI Copilot — Rollout, Migrações e Implantação

**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Specs temáticas:** `53–66`

## 1. Princípio

Rollout é progressivo por risco/capability/source/asset, mas nunca mantém duas authorities permanentes.

```text
read before write
observe before act
prepare before autonomous act
simulation before apply
offline read before offline action
model eval before deployment
review before Marketplace publish
```

## 2. Macro rollout

```text
C0 foundations/inventory
→ C1 standalone bootstrap
→ C2 context/navigation
→ C3 capability foundations
→ C4 read-only connected/analytical pilots
→ C5 governed writes/executors/artifacts
→ C6 product/governance experiences
→ C7 selected autonomy/Edge/Marketplace scale
```

## 3. Internal/domain rollout

```text
read-only Domain capabilities
→ Graph/Semantic/process analysis
→ PREPARE/preview
→ explicit governed writes
→ durable workflows
→ selected autonomous ACT only after C7 gates
```

## 4. External/provider rollout

Per provider:

```text
inventory/auth contract
→ narrow read-only connection
→ Source/Evidence validation
→ draft capability
→ explicit governed write
→ webhook/subscription/reconciliation
→ selected proactive capability much later
```

Provider-neutral planner remains unchanged.

## 5. Process Intelligence rollout

```text
one well-understood process + clean event log
→ reconstruct/validate trace
→ variants/conformance/bottleneck pilot
→ owner review
→ automation opportunity backlog
→ before/after measurement
→ additional processes
```

Do not start with company-wide desktop Task Mining. Actor-level telemetry requires separate privacy/governance pilot.

## 6. Semantic Layer rollout

```text
high-value disputed KPIs
→ owner/formula/grain/source freeze
→ semantic query pilot
→ cross-UI consistency checks
→ broader glossary/metrics
→ federated/materialized optimization later
```

No bulk migration of all BI models before priority/owner validation.

## 7. Personal Memory rollout

```text
opt-in low-risk preferences
→ user view/correct/delete controls
→ followed topics/work continuity
→ personalized briefing
→ advanced personalization only after privacy/eval evidence
```

Never bootstrap memory by silently ingesting personal mailbox/history into durable memory.

## 8. Analysis Sandbox rollout

```text
isolated read-only sandbox
→ bounded datasets
→ reproducible charts/tables
→ artifact generation
→ advanced statistical/forecast/optimization workloads
→ scaled pools C7
```

No production DB credentials or unrestricted network at any stage.

## 9. Artifact Workspace rollout

```text
report/chart drafts
→ version/provenance/ACL
→ human edit/review
→ Case/Task/Meeting attachment
→ export/share
→ governed templates/library
```

External send/share remains separate action.

## 10. Predictive / Prescriptive rollout

```text
historical model validation
→ read-only prediction pilot
→ calibration/drift monitoring
→ recommendation/PREPARE
→ scenario/what-if
→ selected ACT only after C7 policy/outcome proof
```

Prediction is never promoted to fact by rollout stage.

## 11. Operational Twin rollout

```text
bounded one-process/line scenario model
→ validate live source mapping/freshness
→ what-if comparison
→ user scenario workspace
→ apply remains separate governed action
→ expand only after accuracy/value proof
```

## 12. Automation / RPA rollout

Prefer API executor first. For legacy RPA:

```text
one deterministic capability
→ package/version/credential/worker isolation
→ manual trigger + Outcome verification
→ Durable Workflow integration
→ PREPARE/explicit execute
→ selected autonomous execution only after C7
```

RPA→API migration later changes adapter/mapping, not planner/workflow.

## 13. MCP / A2A rollout

```text
inventory/discovery
→ security review
→ APPROVED read-only server/agent
→ narrow pilot
→ monitored usage/result provenance
→ write capability under same Decision gates
→ autonomous delegation only C7
```

Discovery never auto-enables.

## 14. AI Control Tower rollout

Start with inventory/read-only governance view:

```text
asset registry
→ owner/version/risk/eval/health
→ cost/usage
→ incidents/dependencies
→ kill switches/rollout controls
→ verified value/ROI
```

Control Tower must be useful before it becomes a broad admin command surface.

## 15. Model lifecycle rollout

```text
inventory active models/providers
→ minimum owner/version/eval registry
→ deployment health
→ drift/cost telemetry
→ rollback/revoke
→ advanced Model Router/Edge deployment
```

Existing production model with unknown owner/eval becomes governance debt, not auto-approved.

## 16. Capability Marketplace rollout

```text
catalog read-only
→ internal publisher review
→ approved non-executable templates/packs
→ connectors/models/automations with stronger gates
→ publish/enable workflows
→ supply-chain automation
```

No public/external Marketplace auto-install into production.

## 17. Edge / Offline rollout

```text
network/device inventory
→ selected Frontline device cohort
→ read-only current procedure/cache
→ local inference pilot
→ buffered events/sync
→ fleet health/rollback
→ bounded offline action only after separate C7 proof
```

Loss of cloud never upgrades permission.

## 18. Database/schema migration pattern

```text
EXPAND
→ compatible readers
→ writers
→ optional backfill
→ CUTOVER
→ monitor
→ CLEANUP
```

No migration from Chat DB.

Definitions/models/packages are versioned rather than silently overwritten.

## 19. Provider/executor/model migration

Volatile implementation swaps use adapters and canary:

```text
new provider/executor/model
→ contract/eval compatibility
→ cohort/canary
→ compare Outcome/quality
→ cutover
→ revoke/deprecate old
→ cleanup
```

## 20. Derived index/cache migration

External/process/semantic/Graph/Edge caches are derived. Prefer rebuild/invalidate where possible. Preserve user/source/connection/domain isolation and freshness.

## 21. Feature flags / rollout controls

Examples:

```text
internet_research_enabled
provider_x_enabled
process_intelligence_enabled
personal_memory_enabled
analysis_sandbox_enabled
prediction_x_enabled
automation_x_enabled
mcp_server_x_enabled
a2a_agent_x_enabled
edge_cohort_x_enabled
marketplace_asset_x_enabled
model_deployment_x_enabled
```

Each flag has owner/purpose/risk/exit criteria/rollback. Flag never grants permission.

## 22. Kill switches

Independent disable where material:

- Internet/provider/connection/external send;
- Watch ACT/autonomy;
- specific automation/executor/RPA worker class;
- MCP server/A2A agent;
- sandbox;
- specific model/deployment;
- Marketplace asset;
- Edge package/device capability;
- media/biometric capture;
- OT integration.

## 23. Cohort strategy

Use the smallest cohort that proves value/safety:

```text
TI/internal owner
→ selected specialists/power users
→ one process/team/site/device cohort
→ wider departments
→ broader rollout
```

Personal connections/memory remain owner-specific regardless of broad feature flag.

## 24. Metrics before expansion

Require metrics appropriate to capability:

```text
verified Outcome rate
privacy/security incidents = 0 target
process before/after improvement
metric reproducibility
memory correction/opt-out
sandbox failures/blocked escapes
prediction calibration/drift
artifact usefulness/edit preservation
MCP/A2A blocked/unapproved calls
model eval freshness/rollback
Edge cache/sync health
cost vs verified business value
```

## 25. Stop-the-line

Pause rollout on any release blocker from `20`, especially data/credential leak, duplicate autonomous effect, false-success Outcome, Process Mining surveillance, tool/agent trust bypass, memory cross-user leak, semantic formula drift, sandbox escape, prediction-as-fact, simulation production mutation, Edge authority expansion, revoked asset still active, supply-chain bypass or OT safety boundary violation.

## 26. Rollback

Rollback preserves source/connection/state integrity, prevents duplicate side effects, marks stale/degraded projections truthfully, revokes old credentials/assets/packages where needed and maintains interpretability of historical Evidence/Outcome/artifacts.

## 27. Final maturity criterion

A capability is mature only when it remains owner-driven, auditable, independently disableable/rollbackable, privacy/security scoped, observable for real outcomes and replaceable behind canonical contracts without destabilizing the rest of the Copilot.
