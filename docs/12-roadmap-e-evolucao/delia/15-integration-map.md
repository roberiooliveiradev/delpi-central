# 15 — Mapa de integração da DÉLIA

**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Specs temáticas:** `53–66`

## 1. Mapa macro

```text
Users / Devices / Meeting / Frontline / Teams
                    │
                    ▼
Portal → DÉLIA MFE → Gateway → DÉLIA API
                              │
     ┌────────────────────────┼───────────────────────────┐
     ▼                        ▼                           ▼
Keycloak/Core           Domain APIs/OpenAPI       External Providers
identity + RBAC         business authority        OAuth/API/Webhooks
     │                        │                           │
     └────────────────────────┼───────────────────────────┘
                              ▼
                    Evidence / Context / Graph
                              │
             ┌────────────────┼─────────────────┐
             ▼                ▼                 ▼
        Semantic Layer  Process Intelligence  Models/Sandbox
             │                │                 │
             └────────────────┼─────────────────┘
                              ▼
                      Policy / Decision
                              ▼
                    DÉLIA Durable Work
                              ▼
                 semantic execution request
                              ▼
                     Automation Hub
             API / Function / RPA / Tool path
                              ▼
                     technical result
                              ▼
                authoritative Outcome Verification
                              ▼
                    Audit / Notification
```

Keycloak e Core aparecem próximos apenas no diagrama: são authorities distintas. Keycloak = identity/SSO; Core = apps/routes/RBAC/governance.

Cross-cutting: AI Control Tower, Personal Memory, Artifact Workspace, MCP/A2A, Operational Twin, Edge/Offline and Model Lifecycle.

## 2. Portal ↔ DÉLIA

Portal hosts/navigation/published context only. No planner, provider/model/RPA logic, secret storage or semantic calculation in Portal.

## 3. DÉLIA ↔ Core / Keycloak

Keycloak remains identity/SSO authority. Core remains apps/routes/RBAC/governance authority. Memory/device/event/model/tool metadata cannot mutate these authorities.

## 4. DÉLIA ↔ Domain APIs

```text
OpenAPI
→ Action Catalog
→ authorized semantic capability
→ Policy/Decision
→ direct Domain API call when that is the approved contract
→ Outcome/Evidence
```

When authoritative API exists, it is preferred over RPA/computer-use. DÉLIA does not copy domain business rules.

## 5. DÉLIA ↔ Public Internet / External Providers / Teams

- Search + Safe Fetch for public Internet;
- OAuth/API adapters for connected sources;
- provider webhook/change notifications → EventEnvelope;
- source ACL/freshness/provenance preserved;
- credentials stay in secret boundary;
- `read != write`, `draft != send`.

## 6. DÉLIA ↔ Event Sources

```text
Domain/MES/provider/Edge event
→ authenticity/trust validation
→ EventEnvelope
→ dedupe/order/correlation
→ Watch/Workflow/Decision
```

Polling is bounded fallback only. Event never grants permission.

## 7. DÉLIA ↔ Process Intelligence

```text
authorized event logs
→ process event projection
→ traces/variants/conformance/bottlenecks
→ Evidence
→ process/automation candidate
```

Source systems remain event authorities. Process Mining does not become people-scoring authority.

## 8. DÉLIA ↔ Semantic Business Layer

```text
MetricDefinition
→ authorized source query/calculation
→ metric value + version + Evidence
```

Metric metadata never grants row/source access. Graph and Semantic Layer stay separate.

## 9. DÉLIA ↔ Analysis Sandbox

```text
authorized bounded dataset
→ isolated sandbox
→ calculation/model/chart
→ Evidence/Artifact
```

No direct broad production DB credential. Read-only source integration by default.

## 10. DÉLIA ↔ Artifact Workspace

Artifacts store/version content and provenance/ACL. Source data remains source-owned. Export/share/email/Teams send are separate governed actions.

## 11. DÉLIA ↔ Predictive Models / Operational Twin

```text
source features/state
→ approved Model/Simulation Adapter
→ Prediction/Scenario
→ Evidence
→ Recommendation/PREPARE
```

Prediction != fact; simulated state != production state; Apply revalidates live owners.

## 12. DÉLIA ↔ Automation Hub

```text
semantic capability
→ DÉLIA Policy/Decision/Work
→ executor selection/mapping
→ Automation Hub contract
→ technical executor path
→ technical result
→ authoritative Outcome Verifier
```

Automation Hub is technical-execution boundary, not second planner/business/permission authority.

## 13. DÉLIA ↔ RPA

If C0 proves RPA infrastructure and the capability is approved for that fallback:

```text
DÉLIA Work
→ AutomationHubPort / approved execution contract
→ Automation Hub
→ RPA adapter/orchestrator
→ queue/worker/session
→ legacy app
→ authoritative postcondition verification
```

Package/version/credentials/session/idempotency/ambiguous outcome are bounded by the technical execution owner. DÉLIA does not create a parallel `AutomationExecutorPort` that bypasses the Hub boundary.

## 14. DÉLIA ↔ MCP / A2A

```text
MCP:
semantic tool need → approved Tool Adapter → server → normalized result

A2A:
bounded subtask → approved Agent Adapter → external agent → result/artifact
```

Discovery/metadata does not imply trust or permission. Writes pass same Decision/Outcome gates.

## 15. DÉLIA ↔ Personal Memory

Memory store is user-private DÉLIA-owned state/projection when implemented. It receives bounded user-confirmed/preferences data and feeds relevance/presentation only. It does not write Core profile/RBAC unless a separate authorized platform action explicitly does so.

## 16. DÉLIA ↔ AI Control Tower

Control Tower consumes refs/telemetry from models, automations, connectors, tools/agents, Edge and capabilities; sends admin commands for enable/disable/rollout/kill switch through governed admin contracts.

It does not execute domain actions directly.

## 17. DÉLIA ↔ Model Lifecycle

```text
Model Registry/Evals
→ approved deployment
→ Model Adapter/Router
→ inference
→ lineage/metrics
→ drift/rollback/revoke
```

Revoked model removed from selection.

## 18. DÉLIA ↔ Capability Marketplace

```text
package/asset
→ review/evals/security/integrity
→ catalog publish
→ local enable/config
→ existing RBAC/provider authorization still required
```

Marketplace never grants permission.

## 19. DÉLIA ↔ Edge / Offline

```text
approved central content/model/package
→ Edge deployment
→ local bounded cache/inference/event buffer
→ sync/reconcile
```

Device/user identities remain separate. Offline never widens authority. OT segmentation/safety respected.

## 20. Outcome / Notification integration

```text
technical result
→ authoritative postcondition verification
→ VERIFIED_SUCCESS|FAILURE|PENDING|INCONCLUSIVE
→ Evidence/Audit
→ notification/escalation
```

Notification is consequence, not proof.

## 21. Knowledge / Learning integration

External/process/execution/model/analysis evidence can create candidate Knowledge/Playbook/Automation improvement. Publish/update requires review/eval/version/privacy/freshness as appropriate.

## 22. Kill switches

Independent controls where material:

```text
DÉLIA writes
Internet/connector/provider
Watch autonomous ACT
a specific automation/executor
MCP server/A2A agent
sandbox
model/deployment
Marketplace asset
Edge package/device capability
media/biometric capture
OT integration
```

## 23. Failure boundaries

Distinguish source unavailable, no data, permission missing, model stale/OOD, process data incomplete, sandbox failed, agent/tool revoked, executor ambiguous, outcome unverified, Edge offline/stale, package/model revoked.

Never convert infrastructure failure into business conclusion.

## 24. C0 rule

Every integration in this document is either `PROVEN` by the evidence scope registered in `51` or remains `TO_INVENTORY`, `PLANNED` or `TARGET`. No market product/API is treated as DELPI reuse until factual evidence proves owner, contract, consumers and readiness.
