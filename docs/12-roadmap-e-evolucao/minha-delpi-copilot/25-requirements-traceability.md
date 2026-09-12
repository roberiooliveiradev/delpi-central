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
| CP-061 | Descobrir/abrir app iframe `PORTAL_ONLY` | Portal/CopilotBridge | C1.S1–S3 | authorized iframe navigation | PLANNED |
| CP-062 | Handshake seguro Portal ↔ iframe | Portal/IframeBridge | C0.S1–C1.S7 | origin/source/schema/protocol | PLANNED |
| CP-063 | Publicar Workspace Context a partir de iframe | IframeBridge + iframe adapter | C2.S3/C2.S8 | context normalization/security | PLANNED |
| CP-064 | Executar comando visual genérico em iframe | Portal/IframeBridge | C2.S8 | declared capability + observation | PLANNED |
| CP-065 | Classificar iframe `PORTAL_ONLY/CONTEXTUAL/INTERACTIVE/AI_READY` | readiness tooling | C0/C3.S7/C5.S3 | evidence-based classification | PLANNED |
| CP-066 | SDK/helper de Iframe Copilot Bridge | shared/Portal | C5.S2 | contract + lifecycle tests | LOCKED |
| CP-067 | Unknown iframe onboarding sem hardcode | Portal/IframeBridge | C5 | generalization test | LOCKED |
| CP-068 | Proibir Business Action por DOM/click em iframe | Portal/AI/policy | C3 + transversal | architecture/security negative | PLANNED |
| CP-069 | SSO iframe sem token via bridge | Portal/app owner/security | C0/C5 | auth architecture review | TO_INVENTORY |
| CP-070 | Observabilidade de sessão/comandos do iframe bridge | Portal/Observability | C1/C2/C7 | trace correlation/redaction | PLANNED |
| CP-071 | Copilot único sem seleção obrigatória de agente | AI API + Chat MFE | C0/C2/C3/C7 | session without agent + UX cutover | PLANNED |
| CP-072 | Expertise Pack versionado | AI API | C0.S1 + E1/E2 | schema/version/owner | PLANNED |
| CP-073 | Recuperação semântica de expertise | AI API | C2/C3 + E3/E4 | positive/sibling/negative | LOCKED |
| CP-074 | Composição de múltiplas expertises no mesmo turno | AI planner | C3/C4 | cross-domain composition | LOCKED |
| CP-075 | Domain Playbook versionado | AI API/domain owners | C0/C3/C4 | schema/applicability/evidence | PLANNED |
| CP-076 | Playbook → WorkflowPlan sem endpoint hardcoded | AI planner | C4 | no technical authority duplication | LOCKED |
| CP-077 | Expertise não concede RBAC/permissão | Policy/Core/AI | transversal | unauthorized capability/knowledge | PLANNED |
| CP-078 | Multimodalidade independente de agente ativo | AI document vision | C2/C3 | attachment + no-agent test | REVALIDATE |
| CP-079 | Análise de desenho com provenance/confidence | AI multimodal + Engineering | C3/C4 | multimodal evals | LOCKED |
| CP-080 | Migrar presets de `AgentSpecializationService` | AI API | C3/C5 + E7 | migration matrix + parity | TO_INVENTORY |
| CP-081 | Remover gate `userActivatedAgent` para tools operacionais | AI API/policy | C3 + E5 | unauthorized + session-no-agent | BLOCKED_BY_AI_GATE |
| CP-082 | Remover `soft agent handoff` e substituir por retrieval/replan | AI API + Chat MFE | C3 + E6 | no-handoff + recovery behavior | LOCKED |
| CP-083 | Projetos configuram preferred expertise sem criar outro runtime | AI API/projects | C2/C5 + E11 | project context + permission negative | TO_INVENTORY |
| CP-084 | Administração/observabilidade de packs e playbooks | AI admin/observability | C5/C7 + E12 | version/eval/usage/audit | LOCKED |
| CP-085 | Deprecar/remover roteamento legado por `agent_id` após migração | AI API + Chat MFE | C7 + E13 | residual agent-routing zero | LOCKED |
| CP-086 | Unknown/new Expertise Pack entra sem patch no planner central | AI API | C5/C7 | unknown-pack generalization | LOCKED |
| CP-087 | Metamorphic rename de Expertise Pack preserva comportamento semântico | AI evals | C5/C7 | expertise metamorphic gate | LOCKED |
| CP-088 | Prompt injection em PDF/imagem não altera policy | AI multimodal/policy | transversal | multimodal injection negative | PLANNED |
| CP-089 | Packs de referência Qualidade + Engenharia | AI/domain owners | C3/C4 | drawing + root-cause + cross-domain eval | LOCKED |

## 2. Regras de atualização

- toda funcionalidade nova adicionada à especificação deve receber um `CP-*`;
- nenhum `CP-*` pode virar `PASS` sem evidence no ledger;
- `BLOCKED_BY_AI_GATE` só muda quando a dependência OpenAPI-first aplicável tiver evidence atual;
- se uma funcionalidade for removida do produto, registrar decisão/justificativa; não apagar silenciosamente;
- requisito de iframe só é `OUT_OF_SCOPE_WITH_DECISION` quando o release/app realmente não utiliza iframe; a existência de iframe no escopo exige classificação/evidence;
- requisito de expertise não pode ser fechado por documentação apenas: precisa de wiring/runtime/eval do candidate correspondente;
- compatibilidade legada com agents deve possuir exit criteria; `LEGACY_FALLBACK` material impede conclusão do cutover.

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

## 5. Coverage específico de iframe

Quando houver apps iframe no release, o verify final deve ainda apresentar:

```text
TOTAL_IFRAME_APPS
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
NOT_INVENTORIED
SECURITY_GATE_FAIL
```

`NOT_INVENTORIED` deve ser zero para apps iframe no escopo do release.

## 6. Coverage específico de expertise/migração

No verify final da migração para Copilot único:

```text
EXPERTISE_PACKS_ACTIVE
PLAYBOOKS_ACTIVE
PACKS_WITHOUT_OWNER
PACKS_WITHOUT_EVAL
CROSS_DOMAIN_EVAL_PASS
SESSION_WITHOUT_AGENT_PASS
UNAUTHORIZED_CAPABILITY_PASS
UNAUTHORIZED_KNOWLEDGE_PASS
SOFT_HANDOFF_RESIDUALS
AGENT_ROUTING_RESIDUALS
LEGACY_COMPAT_WITH_EXIT_CRITERIA
MULTIMODAL_EXPERTISE_PASS
UNKNOWN_PACK_GENERALIZATION_PASS
```

Critérios finais:

```text
PACKS_WITHOUT_OWNER = 0
PACKS_WITHOUT_EVAL = 0 para packs no release
SOFT_HANDOFF_RESIDUALS = 0
AGENT_ROUTING_RESIDUALS = 0 material
LEGACY_COMPAT_WITH_EXIT_CRITERIA = 0 no cutover final
```
