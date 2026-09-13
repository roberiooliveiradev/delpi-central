# Minha DELPI Copilot

> **Status:** `PLANNED / NOT_STARTED`  
> **Produto:** aplicação nova e standalone  
> **Requirements:** `CP-001…CP-310`  
> **Specs temáticas:** `53–66`  
> **Próxima etapa:** `C0.S0 — Enterprise AI/Platform Foundation Rebaseline`  
> **Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Execution state:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Decisão fundamental

O **Minha DELPI Copilot não é uma expansão do Minha DELPI Chat**.

```text
Minha DELPI Chat                  Minha DELPI Copilot
-------------------------------   --------------------------------
plugins/minha-delpi-chat          plugins/minha-delpi-copilot
minha-delpi-ai-api                minha-delpi-copilot-api
Chat state/runtime                own state/runtime
Chat release                      independent release

                 NO RUNTIME DEPENDENCY
```

## 2. North Star

> **Um único Copilot para escritório, reuniões, chão de fábrica, fontes externas e operações governadas, capaz de perceber eventos, entender pessoas/dados/processos, pesquisar, analisar, prever, simular, decidir, coordenar APIs/automações/pessoas, verificar resultados e aprender sob governança.**

```text
PERCEBER
→ ENTENDER
→ PESQUISAR
→ ANALISAR
→ PREVER/SIMULAR
→ DECIDIR
→ PREPARAR/EXECUTAR
→ VERIFICAR
→ COMUNICAR
→ APRENDER COM GOVERNANÇA
```

## 3. Surfaces

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
TEAMS future surface
BACKGROUND Watches/Workflows
ADMIN governance surfaces
```

Same Copilot API/MFE/product identity/policy/evidence/work runtime.

## 4. Capability map

```text
Conversation / Context
Expertise / Playbooks / Knowledge
Personal Memory / Personalization
Multimodal / Voice / Biometric
Internet Research / External Connectors / Teams
Business Actions / Business Graph
Semantic Business Layer
Event / Decision Intelligence
Process Intelligence / Process Mining
Automation & Execution Hub
Durable Work / Tasks / Cases / Rooms / Inbox / Watch
Analysis Sandbox / Artifact Workspace
Predictive / Prescriptive Intelligence
Operational Twin / Simulation
MCP / A2A interoperability
AI Control Tower
AI Model Lifecycle / MLOps
Capability Marketplace
Edge / Offline Industrial Copilot
Meeting / Frontline
Evidence / Outcome / Evals / Governance
```

## 5. Fundamental boundaries

```text
Core/Keycloak = identity/RBAC authority
Domain APIs = business authority
Portal = host/navigation/context
External providers = external-resource authority
OT/safety systems = machine/safety authority
Copilot = intelligence/policy/orchestration/work/evidence
```

And:

```text
Personal Memory != Organizational Knowledge
Business Graph != Semantic Business Layer
Prediction != FACT
Recommendation != Authorization
Simulate != Apply
Twin != source of truth
PREPARE != ACT
Read != Write
Draft != Send
Technical Success != Verified Business Outcome
MCP/A2A Discovery != Approval
Marketplace Install != Permission
Edge Offline != Wider Authority
```

## 6. Automation principle

Copilot is the brain; Automation & Execution Hub executes.

Default executor preference:

```text
Official API
→ native integration
→ deterministic function/script
→ RPA
→ computer-use
→ Human Task
```

Planner uses semantic capabilities, never UI clicks/selectors.

## 7. Process / Data intelligence

```text
Business Graph     → relationships
Semantic Layer     → official metric/business meaning
Process Intelligence → actual process behavior from event logs
Operational Twin  → scenario projection
```

Each remains a separate responsibility and none becomes master data.

## 8. AI governance

AI Control Tower governs assets/models/automations/connectors/tools/agents/Edge deployments with owner/risk/evals/health/cost/value/incidents/rollout/kill switches.

Model lifecycle and Marketplace assets are versioned/reviewed/revocable. Admin/catalog access never grants underlying business permission.

## 9. Personalization

Personal Memory can remember user preferences/followed work topics and support personalized briefings. User can inspect/correct/delete/disable it. It remains private by default and never replaces live business facts or RBAC.

## 10. Industrial/Edge direction

Frontline may use voice/camera/current procedures/operational context and, when C0/C7 prove feasibility, governed Edge/offline cache/inference/event buffering.

Copilot/Edge/RPA remain **not safety controllers**; free-form machine actuation is blocked by default.

## 11. Canonical authorities

Read in this order:

1. official project instructions + `.cursor` rules;
2. [`16`](./16-execution-master-plan.md) — single C0–C7 order;
3. [`50`](./50-standalone-copilot-application-architecture.md) — standalone boundary;
4. [`17`](./17-component-and-contract-map.md) — owners/contracts;
5. [`49`](./49-architecture-and-design-patterns-standard.md) — code architecture/patterns;
6. [`51`](./51-platform-integration-baseline.md) — factual baseline;
7. [`52`](./52-standalone-repository-and-bootstrap-plan.md) — physical/bootstrap;
8. [`21`](./21-data-and-state-model.md) — state/persistence;
9. [`20`](./20-testing-and-acceptance-matrix.md) — tests/gates;
10. [`25`](./25-requirements-traceability.md) — `CP-*` authority;
11. `53–66` — thematic specs;
12. ledger — actual execution evidence.

Full index: [`INDEX.md`](./INDEX.md).

## 12. Thematic specs

```text
53 Multimodal / Meeting / Frontline / Industrial
54 Biometric Identity / Human Observation
55 Internet Research / External Connectors
56 Microsoft Teams
57 Event-Driven Autonomous Operations / Automation Hub
58 Process Intelligence / Process Mining
59 AI Control Tower
60 MCP / A2A / Tool-Agent Interoperability
61 Personal Memory / Personalization
62 Semantic Business Layer
63 Analysis Sandbox / Artifact Workspace
64 Predictive / Prescriptive / Operational Twin
65 Edge / Offline Industrial Copilot
66 AI Model Lifecycle / Capability Marketplace
```

## 13. Current execution state

```text
PROGRAM = PLANNED / NOT_STARTED
RUNTIME_DIFF = NONE
NEXT = C0.S0
```

C0.S0 is factual inventory only. No Copilot API/MFE/runtime capability is created until C0.S7 `FOUNDATION_FREEZE=PASS`.
