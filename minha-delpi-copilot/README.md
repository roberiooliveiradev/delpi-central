# Minha DELPI Copilot

Ponto de entrada da iniciativa no monorepo `delpi-central`.

O Copilot é uma **aplicação nova e standalone**, com API/MFE/persistência/deploy próprios e integrada às foundations do Portal/Core/Gateway/Keycloak/Domain APIs.

Ele **não** é evolução do `minha-delpi-ai-api` nem de `plugins/minha-delpi-chat`.

## North Star

O target é um único Copilot para **escritório, reuniões, chão de fábrica, fontes externas e operações autônomas governadas**, capaz de:

```text
perceber eventos
→ entender contexto/dados/processos
→ pesquisar/analisar
→ prever/simular
→ decidir sob policy
→ preparar/executar trabalho
→ verificar Outcome real
→ comunicar
→ aprender sob governança
```

Não é apenas Chat+RAG.

## Capability families

```text
Conversation / Context / Expertise / Knowledge
Personal Memory / Personalization
Multimodal / Biometrics / Meeting / Frontline
Internet / External Connectors / Teams
Business Actions / Business Graph
Semantic Business Layer
Event / Decision Intelligence
Process Intelligence / Process Mining
Automation & Execution Hub / RPA / Computer-use boundaries
Durable Work / Tasks / Cases / Rooms / Inbox / Watch
Analysis Sandbox / Artifact Workspace
Predictive / Prescriptive Intelligence / Operational Twin
MCP / A2A interoperability
AI Control Tower / Digital Workforce Governance
AI Model Lifecycle / MLOps
Capability Marketplace
Edge / Offline Industrial Copilot
Evidence / Outcome / Evals / Safety
```

## Documentation canônica

[`../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md)

Key authorities:

- [Execution Master Plan](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/16-execution-master-plan.md)
- [Ownership/Contracts](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/17-component-and-contract-map.md)
- [Tests/Gates](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/20-testing-and-acceptance-matrix.md)
- [State/Persistence](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/21-data-and-state-model.md)
- [Cursor Master Prompt](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md)
- [Requirements CP-001…CP-310](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/25-requirements-traceability.md)
- [Architecture Patterns](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/49-architecture-and-design-patterns-standard.md)
- [Standalone Boundary](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/50-standalone-copilot-application-architecture.md)
- [Platform Baseline](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/51-platform-integration-baseline.md)
- [Index](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/INDEX.md)
- [Execution Ledger](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/evidence/execution-ledger.md)

Thematic architecture is in specs `53–66`.

## Fundamental boundaries

```text
Core/Keycloak = identity/RBAC authority
Domain APIs = business authority
Portal = host/navigation/context
External providers = external source authority
OT/safety = industrial authority
Copilot = intelligence/policy/orchestration/evidence/work
```

And:

```text
Graph != Semantic Layer
Personal Memory != Organizational Knowledge
Prediction != FACT
Recommendation != Authorization
Simulate != Apply
PREPARE != ACT
Technical Success != Verified Business Outcome
MCP/A2A Discovery != Approval
Marketplace Install != Permission
Edge Offline != Wider Authority
```

## Execution state

```text
PROGRAM = PLANNED / NOT_STARTED
REQUIREMENTS = CP-001…CP-310
NEXT_STEP = C0.S0 — Enterprise AI/Platform Foundation Rebaseline
RUNTIME_DIFF = NONE
```

C0.S0 is factual inventory only. No Copilot runtime should be created before `C0.S7 FOUNDATION_FREEZE=PASS`.
