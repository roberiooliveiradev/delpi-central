# Índice rápido — DÉLIA

Entrada principal: [`README.md`](./README.md).

## Authorities para implementar

1. instruções oficiais + `.cursor` rules — autoridade superior.
2. [`16-execution-master-plan.md`](./16-execution-master-plan.md) — única ordem C0–C7.
3. [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md) — standalone boundary.
4. [`17-component-and-contract-map.md`](./17-component-and-contract-map.md) — owners/primitives/contracts.
5. [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md) — layers/patterns/Abstraction Gate.
6. [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md) — factual platform baseline + `TO_INVENTORY` gaps.
7. [`52-standalone-repository-and-bootstrap-plan.md`](./52-standalone-repository-and-bootstrap-plan.md) — physical/bootstrap target.
8. [`21-data-and-state-model.md`](./21-data-and-state-model.md) — state/persistence/retention.
9. [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md) — tests/gates.
10. [`25-requirements-traceability.md`](./25-requirements-traceability.md) — `CP-001…CP-316` single requirement authority.
11. arquitetura técnica / product spec.
12. specs temáticas `53–66`.
13. [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) — execution state/evidence.

Naming: [`68-delia-product-identity-and-naming.md`](./68-delia-product-identity-and-naming.md).
Cross-cutting capability map: [`67-market-capability-expansion-and-intelligence-platform.md`](./67-market-capability-expansion-and-intelligence-platform.md).

## Product / architecture views

- [`01-visao-produto.md`](./01-visao-produto.md)
- [`02-arquitetura.md`](./02-arquitetura.md)
- [`12-roadmap.md`](./12-roadmap.md)
- [`13-functional-catalog.md`](./13-functional-catalog.md)
- [`14-definition-of-done.md`](./14-definition-of-done.md)
- [`15-integration-map.md`](./15-integration-map.md)
- [`19-rollout-and-migrations.md`](./19-rollout-and-migrations.md)
- [`24-product-specification.md`](./24-product-specification.md)
- [`34-market-benchmark-and-product-north-star.md`](./34-market-benchmark-and-product-north-star.md)
- [`48-documentation-governance-and-architecture-review.md`](./48-documentation-governance-and-architecture-review.md)
- [`67-market-capability-expansion-and-intelligence-platform.md`](./67-market-capability-expansion-and-intelligence-platform.md)
- [`68-delia-product-identity-and-naming.md`](./68-delia-product-identity-and-naming.md)

## Core thematic specs

```text
03 Capability Model
04 Platform Actions
05 Workspace Context
06 Business Action Parity
07 Agentic/Durable Workflows
08 Security / Autonomy / Audit
09 UX
10 AI-ready standard
11 Observability / Evals
18 App onboarding
26 Iframe bridge
27–30 DÉLIA / Expertise / Playbooks / Multimodal
32 Expertise runtime
33 reference expertise pilots
35 Business Graph
36 Tasks / Cases / Rooms
37 Inbox / Watch
38 Evidence / Provenance
39 Decision / Simulation
40 Organizational Knowledge / Learning
41 Expertise Studio
42 Model Router / Compute Policy
43 Durable Workflow Runtime
44 Operational Intelligence implementation map
```

## Active enterprise/industrial specs `53–66`

- [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)
- [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)
- [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)
- [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)
- [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md) — includes Recurring Governed Work / Scheduling target and boundaries
- [`58-process-intelligence-and-process-mining.md`](./58-process-intelligence-and-process-mining.md)
- [`59-ai-control-tower-and-digital-workforce-governance.md`](./59-ai-control-tower-and-digital-workforce-governance.md)
- [`60-agent-interoperability-mcp-a2a-and-tool-protocols.md`](./60-agent-interoperability-mcp-a2a-and-tool-protocols.md)
- [`61-personal-memory-and-personalization.md`](./61-personal-memory-and-personalization.md)
- [`62-semantic-business-layer-and-governed-metrics.md`](./62-semantic-business-layer-and-governed-metrics.md)
- [`63-analysis-sandbox-and-artifact-workspace.md`](./63-analysis-sandbox-and-artifact-workspace.md)
- [`64-predictive-prescriptive-intelligence-and-operational-twin.md`](./64-predictive-prescriptive-intelligence-and-operational-twin.md)
- [`65-edge-offline-industrial-copilot.md`](./65-edge-offline-industrial-copilot.md)
- [`66-ai-model-lifecycle-and-capability-marketplace.md`](./66-ai-model-lifecycle-and-capability-marketplace.md)

Prefixos temáticos `58` e `59` agora são exclusivos de Process Intelligence e AI Control Tower. Cross-cutting docs usam `67/68`.

## Recurring Governed Work / Scheduling

```text
Product target / semantics        → 57
Canonical order / phase mapping   → 16
Owner / contract boundary         → 17
State / persistence candidates    → 21
Acceptance / negative gates       → 20
Requirements                      → CP-311–CP-316 in 25
Cursor execution discipline       → 22 / 23
Execution evidence/status         → ledger
```

Interpretation:

```text
Recurring Governed Work = TARGET first-class capability
physical scheduler/timer owner = TO_INVENTORY until C0 proof
schedule != permission
C5 may allow bounded governed occurrence ACT under live gates
C6 Watch still has no autonomous ACT by default
runtime implementation = not PROVEN until evidence
```

## Reference-only / superseded

```text
31 old Chat agent migration plan
45 old testing extension
46 old requirements extension
47 old Cursor prompt extension
```

Não usar como authority atual.

## Quick routing

```text
what next?                     → 16
product boundary?              → 50
who owns it?                   → 17
how to build?                  → 49
what exists today?             → 51
where/how boot?                → 52
state/persistence?             → 21
how to prove?                  → 20
which CP?                      → 25
market capability map?         → 67
product naming?                → 68
security/autonomy?             → 08
UX?                            → 09
observability/evals?           → 11
media/meeting/frontline?       → 53
biometrics/people analysis?    → 54
internet/external?             → 55
Teams?                         → 56
autonomous operations/RPA?     → 57
scheduled/recurring work?      → 57 + 16/17/20/21/25 CP-311–316
Process Mining?                → 58
AI governance/control tower?   → 59
MCP/A2A?                       → 60
personal memory?               → 61
business metric semantics?     → 62
analysis/artifacts?            → 63
predictive/twin?               → 64
Edge/offline?                  → 65
models/marketplace?            → 66
what has actually executed?    → ledger
```

## Fundamental anti-drift rules

```text
DÉLIA = product name
delia-api / plugins/delia / /apps/delia* = FROZEN_CANDIDATE C0.S1
minha-delpi-copilot-* = HISTORICAL / SUPERSEDED as active target
Chat runtime dependency = forbidden
one execution order = 16
one CP authority = 25
Keycloak = identity/SSO
Core = apps/routes/RBAC/governance
Domain APIs = business authority
Portal = host/navigation/published context
DÉLIA = intelligence/Evidence/Policy/Decision/Work orchestration
Automation Hub = technical execution
Physical scheduler = technical time trigger, not Work/permission authority
Schedule != Permission
Recurring Governed Work != Watch autonomous ACT
Graph != Semantic Layer
Memory != Knowledge
Process Mining != employee scoring
Control Tower != business permission
MCP/A2A discovery != approval
Sandbox != unrestricted shell
Prediction != FACT
Recommendation != Authorization
Simulate != Apply
Edge offline != wider authority
Marketplace install != permission
Technical success != verified Outcome
PREPARE != ACT
C5 may allow governed ACT
C7 = advanced autonomous ACT; L5 default OFF
OT safety remains external authority
```
