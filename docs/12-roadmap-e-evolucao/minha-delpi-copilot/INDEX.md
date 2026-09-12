# Índice rápido — Minha DELPI Copilot

Entrada principal: [`README.md`](./README.md).

## Authorities para implementar

1. [`16-execution-master-plan.md`](./16-execution-master-plan.md) — única ordem C0–C7.
2. [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md) — boundary: API/MFE próprios; Chat separado.
3. [`17-component-and-contract-map.md`](./17-component-and-contract-map.md) — owners/primitives/contracts.
4. [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md) — layers/patterns/Abstraction Gate, inclusive media/realtime/OT boundaries.
5. [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md) — fatos do Portal/Core/Gateway/APIs/MFEs e inventários `TO_INVENTORY`.
6. [`52-standalone-repository-and-bootstrap-plan.md`](./52-standalone-repository-and-bootstrap-plan.md) — estrutura física e bootstrap.
7. [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md) — gates/tests.
8. [`21-data-and-state-model.md`](./21-data-and-state-model.md) — state/persistence/media refs.
9. [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md) — prompt mestre.
10. [`25-requirements-traceability.md`](./25-requirements-traceability.md) — requirements `CP-001…CP-181`.
11. [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) — execution evidence/status.

## Produto/arquitetura

- [`01-visao-produto.md`](./01-visao-produto.md)
- [`02-arquitetura.md`](./02-arquitetura.md)
- [`12-roadmap.md`](./12-roadmap.md)
- [`13-functional-catalog.md`](./13-functional-catalog.md)
- [`14-definition-of-done.md`](./14-definition-of-done.md)
- [`15-integration-map.md`](./15-integration-map.md)
- [`19-rollout-and-migrations.md`](./19-rollout-and-migrations.md)
- [`24-product-specification.md`](./24-product-specification.md)
- [`48-documentation-governance-and-architecture-review.md`](./48-documentation-governance-and-architecture-review.md)

## Specs temáticas ativas

- `03–11` capabilities/platform/context/actions/workflows/security/UX/AI-ready/observability
- `18` app onboarding
- `26` iframe bridge
- `27–30` Copilot único/expertise/playbooks/multimodal
- `32` runtime nativo de Expertise da Copilot API
- `33` reference expertise pilots
- `34` market benchmark
- `35` Business Graph
- `36` Tasks/Cases/Rooms
- `37` Inbox/Watch
- `38` Evidence
- `39` Decision/Simulation
- `40` Knowledge/Learning
- `41` Expertise Studio
- `42` Model Router
- `43` Durable Workflow
- `44` mapa temático da inteligência operacional, subordinado ao `16`
- [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md) — voz/imagem/vídeo, Meeting, Frontline, shared devices, privacy e industrial/OT safety.

## Reference/superseded

- `31` antigo plano de migração de agents do Chat — **SUPERSEDED / REFERENCE_ONLY**
- `45` antiga extensão de testing gates — **SUPERSEDED / REFERENCE_ONLY**
- `46` antiga extensão de requirements — **SUPERSEDED / REFERENCE_ONLY**
- `47` antiga extensão do prompt Cursor — **SUPERSEDED / REFERENCE_ONLY**

## Regra rápida

```text
what next?             → 16
product boundary?      → 50
who owns it?           → 17
how to build?          → 49
platform facts?        → 51
where/how boot?        → 52
media/meeting/frontline? → 53
state/media refs?      → 21
how to prove?          → 20
which requirement?     → 25
what is executed?      → ledger
```

Nenhuma spec temática pode reintroduzir dependência de runtime no Minha DELPI Chat, redefinir a fase indicada pelo `16`, criar `FrontlineContext` paralelo ao WorkspaceContext, iniciar captura oculta ou transformar autonomia empresarial em autoridade física de máquina.