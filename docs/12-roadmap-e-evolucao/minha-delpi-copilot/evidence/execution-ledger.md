# Minha DELPI Copilot — Execution Ledger

**Status do programa:** `PLANNED / NOT_STARTED`  
**Plano ativo:** [`../16-execution-master-plan.md`](../16-execution-master-plan.md)  
**Extensão operacional:** [`../44-operational-intelligence-implementation-plan.md`](../44-operational-intelligence-implementation-plan.md)  
**Protocolo:** [`../22-cursor-execution-protocol.md`](../22-cursor-execution-protocol.md)  
**Prompt mestre:** [`../23-prompt-cursor-execucao.md`](../23-prompt-cursor-execucao.md)  
**Próxima etapa obrigatória:** **C0.S0 — Rebaseline e inventário real**

## 1. Regra do ledger

Este arquivo registra o estado executável vigente. Não apagar histórico; adicionar eventos e atualizar a tabela de status quando evidence justificar.

Uma etapa só muda para `PASS` quando `COMPLETE_GATE=PASS` no HEAD correspondente.

## 2. Status por fase

| Fase | Status | Etapa atual | Dependência/bloqueio |
|---|---|---|---|
| C0 Fundação/inventário | **NOT_STARTED** | **C0.S0** | nenhuma; iniciar aqui |
| C1 Platform Actions | LOCKED | — | C0 completo |
| C2 Workspace Context | LOCKED | — | C1 base + contratos C0 |
| C3 Business Action Parity | LOCKED | — | C2 + gates AI/OpenAPI-first relevantes |
| C4 Agentic/Durable Workflows | LOCKED | — | C3 |
| C5 Ecossistema AI-ready / expertise / graph-cases waves | LOCKED | — | C3/C4 foundation |
| C6 Autonomia governada / decision gates / watch ACT | LOCKED | — | C4/C5 + safety gates |
| C7 Rollout final | LOCKED | — | C0–C6 required gates |
| O0–O13 Inteligência operacional | LOCKED | O0 após inventário | dependem das fases C* conforme `44-*` |

## 3. Dependência externa vigente

A iniciativa `minha-delpi-ai-api/docs/roadmap/llm-json-decoupling/` está documentada com `VERIFY_FINAL_FAILED` após auditoria pós-fechamento.

Classificação para o Copilot:

```text
C0-C2 = podem avançar
C3 scaffolding/tests = pode avançar se não mascarar dependência
C3 production-ready Business Actions = BLOCKED até gates relevantes PASS
C4+ production workflows com Business Actions = BLOCKED pela mesma dependência
```

O Copilot não assume ownership da correção da Onda J.

## 4. Decisão arquitetural vigente — Copilot único

```text
SINGLE_COPILOT_IDENTITY = TARGET
DEPARTMENT_AGENT_ROUTING = TO_MIGRATE
EXPERTISE_PACKS = PLANNED
DOMAIN_PLAYBOOKS = PLANNED
MULTIMODAL_EXPERTISE = REUSE_EXISTING_RUNTIME
SOFT_AGENT_HANDOFF = TO_DEPRECATE
AGENT_REQUIRED_OPERATIONAL_TOOLS = TO_MIGRATE
```

Fontes: `27`–`33`.

Essa decisão **não altera a próxima etapa**: continua C0.S0.

## 5. Decisão estratégica vigente — camada operacional inteligente

A evolução de produto passa a incluir, de forma faseada:

```text
DELPI_BUSINESS_GRAPH = PLANNED
EVIDENCE_PROVENANCE_LAYER = PLANNED
COPILOT_TASKS = PLANNED
COPILOT_CASES = PLANNED
INTERACTION_ROOMS_INTEGRATION = TO_INVENTORY
COPILOT_INBOX = PLANNED
COPILOT_WATCH = PLANNED
DURABLE_WORKFLOW_RUNTIME = PLANNED
DECISION_GATES = PLANNED
WHAT_IF_SIMULATION = LOCKED_BY_DOMAIN_MODEL
ORGANIZATIONAL_EXPERIENCE_KNOWLEDGE = PLANNED
EXPERTISE_STUDIO = PLANNED
MODEL_ROUTER = LOCKED_BY_BASELINE
```

Fontes canônicas: `34`–`47`.

Esta decisão é **PLAN_ONLY**. Nenhum desses itens deve ser reportado como runtime existente sem evidence futura.

## 6. Registro de execução

| Data | HEAD | Etapa | Evento | Status/evidence |
|---|---|---|---|---|
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | Planejamento | documentação arquitetural/funcional e plano executável criados | PLAN_ONLY |
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | Planejamento | integração de apps iframe incorporada: Iframe Copilot Bridge, classes I0–I3, segurança e CP-061–CP-070 | PLAN_ONLY; sem runtime diff |
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | Planejamento | decisão de Copilot único incorporada: Expertise Packs, Domain Playbooks, multimodalidade, migração de agent specialization/handoff/activation e CP-071–CP-089 | PLAN_ONLY; sem runtime diff |
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | Planejamento | expansão de produto para camada operacional inteligente: Business Graph, Tasks/Cases/Rooms, Inbox/Watch, Evidence/Provenance, Decision Gates, Simulation, Organizational Knowledge, Expertise Studio, Model Router e Durable Workflow; CP-090–CP-129 | PLAN_ONLY; sem runtime diff |

## 7. Escopo obrigatório no C0.S0 — apps/iframe

Inventariar:

```text
renderMode
entry/origin authority
allowed origins
SSO/auth mode
bridge existente?
protocol/version
context publish
visual commands
Business API/OpenAPI
CSP/frame constraints
security owner
iframe integration class
```

Fonte: [`../26-iframe-copilot-bridge.md`](../26-iframe-copilot-bridge.md).

## 8. Escopo obrigatório no C0.S0 — agents/skills/expertise

Inventariar e classificar:

```text
agent entities/tables/repositories
agent CRUD/admin
agent metadata/instructions
AgentSpecializationService
ChatWorkspaceAgentActivationService
ChatSoftAgentHandoffService
ChatSkillRegistry
allowed actions by agent
session.agent_id
chat_mode common/agent
project default agent
knowledge scopes/namespaces by agent
agent selector UX
soft handoff UX/events
agent-related tests/fixtures/scripts/docs
usage telemetry
multimodal skills and has_agent dependencies
```

Classificação:

```text
KEEP
MIGRATE_TO_EXPERTISE
MIGRATE_TO_PROJECT_CONTEXT
MIGRATE_TO_CAPABILITY_POLICY
DEPRECATE
REMOVE
NOT_PROVEN
```

## 9. Escopo obrigatório no C0.S0 — inteligência operacional

Inventariar com arquivo/símbolo/owner/evidence:

```text
canonical entity types/IDs
existing entity relations/deep links
existing event bus and event types
background jobs/queues/workers
notifications/inbox patterns
interaction rooms/chats
approval/confirmation models
workflow/task persistence
checkpoint/resume mechanisms
audit/provenance metadata
knowledge sources/version/lifecycle
model/provider abstractions
latency/token/cost metrics
existing case/request domains usable as Task/Case foundation
```

Classificar cada item:

```text
REUSE
EXTEND
MIGRATE
CREATE_REQUIRED
NOT_PROVEN
OUT_OF_SCOPE_WITH_DECISION
```

C0.S0 deve atualizar `44-operational-intelligence-implementation-plan.md` se o inventário provar owners/infra diferentes das hipóteses.

## 10. Baseline já observado para revalidar

Há findings prévios a confirmar no HEAD executado:

- `AgentSpecializationService` possui presets por domínio;
- `ChatWorkspaceAgentActivationService` condiciona tools operacionais ao agent activation;
- `ChatSoftAgentHandoffService` oferece troca de agente;
- `ChatSkillRegistry` possui document vision/drawing/quality skills;
- existe runtime multimodal reaproveitável;
- a plataforma possui event-driven e salas de interação documentadas, mas o C0.S0 deve localizar contratos/runtime reais antes de reuse.

Esses são findings para revalidar, não autorização para runtime diff.

## 11. Requisitos e gates

Faixas vigentes:

```text
CP-001–CP-060 = core inicial
CP-061–CP-070 = iframe
CP-071–CP-089 = Copilot único / expertise / migração agents
CP-090–CP-129 = inteligência operacional
```

Fontes:

- [`../25-requirements-traceability.md`](../25-requirements-traceability.md);
- [`../46-operational-intelligence-requirements.md`](../46-operational-intelligence-requirements.md).

Gates adicionais: [`../45-operational-intelligence-testing-gates.md`](../45-operational-intelligence-testing-gates.md).

## 12. Template de evento

```text
DATE:
STEP:
OPERATIONAL_STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
CP_REQUIREMENTS:
EVIDENCE:
TESTS:
COMPLETE_GATE:
NEXT_UNLOCKED:
NOTES:
```

Para expertise/migração:

```text
EXPERTISE_PACKS_TOUCHED:
PLAYBOOKS_TOUCHED:
LEGACY_AGENT_CONSUMERS_FOUND:
MIGRATION_CLASSIFICATION:
RESIDUAL_AGENT_ROUTING:
```

Para inteligência operacional:

```text
REUSED_COMPONENTS:
NEW_COMPONENTS_JUSTIFIED:
DATA_AUTHORITIES:
ENTITY_RELATIONS:
EVENT_SOURCES:
PROVENANCE:
IDEMPOTENCY:
RELOAD_RESUME:
```

## 13. Estados permitidos

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

## 14. COMPLETE_GATE

Bloqueantes materiais:

```text
PARTIAL
INCONCLUSIVE
PENDING
LEGACY_FALLBACK
SHADOW_ONLY sem exit criteria
TODO/FIXME/HACK/TEMPORARY
TEST_NOT_RUN
STALE_EVIDENCE
SOFT_AGENT_HANDOFF_RESIDUAL
AGENT_REQUIRED_TOOL_GATE
UNKNOWN_AGENT_CONSUMER
UNFILTERED_GRAPH_TRAVERSAL
MATERIAL_CLAIM_WITHOUT_PROVENANCE
CASE_ROOM_PERMISSION_LEAK
WATCH_ACT_WITHOUT_POLICY
DUPLICATE_WRITE_AFTER_RESUME
STALE_APPROVAL
NON_REPRODUCIBLE_SIMULATION
AUTO_PUBLISHED_EXPERIENCE
MODEL_ROUTER_WITHOUT_BASELINE
```

## 15. Próxima ação

O Cursor deve ler `23-prompt-cursor-execucao.md` e iniciar **C0.S0**. A existência dos planos O0–O13 não libera sua execução antes das dependências do plano C0–C7.