# DÉLIA — Rollout, Migrações e Implantação

**Status:** `PLANNED / TARGET`  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)

## 1. Princípio

Rollout é progressivo por risco/capability/source/asset, sem manter duas authorities permanentes e sem tratar rollout como permission grant.

```text
read != write
PREPARE != ACT
recommendation != authorization
simulation != apply
technical success != business outcome
```

Progressão de autonomia:

```text
observe before advice
advice before prepare
prepare before governed ACT
C5 governed ACT before C7 advanced/autonomous ACT
```

## 2. Macro rollout

```text
C0 foundations/inventory
→ C1 standalone bootstrap
→ C2 context/navigation
→ C3 capability foundations
→ C4 read-only connected/analytical pilots
→ C5 governed ACT + Durable Work + approved execution contracts
→ C6 product/governance experiences
→ C7 selected advanced autonomy/Edge/Marketplace scale
```

Este documento não prova que qualquer piloto/cohort/runtime já exista.

## 3. Internal/domain rollout

```text
read-only Domain capabilities
→ Graph/Semantic/process analysis
→ PREPARE/preview
→ explicit governed ACT from C5 when capability is authorized and gated
→ Durable Work
→ selected autonomous ACT only after C7 gates
```

## 4. External/provider rollout

Per provider:

```text
inventory/auth contract
→ narrow read-only connection
→ Source/Evidence validation
→ draft capability
→ explicit governed write/ACT when C5 gates allow
→ webhook/subscription/reconciliation
→ selected autonomous/proactive ACT only after C7 gates
```

Provider-neutral planner remains unchanged. Provider scope never becomes Core/domain permission.

## 5. Process Intelligence rollout

```text
one well-understood process + authorized event log
→ reconstruct/validate trace
→ variants/conformance/bottleneck pilot
→ owner review
→ automation opportunity candidate backlog
→ before/after measurement
→ additional processes
```

Do not start with company-wide desktop Task Mining. Actor-level telemetry requires explicit privacy/governance justification and may remain out of scope.

## 6. Semantic Layer rollout

```text
high-value disputed KPIs
→ owner/formula/grain/source freeze
→ semantic query pilot
→ cross-UI consistency checks
→ broader glossary/metrics
→ federation/materialization only if justified later
```

No bulk migration of BI models before priority/owner validation.

## 7. Personal Memory rollout

```text
opt-in low-risk preferences
→ user view/correct/delete/disable controls
→ followed topics/work continuity
→ personalized briefing
→ advanced personalization only after privacy/eval evidence
```

Never bootstrap durable memory by silently ingesting personal mailbox/history. Personal Memory never grants authorization.

## 8. Analysis Sandbox rollout

```text
isolated read-only sandbox
→ bounded datasets
→ reproducible charts/tables
→ artifact generation
→ advanced statistical/forecast/optimization workloads
→ scaled pools only when justified
```

No unrestricted production credentials/network at any stage.

## 9. Artifact Workspace rollout

```text
report/chart drafts
→ version/provenance/ACL
→ human edit/review
→ Case/Task/Meeting attachment
→ export/share PREPARE
→ separately governed external send/share
```

## 10. Predictive / Prescriptive rollout

```text
historical model validation
→ read-only prediction pilot
→ calibration/drift monitoring
→ recommendation/PREPARE
→ scenario/what-if
→ governed ACT from C5 only where the underlying action capability is explicitly authorized
→ advanced/autonomous predictive/prescriptive ACT only after C7 gates
```

Prediction is never promoted to FACT by rollout stage.

## 11. Operational Twin rollout

```text
bounded scenario model
→ validate live source mapping/freshness
→ what-if comparison
→ scenario workspace
→ separate live Apply intent
→ live AuthZ/Policy/Decision
→ governed ACT path
```

Twin/scenario remains projection, not source of truth.

## 12. Automation / RPA rollout

Prefer authoritative API first. For legacy RPA or computer-use:

```text
semantic capability
→ DÉLIA Policy/Decision/Work
→ Automation Hub / approved technical executor
→ package/version/credential/worker/session isolation
→ technical result
→ authoritative Outcome verification
```

Progression may be:

```text
manual/explicit governed trigger
→ Durable Work integration
→ PREPARE + governed ACT from C5 when all gates pass
→ selected autonomous execution only after C7 gates
```

RPA→API migration changes executor mapping/adapter, not planner semantics. DÉLIA does not own RPA worker mechanics by default.

## 13. MCP / A2A rollout

```text
inventory/discovery
→ security review
→ APPROVED read-only server/agent
→ narrow pilot
→ monitored usage/result provenance
→ write capability under same C5 governance when authorized
→ autonomous delegation only after C7 gates
```

Discovery never auto-enables or grants permission.

## 14. AI Control Tower rollout

Start with inventory/read-only governance projection when owner/contracts exist:

```text
asset inventory
→ owner/version/risk/eval/health
→ cost/usage
→ incidents/dependencies
→ kill switches/rollout controls
→ verified value
```

Control Tower is not business permission authority or second planner.

## 15. Model lifecycle rollout

```text
inventory active models/providers
→ canonical owner/version/eval registry or source
→ deployment health
→ drift/cost telemetry
→ rollback/revoke
→ advanced routing/Edge deployment
```

Unknown owner/eval means governance debt, not auto-approval.

## 16. Capability Marketplace rollout

```text
catalog read-only
→ publisher review
→ approved non-executable assets
→ stronger gates for connectors/models/automations/executable assets
→ publish/enable workflows
→ supply-chain controls
```

Install/enable never grants RBAC/provider scope.

## 17. Edge / Offline rollout

```text
network/device inventory
→ selected Frontline device cohort
→ read-only current procedure/cache
→ bounded local inference pilot
→ buffered events/sync
→ fleet health/rollback
→ bounded offline action only after separate safety/authority proof
```

Loss of cloud never upgrades permission. Edge does not grant OT authority.

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

Only DÉLIA-owned persistence is migrated here. No migration from Chat DB and no migration of another bounded context's database.

## 19. Provider/executor/model migration

Volatile implementation swaps use contract/eval compatibility and canary when justified:

```text
new provider/executor/model
→ owner/contract/eval compatibility
→ cohort/canary
→ compare quality/technical result/verified Outcome
→ cutover
→ revoke/deprecate old
→ cleanup
```

## 20. Derived index/cache migration

External/process/semantic/Graph/Edge caches are derived only when their owners/contracts say so. Prefer rebuild/invalidate where possible. Preserve source/user/domain isolation and freshness.

## 21. Feature flags / rollout controls

Flags are operational controls, never authorization. Each has owner/purpose/risk/exit criteria/rollback and cannot bypass Core/domain Policy/Decision.

## 22. Kill switches

Independent disable where material:

- Internet/provider/connection/external send;
- selected Watch ACT/autonomy;
- specific automation/executor/RPA worker class;
- MCP server/A2A agent;
- sandbox;
- specific model/deployment;
- Marketplace asset;
- Edge package/device capability;
- media/biometric capture;
- OT integration.

## 23. Cohort strategy

Use the smallest cohort that proves value/safety. Personal connections/memory remain owner-specific regardless of broad rollout.

## 24. Metrics before expansion

Use capability-appropriate metrics: verified Outcome rate, security/privacy incidents, process before/after improvement, metric reproducibility, memory corrections/opt-out, sandbox isolation failures, prediction calibration/drift, artifact edit preservation, tool/agent trust blocks, model eval freshness, Edge sync health and cost vs verified business value.

## 25. Stop-the-line

Pause rollout on release blockers from `20`, especially authority/permission bypass, data/credential leak, duplicate material effect, false-success Outcome, worker surveillance, tool/agent trust bypass, memory leak, semantic formula drift, sandbox escape, prediction-as-fact, simulation→production mutation, Edge authority expansion, revoked asset still active, supply-chain bypass or OT safety-boundary violation.

## 26. Rollback

Rollback preserves source/state integrity, prevents duplicate side effects, marks stale/degraded projections truthfully, revokes credentials/assets/packages where applicable and preserves interpretability of historical Evidence/Outcome/artifacts.

## 27. Final maturity criterion

A capability é madura somente quando owner/source/contract estão claros, permissions continuam nas authorities canônicas, rollout é auditável e reversível, real outcomes são observáveis, e provider/executor/model pode ser substituído por contrato sem destabilizar DÉLIA.
