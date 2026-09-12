# 13 — Catálogo funcional do Minha DELPI Copilot

## 1. Objetivo

Descrever as capacidades do produto independentemente da fase, sem duplicar a ordem de implementação. A sequência canônica vive em `16-execution-master-plan.md`.

## 2. Conversa e entendimento

- linguagem natural PT-BR;
- pedidos simples/compostos;
- follow-up contextual;
- clarify mínimo;
- entity resolution;
- structured goals;
- memória/references sem chain-of-thought.

## 3. Navegação e contexto

- abrir app/rota/entidade;
- selecionar view/aba;
- aplicar filtro visual;
- focus;
- deep link;
- Workspace Context;
- context chips;
- contexto por MFE/iframe.

## 4. Copilot único e especialização

- uma identidade de produto;
- Expertise Packs;
- Domain Playbooks;
- composição cross-domain;
- project preferences;
- unknown pack sem core patch;
- nenhuma capability concedida por expertise.

## 5. Knowledge

- procedimentos/manuais/normas;
- help contextual;
- Reference Knowledge;
- Operational Knowledge;
- Decision Knowledge;
- Experience Knowledge;
- Semantic Knowledge;
- ACL em todas as camadas.

## 6. Multimodalidade

- PDF;
- imagem;
- desenho técnico;
- foto de defeito;
- certificados/relatórios;
- OCR/VLM quando necessário;
- page/region provenance;
- confidence/limitations.

## 7. Evidence e explicabilidade

- SourceRef/EvidenceRef;
- freshness;
- facts;
- calculations;
- hypotheses;
- conclusions;
- recommendations;
- conflicting evidence;
- source expansion na UX.

## 8. Business Reads

Quando APIs/actions autorizadas existirem:

- produtos/estoque/estrutura;
- comercial;
- suprimentos;
- produção;
- financeiro;
- qualidade;
- engenharia;
- manutenção;
- solicitações;
- demais domínios onboarded.

Concreto = OpenAPI/Action Catalog + RBAC, nunca lista hardcoded deste documento.

## 9. DELPI Business Graph

- canonical EntityRef;
- relações cross-domain;
- authoritative/inferred provenance;
- permission-aware traversal;
- source API fetch;
- depth/cycle budgets;
- sibling relation onboarding.

## 10. Análise

- comparar períodos/entidades;
- métricas/cálculos grounded;
- anomalias/tendências quando método suportar;
- causalidade somente com evidence suficiente;
- cross-domain synthesis;
- limitação explícita.

## 11. Recommendations

Próximos passos baseados em:

- goals;
- evidence/outcomes;
- Workspace Context;
- authorized capabilities;
- policy;
- work state.

Sugestão não é execução.

## 12. Business Writes

Conforme API/RBAC/policy:

- criar;
- editar;
- aprovar/rejeitar;
- atribuir;
- comentar;
- cancelar/arquivar;
- iniciar processos.

Sempre via Business Action, não UI automation.

## 13. Decision Gates

- NO_GATE;
- ACKNOWLEDGE;
- CONFIRM;
- REVIEW_AND_CONFIRM;
- APPROVAL_WORKFLOW;
- BLOCK.

Inclui impact preview, args hash, evidence refs, expiry e revalidation.

## 14. Artefatos

- relatório;
- resumo executivo;
- tabela;
- comunicação/e-mail;
- plano de ação;
- documentação;
- apresentação/arquivo quando capability existir.

Artefato não executa business write implicitamente.

## 15. Workflows

- goal/DAG;
- dependencies;
- safe parallel reads;
- Decision Gates;
- retry/idempotency;
- partial failure;
- checkpoints;
- activity;
- cancel/timeout;
- no duplicate write.

## 16. Durable Work

- wait_user;
- wait_approval;
- wait_event;
- wait_time;
- resume após F5/restart;
- event correlation;
- state persistence quando necessário.

## 17. Copilot Tasks

- objective;
- progress;
- steps;
- decisions pendentes;
- result/evidence refs;
- links;
- cancel quando suportado.

## 18. Copilot Cases

- investigação longa;
- entity refs;
- Evidence Board;
- hypotheses/decisions/actions;
- Tasks/Workflows;
- timeline;
- Room;
- artifacts;
- lifecycle/resolution/reopen.

## 19. Interaction Rooms

- participantes;
- mensagens;
- arquivos;
- resumo grounded;
- pending actions;
- Case linkage;
- source permissions preservadas.

## 20. Copilot Inbox

- waiting_for_user;
- working;
- completed;
- alerts;
- Decision/Task/Case/Workflow links;
- dedupe/status lifecycle.

## 21. Copilot Watch

- OBSERVE;
- ADVISE;
- ACT.

Com event matching, dedupe, cooldown, expiry, permission revalidation e autonomy policy.

## 22. Event-driven continuity

- resume workflow por evento;
- alertas;
- acompanhar status;
- continuar investigação após dependência externa;
- preferir event source real a polling hardcoded.

## 23. Organizational Knowledge e Governed Learning

- Decision/Experience records;
- Solution Patterns;
- feedback → candidate;
- review/eval/version/publish;
- rollback;
- nunca auto-publicar conversa/correção.

## 24. Expertise Studio

- draft;
- review;
- eval;
- publish;
- deprecate;
- rollback;
- usage/quality telemetry.

Não é criador de agentes.

## 25. Simulation

- baseline;
- assumptions;
- deterministic/domain model owner;
- projected impact;
- limitations;
- `SIMULATE != APPLY`.

## 26. Model Router

Classes conceituais:

```text
FAST
STANDARD
DEEP_REASONING
MULTIMODAL
LONG_CONTEXT
```

Seleção por Compute Policy, data policy, latency/cost e quality requirements.

## 27. Iframes

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

Contexto/comandos visuais por bridge seguro; Business Actions por API.

## 28. Autonomia

```text
L0 explain
L1 navigate
L2 read/analyze
L3 prepare
L4 governed execute
L5 explicitly allowlisted autonomy
```

L5 OFF por default.

## 29. Administração

- capability/action coverage;
- app readiness;
- expertise/playbooks;
- knowledge lifecycle;
- Task/Case/Workflow;
- Decision Gates;
- Watch;
- model usage/cost;
- failures/retries;
- safe execution;
- audit;
- rollout/kill switch.

## 30. Onboarding AI-ready

```text
L1 discoverable
L2 context-ready
L3 read-ready
L4 write-ready
L5 workflow-ready
```

Novo app entra por shared contracts sem patch central.

## 31. Fora do padrão

- DOM automation para substituir API;
- browser/cross-origin hacks;
- bypass de permission;
- endpoint selector hardcoded;
- chain-of-thought persistence;
- agent engine por departamento;
- Business Graph duplicando bancos;
- confirmation system paralelo ao Decision Gate;
- automatic production learning por feedback.

## 32. Experiência final

O usuário deve sentir que o Copilot:

```text
sabe onde estou
+ entende o objetivo
+ encontra entidades/fontes corretas
+ aplica conhecimento especializado
+ mostra evidence
+ navega e executa com governança
+ acompanha trabalho ao longo do tempo
+ colabora com pessoas
+ aprende somente por processo governado
+ respeita minhas permissões
```
