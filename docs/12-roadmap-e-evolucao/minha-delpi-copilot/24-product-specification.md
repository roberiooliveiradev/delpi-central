# Minha DELPI Copilot — Especificação Funcional e Técnica Completa

**Status:** especificação canônica de produto  
**Produto:** aplicação standalone nova  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Rastreabilidade:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Definição

O Minha DELPI Copilot é a **interface inteligente entre as pessoas e a operação da DELPI**, implementada como aplicação independente dentro da Minha DELPI.

Ele possui:

```text
Copilot API própria
Copilot MFE próprio
persistência/migrations próprias
manifesto/rotas/permissões próprias
deploy/rollback próprios
```

Ele **não é evolução do Minha DELPI Chat** e não depende do Chat para funcionar.

North Star:

> Entender o contexto da organização, conectar dados, pessoas, processos e aplicações, investigar problemas, executar trabalho, acompanhar resultados e transformar conhecimento empresarial validado em ação governada — no escritório, em reuniões e no chão de fábrica.

```text
PERGUNTAR  → entender, pesquisar, explicar, analisar
FAZER      → abrir, consultar, criar, alterar, aprovar, executar
ACOMPANHAR → monitorar, detectar, alertar, reagir
TRABALHAR  → investigar, colaborar, planejar, acompanhar, concluir
APRENDER   → gerar candidatos de conhecimento e publicar somente por governance
```

## 2. Integração na Minha DELPI

```text
Portal Shell
→ hospeda Copilot MFE federado
→ fornece token/contexto de host

Core API
→ apps/rotas/RBAC/governança

Gateway
→ rota Copilot MFE/API

Domain APIs
→ dados/regras/actions reais

plugin-ui
→ design system

Copilot API
→ inteligência/orquestração/trabalho/evidence/media
```

O Portal é host, não runtime inteligente. Core é authority de permissões, não banco do Copilot. Domain APIs continuam donas do negócio.

## 3. Disponibilidade

A direção de produto é disponibilizar o entry point do Copilot amplamente aos usuários autenticados da Minha DELPI conforme acesso/rollout.

Isso não significa permissões universais.

```text
visible Copilot
+ effective user permissions
+ context
+ capability policy
+ risk/sensitivity
→ available behavior
```

## 4. Superfícies

### Global

Painel contextual para uso cotidiano dentro dos apps.

### Workspace

Página completa para conversas longas, análises, Tasks/Cases, Evidence, artifacts, administration e trabalho complexo.

### Meeting

Sessão assistida para reunião presencial/remota com voz, transcrição, screen/camera quando autorizados, dados reais, decisões, ata e ações candidatas.

### Frontline

Experiência simplificada para operador/técnico/inspetor no posto, priorizando voz hands-free, touch, câmera, desenho/procedimento e contexto operacional.

Todas são surfaces do mesmo MFE/runtime.

## 5. Copilot único

Existe um único Copilot. Domínios especializam o runtime por:

- Expertise Packs;
- Domain Playbooks;
- Knowledge scopes;
- project/preferences;
- authorized capabilities;
- multimodal tools.

Não existe agent runtime por departamento.

## 6. Conversa e entendimento

- PT-BR natural;
- pedidos longos/compostos;
- follow-up contextual;
- goal decomposition;
- entity resolution;
- clarify somente quando necessário;
- structured references/memory;
- sem chain-of-thought persistida/exposta;
- entrada por texto ou voz conforme surface/device.

Conversations/turns são Copilot-owned e não usam sessions/agent_id do Chat.

## 7. Workspace Context

```text
appId
routeId
entityRefs
filters
selection
dateRange
visibleDataRefs
source
device/session metadata bounded quando necessário
```

Bounded/sanitized. Não concede permission.

No Frontline, OP, máquina, produto, lote, operação, material e posto usam preferencialmente `EntityRef`.

## 8. Navegação / Platform Commands

- abrir app;
- abrir rota;
- abrir entidade;
- back/history;
- select/focus view;
- aplicar filtro visual quando app declarar suporte.

LLM escolhe target lógico; Portal resolve rota autorizada. URL arbitrária é proibida.

## 9. Capability architecture

### Platform capabilities

Derivadas de Core apps/routes e generic action definitions.

### Business capabilities

Derivadas diretamente de OpenAPI/contracts das Domain APIs.

```text
Domain OpenAPI
→ Copilot importer/index
→ Copilot Action Catalog
→ authorized Capability Projection
→ semantic retrieval
→ planner
→ schema validation
→ policy/Decision Gate
→ generic executor
→ Domain API
→ Outcome/Evidence
```

Essa cadeia é nativa do Copilot; não usa o Action Catalog/runtime do Minha DELPI Chat.

Modalidade de entrada não altera esse pipeline.

## 10. Business Reads

Consultar, conforme APIs onboarded:

- comercial;
- suprimentos;
- produção;
- qualidade;
- financeiro;
- engenharia;
- manutenção;
- solicitações;
- demais domínios.

A lista não é hardcoded no planner.

## 11. Business Writes

Quando Domain API/policy permitir:

- criar;
- editar;
- aprovar/rejeitar;
- atribuir;
- comentar;
- cancelar/arquivar;
- iniciar processo;
- registrar ocorrência/solicitação;
- demais operations reais.

Nunca usar DOM automation como substituto de API.

Voice/Meeting/Frontline candidate action passa pelo mesmo Decision/action pipeline.

## 12. Decision Gates

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Consideram risk, sensitivity, impact, evidence, arguments hash, expiry, autonomy e approver requirements.

## 13. Entity model e DELPI Business Graph

`EntityRef` e `RelationshipRef` conectam semanticamente domínios:

```text
reclamação
→ produto
→ desenho/revisão
→ OP/lote
→ máquina/operação
→ material
→ fornecedor
→ inspeções
→ não conformidade
→ plano de ação
```

Graph guarda refs/relationships/provenance, não master copies dos dados.

## 14. Evidence / Epistemic UX

Distinguir:

```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

Evidence pode carregar source, entity refs, freshness, page/region/frame/time-range, confidence, limitations, extractor/model version e media ref quando aplicável.

## 15. Expertise Packs

Fornecem:

- terminology;
- signals;
- analysis guidance;
- evidence expectations;
- preferred playbooks;
- knowledge refs;
- multimodal needs;
- output guidance.

Não concedem RBAC nem definem endpoints como authority.

## 16. Domain Playbooks

Métodos versionados como:

- 8D;
- root cause;
- drawing review;
- FMEA;
- shortage/delay analysis;
- trabalho padronizado;
- outros processos corporativos.

Playbook orienta stages/evidence/criteria. Planner resolve capabilities reais.

## 17. Knowledge

- Reference Knowledge;
- Operational Knowledge;
- Decision Knowledge;
- Experience Knowledge;
- Semantic Knowledge.

Knowledge/RAG runtime é próprio do Copilot e respeita ACL/source provenance.

Meeting/Frontline/process observation podem produzir **candidate knowledge**, nunca published truth automaticamente.

## 18. Multimodalidade

Suportar conforme tools/policy:

- PDF;
- imagens;
- desenhos técnicos;
- planilhas/documentos;
- fotos de defeito;
- certificados/relatórios;
- voz/áudio;
- câmera;
- vídeo curto;
- screen share.

```text
input/media
→ native extraction/OCR/STT/Vision
→ structured Evidence
→ Expertise/Playbook
→ optional API/Knowledge reads
→ grounded synthesis
```

A implementação é nova na Copilot API. O pipeline existente do Chat pode ser estudado, mas não é runtime dependency.

## 19. Voice

Voice pode oferecer:

- STT;
- TTS;
- hands-free commands;
- correction/repeat;
- meeting discussion;
- frontline assistance.

Invariante:

```text
voice authorization = typed authorization
```

Voz nunca reduz Decision Gate.

## 20. Camera/image/video

Camera e vídeo podem auxiliar:

- mostrar peça/defeito;
- localizar região;
- comparar referência;
- analisar desenho;
- coletar Evidence;
- acompanhar operação de forma autorizada;
- treinamento contextual.

Progressão:

```text
image/frame
→ short video
→ sampled assisted session
→ advanced realtime only after C7 evidence
```

Não armazenar vídeo contínuo indiscriminadamente.

## 21. Meeting Mode

Meeting Mode deve permitir, conforme device/policy:

- explicit start/stop;
- mic/transcription;
- camera/screen optional;
- perguntas em voz/texto;
- consultas business em tempo real;
- facts/evidence;
- decisions/pending topics;
- candidate actions;
- Task/Case/Room linkage;
- next-meeting continuity.

### Ata viva

Meeting artifact distingue:

```text
transcript
summary
source data/evidence
human-confirmed decision
candidate action
executed/verified action
```

Ação citada na reunião não é executada automaticamente.

## 22. Frontline Mode

Frontline atende operador/técnico/inspetor/manutenção com:

- UI large-touch/simplificada;
- shared-device safe session;
- OP/machine/product/operation context;
- hands-free voice;
- camera/image;
- drawing/procedure current revision;
- quality/maintenance history;
- contextual training;
- register issue/escalate;
- Task/Case linkage.

Exemplo:

```text
user + workstation
+ OP + machine + operation + product
+ voice/camera
→ Copilot
→ Knowledge/API/Graph/Evidence
→ guidance
→ governed action if needed
```

## 23. Training assistance

Copilot pode orientar passo a passo e explicar procedimento/desenho, mas não concede qualificação/certificação oficial automaticamente.

Source/revision vigente deve ser visível quando material.

## 24. Process learning / conhecimento tácito

Fluxo permitido:

```text
observação autorizada
+ user statement/media/context
+ process data
→ candidate insight/practice
→ Evidence
→ specialist/owner review
→ eval
→ version/publish
```

Nunca:

```text
one observed behavior → automatic production rule
```

## 25. Governed Learning / Expertise Studio

```text
feedback/case/meeting/frontline outcome
→ candidate
→ expert review
→ eval
→ version
→ publish
→ canary/rollback
```

Nunca auto-publicar comportamento de produção a partir de correção do usuário.

Expertise Studio gerencia Packs/Playbooks, não agents.

## 26. Workflow / Durable Runtime

```text
WorkflowPlan
→ steps/dependencies
→ canonical capability executors
→ checkpoint
→ wait_user | wait_approval | wait_event | wait_time
→ resume/revalidate
→ complete/fail/cancel
```

Deve sobreviver a restart sem duplicate write.

Meeting/Frontline não criam workflow engine paralelo.

## 27. Copilot Task

Unidade operacional curta/média backed pelo Durable Workflow Runtime.

Mostra objective/status/progress/pending decisions/results/evidence/entity links/meeting/frontline refs quando aplicável.

## 28. Copilot Case

Unidade de investigação/trabalho prolongado com:

- entity refs;
- Evidence Board;
- hypotheses;
- decisions;
- actions;
- Tasks/Workflows;
- timeline;
- room ref;
- artifacts;
- meeting/frontline refs.

Não substitui source permissions.

## 29. Interaction Rooms

C0 deve inventariar a infraestrutura já existente — incluindo salas do Portal Comercial — antes de decidir `REUSE | EXTEND | ADAPTER | CREATE_REQUIRED`.

Room membership não concede acesso aos sources relacionados.

Meeting artifacts podem ser associados sem duplicar raw media.

## 30. Copilot Inbox

Materializa:

```text
waiting_for_user
working
completed
alerts
meeting candidate actions
```

É surface/projection, não outro workflow engine.

## 31. Copilot Watch

```text
OBSERVE
ADVISE
ACT
```

Event/condition-driven quando possível, com dedupe/cooldown/expiry/permission revalidation.

ACT somente em C7 com autonomy policy adequada.

## 32. Simulation

```text
SIMULATE != APPLY
```

Somente modelos/cálculos com owner, premissas e reproducibility. Apply é nova Business Action governada.

## 33. Model Router / Advanced realtime

Model Router é introduzido somente após baseline de quality/cost/latency.

Classes possíveis:

```text
FAST
STANDARD
DEEP_REASONING
MULTIMODAL
LONG_CONTEXT
REALTIME_MEDIA quando justificado
```

Advanced realtime media em C7 exige budgets, backpressure, network-degraded behavior, concurrency e cost telemetry.

## 34. Iframe integration

Classes:

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

Bridge é para contexto/experiência. Business Action continua por API/OpenAPI.

## 35. Autonomia

| Nível | Comportamento |
|---|---|
| L0 | explicar |
| L1 | navegar |
| L2 | consultar/analisar |
| L3 | preparar mudança |
| L4 | executar governado |
| L5 | execute explicit allowlist dentro de limites |

L5 OFF por default.

Autonomia empresarial não autoriza atuação física de máquina.

## 36. Industrial/OT safety

Default:

```text
Copilot → observe/read/explain/recommend
Copilot → prepare governed enterprise action
Copilot -X→ arbitrary physical machine command
```

Qualquer future OT actuation requer gate separado com industrial owner, typed deterministic commands, allowlist, state/preconditions, independent safety PLC/interlocks, human authorization, simulation/test environment, fail-safe e audit.

LLM não substitui safety system.

## 37. Quality/inspection safety

Computer vision pode gerar finding/evidence, mas não aprova/reprova peça por default quando o processo exige medição/tolerância/equipamento/autoridade oficial.

```text
visual finding
→ Evidence/Hypothesis
→ official inspection rule/data
→ authorized decision
```

## 38. Privacy / media / shared devices

Obrigatório:

- capture visível;
- purpose/consent/policy;
- transcript/raw-audio/raw-video/screen/derived Evidence com lifecycles separados;
- data minimization;
- shared-device user isolation;
- user identity != device identity;
- no facial recognition/emotion detection/hidden surveillance por default.

## 39. Administração/Observabilidade

Governar/observar:

- capabilities/actions;
- OpenAPI sources;
- apps readiness;
- expertise/playbooks;
- knowledge/evidence quality;
- workflows/tasks/cases/watch;
- Meeting/Frontline sessions/artifacts;
- media providers/retention/budgets;
- Decision Gates;
- model usage;
- latency/cost/failure/retry;
- rollout/cohorts;
- privacy incidents;
- kill switch;
- audit.

Sem CoT.

## 40. AI-ready onboarding

Níveis conceituais:

```text
L1 discoverable
L2 context-ready
L3 read-ready
L4 write-ready
L5 workflow-ready
```

Checklist: routes/RBAC, API/OpenAPI, EntityRef/deep-link, WorkspaceContext, evidence, sensitivity/Decision, evals, iframe class.

Frontline-ready pode exigir adicionalmente shared-device/media/context requirements.

## 41. Activity

Mostrar operações e estado, não reasoning privado:

```text
Planejando
Aplicando expertise
Consultando dados
Analisando documento
Ouvindo/Transcrevendo
Analisando imagem/vídeo
Aguardando decisão
Monitorando evento
Concluído
```

## 42. Erros

Distinguir:

- unauthorized;
- not found;
- missing requirement;
- policy blocked;
- pending decision;
- backend unavailable;
- partial failure;
- ambiguous outcome;
- stale evidence;
- unsupported simulation;
- waiting/expired workflow;
- incompatible bridge;
- unavailable capability;
- media permission denied;
- media/provider unavailable;
- retention/policy blocked;
- shared-device session invalid;
- industrial safety blocked.

Nunca narrar success sem verified outcome.

## 43. Não-funcionais

- independent deployment/rollback;
- security by default;
- Clean Architecture/Ports & Adapters;
- accessibility/responsive/large-touch UX;
- observability/auditability;
- data minimization/LGPD;
- versioned contracts;
- idempotency/resilience;
- media/realtime budgets;
- no duplicate authorities;
- generalization tests;
- no Chat runtime dependency;
- explicit industrial safety boundary.

## 44. Fora de escopo/default

- transformar Chat em Copilot;
- migrar Chat agents/sessions;
- depender do Chat API;
- unrestricted desktop/browser control;
- DOM automation as business integration;
- superuser Copilot identity;
- global L5 autonomy;
- automatic production learning;
- automatic endpoint creation;
- multi-agent departmental product UX;
- hidden audio/video capture;
- facial/emotion surveillance;
- raw-media retention sem purpose;
- free-form LLM→PLC/CNC/robot control;
- substituir industrial safety interlocks.

## 45. Reference scenarios

### Contextual read
> “Explique este cliente e compare com o mês passado.”

### Cross-domain
> “Para este item, compare estoque, compras, produção e carteira.”

### Multimodal
> “Analise este desenho e destaque riscos de fabricação.”

### Meeting
> “Copilot, mostre a produção de ontem da Linha 2. Ao final gere a ata e me mostre as ações propostas antes de criá-las.”

### Frontline
> “Estou nesta operação, não consigo encaixar o terminal. Mostre a revisão correta, veja se já aconteceu e me ajude a registrar o problema.”

### Governed write
> “Crie uma solicitação para Compras revisar este item.”

### Durable investigation
> “Investigue a reclamação, monte um 8D e acompanhe até Engenharia liberar nova revisão.”

### Proactive
> “Me avise quando a nova revisão chegar e reanalise o caso.”

## 46. Anchor scenario

```text
reclamação
→ Case
→ Business Graph
→ drawing analysis
→ Evidence Board
→ Engineering + Quality Expertise
→ 8D Playbook
→ Task/Durable Workflow
→ wait_event
→ Watch/Inbox
→ reanalysis
→ Decision Gate
→ Domain API Action
→ Outcome/Evidence/Audit
→ Experience candidate
```

Tudo executado pela Copilot API própria.

## 47. Product Complete

O release completo exige, para o escopo declarado:

- standalone API/MFE/deploy confirmed;
- Chat-offline independence;
- Portal/Core/Gateway integration;
- navigation/context;
- intelligence core;
- reads/evidence;
- multimodal foundations quando incluídas;
- writes/Decision Gates conforme release;
- durable work/proactivity conforme release;
- Meeting/Frontline gates quando incluídos;
- media/privacy/shared-device compliance;
- industrial safety boundary;
- security/evals/generalization;
- observability/rollback;
- CP coverage;
- no hidden Chat fallback.

Estado real vive no execution ledger.