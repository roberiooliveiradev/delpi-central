# Minha DELPI Copilot — Matriz Canônica de Rastreabilidade

**Objetivo:** garantir owner, fase, gate e status de cada requisito.  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Testes:** [`20-testing-and-acceptance-matrix.md`](./20-testing-and-acceptance-matrix.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

> Esta é a única authority `CP-*`. IDs históricos não são reutilizados nem apagados; requisitos ligados à migração do Minha DELPI Chat são preservados como `OUT_OF_SCOPE_WITH_DECISION`.

## 1. Status

```text
PLANNED
REVALIDATE
TO_INVENTORY
LOCKED
IN_PROGRESS
BLOCKED_WITH_EVIDENCE
FAIL
PASS
OUT_OF_SCOPE_WITH_DECISION
```

`BLOCKED_BY_AI_GATE` foi removido do Copilot: o runtime OpenAPI-first será construído nativamente na nova Copilot API e não depende do roadmap do Chat.

## 2. C0 — Platform + Architecture Foundation Freeze

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-051 | Correlação/observabilidade transversal | Copilot API/Portal/Observability | contracts/traces | PLANNED |
| CP-055 | Prompt/tool/context injection safety | Copilot Policy | security semantics | PLANNED |
| CP-056 | Secret redaction | todos os owners | redaction contract | PLANNED |
| CP-057 | Idempotency semantics de writes | Domain API + Copilot orchestration | C0 contract; runtime C5 | PLANNED |
| CP-072 | Expertise Pack versionado | Copilot API | primitive/schema | PLANNED |
| CP-075 | Domain Playbook versionado | Copilot API/domain owners | primitive/schema | PLANNED |
| CP-077 | Expertise não concede RBAC | Core/Copilot Policy | invariant | PLANNED |
| CP-088 | PDF/imagem não altera policy | Copilot Multimodal/Policy | safety contract; C3 eval | PLANNED |
| CP-091 | EntityRef cross-domain canônico | Copilot shared/domain owners | primitive | PLANNED |
| CP-092 | RelationshipRef com provenance | Graph/domain owners | primitive | PLANNED |
| CP-093 | EvidenceRef transversal | Copilot API | primitive | PLANNED |
| CP-094 | Epistemic classes canônicas | Copilot synthesis | semantics | PLANNED |
| CP-095 | Evidence multimodal page/region | Copilot Multimodal | contract; runtime C3 | PLANNED |
| CP-105 | Workflow persistence/checkpoint contract | Copilot Work Runtime | lifecycle contract | PLANNED |
| CP-106 | `wait_user` semantics | Copilot Work Runtime | lifecycle contract | PLANNED |
| CP-107 | `wait_approval` semantics | Copilot Work/Policy | lifecycle contract | PLANNED |
| CP-108 | `wait_event` semantics | Copilot Work/Event | lifecycle contract | PLANNED |
| CP-109 | No duplicate write after resume | Copilot Work/Executor | idempotency contract | PLANNED |
| CP-110 | Decision Gate proporcional a risco | Copilot Policy | contract | PLANNED |
| CP-111 | Approval workflow humano | Copilot Policy/Work | contract | PLANNED |
| CP-123 | Provider data-policy filtering | Copilot Security | policy contract | PLANNED |
| CP-130 | Clean Architecture + Ports & Adapters + DDD pragmático | Architecture | architecture freeze | PLANNED |
| CP-131 | Layer/dependency direction canônicas | Architecture | conformance | PLANNED |
| CP-132 | DI/Composition Root + adapters/ports | Architecture/owners | wiring conformance | PLANNED |
| CP-133 | Pattern Decision Matrix | Architecture | review | PLANNED |
| CP-134 | Abstraction Gate | Architecture | no unjustified abstraction | PLANNED |
| CP-135 | Error/Result model transversal | Application/Interfaces | contract/conformance | PLANNED |
| CP-136 | EventEnvelope + Outbox/Idempotency/Resilience rules | Platform/Work | conformance | PLANNED |
| CP-137 | State Machine para lifecycles não triviais | Domain/Policy/Work | transition tests | PLANNED |
| CP-138 | Frontend state ownership | Portal/Copilot MFE | frontend conformance | PLANNED |
| CP-139 | Adapter/ACL/Strangler para integrações legadas quando necessário | Architecture | migration gate | PLANNED |
| CP-140 | Architecture conformance + ADR process | Architecture | conformance/ADR | PLANNED |
| CP-146 | Zero dependência de runtime do Minha DELPI Chat | Copilot Platform | Chat-offline/scan | PLANNED |
| CP-147 | Persistência/migration chain próprias do Copilot | Copilot API | storage ownership | PLANNED |
| CP-154 | Inventário Portal/Core/Gateway/APIs/MFEs antes do runtime | Architecture | C0.S0 evidence | PLANNED |
| CP-157 | Media capture/consent/retention classes definidas antes do runtime multimodal contínuo | Copilot Security/Architecture | media/privacy foundation | PLANNED |
| CP-158 | Shared-device identity/session isolation | Copilot/Portal/Security | device session negative tests | PLANNED |
| CP-175 | Raw media minimization e retention class-specific | Copilot Media/Security | retention/data minimization | PLANNED |
| CP-176 | Sem facial recognition/emotion detection/hidden surveillance por default | Security/Governance | privacy negative gate | PLANNED |
| CP-178 | Arbitrary LLM→machine command proibido | Copilot/Industrial Safety | OT boundary gate | PLANNED |
| CP-179 | Future OT actuation exige safety gate separado | Industrial owner/Copilot | separate architecture/risk approval | PLANNED |

## 3. C1 — Standalone Application Bootstrap

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-141 | Copilot API standalone | `minha-delpi-copilot-api` | own service/health/tests | LOCKED |
| CP-142 | Copilot MFE standalone | `plugins/minha-delpi-copilot` | build/federation/tests | LOCKED |
| CP-143 | Manifesto próprio do Copilot | Copilot/Core | schema/registration | LOCKED |
| CP-144 | Gateway route própria API/MFE | Gateway | dev/prod parity | LOCKED |
| CP-145 | Compose/deploy próprios | Infra | independent service/start | LOCKED |
| CP-148 | Portal federated full-page mount | Portal/Copilot MFE | authorized mount/F5 | LOCKED |
| CP-149 | Global Copilot panel usando o mesmo MFE/runtime | Portal/Copilot MFE | surface parity | LOCKED |
| CP-150 | JWT + Core/RBAC integration | Copilot API/Core | auth negatives | LOCKED |
| CP-152 | Health + independent rollback/shutdown | Copilot/Infra | Chat-offline rollback | LOCKED |
| CP-153 | Reuso obrigatório de `@delpi/plugin-ui`/shared federation | Copilot MFE | federation/UI conformance | LOCKED |
| CP-155 | Entry point do Copilot amplamente disponibilizável conforme acesso/rollout | Portal/Core/Copilot MFE | access/visibility gate | LOCKED |

## 4. C2 — Portal Context + Platform Commands

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-001 | Copilot global no Portal | Copilot MFE + Portal | panel/full-page UX | LOCKED |
| CP-002 | Abrir app | Portal/CopilotBridge | authorized navigation | LOCKED |
| CP-003 | Abrir rota | Portal/CopilotBridge | authorized navigation | LOCKED |
| CP-004 | Abrir entidade | Portal + app contract | EntityRef/deep-link | LOCKED |
| CP-005 | Voltar/navegar histórico | Portal | router behavior | LOCKED |
| CP-006 | Selecionar aba/focar view | Portal/MFE/Iframe | typed command | LOCKED |
| CP-007 | Aplicar filtro visual | MFE/Iframe + Portal | view contract | LOCKED |
| CP-008 | Contexto do app atual | Portal | WorkspaceContext | LOCKED |
| CP-009 | Contexto de entidade | MFE/Iframe | EntityRef | LOCKED |
| CP-010 | Contexto filtros/período | MFE/Iframe | stale/security | LOCKED |
| CP-011 | Context chips | Copilot MFE | UX/relevance | LOCKED |
| CP-012 | “Explique o que estou vendo” | Copilot API + Context | grounding | LOCKED |
| CP-025 | Deep link após execução | Portal/MFE | result navigation | LOCKED |
| CP-059 | Platform Capability Projection | Portal/Copilot API | Core authority | LOCKED |
| CP-061 | Abrir iframe `PORTAL_ONLY` | Portal/CopilotBridge | authorized navigation | LOCKED |
| CP-062 | Handshake seguro Portal↔iframe | Portal/IframeBridge | security contract | LOCKED |
| CP-063 | Workspace Context de iframe | IframeBridge | normalization | LOCKED |
| CP-064 | Comando visual genérico iframe | Portal/IframeBridge | declared capability | LOCKED |
| CP-065 | Classificar iframe I0–I3 | Readiness | evidence | LOCKED |
| CP-068 | Proibir Business Action via DOM/click | Portal/Copilot Policy | negative gate | LOCKED |
| CP-069 | SSO iframe sem token pelo bridge | Portal/App/Security | auth architecture | TO_INVENTORY |
| CP-070 | Observabilidade iframe bridge | Portal/Observability | trace/redaction | LOCKED |
| CP-156 | Paridade de RBAC/policy entre Global/Workspace/Meeting/Frontline | Portal/Copilot Policy | surface parity | LOCKED |
| CP-159 | Contexto operacional OP/máquina/produto/operação/posto usa WorkspaceContext + EntityRef | Portal/MFE/Copilot | operational context contract | LOCKED |
| CP-171 | Device metadata não substitui identidade/autorização | Portal/Copilot Security | shared-device/context negative | LOCKED |

## 5. C3 — Intelligence Core Standalone + Multimodal Foundations

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-026 | RAG de procedimentos/documentos | Copilot Knowledge | grounding/security | LOCKED |
| CP-028 | Redigir e-mail/texto | Copilot capability | faithfulness | LOCKED |
| CP-053 | Send/stream parity | Copilot API/MFE | transport parity | LOCKED |
| CP-071 | Um único Copilot sem seleção de agente | Copilot API/MFE | no agent runtime | LOCKED |
| CP-073 | Recuperação semântica de expertise | Copilot API | positive/sibling/negative | LOCKED |
| CP-074 | Composição multi-expertise | Copilot Planner | cross-domain | LOCKED |
| CP-078 | Multimodalidade sem agent dependency | Copilot Multimodal | attachment eval | LOCKED |
| CP-079 | Análise de desenho com provenance/confidence | Copilot + Engineering | multimodal eval | LOCKED |
| CP-083 | Projects/preferred expertise sem outro runtime | Copilot API | permission negative | TO_INVENTORY |
| CP-086 | Unknown Expertise Pack sem planner patch | Copilot API | generalization | LOCKED |
| CP-087 | Metamorphic rename de Expertise Pack | Copilot Evals | equivalence | LOCKED |
| CP-089 | Packs referência Qualidade + Engenharia | Copilot/domain owners | pilot evals | LOCKED |
| CP-151 | OpenAPI ingestion + Action Catalog próprios do Copilot | Copilot API | independent catalog/importer | LOCKED |
| CP-160 | Speech-to-text/text-to-speech baseline por ports/adapters quando priorizado | Copilot Media | voice eval/provider abstraction | LOCKED |
| CP-161 | Voice command preserva mesma RBAC/policy/Decision semantics do texto | Copilot Policy/Planner | modality parity | LOCKED |
| CP-162 | Camera/image Evidence com frame/region/confidence/limitations | Copilot Multimodal | visual evidence eval | LOCKED |
| CP-163 | Short-video ingestion com time-range provenance e bounded processing | Copilot Media | video eval/budget | LOCKED |
| CP-164 | Screen share bounded/consented sem virar DOM automation | Copilot MFE/Media/Security | screen-share safety | LOCKED |
| CP-177 | Visual finding não vira decisão oficial de qualidade por default | Copilot/Quality Policy | epistemic/quality negative | LOCKED |

## 6. C4 — Business Reads + Business Graph

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-013 | Consultar Business Action | Copilot Action Runtime | read/RBAC/outcome | LOCKED |
| CP-014 | Consultar múltiplas APIs | Copilot Planner | multi-provider | LOCKED |
| CP-015 | Analisar/comparar dados | Copilot synthesis | grounded evidence | LOCKED |
| CP-027 | Gerar resumo/relatório grounded | Copilot Artifact | evidence/faithfulness | LOCKED |
| CP-029 | Recomendar próximos passos | Copilot synthesis | contextual/allowed | LOCKED |
| CP-043 | Unknown OpenAPI provider | Copilot API | full-chain unknown | LOCKED |
| CP-044 | Metamorphic provider/path/opId | Copilot Evals | metamorphic | LOCKED |
| CP-058 | Business Capability Projection | Copilot API | no duplicate authority | LOCKED |
| CP-090 | DELPI Business Graph mínimo | Copilot Graph/domain owners | permission traversal | LOCKED |
| CP-128 | Business Graph sibling onboarding | Copilot Graph | no planner hardcode | LOCKED |

## 7. C5 — Governed Writes + Durable Work Foundation

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-016 | Criar registro | Domain API + Copilot executor | Decision/RBAC/outcome | LOCKED |
| CP-017 | Editar registro | Domain API + Copilot executor | write parity | LOCKED |
| CP-018 | Aprovar/rejeitar | Domain API/Copilot Policy | approval/safety | LOCKED |
| CP-019 | Cancelar/arquivar | Domain API/Copilot Policy | destructive gate | LOCKED |
| CP-020 | Adicionar comentário | Domain API | write parity | LOCKED |
| CP-021 | Atribuir responsável | Domain API | permission/gate | LOCKED |
| CP-022 | Preview de write | Copilot API/MFE | argsHash/impact | LOCKED |
| CP-023 | Decision/confirmation UI | Copilot MFE/API | Decision Gate | LOCKED |
| CP-024 | Revalidar após decisão | Copilot Policy/Executor | TOCTOU | LOCKED |
| CP-030 | Plano operacional visível | Copilot API/MFE | no CoT/activity | LOCKED |
| CP-031 | Workflow multi-app | Copilot Work Runtime | compound outcome | LOCKED |
| CP-032 | Parallel safe reads | Copilot Work Runtime | safety | LOCKED |
| CP-033 | Dependências entre steps | Copilot Work Runtime | DAG | LOCKED |
| CP-034 | Partial failure truthful | Copilot Work Runtime | outcome | LOCKED |
| CP-035 | Retry seguro | Copilot Work Runtime | idempotency | LOCKED |
| CP-036 | Pause por decisão | Copilot Work/Decision | persistence | LOCKED |
| CP-037 | Reload/resume | Copilot Work Persistence | no duplicate write | LOCKED |
| CP-038 | Audit trail workflow | Copilot Observability | coverage | LOCKED |
| CP-045 | Autonomia L0–L2 | Copilot Policy | safe reads/navigation/prepare | LOCKED |
| CP-054 | Simulate/admin preview de action | Copilot Admin | parity | LOCKED |
| CP-076 | Playbook→WorkflowPlan sem endpoint hardcoded | Copilot Planner | authority separation | LOCKED |
| CP-168 | Candidate action de voz/reunião/frontline exige transition governada antes de write | Copilot Policy/Work | Decision/idempotency | LOCKED |

## 8. C6 — Product Work + Proactivity + Meeting/Frontline + Ecosystem

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-039 | AI-ready SDK/templates | Shared/Portal/Copilot | contracts | LOCKED |
| CP-040 | Readiness scanner | Copilot Tooling | factual inventory | LOCKED |
| CP-041 | Coverage dashboard | Copilot Admin/Observability | metrics | LOCKED |
| CP-042 | Unknown app onboarding | Core/Portal/Copilot | no hardcode | LOCKED |
| CP-060 | Admin de capabilities/coverage | Copilot Admin | admin RBAC | LOCKED |
| CP-066 | Iframe Copilot Bridge SDK | Shared/Portal | contract/lifecycle | LOCKED |
| CP-067 | Unknown iframe onboarding | Portal/IframeBridge | generalization | LOCKED |
| CP-084 | Admin/observability packs/playbooks | Copilot Admin | version/eval/audit | LOCKED |
| CP-096 | Copilot Task persistente | Copilot Work | restart/resume | LOCKED |
| CP-097 | Copilot Case | Copilot Work/Product | lifecycle/evidence | LOCKED |
| CP-098 | Evidence Board | Copilot Case | same EvidenceRef | LOCKED |
| CP-099 | Interaction Room ligada a Case | Copilot + room owner | RBAC/context | TO_INVENTORY |
| CP-100 | Copilot Inbox | Copilot Work/MFE | lifecycle | LOCKED |
| CP-101 | Watch por condição/evento | Copilot Work/Events | dedupe/RBAC | LOCKED |
| CP-102 | Watch OBSERVE | Copilot Work | audit | LOCKED |
| CP-103 | Watch ADVISE | Copilot Work/AI | grounded alert | LOCKED |
| CP-114 | Reference Knowledge lifecycle | Copilot Knowledge | owner/version/scope | LOCKED |
| CP-115 | Decision Knowledge | Copilot Case/Knowledge | provenance/no-CoT | LOCKED |
| CP-116 | Experience Knowledge | Copilot Case/Knowledge | governed promotion | LOCKED |
| CP-117 | Solution Pattern lifecycle | Copilot Knowledge/Expertise | review/eval/version | LOCKED |
| CP-118 | Governed Learning Loop | Copilot Admin | no auto-publish | LOCKED |
| CP-119 | Expertise Studio lifecycle | Copilot Admin | draft→publish | LOCKED |
| CP-120 | Expertise/Playbook rollback | Copilot Admin | version/eval | LOCKED |
| CP-124 | Task Completion metric | Copilot Observability | metric validity | LOCKED |
| CP-125 | Case resolution learning candidate | Copilot Case/Knowledge | candidate only | LOCKED |
| CP-126 | Inbox decision→workflow resume | Copilot MFE/Work | correlation | LOCKED |
| CP-127 | Room summary grounded em Case | Copilot/Room | evidence/RBAC | TO_INVENTORY |
| CP-165 | Meeting Mode com lifecycle explícito de captura | Copilot MFE/API | explicit start/stop/indicators | LOCKED |
| CP-166 | Meeting consulta dados reais com permissões do usuário | Copilot API/Domain APIs | meeting read parity | LOCKED |
| CP-167 | Ata viva distingue transcript/resumo/decisão/action/outcome | Copilot Meeting/Artifact | semantic/evidence gate | LOCKED |
| CP-169 | Frontline Mode no mesmo MFE/API | Copilot MFE/API | frontline surface parity | LOCKED |
| CP-170 | Hands-free voice com fallback touch/text | Copilot Frontline | noisy/permission/accessibility tests | LOCKED |
| CP-172 | Training assistance referencia procedimento/desenho/revisão vigente | Copilot Knowledge/Domain owners | source freshness | LOCKED |
| CP-173 | Observação de processo gera somente Knowledge/Experience candidate | Copilot Knowledge | candidate provenance | LOCKED |
| CP-174 | Meeting/frontline candidate exige review/eval antes de virar conhecimento publicado | Copilot Knowledge/Expertise | governed learning | LOCKED |
| CP-181 | Meeting/Frontline accessibility e large-touch/shared-device UX | Copilot MFE | accessibility/frontline gate | LOCKED |

## 9. C7 — Autonomy + Advanced Realtime + Optimization + Rollout

| ID | Requisito | Owner | Gate | Status |
|---|---|---|---|---|
| CP-046 | Autonomia L3 prepare | Copilot Policy | no persistence | LOCKED |
| CP-047 | Autonomia L4 governed write | Copilot Policy | Decision Gate | LOCKED |
| CP-048 | Autonomia L5 limitada | Copilot Policy/Admin | allowlist/limits/kill switch | LOCKED |
| CP-049 | Emergency stop | Copilot Admin/Policy | kill switch | LOCKED |
| CP-050 | Rollout/cohort controls | Platform/Copilot Admin | canary/rollback | LOCKED |
| CP-052 | TCR/First Plan Success metrics | Copilot Observability | metric validity | LOCKED |
| CP-104 | Watch ACT | Copilot Policy/Work | autonomy/Decision | LOCKED |
| CP-112 | What-if Simulation | Domain analytics/Copilot | reproducible model | LOCKED |
| CP-113 | Simulate→Apply separado | Domain API/Copilot Policy | new gate | LOCKED |
| CP-121 | Model Router | Copilot Infrastructure | quality/cost/latency | LOCKED |
| CP-122 | Compute Policy | Copilot Policy | provider constraints | LOCKED |
| CP-129 | Anchor reclamação→8D→Watch→ação | Cross-domain/Copilot | full integration | LOCKED |
| CP-180 | Advanced realtime media possui budgets/backpressure/degraded mode/cost telemetry | Copilot Media/Infra | realtime reliability gate | LOCKED |

## 10. Requisitos históricos do Chat — fora do escopo Copilot

| ID | Requisito histórico | Decisão | Status |
|---|---|---|---|
| CP-080 | Migrar presets de `AgentSpecializationService` | pertence ao Chat; Copilot cria Expertise nativa | OUT_OF_SCOPE_WITH_DECISION |
| CP-081 | Remover `userActivatedAgent` do Chat | pertence ao Chat | OUT_OF_SCOPE_WITH_DECISION |
| CP-082 | Remover soft agent handoff do Chat | pertence ao Chat | OUT_OF_SCOPE_WITH_DECISION |
| CP-085 | Remover routing legado `agent_id` do Chat | pertence ao Chat | OUT_OF_SCOPE_WITH_DECISION |

Esses IDs não podem ser reativados como dependência do Copilot.

## 11. Regras de atualização

- requisito novo recebe novo CP-ID;
- nenhum CP vira PASS por documentação apenas;
- runtime só passa com wiring + integration/eval;
- `TO_INVENTORY` não vira PLANNED por suposição;
- requisito removido recebe `OUT_OF_SCOPE_WITH_DECISION`;
- nenhum requisito Copilot pode ser bloqueado por refactor do Chat;
- shared reuse precisa ser platform-neutral;
- phase canonical é C0–C7 do `16`;
- modality não pode criar bypass de RBAC/policy;
- OT physical actuation não é inferida a partir de autonomia L5.

## 12. Coverage final

```text
TOTAL_REQUIREMENTS
PASS
LOCKED/BLOCKED
FAIL
OUT_OF_SCOPE_WITH_DECISION
UNMAPPED
```

Famílias:

```text
STANDALONE_FOUNDATION
ARCHITECTURE_PATTERNS
PORTAL_CONTEXT
INTELLIGENCE
MULTIMODAL_MEDIA
MEETING
FRONTLINE
PRIVACY_SHARED_DEVICE
INDUSTRIAL_OT_SAFETY
BUSINESS_READS_GRAPH
GOVERNED_WRITES_DURABLE
PRODUCT_WORK_PROACTIVITY
AUTONOMY_OPTIMIZATION
IFRAME
EXPERTISE
EVIDENCE
```

`UNMAPPED = 0` para qualquer release declarado completo.