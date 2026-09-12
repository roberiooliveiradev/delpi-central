# 11 — Observabilidade, métricas e evals

## 1. Objetivo

O Copilot deve ser mensurável como produto, sistema de IA e camada operacional. Não basta responder: precisamos provar seleção correta, evidence, policy, execução real, continuidade e valor entregue.

## 2. Perguntas fundamentais

A observabilidade deve responder:

- qual objetivo o usuário tentou cumprir?;
- qual Workspace/Entity Context foi usado?;
- quais capabilities estavam autorizadas?;
- quais candidates foram recuperadas?;
- quais expertise/playbooks foram selecionados?;
- quais sources/evidence sustentaram a resposta?;
- quais argumentos foram validados?;
- qual policy/Decision Gate decidiu?;
- qual action realmente executou?;
- qual outcome retornou?;
- workflow/task/case permaneceu consistente?;
- houve wait/resume/retry?;
- quanto tempo/tokens/tools/custo?;
- houve correction/replan?;
- o usuário concluiu o trabalho?.

## 3. Correlation model

Preferir correlation compartilhada:

```text
requestId
conversationId
turnId
traceId
workflowId?
taskId?
caseId?
decisionId?
watchId?
```

Não criar correlação incompatível por feature.

## 4. Spans/eventos sugeridos

```text
copilot.turn
├─ understand
├─ capability_discovery
├─ expertise_retrieval
├─ playbook_retrieval
├─ knowledge_retrieval
├─ multimodal_extract
├─ evidence_compose
├─ planning
├─ policy_check
├─ decision_gate
├─ execute.step.N
├─ graph_traversal
├─ observe_outcome
├─ checkpoint
├─ synthesis
├─ presentation
└─ persist

copilot.workflow
copilot.task
copilot.case
copilot.watch
```

## 5. Metadata útil

```text
appId/routeId
entity types/count
model/provider
responseMode
candidateCount/topK
selectedCapabilityIds
selectedActionIds
selectedExpertise key/version/hash
selectedPlaybook key/version/hash
evidence/source counts
policy outcome
decision gate level/outcome
workflow/task/case status
tool/API durations
HTTP outcome
token usage
result size
retry/replan/fallback flags
error classification
```

`agentId` pode existir apenas como legacy compatibility telemetry enquanto necessário; não é eixo de produto final.

## 6. Métricas de produto

### Task Completion Rate

Medir conclusão por:

- turn simples;
- navigation;
- read;
- analysis;
- write;
- Task;
- Case;
- Workflow.

### First Plan Success Rate

Percentual concluído sem replan causado por seleção/argumento incorreto.

### Clarification Efficiency

Perguntas adicionais comparadas ao mínimo realmente necessário.

### Correction Rate

Correção de entidade, contexto, action, interpretation, evidence ou recommendation.

### Safe Execution Rate

Writes concluídos com RBAC/policy/Decision Gate/idempotency corretos.

### Evidence Coverage

Percentual de claims materiais sourceáveis apresentados com provenance adequada.

### Case Resolution Rate

Cases resolvidos/fechados com outcome verificável.

### Watch Signal Quality

Alertas úteis versus duplicados/falsos/ignorados.

### Capability/App Readiness Coverage

Cobertura L1–L5, iframe classes e capability families.

## 7. Métricas técnicas

- latency P50/P95 por estágio e surface;
- tokens input/output;
- calls LLM por turno/workflow;
- tools por turno/workflow;
- retries/replans;
- retrieval candidate counts;
- evidence size/count;
- graph traversal depth/latency;
- HTTP error/partial failure;
- workflow wait/resume latency;
- duplicate event/write prevented;
- provider/model availability;
- cost por task/case quando disponível.

## 8. Evals families

Reutilizar R1–R11 e acrescentar famílias do Copilot:

1. no-tool/direct;
2. navigation;
3. Workspace Context follow-up;
4. single/multi-provider read;
5. unknown OpenAPI;
6. true metamorphic provider/path/opId;
7. expertise selection positive/sibling/negative;
8. unknown/metamorphic Expertise Pack;
9. Playbook applicability;
10. multimodal evidence;
11. epistemic labeling;
12. Business Graph traversal;
13. single write + Decision Gate;
14. destructive/approval workflow;
15. durable wait/resume;
16. crash/no duplicate write;
17. Task/Case lifecycle;
18. Room/Inbox permissions;
19. Watch event/dedupe;
20. injection multi-source;
21. unknown app/iframe/relation;
22. send/stream parity;
23. simulation;
24. model routing;
25. anchor workflow end-to-end.

## 9. Generalization

Obrigatório provar casos desconhecidos sem core patch:

```text
provider
app
iframe
Expertise Pack
entity/relationship type
```

quando a feature correspondente estiver no release.

## 10. Metamorphic tests

Renomear metadata técnica preservando semântica:

- provider/path/operationId;
- app/route internal IDs quando contract permitir;
- expertise key;
- relation technical identifier.

Comportamento semântico deve permanecer equivalente quando authority semântica/schema não mudou.

## 11. Safety evals

- unauthorized capability ausente/bloqueada;
- Workspace/Pack/Playbook/RAG/Tool/Event/Room injection não altera policy;
- Decision antiga não autoriza payload novo;
- URL arbitrária rejeitada;
- retry write não idempotente bloqueado;
- Graph não vaza node;
- Room/Case membership não concede source access;
- Watch ACT sem policy bloqueado;
- provider proibido por data policy não recebe payload;
- secrets/PII não aparecem em logs indevidos.

## 12. Evidence quality evals

- FACT possui source quando material;
- CALCULATION inputs/metodologia consistentes;
- HYPOTHESIS não vira fato;
- conflict/staleness aparece;
- multimodal region é rastreável;
- conclusion sem evidence suficiente é limitada;
- recommendation não é narrada como execução.

## 13. Durable work evals

- checkpoint;
- F5/restart;
- wait_user;
- wait_approval;
- wait_event;
- duplicate event;
- crash after write;
- concurrent resume;
- cancel/expire;
- policy change durante wait;
- no duplicate effect.

## 14. UX evals

- activity = estado real;
- context chips corretos;
- evidence progressive disclosure;
- Decision Gate compreensível;
- Task/Case progress verdadeiro;
- Inbox state correto;
- simulation claramente rotulada;
- nenhuma tarefa normal exige troca de agente;
- accessibility.

## 15. Candidate protocol

```text
baseline
→ implementation
→ candidate SHA/config/contracts hashes
→ offline evals
→ integration/live
→ surface validation
→ adversarial/residual scan
→ release decision
```

Evidence de candidate anterior não fecha candidate materialmente alterado.

## 16. Release blockers

```text
required safety FAIL/INCONCLUSIVE
foundation duplicada
unauthorized capability executável
claim material sem provenance quando required
write sem policy/Decision Gate
unknown contract case exige hardcode
metamorphic rename quebra semântica
workflow resume duplica efeito
Case/Room/Graph vaza data
Watch ACT sem policy
simulation vira fato
provider data policy violada
activity afirma execução inexistente
R8 acima do threshold vigente
evidence não reproduzível
```

## 17. Dashboards/admin

Visões futuras:

- usage/success/failure por capability/app;
- expertise/playbook selection quality;
- evidence coverage;
- decisions/approvals;
- workflow/task/case outcomes;
- Watch alerts;
- top blocked intents;
- latency/cost/model usage;
- user feedback;
- AI-ready coverage;
- legacy migration progress.

## 18. Regra de privacidade

Observabilidade registra decisões operacionais estruturadas, não prompt interno/chain-of-thought, JWT, secrets ou payload sensível integral.