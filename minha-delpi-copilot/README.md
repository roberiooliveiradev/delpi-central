# Minha DELPI Copilot

Ponto de entrada da iniciativa no monorepo `delpi-central`.

O Copilot é uma **aplicação nova e standalone** da Minha DELPI, composta por API e MFE próprios e integrada ao Portal/Core/Gateway/Keycloak/APIs existentes.

Ele não é evolução do `minha-delpi-ai-api` nem de `plugins/minha-delpi-chat`.

A visão alvo é **um único Copilot para escritório, reuniões e chão de fábrica**, com surfaces Global, Workspace, Meeting e Frontline sobre o mesmo runtime e governança.

## Documentação canônica

[`../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md)

## Estado

```text
PROGRAM = PLANNED / NOT_STARTED
NEXT_STEP = C0.S0 — Platform/Media/Device/OT inventory
```

## Authorities

- [Plano Mestre](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/16-execution-master-plan.md)
- [Boundary standalone](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/50-standalone-copilot-application-architecture.md)
- [Ownership/contracts](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/17-component-and-contract-map.md)
- [Architecture/design patterns](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/49-architecture-and-design-patterns-standard.md)
- [Platform integration baseline](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/51-platform-integration-baseline.md)
- [Repository/bootstrap plan](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/52-standalone-repository-and-bootstrap-plan.md)
- [Multimodal/Meeting/Frontline/Industrial](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/53-multimodal-meeting-frontline-and-industrial-copilot.md)
- [Tests/acceptance](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/20-testing-and-acceptance-matrix.md)
- [State/persistence/media](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/21-data-and-state-model.md)
- [Cursor prompt](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md)
- [Product specification](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/24-product-specification.md)
- [Traceability CP-001…CP-181](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/25-requirements-traceability.md)
- [Documentation governance](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/48-documentation-governance-and-architecture-review.md)
- [Execution ledger](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/evidence/execution-ledger.md)

## Target owners

```text
minha-delpi-copilot-api/       → new intelligence/work/media backend
plugins/minha-delpi-copilot/   → Global/Workspace/Meeting/Frontline federated MFE
portal/                        → host/context/navigation
core-api/                      → apps/routes/RBAC/governance
keycloak                       → identity/SSO
gateway/                       → routing
plugins/plugin-ui/             → shared design system
Domain APIs                    → business data/rules
OT/domain systems              → machine/process truth and industrial safety owners
```

## Ordem de construção

```text
C0 Platform + Architecture + Media/Privacy/OT Foundation Freeze
→ C1 Standalone Application Bootstrap
→ C2 Portal + Operational Context + Platform Commands
→ C3 Intelligence Core + Multimodal Foundations
→ C4 Business Reads + Graph
→ C5 Governed Writes + Durable Foundation
→ C6 Product Work + Meeting/Frontline + Proactivity + Ecosystem
→ C7 Advanced Realtime + Autonomy + Optimization + Rollout
```

## Boundaries essenciais

```text
Minha DELPI Chat offline
→ Copilot continua funcional

voice/image/video
→ same RBAC/policy as text

shared device
→ user A cannot leak into user B

process observation
→ candidate knowledge, not automatic rule

free-form LLM output
-X→ physical machine command
```

No Chat runtime/API/database fallback is allowed. Copilot is not an industrial safety controller.

## Primeira ação

Abrir o [prompt mestre](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md) e executar apenas **C0.S0**.

Nenhuma pasta/runtime do Copilot deve ser criada antes de `C0.S7 FOUNDATION_FREEZE=PASS`.