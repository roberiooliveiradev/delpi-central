# Minha DELPI Copilot — Matriz Canônica de Rastreabilidade

**Objetivo:** garantir que toda funcionalidade e requisito arquitetural possua owner, fase canônica, gate e status.  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Arquitetura/patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Testes:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)

> Este documento é a authority de requisitos `CP-*`. O arquivo `46-operational-intelligence-requirements.md` passa a ser apenas referência histórica/temática; requisitos CP-090–CP-129 estão consolidados aqui.

## 1. Status permitidos

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

## 2. C0 — Fundação/contratos/arquitetura

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-051 | Observabilidade/correlação de capability | AI/Portal/Observability | C0 contracts/traces | PLANNED |
| CP-055 | Segurança prompt/tool/context injection | AI/Policy | C0 safety semantics + transversal | PLANNED |
| CP-056 | Secret redaction | todos os owners | C0 redaction contract | PLANNED |
| CP-057 | Idempotency de writes | Domain API + orchestration | C0 semantics; runtime C4/C5 | PLANNED |
| CP-072 | Expertise Pack versionado | AI API | C0 primitive/schema | PLANNED |
| CP-075 | Domain Playbook versionado | AI/domain owners | C0 primitive/schema | PLANNED |
| CP-077 | Expertise não concede RBAC/permissão | Core/Policy/AI | C0 invariant | PLANNED |
| CP-088 | Injection em PDF/imagem não altera policy | AI multimodal/Policy | C0 safety + C2 eval | PLANNED |
| CP-091 | EntityRef cross-domain canônico | shared/domain owners | C0 primitive | PLANNED |
| CP-092 | RelationshipRef com provenance | domain owners/Graph | C0 primitive | PLANNED |
| CP-093 | EvidenceRef transversal | AI/Presentation | C0 primitive | PLANNED |
| CP-094 | Epistemic classes FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION | AI synthesis | C0 semantics | PLANNED |
| CP-095 | Evidence multimodal por página/região | Multimodal | C0 contract; runtime C2 | PLANNED |
| CP-105 | Durable Workflow persistence/checkpoint contract | Workflow runtime | C0 lifecycle; runtime C5 | PLANNED |
| CP-106 | `wait_user` semantics | Workflow runtime | C0 lifecycle; runtime C5 | PLANNED |
| CP-107 | `wait_approval` semantics | Workflow/Policy | C0 lifecycle; runtime C5 | PLANNED |
| CP-108 | `wait_event` semantics | Workflow/Event | C0 lifecycle; runtime C5 | PLANNED |
| CP-109 | No duplicate write after resume | Workflow/Executor | C0 idempotency; runtime C5 | PLANNED |
| CP-110 | Decision Gate proporcional a risco | Policy | C0 contract; runtime C4 | PLANNED |
| CP-111 | Approval workflow humano | Policy/Workflow | C0 contract; runtime C4/C5 | PLANNED |
| CP-123 | Provider data-policy filtering | AI/Security | C0 policy contract; runtime C7 | PLANNED |
| CP-130 | Architecture style canônico: Clean Architecture + Ports & Adapters + DDD pragmático | Platform Architecture | C0 architecture freeze | PLANNED |
| CP-131 | Layer responsibilities e dependency direction canônicas | Platform Architecture | dependency conformance | PLANNED |
| CP-132 | DI/Composition Root e external dependencies atrás de adapters/ports quando boundary justificar | Platform Architecture + owners | wiring/conformance | PLANNED |
| CP-133 | Pattern Decision Matrix canônica para Repository/Use Case/State Machine/Policy/Adapter/Event/etc. | Platform Architecture | pattern matrix review | PLANNED |
| CP-134 | Abstraction Gate para interface/port/repository/factory/strategy/registry/base class | Platform Architecture | no unjustified abstraction | PLANNED |
| CP-135 | Error/Result model transversal e tradução de erros de infraestrutura | Application/Interfaces | error contract/conformance | PLANNED |
| CP-136 | Event model + EventEnvelope + Outbox/Idempotency/Resilience rules sem event bus paralelo | Platform/Workflow | event/resilience conformance | PLANNED |
| CP-137 | State Machine pattern para lifecycles não triviais | Work/Policy/Domain owners | transition tests | PLANNED |
| CP-138 | Frontend state ownership: server/workspace/conversation/local vs durable backend state | Portal/Chat/MFEs | frontend architecture conformance | PLANNED |
| CP-139 | Migração legada via Adapter + Anti-Corruption Layer + Strangler + exit criteria quando aplicável | AI/Platform | migration/residual gate | PLANNED |
| CP-140 | Architectural conformance + exception/ADR process obrigatório | Platform Architecture | architecture gate/ADR | PLANNED |

## 3. C1 — Portal, navegação e Workspace Context

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-001 | Chat global no Portal | Chat MFE + Portal | surface/UX | PLANNED |
| CP-002 | Abrir app | Portal/CopilotBridge | authorized navigation | PLANNED |
| CP-003 | Abrir rota | Portal/CopilotBridge | authorized navigation | PLANNED |
| CP-004 | Abrir entidade | Portal + app contract | EntityRef/deep-link | PLANNED |
| CP-005 | Voltar/navegar histórico | Portal | router behavior | PLANNED |
| CP-006 | Selecionar aba/focar view | Portal/MFE/Iframe | typed view command | PLANNED |
| CP-007 | Aplicar filtro visual | MFE/Iframe + Portal | Workspace/view contract | PLANNED |
| CP-008 | Contexto do app atual | Portal | WorkspaceContext | PLANNED |
| CP-009 | Contexto de entidade | MFE/Iframe | EntityRef | PLANNED |
| CP-010 | Contexto de filtros/período | MFE/Iframe | stale/security | PLANNED |
| CP-011 | Context chips | Chat MFE | UX/relevance | PLANNED |
| CP-012 | “Explique o que estou vendo” | AI + Context | grounding/R6/R9 | PLANNED |
| CP-025 | Deep link após execução | Portal/MFE | result navigation | PLANNED |
| CP-053 | Send/stream parity | AI/Chat | R7 | PLANNED |
| CP-059 | Capability projection platform | Portal/AI | `/me/apps` authority | PLANNED |
| CP-061 | Descobrir/abrir iframe `PORTAL_ONLY` | Portal/CopilotBridge | authorized navigation | PLANNED |
| CP-062 | Handshake seguro Portal↔iframe | Portal/IframeBridge | origin/source/schema/protocol | PLANNED |
| CP-063 | Workspace Context a partir de iframe | IframeBridge | normalization/security | PLANNED |
| CP-064 | Comando visual genérico em iframe | Portal/IframeBridge | declared capability/result | PLANNED |
| CP-065 | Classificar iframe I0–I3 | Readiness | evidence classification | PLANNED |
| CP-068 | Proibir Business Action por DOM/click | Portal/AI/Policy | architecture negative | PLANNED |
| CP-069 | SSO iframe sem token via bridge | Portal/App/Security | auth architecture | TO_INVENTORY |
| CP-070 | Observabilidade do iframe bridge | Portal/Observability | trace/redaction | PLANNED |

## 4. C2 — Intelligence Core

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-026 | RAG de procedimentos/documentos | AI/Knowledge | grounding/security | REVALIDATE |
| CP-028 | Redigir e-mail/texto | AI capability | faithfulness | REVALIDATE |
| CP-071 | Copilot único sem seleção obrigatória de agente | AI API + Chat | session-without-agent | PLANNED |
| CP-073 | Recuperação semântica de expertise | AI API | positive/sibling/negative | LOCKED |
| CP-074 | Composição de múltiplas expertises | AI planner | cross-domain composition | LOCKED |
| CP-078 | Multimodalidade independente de agente ativo | AI multimodal | no-agent attachment eval | REVALIDATE |
| CP-079 | Análise de desenho com provenance/confidence | AI + Engineering | multimodal eval | LOCKED |
| CP-083 | Projects com preferred expertise sem outro runtime | AI projects | project context + permission negative | TO_INVENTORY |
| CP-086 | Unknown Expertise Pack sem planner patch | AI | generalization | LOCKED |
| CP-087 | Metamorphic rename de Expertise Pack | AI evals | semantic equivalence | LOCKED |
| CP-089 | Packs referência Qualidade + Engenharia | AI/domain owners | drawing/root-cause/cross-domain | LOCKED |

## 5. C3 — Business Reads + Business Graph

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-013 | Consultar Business Action | AI/Action Catalog | R1/R2/R3/R9 | BLOCKED_BY_AI_GATE |
| CP-014 | Consultar múltiplas APIs | AI planner | multi-provider | BLOCKED_BY_AI_GATE |
| CP-015 | Analisar/comparar dados | AI synthesis | grounded outcome | BLOCKED_BY_AI_GATE |
| CP-027 | Gerar resumo/relatório grounded | AI/artifact | evidence/faithfulness | PLANNED |
| CP-029 | Recomendar próximos passos | AI synthesis | contextual/allowed | BLOCKED_BY_AI_GATE |
| CP-043 | Unknown OpenAPI provider | AI | full-chain unknown | BLOCKED_BY_AI_GATE |
| CP-044 | Metamorphic provider/path/opId | AI | metamorphic gate | BLOCKED_BY_AI_GATE |
| CP-058 | Capability projection business | AI | no duplicate catalog | LOCKED |
| CP-090 | DELPI Business Graph mínimo | AI/Platform + domain owners | permission-aware traversal | LOCKED |
| CP-128 | Business Graph sibling onboarding | Graph | no planner hardcode | LOCKED |

## 6. C4 — Governed Writes + Decision Gates

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-016 | Criar registro | Domain API + AI executor | Decision Gate/RBAC/outcome | BLOCKED_BY_AI_GATE |
| CP-017 | Editar registro | Domain API + AI executor | write parity | BLOCKED_BY_AI_GATE |
| CP-018 | Aprovar/rejeitar | Domain API/Policy | approval/safety | BLOCKED_BY_AI_GATE |
| CP-019 | Cancelar/arquivar | Domain API/Policy | destructive gate | BLOCKED_BY_AI_GATE |
| CP-020 | Adicionar comentário | Domain API | write parity | BLOCKED_BY_AI_GATE |
| CP-021 | Atribuir responsável | Domain API | permission/gate | BLOCKED_BY_AI_GATE |
| CP-022 | Preview de write | AI + Chat | argsHash/impact UX | PLANNED |
| CP-023 | Decision/confirmation UI | AI + Chat | R10 | PLANNED |
| CP-024 | Revalidar após decisão | Policy/Executor | TOCTOU/RBAC | PLANNED |
| CP-045 | Autonomia L0–L2 | Policy | safe execution | PLANNED |
| CP-054 | Simulate/admin preview de action | AI admin | surface parity | PLANNED |
| CP-080 | Migrar presets de AgentSpecializationService | AI | migration parity | TO_INVENTORY |
| CP-081 | Remover gate `userActivatedAgent` para tools operacionais | AI/Policy | unauthorized + no-agent | BLOCKED_BY_AI_GATE |
| CP-082 | Remover soft agent handoff | AI + Chat | replan/clarify | LOCKED |

## 7. C5 — Durable Work

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-030 | Plano operacional visível | AI + Chat | no CoT/activity | PLANNED |
| CP-031 | Workflow multi-app | Orchestrator | compound outcome | LOCKED |
| CP-032 | Parallel reads | Orchestrator | safety/efficiency | LOCKED |
| CP-033 | Dependências entre steps | Orchestrator | DAG correctness | LOCKED |
| CP-034 | Partial failure | Orchestrator | truthful outcome | LOCKED |
| CP-035 | Retry seguro | Orchestrator | idempotency | LOCKED |
| CP-036 | Pause por decisão | Workflow/Decision | persistence/R10 | LOCKED |
| CP-037 | Reload/resume | Persistence | no duplicate write | LOCKED |
| CP-038 | Audit trail de workflow | Observability | coverage | LOCKED |
| CP-076 | Playbook→WorkflowPlan sem endpoint hardcoded | Planner | authority separation | LOCKED |
| CP-096 | Copilot Task persistente | Workflow/Product | restart/resume | LOCKED |
| CP-097 | Copilot Case | Product/Workflow | lifecycle/evidence | LOCKED |
| CP-098 | Evidence Board | Case/AI | same EvidenceRef + status | LOCKED |
| CP-099 | Interaction Room ligada a Case | Portal/Room | RBAC/context | TO_INVENTORY |
| CP-100 | Copilot Inbox | Portal/Workflow | pending/result lifecycle | LOCKED |
| CP-124 | Task Completion por Task/Case | Observability | metric validity | LOCKED |
| CP-126 | Inbox decision→workflow resume | Portal/Workflow | correlation/revalidation | LOCKED |
| CP-127 | Room summary grounded em Case | AI/Room | evidence/RBAC | TO_INVENTORY |

## 8. C6 — Proatividade + AI-ready + Learning

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-039 | AI-ready SDK/templates | Shared/Portal | contract tests | LOCKED |
| CP-040 | Readiness scanner | Tooling | factual inventory | PLANNED |
| CP-041 | Coverage dashboard | Admin/Observability | metrics | LOCKED |
| CP-042 | Unknown app onboarding | Core/Portal/AI | no core hardcode | LOCKED |
| CP-060 | Administração de capabilities/coverage | Admin | admin RBAC | LOCKED |
| CP-066 | SDK de Iframe Copilot Bridge | Shared/Portal | contract/lifecycle | LOCKED |
| CP-067 | Unknown iframe onboarding | Portal/IframeBridge | generalization | LOCKED |
| CP-084 | Admin/observability de packs/playbooks | AI admin | version/eval/audit | LOCKED |
| CP-101 | Watch por condição/evento | Workflow/Events | event/dedupe/RBAC | LOCKED |
| CP-102 | Watch OBSERVE | Workflow | audit-only | LOCKED |
| CP-103 | Watch ADVISE | Workflow/AI | grounded alert | LOCKED |
| CP-114 | Reference Knowledge lifecycle | Knowledge | owner/version/scope | REVALIDATE |
| CP-115 | Decision Knowledge | Case/Knowledge | provenance/no-CoT | LOCKED |
| CP-116 | Experience Knowledge | Case/Knowledge | governed promotion | LOCKED |
| CP-117 | Solution Pattern lifecycle | Knowledge/Expertise | review/eval/version | LOCKED |
| CP-118 | Governed Learning Loop | AI admin | no auto-publish | LOCKED |
| CP-119 | Expertise Studio lifecycle | AI admin | draft→publish gates | LOCKED |
| CP-120 | Expertise/Playbook rollback | AI admin | version/eval | LOCKED |
| CP-125 | Case resolution learning candidate | Case/Knowledge | candidate only | LOCKED |

## 9. C7 — Optimization/Autonomy/Rollout

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-046 | Autonomia L3 prepare | Policy/AI | no persistence | LOCKED |
| CP-047 | Autonomia L4 governed write | Policy/AI | Decision Gate | LOCKED |
| CP-048 | Autonomia L5 limitada | Policy/Admin | allowlist/limits/kill switch | LOCKED |
| CP-049 | Emergency stop | Admin/Policy | kill switch | LOCKED |
| CP-050 | Rollout/cohort controls | Platform/Admin | canary/rollback | LOCKED |
| CP-052 | TCR/First Plan Success metrics | Observability | metric validity | LOCKED |
| CP-085 | Remover routing legado por `agent_id` | AI + Chat | residual zero | LOCKED |
| CP-104 | Watch ACT | Policy/Workflow | L5/Decision Gate | LOCKED |
| CP-112 | What-if Simulation | Domain analytics | reproducible model | LOCKED |
| CP-113 | Simulate→Apply separado | Domain API/Policy | new gate | LOCKED |
| CP-121 | Model Router | AI infrastructure | quality/cost/latency | LOCKED |
| CP-122 | Compute Policy | AI/Policy | provider/model constraints | LOCKED |
| CP-129 | Anchor reclamação→8D→Watch→ação | Cross-domain | full integration | LOCKED |

## 10. Regras de atualização

- requisito novo recebe novo `CP-*`; nunca reutilizar ID;
- nenhum CP vira PASS por documentação apenas;
- `BLOCKED_BY_AI_GATE` muda somente com evidence vigente dos gates externos;
- requisitos de contrato/arquitetura em C0 podem ser PASS sem runtime completo, desde que o gate seja de schema/ownership/conformance e isso esteja explícito;
- runtime requirement só passa com wiring + integration/eval;
- `TO_INVENTORY` não vira PLANNED por suposição;
- requisito removido recebe `OUT_OF_SCOPE_WITH_DECISION` ou decisão de deprecação; não apagar silenciosamente;
- `LEGACY_FALLBACK` precisa exit criteria;
- phase canonical é C0–C7 do Plano Mestre; tags antigas E*/O* são somente referência histórica;
- requisito de design pattern não autoriza criar a abstração: o Abstraction Gate continua obrigatório.

## 11. Coverage final

Gerar por release:

```text
TOTAL_REQUIREMENTS
PASS
LOCKED/BLOCKED
FAIL
OUT_OF_SCOPE_WITH_DECISION
UNMAPPED
```

E por família:

```text
FOUNDATION
ARCHITECTURE_PATTERNS
PLATFORM_CONTEXT
INTELLIGENCE
BUSINESS_READS_GRAPH
GOVERNED_WRITES
DURABLE_WORK
PROACTIVITY_ECOSYSTEM
OPTIMIZATION_AUTONOMY
IFRAME
EXPERTISE
EVIDENCE
```

`UNMAPPED = 0` para qualquer release declarado completo.