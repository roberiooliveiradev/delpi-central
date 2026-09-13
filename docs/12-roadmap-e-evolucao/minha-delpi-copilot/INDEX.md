# Índice rápido — Minha DELPI Copilot

Entrada principal: [`README.md`](./README.md).

## Authorities para implementar

1. [`16-execution-master-plan.md`](./16-execution-master-plan.md) — única ordem C0–C7.
2. [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md) — boundary: API/MFE próprios; Chat separado.
3. [`17-component-and-contract-map.md`](./17-component-and-contract-map.md) — owners/primitives/contracts.
4. [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md) — layers/patterns/Abstraction Gate, inclusive media/biometric/external/automation/OT boundaries.
5. [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md) — fatos atuais e inventários `TO_INVENTORY`.
6. [`52-standalone-repository-and-bootstrap-plan.md`](./52-standalone-repository-and-bootstrap-plan.md) — estrutura física e bootstrap.
7. [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md) — gates/tests.
8. [`21-data-and-state-model.md`](./21-data-and-state-model.md) — state/persistence/media/biometric/external/automation refs.
9. [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md) — prompt mestre.
10. [`25-requirements-traceability.md`](./25-requirements-traceability.md) — requirements `CP-001…CP-248`.
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
- `32–44` expertise, benchmark, Graph, work, Evidence, Decision, Knowledge, Model Router e Durable Workflow
- [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md) — multimodal/Meeting/Frontline/industrial safety.
- [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md) — face/voz closed-set e Human Observation governance.
- [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md) — Internet Research, OAuth, external connectors/actions/events/learning.
- [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md) — Teams chats/canais/meetings/transcripts/events/app surface.
- [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md) — Event/Signal Plane, Decision Intelligence, API/RPA/computer-use executors, Automation & Execution Hub, Outcome verification e autonomous operations.

## Reference/superseded

- `31` antigo plano de migração de agents do Chat — **SUPERSEDED / REFERENCE_ONLY**
- `45–47` extensões antigas — **SUPERSEDED / REFERENCE_ONLY**

## Regra rápida

```text
what next?                  → 16
product boundary?           → 50
who owns it?                → 17
how to build?               → 49
platform facts?             → 51
where/how boot?             → 52
media/meeting/frontline?     → 53
biometric/people analysis?  → 54
internet/external sources?  → 55
Microsoft Teams?            → 56
events/RPA/autonomy/Hub?    → 57
state/execution refs?       → 21
how to prove?               → 20
which requirement?          → 25
what is executed?           → ledger
```

Nenhuma spec temática pode reintroduzir dependência do Minha DELPI Chat, redefinir a fase de `16`, transformar event payload em permission, expor credentials, colocar business rule dentro de RPA, emitir click/selector no planner, criar segundo Workflow/planner no Automation Hub, confundir `PREPARE` com `ACT`, habilitar L5 global irrestrito ou transformar autonomia empresarial em autoridade física de máquina.
