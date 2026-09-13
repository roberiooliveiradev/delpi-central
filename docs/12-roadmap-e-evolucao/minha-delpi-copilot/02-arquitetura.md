# 02 — Arquitetura do Minha DELPI Copilot

**Status:** arquitetura alvo canônica  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Order:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Specs temáticas:** `53–66`

## 1. Decisão principal

Minha DELPI Copilot é aplicação standalone com API/MFE/persistence/deploy próprios. Chat é sistema separado/reference-only.

O target não é apenas conversational AI; é uma camada de inteligência empresarial/industrial governada.

## 2. Arquitetura macro

```text
Users / Devices / Meeting / Frontline / Teams
                    │
                    ▼
              Portal / Copilot Host
                    │
                    ▼
             Copilot Federated MFE
                    │
                    ▼
               Gateway / Nginx
                    │
                    ▼
            Copilot Standalone API
 ┌──────────────────┼──────────────────────────────────────────┐
 │                  │                                          │
 ▼                  ▼                                          ▼
Platform         Intelligence/Data                        Work/Execution
Core/RBAC        ├ Conversation/Planner                  ├ Policy/Decision
Domain APIs      ├ Expertise/Knowledge                   ├ Durable Workflow
External/Teams   ├ Personal Memory                      ├ Task/Case/Watch
Media/Biometric  ├ Business Graph                       ├ Automation Hub
Events           ├ Semantic Business Layer              └ Outcome Verification
OT read sources  ├ Process Intelligence
                 ├ Analysis/Artifacts
                 ├ Predictive/Prescriptive/Twin
                 ├ MCP/A2A interoperability
                 └ Model/AI Asset governance
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
   Provider/API   Sandbox      Edge Runtime
   adapters       adapters     integration
        │           │            │
        └───────────┴────────────┘
                    ▼
              Evidence / Audit
                    ▼
      Copilot-owned persistence/projections
```

Control Tower is governance plane across these assets, not another intelligence runtime.

## 3. Authority Matrix

| Concept | Authority |
|---|---|
| authentication | Keycloak |
| users/apps/routes/RBAC | Core API |
| navigation/hosting | Portal |
| business data/rules/actions | Domain APIs |
| external resource/scope | provider + connection owner |
| process intended design | process business owner |
| process observed traces | source event logs + Copilot derived projection |
| metric definition | metric business owner + Semantic Layer registry |
| personal memory | user + Copilot memory lifecycle |
| organizational knowledge | Knowledge governance/source owners |
| business graph | Copilot projection over source refs |
| prediction/model | model owner/provider + model registry/evals |
| scenario/twin | Copilot/domain projection; source state remains external |
| automation execution | executor owner + Copilot orchestration |
| verified business outcome | authoritative domain/provider source |
| AI asset governance | AI Control Tower projection/admin |
| tool/agent integration | approved MCP/A2A owner + Copilot policy |
| Edge device/runtime | device/Edge owner + Copilot package/sync governance |
| industrial safety | OT/safety owner |

## 4. Clean Architecture

```text
Domain
↑
Application
↑
Interfaces / Adapters
↑
Infrastructure
```

Domain/Application never import provider/model/RPA/MCP/A2A/sandbox/Edge SDKs.

## 5. Business / semantic / process data planes

Keep distinct:

```text
Domain APIs       → authoritative records/rules
Business Graph    → relationships
Semantic Layer    → official metric/business meaning
Process Intelligence → observed process traces/variants
Operational Twin → scenario projection
```

No one layer absorbs all others.

## 6. Conversation / Personal Memory / Knowledge

Keep distinct:

```text
Conversation History → current dialog continuity
WorkspaceContext     → current app/entity context
Personal Memory      → user preferences/continuity
Organizational Knowledge → reviewed reusable knowledge
```

Memory cannot become permission or live business truth.

## 7. Event / Decision architecture

```text
source event
→ validation/authenticity
→ EventEnvelope
→ dedupe/order/correlation
→ DecisionPathPolicy
   FAST | OPERATIONAL | REASONING
→ structured result/decision candidate
```

Not every event invokes LLM. Deterministic readiness uses Policy/Specification when possible.

## 8. Process Intelligence architecture

```text
authorized event logs
→ normalized process events
→ case traces
→ variants/conformance/bottlenecks
→ Evidence
→ improvement/automation candidate
```

Process Mining != employee surveillance.

## 9. Semantic Business Layer architecture

```text
question
→ resolve MetricDefinition
→ source query/calculation
→ value + definition version + Evidence
```

LLM interprets intent, not formula authority.

## 10. Analysis / Artifact architecture

```text
authorized data
→ isolated Analysis Sandbox
→ calculation/model/chart
→ Evidence
→ Artifact Workspace
```

Sandbox is bounded/read-only by default. Artifact has lineage/version/ACL/human-edit preservation.

## 11. Predictive / Prescriptive / Twin architecture

```text
source features/state
→ approved model/solver
→ Prediction / Scenario / Recommendation
→ Evidence
→ PREPARE / Decision
```

```text
prediction != fact
recommendation != authorization
simulated state != production state
simulate != apply
```

## 12. External / Teams / Internet architecture

Keep provider-neutral adapters, safe egress, least-privilege OAuth, Source/Evidence/freshness, source ACL and `read != write`, `draft != send`.

## 13. MCP / A2A architecture

```text
Copilot semantic capability/subtask
→ trust/allowlist/policy
→ MCP Tool Adapter or A2A Agent Adapter
→ result/artifact
→ normalized Evidence/Outcome
```

Discovery != approval. External agent/tool is not policy authority.

## 14. Automation & Execution architecture

```text
intent/event
→ semantic capability
→ Policy/Decision
→ Durable Workflow
→ executor mapping
→ API | Function | RPA | Computer-Use | Human Task
→ technical result
→ Outcome Verification
→ Evidence/Audit/Notification
```

Default executor preference is API→native integration→function→RPA→computer-use→human.

## 15. AI Control Tower architecture

Control Tower aggregates AIAsset/model/automation/tool/Edge projections and offers health/risk/eval/cost/value/incidents/rollout/kill switches.

It is not a second planner or business permission authority.

## 16. Model Lifecycle / Marketplace

```text
Model: experiment → eval → approve → deploy → monitor → rollback/revoke
Marketplace asset: draft → review → approve → publish → deprecate/revoke
```

Model Router only selects approved model. Marketplace install does not grant RBAC/provider scope.

## 17. Edge / Offline architecture

```text
central approved package/content/model
→ versioned Edge deployment
→ local bounded inference/cache/event buffer
→ sync/reconcile
```

Offline mode explicit; cache revision/freshness required; no authority widening or free-form OT actuation.

## 18. Security invariants

```text
external/tool/agent/model/package content = untrusted
provider/tool/RPA/model secrets → protected boundary only
Process Mining != worker score
Personal Memory != org truth
Sandbox != unrestricted shell
Prediction != FACT
Twin != system of record
Control Tower admin != business permission
Marketplace install != permission
Edge offline != wider authority
L5 default = OFF
Copilot != safety controller
```

## 19. Physical/deployment rule

Thematic capability name does not imply service. Default implementation remains new Copilot API/MFE with internal bounded modules/adapters. Split into neutral/shared service only when C0 evidence/ADR proves ownership, consumers, scale/isolation and lifecycle justify it.

## 20. Generalization target

Architecture must onboard without planner core rewrite:

- new Domain OpenAPI;
- new metric/process source;
- new provider/connector;
- new executor;
- new model;
- new MCP server/A2A agent;
- new Edge device class;
- new Marketplace asset type compatible with canonical contracts.

## 21. Sequence

```text
C0 foundations
→ C1 standalone bootstrap
→ C2 context/commands
→ C3 capability foundations
→ C4 reads/analysis/discovery
→ C5 governed writes/executors/artifacts
→ C6 product governance/experience
→ C7 advanced autonomy/Edge/Twin/Marketplace scale
```

## 22. Structural success

The architecture is correct when capabilities can expand without creating duplicate authorities, provider/model/executor hardcode, unsafe secrets, hidden surveillance, unverified success or Chat dependency, and every material output/action remains traceable to sources, versions, policies and verified outcomes.
