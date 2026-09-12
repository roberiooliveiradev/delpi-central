# Minha DELPI Copilot

Ponto de entrada da iniciativa no monorepo `delpi-central`.

O Copilot é a **camada inteligente operacional da Minha DELPI**: pergunta, faz, acompanha e trabalha sobre a plataforma existente usando as mesmas permissions, APIs/use cases e regras de negócio.

## Documentação canônica

[`../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md)

## Estado

```text
PROGRAM = PLANNED / NOT_STARTED
NEXT_STEP = C0.S0 — Rebaseline e inventário total
```

## Authorities principais

- [Plano Mestre foundation-first](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/16-execution-master-plan.md)
- [Ownership e contracts](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/17-component-and-contract-map.md)
- [Arquitetura e design patterns](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/49-architecture-and-design-patterns-standard.md)
- [Testes e aceite](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/20-testing-and-acceptance-matrix.md)
- [Dados e estado](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/21-data-and-state-model.md)
- [Prompt mestre do Cursor](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md)
- [Especificação do produto](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/24-product-specification.md)
- [Rastreabilidade CP-001…CP-140](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/25-requirements-traceability.md)
- [Governança documental](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/48-documentation-governance-and-architecture-review.md)
- [Execution ledger](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/evidence/execution-ledger.md)

## Ordem de construção

```text
C0 Foundations
→ C1 Platform/Context
→ C2 Intelligence Core
→ C3 Business Reads + Graph
→ C4 Governed Writes
→ C5 Durable Work
→ C6 Proactivity/Ecosystem/Learning
→ C7 Optimization/Autonomy/Rollout
```

### Primeiro freeze

```text
C0.S0 inventory + patterns reais do repo
→ C0.S1 authorities/bounded contexts
→ C0.S2 shared primitives
→ C0.S3 ports/persistence boundaries
→ C0.S4 cross-cutting semantics + architecture/pattern freeze
→ C0.S5 contract/conformance harness
→ C0.S6 FOUNDATION_FREEZE
```

Nenhum runtime feature work deve preceder esse gate.

O freeze inclui, além dos contratos, validação de:

```text
Clean Architecture
Ports & Adapters
DDD pragmático
layer/dependency rules
Pattern Decision Matrix
error/event/state/persistence/frontend rules
resilience/idempotency
migration/strangler patterns
Abstraction Gate
architectural exception/ADR process
```

## Owners a evoluir

- `minha-delpi-ai-api` — intelligence/retrieval/planning/policy/execution coordination/evidence/workflow orchestration;
- `plugins/minha-delpi-chat` — UX conversacional, activity, evidence, Decision Gates, rendering;
- `portal` — Router, CopilotBridge, Workspace Context, IframeBridge, global surfaces;
- Core API — apps/routes/RBAC/governance;
- APIs de domínio — Business Actions/OpenAPI/use cases/outcomes;
- MFEs/iframes — context, EntityRefs, deep links, visual capabilities;
- infraestrutura existente de events/jobs/rooms/notifications — reutilizar antes de criar nova.

Não criar um segundo motor de IA, Graph como banco mestre, Task engine separado, agent runtime por departamento ou arquitetura/pattern local concorrente.

## Primeira ação do Cursor

Abrir o [prompt mestre](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md) e executar **somente C0.S0**.

C0.S0 é inventário/evidence: além dos componentes funcionais, deve mapear patterns/layers/DI/errors/events/state/resilience/migrations reais do repositório para validar o documento `49` antes do `FOUNDATION_FREEZE`.

C0.S0 não implementa CopilotBridge, Graph, Expertise, Decision Gate, Workflow, Task, Case, Watch ou Model Router.