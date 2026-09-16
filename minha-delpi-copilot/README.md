# DÉLIA — HISTORICAL technical placeholder (`minha-delpi-copilot`)

Este diretório é apenas um **ponto de entrada documental histórico** da iniciativa no monorepo `delpi-central`.

**Classificação:** `HISTORICAL` / `SUPERSEDED` como namespace técnico ativo.

Não é evidência de runtime implementado. O freeze candidato C0.S1 (`PLANNED / FROZEN_CANDIDATE`; ver `docs/.../delia/68-delia-product-identity-and-naming.md`) define:

```text
API  = delia-api/          (container delpi-delia-api; Gateway /apps/delia-api/)
MFE  = plugins/delia/      (container delpi-delia; /apps/delia)
APP  = delia
```

Pastas `delia-api/` e `plugins/delia/` **não** são criadas nesta etapa documental.

A **DÉLIA — DELPI · Ecossistema de Ligações, Inteligência e Automação** é uma aplicação nova e standalone, com API/MFE/persistência/deploy próprios quando implementados e integrada às foundations comprovadas do Portal/Core/Gateway/Keycloak/Domain APIs.

Ela **não** é evolução do `minha-delpi-ai-api` nem de `plugins/minha-delpi-chat`.

## North Star

O target é uma única DÉLIA para **escritório, reuniões, chão de fábrica, fontes externas e operações governadas**, capaz de:

```text
perceber eventos
→ entender contexto/dados/processos
→ pesquisar/analisar
→ prever/simular
→ decidir sob policy
→ preparar/executar trabalho governado
→ verificar Outcome real
→ comunicar
→ aprender sob governança
```

Não é apenas Chat + RAG.

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
Edge / Offline Industrial
Evidence / Outcome / Evals / Safety
```

## Documentação canônica

[`../docs/12-roadmap-e-evolucao/delia/README.md`](../docs/12-roadmap-e-evolucao/delia/README.md)

Key authorities:

- [Execution Master Plan](../docs/12-roadmap-e-evolucao/delia/16-execution-master-plan.md)
- [Ownership/Contracts](../docs/12-roadmap-e-evolucao/delia/17-component-and-contract-map.md)
- [Tests/Gates](../docs/12-roadmap-e-evolucao/delia/20-testing-and-acceptance-matrix.md)
- [State/Persistence](../docs/12-roadmap-e-evolucao/delia/21-data-and-state-model.md)
- [Cursor Master Prompt](../docs/12-roadmap-e-evolucao/delia/23-prompt-cursor-execucao.md)
- [Requirements CP-001…CP-316](../docs/12-roadmap-e-evolucao/delia/25-requirements-traceability.md)
- [Architecture Patterns](../docs/12-roadmap-e-evolucao/delia/49-architecture-and-design-patterns-standard.md)
- [Standalone Boundary](../docs/12-roadmap-e-evolucao/delia/50-standalone-copilot-application-architecture.md)
- [Platform Baseline](../docs/12-roadmap-e-evolucao/delia/51-platform-integration-baseline.md)
- [Bootstrap Target](../docs/12-roadmap-e-evolucao/delia/52-standalone-repository-and-bootstrap-plan.md)
- [Product Identity / Naming](../docs/12-roadmap-e-evolucao/delia/68-delia-product-identity-and-naming.md)
- [Index](../docs/12-roadmap-e-evolucao/delia/INDEX.md)
- [Execution Ledger](../docs/12-roadmap-e-evolucao/delia/evidence/execution-ledger.md)

Thematic architecture is in specs `53–66`.

## Fundamental boundaries

```text
Keycloak = identity/SSO
Core API = apps/routes/RBAC/governance
Domain APIs = business data/rules
Portal = host/navigation/context
DÉLIA = intelligence/context/Evidence/Policy/Decision/Work/orchestration/outcome coordination
Automation Hub = technical execution (external boundary TARGET; not inside DÉLIA)
Chat = REFERENCE_ONLY / INVENTORY_SOURCE
```
