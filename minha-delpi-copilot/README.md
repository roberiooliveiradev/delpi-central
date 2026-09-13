# Minha DELPI Copilot

Ponto de entrada da iniciativa no monorepo `delpi-central`.

O Copilot é uma **aplicação nova e standalone** da Minha DELPI, composta por API e MFE próprios e integrada ao Portal/Core/Gateway/Keycloak/APIs existentes.

Ele não é evolução do `minha-delpi-ai-api` nem de `plugins/minha-delpi-chat`.

A visão alvo é **um único Copilot para escritório, reuniões, chão de fábrica e fontes externas autorizadas**, com surfaces Global, Workspace, Meeting e Frontline sobre o mesmo runtime/governança, incluindo multimodalidade, biometria governada, Internet Research e External Connectors.

## Documentação canônica

[`../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md)

## Estado

```text
PROGRAM = PLANNED / NOT_STARTED
NEXT_STEP = C0.S0 — Platform/Media/Device/Biometric/External/OT inventory
```

## Authorities

- [Plano Mestre](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/16-execution-master-plan.md)
- [Boundary standalone](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/50-standalone-copilot-application-architecture.md)
- [Ownership/contracts](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/17-component-and-contract-map.md)
- [Architecture/design patterns](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/49-architecture-and-design-patterns-standard.md)
- [Platform integration baseline](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/51-platform-integration-baseline.md)
- [Repository/bootstrap plan](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/52-standalone-repository-and-bootstrap-plan.md)
- [Multimodal/Meeting/Frontline/Industrial](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/53-multimodal-meeting-frontline-and-industrial-copilot.md)
- [Biometric Identity/Human Observation](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/54-biometric-identity-and-human-observation-governance.md)
- [Internet Research/External Connectors](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/55-internet-research-and-external-connectors.md)
- [Tests/acceptance](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/20-testing-and-acceptance-matrix.md)
- [State/persistence](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/21-data-and-state-model.md)
- [Cursor prompt](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md)
- [Product specification](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/24-product-specification.md)
- [Traceability CP-001…CP-214](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/25-requirements-traceability.md)
- [Documentation governance](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/48-documentation-governance-and-architecture-review.md)
- [Execution ledger](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/evidence/execution-ledger.md)

## Target owners

```text
minha-delpi-copilot-api/       → intelligence/work/media/biometric/external backend
plugins/minha-delpi-copilot/   → Global/Workspace/Meeting/Frontline federated MFE
portal/                        → host/context/navigation
core-api/                      → apps/routes/RBAC/governance/user authority
keycloak                       → identity/SSO
gateway/                       → routing
plugins/plugin-ui/             → shared design system
Domain APIs                    → business data/rules
External Providers             → external account/resource authority
Secret/Vault owner             → provider credential material
OT/domain systems              → machine/process truth and industrial safety owners
```

## Ordem de construção

```text
C0 Platform + Architecture + Media/Privacy/Biometric/External/OT Foundation Freeze
→ C1 Standalone Application Bootstrap
→ C2 Portal + Operational Context + Platform Commands
→ C3 Intelligence + Multimodal/Biometric/Internet/Connector Foundations
→ C4 Business + External Reads + Graph
→ C5 Governed Business/External Writes + Durable Foundation
→ C6 Product Work + Meeting/Frontline + External Events + Ecosystem
→ C7 Advanced Realtime + External Proactivity + Autonomy + Rollout
```

## Boundaries essenciais

```text
Minha DELPI Chat offline
→ Copilot continua funcional

Internet/public content
→ untrusted Source/Evidence, not policy authority

External connection scope
-X→ Core permission elevation

Provider token/secret
-X→ LLM / MFE / ordinary log

personal connection
-X→ organization-wide source automatically

read
-X→ write

draft
-X→ send automatically

provider event
-X→ ungoverned action

biometric match
-X→ permission grant

Human Observation
→ observable process evidence, not psychological/person score

free-form LLM output
-X→ physical machine command
```

## Primeira ação

Abrir o [prompt mestre](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md) e executar apenas **C0.S0**.

Nenhuma pasta/runtime do Copilot deve ser criada antes de `C0.S7 FOUNDATION_FREEZE=PASS`.
