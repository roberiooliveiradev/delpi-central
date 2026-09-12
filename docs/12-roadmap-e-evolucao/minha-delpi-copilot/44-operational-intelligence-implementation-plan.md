# Minha DELPI Copilot — Extensão de Implementação da Inteligência Operacional

**Status:** extensão executável do plano C0–C7  
**Autoridade:** complementa `16-execution-master-plan.md`; não altera a regra de começar por C0.S0.

## 1. Objetivo

Implantar de forma incremental os componentes estratégicos descritos em `34`–`43`, sem big-bang e sem criar arquitetura paralela.

## 2. Dependências

```text
C0-C2
→ contracts/context/platform foundation

C3
→ business reads/writes + evidence foundation

C4
→ workflows + checkpoints + Task foundation

C5
→ AI-ready ecosystem + expertise + Business Graph + Cases

C6
→ Decision Gates + Watch/controlled proactivity

C7
→ rollout/metrics

POST-C7 / waves específicas
→ simulation advanced
→ experience knowledge at scale
→ advanced model routing
```

## 3. O0 — Inventário obrigatório em C0.S0

Adicionar ao inventário:

- canonical entity IDs e relações entre domínios;
- event bus/event types existentes;
- salas de interação já existentes nos portais;
- notification/inbox patterns existentes;
- workflows/background jobs/queues atuais;
- approval/confirmation models atuais;
- audit/provenance metadata disponível;
- knowledge sources e lifecycle;
- model/provider abstractions e métricas;
- persistência de workflows/tasks atual;
- cases/solicitações que possam ser reutilizados em vez de novo conceito.

Não criar `BusinessGraph`, `Case` ou engine durável antes de provar gaps e owners.

## 4. O1 — Evidence Foundation

**Entrada:** C2/C3 foundation.

Entregas:

- `EvidenceRefV1` ou equivalente canônico;
- classificação FACT/CALCULATION/HYPOTHESIS/CONCLUSION/RECOMMENDATION;
- provenance em normalized results;
- freshness semantics;
- multimodal region/page provenance;
- UI mínima de fontes/evidências.

**Gate:** análise piloto consegue rastrear claims materiais até fontes autorizadas.

## 5. O2 — Business Graph mínimo

Entregas:

- canonical `EntityRef` reutilizado/expandido;
- `RelationshipRef`;
- graph query port;
- 3–5 relações cross-domain de alto valor;
- permission-aware traversal;
- source API fetch após traversal.

Piloto recomendado:

```text
reclamação → produto → OP/lote → material/fornecedor
```

**Gate:** novo relation type entra por contrato/config/owner adequado, sem hardcode no planner.

## 6. O3 — Copilot Task

Entregas:

- Task lifecycle/status;
- vínculo com WorkflowPlan;
- progress/activity;
- result/evidence refs;
- pending decisions;
- reload/resume.

**Gate:** uma tarefa multi-step sobrevive a F5/restart sem repetir write.

## 7. O4 — Durable Workflow Foundation

Entregas:

- workflow instance/step persistence;
- checkpoint;
- `wait_user`;
- `wait_approval`;
- resume com RBAC/policy revalidation;
- locking/idempotency.

Não introduzir engine externa antes de inventariar infraestrutura existente.

## 8. O5 — Case + Evidence Board

Entregas:

- Case lifecycle;
- objective/entity refs;
- evidence board;
- hypotheses/decisions/actions como estruturas explícitas;
- timeline;
- ligação Task/Workflow.

Piloto recomendado: investigação de Qualidade ou atraso operacional.

## 9. O6 — Interaction Room

Reutilizar o padrão de sala já existente quando possível.

Entregas:

- Case ↔ Room;
- participantes;
- mensagens;
- arquivos;
- Copilot contextual;
- decisões e pendências;
- summaries/digests.

**Gate:** autorização da sala não vaza dados de entidades sem permission.

## 10. O7 — Copilot Inbox

Entregas:

```text
waiting_for_user
working
completed
alerts
```

Itens linkam para Task/Case/Workflow/EntityRef.

Iniciar read-only; nenhuma execução automática na primeira onda.

## 11. O8 — Watch / Events

Entregas:

- Watch contract;
- event matching;
- dedupe/cooldown;
- OBSERVE/ADVISE;
- resume de workflows waiting_event;
- permission revalidation no disparo.

**ACT permanece bloqueado** até C6/autonomy gates.

## 12. O9 — Decision Gates

Migrar confirmação simples progressivamente:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Entregas:

- impact preview;
- arguments/evidence hash;
- expiry;
- approval state;
- revalidation antes de execute.

## 13. O10 — Organizational Experience

Entregas:

- DecisionRecord;
- ExperienceRecord;
- SolutionPattern candidate/publish lifecycle;
- owner/reviewer;
- Case → candidate experience promotion.

Nunca publicar automaticamente a partir de uma conversa.

## 14. O11 — Expertise Studio

Primeiro MVP pode ser admin técnico:

- repositories;
- schemas;
- versioning;
- draft/review/publish;
- eval runner;
- rollback.

UI completa vem após contratos estáveis.

## 15. O12 — What-if / Simulation

Somente por domínio com modelo owner claro.

Primeiro piloto deve escolher problema com:

- baseline mensurável;
- regra/cálculo reproduzível;
- risco controlado;
- diferença clara entre simulate e apply.

## 16. O13 — Model Router

Não iniciar antes de baseline de qualidade/custo/latência.

Entregas:

- task requirements classification;
- compute policy;
- classes FAST/STANDARD/DEEP/MULTIMODAL/LONG_CONTEXT;
- provider/model mapping central;
- privacy constraints;
- fallback/evals.

## 17. Sequência recomendada

```text
O0 inventory
→ O1 evidence
→ O2 graph minimum
→ O3 tasks
→ O4 durable workflow
→ O5 cases
→ O6 rooms
→ O7 inbox
→ O8 watch advise
→ O9 decision gates
→ O10 experience knowledge
→ O11 expertise studio
→ O12 simulation pilots
→ O13 model router
```

Alguns tracks podem avançar em paralelo após contracts, mas seus gates não devem ser fundidos artificialmente.

## 18. Feature flags

Flags candidatas, apenas se o projeto já possui mecanismo coerente:

```text
copilot_business_graph
copilot_tasks
copilot_cases
copilot_inbox
copilot_watch
copilot_decision_gates
copilot_experience_knowledge
copilot_simulation
copilot_model_router
```

Toda flag temporária precisa owner e exit criteria.

## 19. Não fazer

- implementar os 10 componentes em um único PR;
- criar databases/services novos sem inventário;
- introduzir event bus paralelo se já existir um;
- criar Case duplicando Minhas Solicitações ou outro domínio sem análise;
- implementar Watch com polling app-specific no core;
- criar graph duplicando tabelas inteiras;
- fazer Model Router antes de métricas;
- usar LLM para cálculo que possui regra determinística owner.

## 20. COMPLETE_GATE

Cada `O*` segue o mesmo protocolo do plano mestre:

```text
inventory
→ owner/contracts
→ baseline
→ implementation
→ wiring
→ positive/sibling/negative
→ security
→ generalization
→ residual scan
→ evidence
→ COMPLETE_GATE
```