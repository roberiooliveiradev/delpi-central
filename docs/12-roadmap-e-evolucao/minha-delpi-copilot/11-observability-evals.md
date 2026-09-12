# 11 — Observabilidade, métricas e evals

**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Objetivo

O Copilot deve ser mensurável como produto, sistema de IA e camada operacional independente. Não basta responder: precisamos provar seleção correta, Evidence, policy, execução real, continuidade, valor entregue, privacy/safety e ausência de dependência do Minha DELPI Chat.

Meeting/Frontline/media também precisam ser observáveis sem transformar telemetry em armazenamento oculto de áudio/vídeo ou mecanismo de vigilância.

## 2. Perguntas fundamentais

A observabilidade deve responder:

- qual objetivo o usuário tentou cumprir?;
- qual surface foi usada?;
- qual Workspace/Entity Context foi usado?;
- qual user/device session estava ativa?;
- quais capabilities estavam autorizadas?;
- quais candidates foram recuperadas?;
- quais expertise/playbooks foram selecionados?;
- quais sources/evidence sustentaram a resposta?;
- qual modality foi usada?;
- houve media session e qual retention class/policy se aplicou?;
- quais argumentos foram validados?;
- qual policy/Decision Gate decidiu?;
- qual action realmente executou?;
- qual outcome retornou?;
- workflow/task/case permaneceu consistente?;
- Meeting gerou decisão/action candidate ou ação executada?;
- Frontline guidance/escalation foi concluída?;
- houve wait/resume/retry?;
- quanto tempo/tokens/tools/media/custo?;
- houve correction/replan?;
- o usuário concluiu o trabalho?;
- alguma tentativa violou privacy/shared-device/OT boundary?;
- algum componente do Chat foi chamado indevidamente?.

## 3. Correlation model

Preferir correlation compartilhada do Copilot:

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
meetingId?
frontlineSessionId?
mediaSessionId?
deviceRef? bounded/non-sensitive
```

Não criar correlação incompatível por feature nem reutilizar IDs internos do Chat como authority.

## 4. Spans/eventos sugeridos

```text
copilot.turn
├─ understand
├─ capability_discovery
├─ expertise_retrieval
├─ playbook_retrieval
├─ knowledge_retrieval
├─ media_ingest
├─ speech_transcribe
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
copilot.media_session
copilot.meeting
copilot.frontline_session
```

Namespaces de telemetry devem ser próprios do Copilot.

## 5. Metadata útil

```text
surface = global|workspace|meeting|frontline
appId/routeId
entity types/count
device class, sem identity sensível desnecessária
modality = text|voice|image|video|screen|document
media kind/duration/size class
retention class/policy version
capture persisted? yes/no
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
meeting/frontline status
tool/API/media stage durations
HTTP outcome
token usage
result size
retry/replan/fallback flags
error classification
```

Não logar raw media/payload sensível apenas para “observabilidade”.

`agentId`, `chat_mode`, `userActivatedAgent` e outros campos do Minha DELPI Chat **não fazem parte do modelo de telemetry do Copilot**.

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
- Workflow;
- Meeting goal;
- Frontline assistance goal.

### First Plan Success Rate

Percentual concluído sem replan causado por seleção/argumento incorreto.

### Clarification Efficiency

Perguntas adicionais comparadas ao mínimo realmente necessário.

### Correction Rate

Correção de entidade, contexto, action, interpretation, evidence, recommendation, transcript ou visual finding.

### Safe Execution Rate

Writes concluídos com RBAC/policy/Decision Gate/idempotency corretos.

### Evidence Coverage

Percentual de claims materiais sourceáveis apresentados com provenance adequada.

### Case Resolution Rate

Cases resolvidos/fechados com outcome verificável.

### Watch Signal Quality

Alertas úteis versus duplicados/falsos/ignorados.

### Meeting Action Closure Rate

Ações confirmadas em reunião que chegam a outcome verificável dentro do prazo/fluxo aplicável.

### Meeting Summary Correction Rate

Percentual de atas/resumos que exigem correção material de decisão, responsável, prazo ou fato.

### Frontline Help Resolution Rate

Sessões de assistência resolvidas sem escalation desnecessária e com guidance grounded.

### Escalation Quality

Escalations que chegam ao owner correto com contexto/Evidence suficiente.

### Capability/App/Frontline Readiness Coverage

Cobertura L1–L5, iframe classes e readiness Frontline quando aplicável.

### Standalone Independence Rate

Execuções que completam sem chamadas/imports/storage do Minha DELPI Chat. Target: **100%** fora de testes explicitamente reference-only.

### Safety/privacy targets

```text
hidden capture incidents = 0
shared-device state leaks = 0
unauthorized media retention = 0
arbitrary OT command attempts executed = 0
safety interlock bypass = 0
```

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
- STT/TTS/vision provider latency/error when used;
- media ingest/transcription/video processing latency;
- media session duration/concurrency;
- frame/video sampling rate when applicable;
- network degradation/fallback rate;
- raw-media persisted versus transient count by policy class;
- cost por task/case/meeting/frontline session quando disponível;
- surface policy parity;
- independence violations = 0.

## 8. Evals families

Aplicar R1–R11 quando pertinente e acrescentar famílias do Copilot:

1. no-tool/direct;
2. navigation;
3. Workspace Context follow-up;
4. single/multi-provider read;
5. unknown OpenAPI;
6. true metamorphic provider/path/opId;
7. expertise selection positive/sibling/negative;
8. unknown/metamorphic Expertise Pack;
9. Playbook applicability;
10. document/image multimodal Evidence;
11. voice STT/TTS/modality parity;
12. camera/video provenance/uncertainty;
13. epistemic labeling;
14. Business Graph traversal;
15. single write + Decision Gate;
16. destructive/approval workflow;
17. durable wait/resume;
18. crash/no duplicate write;
19. Task/Case lifecycle;
20. Room/Inbox permissions;
21. Watch event/dedupe;
22. injection multi-source/media;
23. unknown app/iframe/relation;
24. send/stream/voice parity;
25. Global/Workspace/Meeting/Frontline security parity;
26. Meeting capture/ata/action candidate;
27. shared-device/Frontline user isolation;
28. Frontline guidance/escalation;
29. process-learning candidate governance;
30. simulation;
31. model routing;
32. advanced realtime budgets/fallback when enabled;
33. industrial/OT negative safety cases;
34. standalone independence with Chat unavailable;
35. anchor workflows end-to-end.

## 9. Generalization

Obrigatório provar casos desconhecidos sem core patch:

```text
provider
app
iframe
Expertise Pack
entity/relationship type
device class/media provider when the abstraction claims generalization
```

quando a feature correspondente estiver no release.

## 10. Metamorphic tests

Renomear metadata técnica preservando semântica:

- provider/path/operationId;
- app/route internal IDs quando contract permitir;
- expertise key;
- relation technical identifier;
- media provider implementation quando port contract permanecer equivalente.

Comportamento semântico deve permanecer equivalente quando authority/schema não mudou.

## 11. Safety evals

- unauthorized capability ausente/bloqueada;
- Workspace/Pack/Playbook/RAG/Tool/Event/Room/media injection não altera policy;
- Decision antiga não autoriza payload novo;
- URL arbitrária rejeitada;
- retry write não idempotente bloqueado;
- Graph não vaza node;
- Room/Case membership não concede source access;
- Watch ACT sem policy bloqueado;
- provider proibido por data policy não recebe payload;
- secrets/PII/raw media não aparecem em logs indevidos;
- Chat runtime indisponível não degrada autorização/execução;
- mic/camera/screen não iniciam ocultamente;
- F5/reconnect não reativa capture silenciosamente;
- voice command não amplia RBAC;
- user B em shared device não recebe state do user A;
- visual finding não vira quality fact sem authority;
- meeting statement não executa write implicitamente;
- process observation não muda production behavior automaticamente;
- free-form LLM→machine command bloqueado;
- Copilot L5 não relaxa OT safety.

## 12. Evidence quality evals

- FACT possui source quando material;
- CALCULATION inputs/metodologia consistentes;
- HYPOTHESIS não vira fato;
- conflict/staleness aparece;
- multimodal page/region/frame/time-range rastreável;
- voice/transcript segment rastreável quando necessário e permitido;
- confidence/limitations coerentes;
- conclusion sem evidence suficiente é limitada;
- recommendation não é narrada como execução.

## 13. Meeting evals

- capture start/stop explícito;
- indicators corretos;
- transcript accuracy em amostras representativas;
- live queries obey RBAC;
- facts sourced;
- summary faithfulness;
- decision extraction distinguish candidate/confirmed;
- action extraction does not execute;
- ata viva links evidence/tasks/cases corretamente;
- source revocation respected;
- retention classes honored;
- no Chat dependency.

## 14. Frontline evals

- large-touch/accessibility;
- noisy environment speech;
- text/touch fallback;
- current OP/machine/product/operation context;
- wrong/stale context correction;
- procedure/drawing revision freshness;
- camera finding confidence;
- unavailable network/provider safe degradation;
- escalation owner correctness;
- issue registration governance;
- shared-device switch isolation;
- no hidden surveillance;
- no physical machine command path.

## 15. Durable work evals

- checkpoint;
- F5/restart;
- wait_user;
- wait_approval;
- wait_event;
- duplicate event;
- repeated voice/transcript action;
- crash after write;
- concurrent resume;
- cancel/expire;
- policy change durante wait;
- no duplicate effect.

## 16. UX evals

- activity = estado real;
- context chips corretos;
- evidence progressive disclosure;
- Decision Gate compreensível;
- Task/Case progress verdadeiro;
- Inbox state correto;
- simulation claramente rotulada;
- nenhuma tarefa normal exige troca de agente;
- mesmas conversas/estado entre surfaces quando contrato prevê continuidade;
- capture/privacy indicators;
- Meeting/Frontline accessibility;
- captions/transcript and non-voice fallback.

## 17. Candidate protocol

```text
baseline
→ implementation
→ candidate SHA/config/contracts/policy hashes
→ offline evals
→ integration/live
→ surface/media validation
→ privacy/shared-device/OT validation when applicable
→ independence validation
→ adversarial/residual scan
→ release decision
```

Evidence de candidate anterior não fecha candidate materialmente alterado.

## 18. Release blockers

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
evidence não reproduzível
Chat runtime dependency detectada
Copilot storage/telemetry usando Chat authority
hidden media capture
undefined/violated media retention
shared-device state leak
voice permission bypass
unvalidated visual finding promoted to fact
hidden worker surveillance
arbitrary LLM OT command
safety interlock bypass
```

## 19. Dashboards/admin

Visões futuras:

- usage/success/failure por capability/app/surface;
- expertise/playbook selection quality;
- evidence coverage;
- decisions/approvals;
- workflow/task/case outcomes;
- Meeting action closure/summary corrections;
- Frontline help/escalation outcomes;
- Watch alerts;
- media session/provider latency/cost/failures;
- retention/deletion compliance;
- shared-device/session violations;
- privacy/safety blocks;
- top blocked intents;
- model usage;
- user feedback;
- AI-ready/Frontline readiness coverage;
- standalone independence violations;
- rollout/readiness progress.

## 20. Regra de privacidade

Observabilidade registra decisões operacionais estruturadas, não prompt interno/chain-of-thought, JWT, secrets, full sensitive payload, raw audio/video/screenshots ou biometric data sem purpose/owner/policy explícitos.

Telemetry não deve se transformar em um sistema de vigilância de trabalhadores.