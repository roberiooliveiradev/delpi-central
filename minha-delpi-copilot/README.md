# Minha DELPI Copilot

Ponto de entrada da iniciativa no monorepo `delpi-central`.

O Copilot é uma **aplicação nova e standalone** da Minha DELPI, composta por API e MFE próprios e integrada ao Portal/Core/Gateway/Keycloak/APIs existentes.

Ele não é evolução do `minha-delpi-ai-api` nem de `plugins/minha-delpi-chat`.

## Documentação canônica

[`../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md)

## Estado

```text
PROGRAM = PLANNED / NOT_STARTED
NEXT_STEP = C0.S0 — Platform/monorepo inventory
```

## Authorities

- [Plano Mestre](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/16-execution-master-plan.md)
- [Boundary standalone](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/50-standalone-copilot-application-architecture.md)
- [Ownership/contracts](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/17-component-and-contract-map.md)
- [Architecture/design patterns](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/49-architecture-and-design-patterns-standard.md)
- [Platform integration baseline](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/51-platform-integration-baseline.md)
- [Repository/bootstrap plan](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/52-standalone-repository-and-bootstrap-plan.md)
- [Tests/acceptance](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/20-testing-and-acceptance-matrix.md)
- [State/persistence](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/21-data-and-state-model.md)
- [Cursor prompt](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md)
- [Product specification](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/24-product-specification.md)
- [Traceability CP-001…CP-154](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/25-requirements-traceability.md)
- [Documentation governance](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/48-documentation-governance-and-architecture-review.md)
- [Execution ledger](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/evidence/execution-ledger.md)

## Target owners

```text
minha-delpi-copilot-api/       → new backend/runtime
plugins/minha-delpi-copilot/   → new federated MFE
portal/                        → host/context/navigation
core-api/                      → apps/routes/RBAC/governance
keycloak                       → identity/SSO
gateway/                       → routing
plugins/plugin-ui/             → shared design system
Domain APIs                    → business data/rules
```

## Ordem de construção

```text
C0 Platform + Architecture Foundation Freeze
→ C1 Standalone Application Bootstrap
→ C2 Portal Context + Platform Commands
→ C3 Intelligence Core
→ C4 Business Reads + Graph
→ C5 Governed Writes + Durable Foundation
→ C6 Product Work + Proactivity + Ecosystem
→ C7 Autonomy + Optimization + Rollout
```

## Boundary test

A arquitetura só está correta se:

```text
Minha DELPI Chat offline
→ Copilot API continues healthy
→ Copilot MFE continues mountable
→ Portal/Core/Domain integration continues functional
```

No Chat runtime/API/database fallback is allowed.

## Primeira ação

Abrir o [prompt mestre](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md) e executar apenas **C0.S0**.

Nenhuma pasta/runtime do Copilot deve ser criada antes de `C0.S7 FOUNDATION_FREEZE=PASS`.