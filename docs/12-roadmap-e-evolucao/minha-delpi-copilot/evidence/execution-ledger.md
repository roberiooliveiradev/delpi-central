# Minha DELPI Copilot — Execution Ledger

**Status do programa:** `PLANNED / NOT_STARTED`  
**Plano ativo:** [`../16-execution-master-plan.md`](../16-execution-master-plan.md)  
**Arquitetura/patterns:** [`../49-architecture-and-design-patterns-standard.md`](../49-architecture-and-design-patterns-standard.md)  
**Governança documental:** [`../48-documentation-governance-and-architecture-review.md`](../48-documentation-governance-and-architecture-review.md)  
**Protocolo:** [`../22-cursor-execution-protocol.md`](../22-cursor-execution-protocol.md)  
**Prompt mestre:** [`../23-prompt-cursor-execucao.md`](../23-prompt-cursor-execucao.md)  
**Próxima etapa obrigatória:** **C0.S0 — Rebaseline e inventário total**

## 1. Regra do ledger

Este arquivo registra somente **estado executável/evidence**, não redefine arquitetura nem ordem.

Uma subetapa só vira `PASS` com `COMPLETE_GATE=PASS` no HEAD correspondente.

## 2. Status canônico

| Fase | Status | Próximo step | Dependência |
|---|---|---|---|
| C0 Foundations | **NOT_STARTED** | **C0.S0** | nenhuma |
| C1 Platform/Context | LOCKED | — | C0.S6 FOUNDATION_FREEZE |
| C2 Intelligence Core | LOCKED | — | C1 + foundations |
| C3 Business Reads + Graph | LOCKED | — | C2 + OpenAPI-first gates aplicáveis |
| C4 Governed Writes | LOCKED | — | C3 read foundations + action gates |
| C5 Durable Work | LOCKED | — | C4 foundations |
| C6 Proactivity/Ecosystem/Learning | LOCKED | — | C5 + safety/evidence |
| C7 Optimization/Autonomy/Rollout | LOCKED | — | C0–C6 required gates |

E*/O* não aparecem como fases independentes. São apenas detalhamentos mapeados no plano mestre.

## 3. C0 sequence

```text
C0.S0 inventory total + architecture/pattern inventory
→ C0.S1 authorities/bounded contexts
→ C0.S2 shared primitives/envelopes
→ C0.S3 ports/persistence boundaries
→ C0.S4 cross-cutting semantics + architecture/pattern freeze
→ C0.S5 contract + architecture conformance harness
→ C0.S6 FOUNDATION_FREEZE
```

Nenhum runtime feature work C1+ antes de `FOUNDATION_FREEZE=PASS`.

## 4. Dependência externa vigente

A iniciativa `minha-delpi-ai-api/docs/roadmap/llm-json-decoupling/` permanece dependência para Business Actions enquanto os gates OpenAPI-first relevantes não estiverem `PASS` no candidate vigente.

```text
C0–C2 = podem avançar
C3+ Business Actions production-ready = BLOCKED_BY_AI_GATE até gates relevantes PASS
```

O Copilot não duplica a correção.

## 5. Decisões arquiteturais vigentes

```text
SINGLE_COPILOT_IDENTITY = TARGET
DEPARTMENT_AGENT_ROUTING = TO_MIGRATE
EXPERTISE_PACKS = PLANNED
DOMAIN_PLAYBOOKS = PLANNED
MULTIMODAL_RUNTIME = REUSE/EXTEND após inventário
DELPI_BUSINESS_GRAPH = PLANNED
EVIDENCE_PROVENANCE = FOUNDATION_CONTRACT
DECISION_GATE = FOUNDATION_CONTRACT
DURABLE_WORKFLOW = PLANNED
COPILOT_TASK = PLANNED
COPILOT_CASE = PLANNED
INTERACTION_ROOM_INTEGRATION = TO_INVENTORY
COPILOT_INBOX = PLANNED
COPILOT_WATCH = PLANNED
ORGANIZATIONAL_KNOWLEDGE = PLANNED
EXPERTISE_STUDIO = PLANNED
SIMULATION = LOCKED_TO_C7
MODEL_ROUTER = LOCKED_TO_C7

ARCHITECTURE_STYLE = CLEAN_ARCHITECTURE_PLUS_PORTS_ADAPTERS_PLUS_PRAGMATIC_DDD
EVENT_DRIVEN = ONLY_WITH_REAL_EVENT_OWNER
STATE_MACHINE = REQUIRED_FOR_NON_TRIVIAL_LIFECYCLE
CQRS = LIGHT_AND_JUSTIFIED_ONLY
DEPENDENCY_INVERSION = REQUIRED
COMPOSITION_ROOT_DI = REQUIRED
FRONTEND_DURABLE_BUSINESS_AUTHORITY = FORBIDDEN
ABSTRACTION_GATE = REQUIRED
LEGACY_MIGRATION = ADAPTER_ACL_STRANGLER_WHEN_APPLICABLE
```

Tudo acima é `PLAN_ONLY` até evidence de runtime futura.

## 6. Registro histórico de planejamento

| Data | HEAD | Evento | Status |
|---|---|---|---|
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | arquitetura inicial do Copilot | PLAN_ONLY |
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | Iframe Copilot Bridge incorporado | PLAN_ONLY |
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | Copilot único + Expertise/Playbooks/migração agents | PLAN_ONLY |
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | Business Graph/Tasks/Cases/Rooms/Inbox/Watch/Evidence/Decision/Knowledge/Simulation/Model Router | PLAN_ONLY |
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | revisão foundation-first: primitives antecipados para C0, authorities documentais consolidadas, E*/O* subordinados a C0–C7 | PLAN_ONLY; sem runtime diff |
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | padrão normativo de arquitetura/design patterns criado: Clean Architecture, Ports & Adapters, DDD pragmático, pattern matrix, Abstraction Gate, migration/resilience/testing rules | PLAN_ONLY; sem runtime diff |
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | requisitos CP-130–CP-140 adicionados para rastrear architecture style, layers, DI, patterns, errors, events, state machines, frontend state, migration e conformance | PLAN_ONLY; sem runtime diff |

## 7. Escopo obrigatório de C0.S0

### Platform/Core

```text
Router/Auth/AppHost/AppLauncher
/me /me/apps /me/routes
manifests/routes/permissions
MFE/iframe/external lifecycle
rooms/notifications/inbox patterns
```

### AI

```text
understanding/planner
Action Catalog/importer/index
executors
policy/confirmation
RAG/ACL
sessions/turn persistence
send/stream/simulate
multimodal
models/providers
observability/evals
```

### Legacy agents/skills

```text
agent entities/repos/controllers/admin
AgentSpecializationService
ChatWorkspaceAgentActivationService
ChatSoftAgentHandoffService
ChatSkillRegistry
agent_id/chat_mode
project default agent
knowledge/actions/tools gated by agent
agent selector/handoff UX
```

### Operational foundations

```text
canonical entity IDs/types
relationships/deep links
event bus/event types
workers/queues/jobs
workflow/checkpoint persistence
approval/confirmation models
idempotency support
audit/provenance
knowledge lifecycle
model/provider metrics
existing request/case concepts
```

### Architecture/pattern foundations

```text
actual backend layers/packages
use case/application service conventions
ports/adapters/gateways/repositories
composition root / DI
DTO/mappers
error/result taxonomy
state machines/lifecycle transitions
domain/integration events + event envelope
outbox/event publication
retry/timeout/circuit-breaker/idempotency
transaction/unit-of-work conventions
migration/compatibility/strangler patterns
frontend ui/state/data organization
server/workspace/conversation/local state owners
query/cache/store conventions
test doubles/contract/integration patterns
```

Classificar findings:

```text
REUSE
EXTEND
MIGRATE
CREATE_REQUIRED
DEPRECATE
REMOVE
NOT_PROVEN
```

Divergência entre código atual e `49`:

```text
ALIGN_DOC
MIGRATE_CODE
ADR_REQUIRED
NOT_PROVEN
```

## 8. Required C0 outputs

- app onboarding matrix factual;
- component/contract map updated from code;
- agent→expertise migration matrix;
- entity/relationship inventory;
- event/job/room/notification inventory;
- persistence/approval/idempotency inventory;
- architecture layer/pattern inventory;
- `49` revalidado contra o código real;
- Pattern Decision Matrix validada;
- Abstraction Gate validado;
- error/event/state/persistence/frontend-state/resilience rules congeladas;
- testing/migration patterns congelados;
- architectural exception/ADR process definido;
- owner gaps;
- ledger with HEAD and evidence.

## 9. Requirements authority

Única authority: [`../25-requirements-traceability.md`](../25-requirements-traceability.md).

Faixas:

```text
CP-001–060 core
CP-061–070 iframe
CP-071–089 single Copilot/expertise
CP-090–129 operational intelligence
CP-130–140 architecture/design patterns
```

`46-*` é reference only.

## 10. Tests authority

Única matriz: [`../20-testing-and-acceptance-matrix.md`](../20-testing-and-acceptance-matrix.md).

Architecture/design-pattern conformance também é required gate via `20` + `49`.

`45-*` é reference only.

## 11. Template de evento

```text
DATE:
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
DEPENDENCY_GATE:
CP_REQUIREMENTS:
CANONICAL_OWNERS:
ARCHITECTURE_LAYER:
DESIGN_PATTERNS_APPLIED:
ABSTRACTION_GATE:
ARCHITECTURAL_EXCEPTION_ADR:
REUSED_FOUNDATIONS:
NEW_FOUNDATIONS_CREATED:
EVIDENCE:
TESTS:
ARCHITECTURAL_CONFORMANCE:
FOUNDATION_DRIFT:
COMPLETE_GATE:
NEXT_UNLOCKED:
NOTES:
```

## 12. Estados permitidos

```text
NOT_STARTED
READY_TO_EXECUTE
IN_PROGRESS
BLOCKED_WITH_EVIDENCE
EXECUTION_DRIFT
FAIL
PASS
LOCKED
```

## 13. COMPLETE_GATE blockers

```text
PARTIAL
INCONCLUSIVE
PENDING
LEGACY_FALLBACK material
SHADOW_ONLY sem exit criteria
TODO/FIXME/HACK/TEMPORARY material
TEST_NOT_RUN
STALE_EVIDENCE
DUPLICATE_AUTHORITY
FOUNDATION_DRIFT
UNKNOWN_CONSUMER material
ARCHITECTURE_PATTERN_DRIFT
DEPENDENCY_RULE_VIOLATION
UNJUSTIFIED_ABSTRACTION
UNDOCUMENTED_ARCHITECTURAL_EXCEPTION
```

## 14. Primeiro comando de execução

Abrir `23-prompt-cursor-execucao.md` e executar somente **C0.S0**.

Não implementar CopilotBridge, Business Graph, Expertise runtime, Decision Gate, Workflow, Task, Case, Watch ou Model Router antes de suas fases canônicas.

C0.S0 deve primeiro provar os padrões reais do repo; C0.S4/C0.S6 congelam a arquitetura/patterns antes do primeiro runtime feature work.