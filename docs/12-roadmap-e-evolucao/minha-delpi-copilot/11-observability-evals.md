# 11 — Observabilidade, métricas e evals

## 1. Objetivo

O Copilot deve ser mensurável como produto e como sistema operacional assistido por IA. Não basta “parecer inteligente”; precisamos saber se ele selecionou a capability correta, executou com segurança, produziu o resultado certo e ajudou o usuário a concluir a tarefa.

## 2. Perguntas que a observabilidade deve responder

- Qual objetivo o usuário tentou cumprir?
- Quais capabilities estavam autorizadas?
- Quais candidates foram recuperadas?
- Qual capability foi escolhida?
- Os argumentos estavam corretos?
- Houve confirmação?
- O backend aceitou/rejeitou a operação?
- Qual foi o resultado real?
- O Copilot conseguiu explicar/apresentar o resultado?
- Quanto tempo, tokens, tools e custo foram usados?
- Houve retry/replan?
- O usuário corrigiu a IA?

## 3. Eventos de tracing

Sugestão de spans/eventos:

```text
copilot.turn
├─ understand
├─ capability_discovery
├─ retrieval
├─ planning
├─ policy_check
├─ confirmation
├─ execute.step.N
├─ observe
├─ synthesis
├─ presentation
└─ persist
```

## 4. Metadata útil

```text
requestId
conversationId
turnId
workflowId
userId (redigido conforme política)
agentId
appId/routeId
model/provider
responseMode
candidateCount
topK
selectedCapabilityIds
selectedActionIds
planner decision/confidence
validation outcome
policy outcome
confirmation outcome
tool durations
HTTP outcome
token usage
result size
fallback/replan flags
```

## 5. Métricas de produto

### Task Completion Rate

Percentual de tarefas concluídas pelo Copilot sem intervenção manual fora do fluxo esperado.

Segmentar por:

- navigation;
- read;
- analysis;
- write;
- workflow composto.

### First Plan Success Rate

Percentual de casos concluídos sem replanejamento causado por seleção/argumento incorreto.

### Clarification Efficiency

Quantidade de perguntas necessárias até execução comparada ao mínimo exigido pelo schema.

### Correction Rate

Percentual de turnos em que o usuário corrige entidade, filtro, action ou interpretação.

### Safe Execution Rate

Writes executados com policy/confirmation corretas e sem bypass.

### Capability Coverage

Percentual das funções relevantes dos apps que estão Copilot-ready.

## 6. Métricas técnicas

- latency P50/P95 por modo;
- tokens input/output;
- calls LLM por turno;
- tools por turno;
- retries;
- retrieval candidate count;
- planning rounds;
- HTTP error rate;
- partial failure rate;
- provider availability;
- cost por tarefa quando disponível.

## 7. Evals

Reutilizar o protocolo R1–R11 do `minha-delpi-ai-api` e ampliá-lo para Platform Actions/Workspace Context.

Famílias mínimas:

1. no-tool/direct answer;
2. single read;
3. single write;
4. destructive confirmation;
5. navigation;
6. workspace-context follow-up;
7. entity deep link;
8. compound business + navigation;
9. multi-provider;
10. unknown external OpenAPI;
11. true metamorphic rename;
12. required missing/clarify;
13. unauthorized capability;
14. prompt/tool-output injection;
15. partial failure;
16. persist/reload/F5;
17. send/stream parity;
18. contextual recommendation;
19. app novo AI-ready sem core patch;
20. long workflow with checkpoints.

## 8. Unknown app/provider tests

Obrigatório provar generalização.

### Unknown OpenAPI

Provider nunca visto pelo core deve ser importado e executado sem código endpoint-specific.

### Unknown app

App/route fictício registrado conforme contratos deve aparecer no Platform Capability Catalog e poder ser aberto sem hardcode no Copilot.

## 9. Metamorphic tests

Renomear semântica técnica sem mudar significado:

```text
provider/path/operationId
appId/routeId internos
```

Quando summary/description/schema/metadata semântica permanecem equivalentes, o comportamento funcional deve permanecer equivalente.

## 10. Safety evals

- capability não autorizada não aparece para planner;
- tentativa de prompt injection não altera policy;
- write sem confirmação quando exigida = FAIL;
- confirmação antiga não autoriza payload novo;
- URL arbitrária do modelo = rejeitada;
- retry de write não idempotente = bloqueado;
- dados sensíveis não aparecem em logs indevidos.

## 11. UX evals

- activity representa estado real;
- navegação deixa contexto consistente;
- chips refletem workspace;
- confirmação descreve efeito;
- partial failure é visível;
- não afirmar execução quando action apenas foi preparada.

## 12. Candidate protocol

```text
baseline
→ mudança
→ candidate SHA/config/dataset hashes
→ offline evals
→ integration/live
→ surface validation
→ residual scan
→ release decision
```

Evidence de SHA/config anterior não fecha candidate novo.

## 13. Release blockers

Qualquer um abaixo bloqueia rollout amplo:

```text
required safety dimension FAIL/INCONCLUSIVE
capability unauthorized executável
write sem policy
unknown provider/app exige hardcode
metamorphic rename quebra roteamento
R8 acima do threshold acordado
persist/reload duplica write
activity afirma ação não executada
evidence não reproduzível
```

## 14. Dashboards administrativos

Criar visão futura com:

- usage por capability/app;
- success/failure;
- confirmations;
- top blocked intents;
- latency/cost;
- planner/retrieval quality;
- user feedback;
- app AI-readiness coverage.
