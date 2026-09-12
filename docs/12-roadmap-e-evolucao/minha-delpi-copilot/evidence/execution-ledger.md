# Minha DELPI Copilot — Execution Ledger

**Status do programa:** `PLANNED / NOT_STARTED`  
**Plano ativo:** [`../16-execution-master-plan.md`](../16-execution-master-plan.md)  
**Protocolo:** [`../22-cursor-execution-protocol.md`](../22-cursor-execution-protocol.md)  
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
| C4 Agentic Workflows | LOCKED | — | C3 |
| C5 Ecossistema AI-ready | LOCKED | — | C3/C4 foundation |
| C6 Autonomia governada | LOCKED | — | C4/C5 + safety gates |
| C7 Rollout final | LOCKED | — | C0–C6 required gates |

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

A arquitetura de produto passa a adotar:

```text
SINGLE_COPILOT_IDENTITY = TARGET
DEPARTMENT_AGENT_ROUTING = TO_MIGRATE
EXPERTISE_PACKS = PLANNED
DOMAIN_PLAYBOOKS = PLANNED
MULTIMODAL_EXPERTISE = REUSE_EXISTING_RUNTIME
SOFT_AGENT_HANDOFF = TO_DEPRECATE
AGENT_REQUIRED_OPERATIONAL_TOOLS = TO_MIGRATE
```

Fonte canônica:

- [`../27-single-copilot-specialization-architecture.md`](../27-single-copilot-specialization-architecture.md);
- [`../28-expertise-pack-specification.md`](../28-expertise-pack-specification.md);
- [`../29-domain-playbooks-specification.md`](../29-domain-playbooks-specification.md);
- [`../30-multimodal-expertise-and-drawing-analysis.md`](../30-multimodal-expertise-and-drawing-analysis.md);
- [`../31-agent-to-expertise-migration-plan.md`](../31-agent-to-expertise-migration-plan.md);
- [`../32-expertise-runtime-implementation-plan.md`](../32-expertise-runtime-implementation-plan.md);
- [`../33-reference-expertise-packs-quality-engineering.md`](../33-reference-expertise-packs-quality-engineering.md).

Essa decisão **não altera a próxima etapa**: continua sendo C0.S0. Nenhum runtime deve ser alterado com base apenas na documentação antes do inventário real de consumers, persistência, UI, sessions, projects e admin de agents/skills.

## 5. Registro de execução

| Data | HEAD | Etapa | Evento | Status/evidence |
|---|---|---|---|---|
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | Planejamento | documentação arquitetural/funcional e plano executável criados | PLAN_ONLY |
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | Planejamento | integração de apps iframe incorporada ao produto/plano: `Iframe Copilot Bridge`, classes `PORTAL_ONLY/CONTEXTUAL/INTERACTIVE/AI_READY`, contratos, segurança, testes e CP-061–CP-070 | PLAN_ONLY; sem runtime diff |
| 2026-09-12 | `TO_CAPTURE_AT_C0.S0` | Planejamento | decisão de **Copilot único** incorporada: Expertise Packs, Domain Playbooks, multimodalidade, migração de agent specialization/handoff/activation e CP-071–CP-089 | PLAN_ONLY; sem runtime diff; architecture target defined |

## 6. Escopo adicional obrigatório no C0.S0 — apps/iframe

O inventário deve cobrir explicitamente apps `iframe` e `external` e registrar, quando aplicável:

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

Fonte canônica: [`../26-iframe-copilot-bridge.md`](../26-iframe-copilot-bridge.md).

## 7. Escopo adicional obrigatório no C0.S0 — agents/skills/expertise

O inventário deve localizar producer/consumer e classificar pelo menos:

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
multimodal skills and their has_agent dependencies
```

Cada item deve receber uma classificação:

```text
KEEP
MIGRATE_TO_EXPERTISE
MIGRATE_TO_PROJECT_CONTEXT
MIGRATE_TO_CAPABILITY_POLICY
DEPRECATE
REMOVE
NOT_PROVEN
```

C0.S0 também deve registrar se existem consumers externos ou contratos públicos que impeçam remoção imediata.

## 8. Baseline arquitetural já observado para revalidar no C0.S0

Há evidência documental/código previamente observada de que:

- `AgentSpecializationService` contém presets por domínio com knowledge/guidelines/allowedTools;
- `ChatWorkspaceAgentActivationService.operational_tools_enabled()` depende de `userActivatedAgent && actionsEnabled`;
- `ChatSoftAgentHandoffService` oferece `switch_agent_and_resend`;
- `ChatSkillRegistry` contém skills úteis como document vision/drawing analysis/quality action plans e possui branches dependentes de `has_agent`;
- existe runtime de document vision/drawing analysis que deve ser preferencialmente reaproveitado.

Esses pontos são **findings para revalidar**, não autorização para editar antes do inventário completo.

## 9. Template de evento

```text
DATE:
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
EVIDENCE:
TESTS:
COMPLETE_GATE:
NEXT_UNLOCKED:
NOTES:
```

Para etapas de expertise/migração adicionar:

```text
EXPERTISE_PACKS_TOUCHED:
PLAYBOOKS_TOUCHED:
LEGACY_AGENT_CONSUMERS_FOUND:
MIGRATION_CLASSIFICATION:
EXPERTISE_SELECTION_EVIDENCE:
RESIDUAL_AGENT_ROUTING:
```

## 10. Estados permitidos

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

Evitar aliases vagos como “quase pronto”, “feito com ressalva” ou “100% salvo X”.

## 11. COMPLETE_GATE

Bloqueantes de PASS quando materiais ao step:

```text
PARTIAL
INCONCLUSIVE
PENDING
LEGACY_FALLBACK
SHADOW_ONLY sem exit criteria
TODO/FIXME/HACK/TEMPORARY
TEST_NOT_RUN
STALE_EVIDENCE
```

Para o cutover de Copilot único, também bloqueiam:

```text
SOFT_AGENT_HANDOFF_RESIDUAL material
AGENT_REQUIRED_TOOL_GATE material
UNMIGRATED_AGENT_SPECIALIZATION material
UNKNOWN_AGENT_CONSUMER
UNAUTHORIZED_KNOWLEDGE regression
UNAUTHORIZED_CAPABILITY regression
```

## 12. Primeiro comando de execução

O Cursor deve abrir [`../23-prompt-cursor-execucao.md`](../23-prompt-cursor-execucao.md), ler também [`../27-single-copilot-specialization-architecture.md`](../27-single-copilot-specialization-architecture.md) e [`../32-expertise-runtime-implementation-plan.md`](../32-expertise-runtime-implementation-plan.md), e iniciar **C0.S0**, sem runtime diff antes de concluir o inventário.
