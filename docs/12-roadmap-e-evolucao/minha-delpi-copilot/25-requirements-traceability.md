# Minha DELPI Copilot — Matriz de Rastreabilidade Funcional

**Objetivo:** garantir que nenhuma funcionalidade descrita no produto fique sem owner, fase de implantação ou gate de aceite.

## 1. Matriz principal

| ID | Funcionalidade | Owner principal | Implantação | Gate principal | Status inicial |
|---|---|---|---|---|---|
| CP-001 | Chat global no Portal | Chat MFE + Portal | C1/C2 | surfaces + UX | PLANNED |
| CP-002 | Abrir app | Portal/CopilotBridge | C1.S1–S3 | authorized navigation | PLANNED |
| CP-003 | Abrir rota | Portal/CopilotBridge | C1.S1–S3 | authorized navigation | PLANNED |
| CP-004 | Abrir entidade | Portal + MFE contract | C1/C2/C3 | deep-link contract | PLANNED |
| CP-005 | Voltar/navegar histórico | Portal | C1 posterior | router behavior | PLANNED |
| CP-006 | Selecionar aba/focar view | Portal/MFE | C2/C5 | typed view command | PLANNED |
| CP-007 | Aplicar filtro visual | MFE + Portal | C2 | WorkspaceContext/view contract | PLANNED |
| CP-008 | Contexto do app atual | Portal | C2.S1–S2 | context contract | PLANNED |
| CP-009 | Contexto de entidade | MFE | C2.S3–S5 | entity refs | PLANNED |
| CP-010 | Contexto de filtros/período | MFE | C2.S3–S5 | stale/security tests | PLANNED |
| CP-011 | Context chips | Chat MFE | C2 | UX/relevance | PLANNED |
| CP-012 | “Explique o que estou vendo” | AI API + context | C2.S6 | grounding/R6/R9 | PLANNED |
| CP-013 | Consultar Business Action | AI API/Action Catalog | C3.S1–S3 | R1/R2/R3/R9 | BLOCKED_BY_AI_GATE |
| CP-014 | Consultar múltiplas APIs | AI planner | C3/C4 | multi-provider | BLOCKED_BY_AI_GATE |
| CP-015 | Analisar/comparar dados | AI synthesis | C3/C4 | grounded outcome | BLOCKED_BY_AI_GATE |
| CP-016 | Criar registro | domain API + AI executor | C3.S4–S5 | write/policy/confirmation | BLOCKED_BY_AI_GATE |
| CP-017 | Editar registro | domain API + AI executor | C3/C5 | write parity | BLOCKED_BY_AI_GATE |
| CP-018 | Aprovar/rejeitar | domain API/policy | C3/C6 | strong confirmation/safety | BLOCKED_BY_AI_GATE |
| CP-019 | Cancelar/arquivar | domain API/policy | C3/C6 | destructive policy | BLOCKED_BY_AI_GATE |
| CP-020 | Adicionar comentário/observação | domain API | C3 | write parity | BLOCKED_BY_AI_GATE |
| CP-021 | Atribuir responsável | domain API | C3 | permission + confirmation | BLOCKED_BY_AI_GATE |
| CP-022 | Preview de write | AI API + Chat MFE | C3.S4 | argsHash/UX | PLANNED |
| CP-023 | Confirmation card | AI API + Chat MFE | C3.S4 | R10 | PLANNED |
| CP-024 | Revalidar após confirmação | AI policy/executor | C3.S5 | TOCTOU/RBAC | PLANNED |
| CP-025 | Deep link após execução | Portal/MFE | C3.S6 | result navigation | PLANNED |
| CP-026 | RAG de procedimentos/documentos | AI API | existente + C2/C4 | grounding/security | REVALIDATE |
| CP-027 | Gerar resumo/relatório | AI/artifact capability | C3/C4 | grounded artifact | PLANNED |
| CP-028 | Redigir e-mail/texto | AI capability | existente/evoluir | faithfulness | REVALIDATE |
| CP-029 | Recomendar próximos passos | AI synthesis | C3/C4 | contextual/allowed | BLOCKED_BY_AI_GATE |
| CP-030 | Plano operacional visível | AI + Chat MFE | C4.S1/S4 | no CoT + activity | PLANNED |
| CP-031 | Workflow multi-app | AI orchestrator | C4 | compound outcome | LOCKED |
| CP-032 | Parallel reads | AI orchestrator | C4.S2/S5 | safety/efficiency | LOCKED |
| CP-033 | Dependências entre steps | AI orchestrator | C4 | DAG correctness | LOCKED |
| CP-034 | Partial failure | AI orchestrator | C4.S3 | truthful result | LOCKED |
| CP-035 | Retry seguro | AI orchestrator | C4.S3 | idempotency | LOCKED |
| CP-036 | Pause por confirmação | workflow + confirmation | C4.S6 | persistence/R10 | LOCKED |
| CP-037 | Reload/resume | AI persistence | C4.S7 | no duplicate write | LOCKED |
| CP-038 | Audit trail do workflow | observability | C4 | audit coverage | LOCKED |
| CP-039 | Plugin AI-ready SDK | shared/Portal | C5.S2 | contract tests | LOCKED |
| CP-040 | Readiness scanner | tooling | C3.S7/C5.S3 | factual inventory | PLANNED |
| CP-041 | Coverage dashboard | admin/observability | C5.S6 | metrics | LOCKED |
| CP-042 | Unknown app onboarding | Core/Portal/AI | C5 | no core hardcode | LOCKED |
| CP-043 | Unknown OpenAPI provider | AI API | C3 | full-chain unknown test | BLOCKED_BY_AI_GATE |
| CP-044 | Metamorphic provider/path/opId | AI API | C3 | metamorphic gate | BLOCKED_BY_AI_GATE |
| CP-045 | Autonomia L0–L2 | policy | C1–C3 | safe execution | PLANNED |
| CP-046 | Autonomia L3 prepare | policy/AI | C6.S2 | no persistence | LOCKED |
| CP-047 | Autonomia L4 confirm | policy/AI | C6.S3 | confirmation | LOCKED |
| CP-048 | Autonomia L5 limitada | policy/admin | C6.S4 | allowlist/limits/kill switch | LOCKED |
| CP-049 | Emergency stop | admin/policy | C6.S5 | kill-switch test | LOCKED |
| CP-050 | Rollout/cohort controls | platform/admin | C7 | canary/rollback | LOCKED |
| CP-051 | Observabilidade de capability | AI/Portal | C0+ transversal | traces | PLANNED |
| CP-052 | Métricas TCR/First Plan Success | observability | C4/C7 | metrics validity | LOCKED |
| CP-053 | Send/stream parity | AI/Chat | C1+ transversal | R7 | PLANNED |
| CP-054 | Simulate/admin preview | AI admin | C3/C6 | surface parity | PLANNED |
| CP-055 | Segurança prompt/tool/context injection | AI/policy | transversal | R10 | PLANNED |
| CP-056 | Secret redaction | all layers | transversal | security tests | PLANNED |
| CP-057 | Idempotency de writes | domain API + orchestrator | C3/C4 | replay tests | PLANNED |
| CP-058 | Capability projection business | AI | C3.S1 | no duplicate catalog | LOCKED |
| CP-059 | Capability projection platform | Portal/AI | C1.S1 | `/me/apps` authority | PLANNED |
| CP-060 | Administração de capabilities/coverage | admin | C5/C6 | RBAC admin | LOCKED |

## 2. Regras de atualização

- toda funcionalidade nova adicionada à especificação deve receber um `CP-*`;
- nenhum `CP-*` pode virar `PASS` sem evidence no ledger;
- `BLOCKED_BY_AI_GATE` só muda quando a dependência OpenAPI-first aplicável tiver evidence atual;
- se uma funcionalidade for removida do produto, registrar decisão/justificativa; não apagar silenciosamente.

## 3. Status permitidos

```text
PLANNED
REVALIDATE
TO_INVENTORY
BLOCKED_BY_AI_GATE
LOCKED
IN_PROGRESS
BLOCKED_WITH_EVIDENCE
FAIL
PASS
OUT_OF_SCOPE_WITH_DECISION
```

## 4. Coverage final

No verify final, gerar resumo:

```text
TOTAL_REQUIREMENTS
PASS
BLOCKED
FAIL
OUT_OF_SCOPE_WITH_DECISION
UNMAPPED
```

`UNMAPPED` deve ser zero. Requisito material `BLOCKED` ou `FAIL` impede declarar a aplicação completa se pertencer ao escopo do release final.