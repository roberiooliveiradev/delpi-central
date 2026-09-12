# Minha DELPI Copilot — Especificação Funcional e Técnica Completa

**Status:** especificação canônica de produto  
**Produto:** aplicação standalone nova  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Rastreabilidade:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)

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
→ apps/rotas/RBAC/governança/user authority

Gateway
→ rota Copilot MFE/API

Domain APIs
→ dados/regras/actions reais

plugin-ui
→ design system

Copilot API
→ inteligência/orquestração/trabalho/evidence/media/biometric capabilities
```

O Portal é host, não runtime inteligente. Core é authority de permissões/usuários corporativos, não banco do Copilot. Domain APIs continuam donas do negócio.

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
Sessão assistida para reunião presencial/remota com voz, transcrição, screen/camera quando autorizados, dados reais, participant identity quando governada, decisões, ata e ações candidatas.

### Frontline
Experiência simplificada para operador/técnico/inspetor no posto, priorizando voz hands-free, touch, câmera, desenho/procedimento, contexto operacional e identity assistance governada quando habilitada.

Todas são surfaces do mesmo MFE/runtime.

## 5. Copilot único

Existe um único Copilot. Domínios especializam o runtime por Expertise Packs, Domain Playbooks, Knowledge scopes, project/preferences, authorized capabilities e multimodal tools.

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

Modalidade de entrada ou biometric identity não alteram esse pipeline de autorização/execução.

## 10. Business Reads

Consultar, conforme APIs onboarded, comercial, suprimentos, produção, qualidade, financeiro, engenharia, manutenção, solicitações e demais domínios.

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

Biometric match não substitui actor/approver autenticado.

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

Graph guarda refs/relationships/provenance, não master copies dos dados nem profiles biométricos de pessoas.

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

Fornecem terminology, signals, analysis guidance, evidence expectations, preferred playbooks, knowledge refs, multimodal needs e output guidance.

Não concedem RBAC nem definem endpoints como authority.

## 16. Domain Playbooks

Métodos versionados como 8D, root cause, drawing review, FMEA, shortage/delay analysis, trabalho padronizado e outros processos corporativos.

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

Voice pode oferecer STT, TTS, hands-free commands, correction/repeat, meeting discussion e frontline assistance.

Invariante:

```text
voice authorization = typed authorization
```

Voz nunca reduz Decision Gate.

Speaker recognition é capability distinta de STT e não autoriza write por si só.

## 20. Camera/image/video

Camera e vídeo podem auxiliar mostrar peça/defeito, localizar região, comparar referência, analisar desenho, coletar Evidence, acompanhar operação autorizada, reconhecer usuário enrolled quando capability estiver habilitada e apoiar treinamento contextual.

Progressão:

```text
image/frame
→ short video
→ sampled assisted session
→ advanced realtime only after C7 evidence
```

Não armazenar vídeo contínuo indiscriminadamente.

## 21. Biometric Identity

O Copilot pode reconhecer/confirmar **usuários conhecidos e previamente enrolled** por face e voz sob governança explícita.

Pipeline alvo:

```text
explicit enrollment
→ protected biometric template
→ current face/voice sample
→ closed-set candidate match
→ confidence + policy + liveness when required
→ correctable userRef association
```

Invariantes:

```text
biometric match != authenticated session
biometric match != Core permission
biometric match != Business Action authorization
```

Requisitos:

- enrollment explícito/revogável/versionado;
- unknown/low-confidence permanece desconhecido ou pede confirmação;
- template protegido e nunca ordinary log data;
- correction não re-enrolla silenciosamente;
- revoke/delete impede uso futuro;
- anti-spoof/liveness quando a finalidade exigir confiança adicional;
- no open-world/indiscriminate identification por default.

## 22. Human Observation

O Copilot pode analisar **padrões objetivos e observáveis relacionados ao processo**, por exemplo:

- sequência de etapas;
- interação com máquina/ferramenta/material;
- repetição/retrabalho;
- tempos entre etapas;
- deslocamentos relevantes ao fluxo;
- pedidos de ajuda;
- uso observável de EPI ou ergonomia quando houver método/owner formal.

Esses resultados são Evidence/Hypothesis/process signals.

Por default, não inferir de face/voice/video/behavior:

- personalidade;
- honestidade/confiabilidade;
- intenção moral/lealdade;
- emoção como truth;
- saúde/diagnóstico;
- atributos sensíveis;
- aptidão profissional global;
- propensão disciplinar.

Biometria/Human Observation não são authority automática para contratação, promoção, punição, remuneração, avaliação formal, suspensão ou desligamento.

## 23. Meeting Mode

Meeting Mode deve permitir, conforme device/policy:

- explicit start/stop;
- mic/transcription;
- camera/screen optional;
- face/speaker participant association quando habilitada;
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
identity candidate/confirmed participant
source data/evidence
human-confirmed decision
candidate action
executed/verified action
```

Ação citada na reunião não é executada automaticamente.

## 24. Frontline Mode

Frontline atende operador/técnico/inspetor/manutenção com:

- UI large-touch/simplificada;
- shared-device safe session;
- optional biometric identity assistance;
- OP/machine/product/operation context;
- hands-free voice;
- camera/image;
- drawing/procedure current revision;
- quality/maintenance history;
- Human Observation bounded ao processo;
- contextual training;
- register issue/escalate;
- Task/Case linkage.

Biometric identity reduz fricção, mas sessão/RBAC continuam authoritative.

## 25. Training assistance

Copilot pode orientar passo a passo e explicar procedimento/desenho, mas não concede qualificação/certificação oficial automaticamente.

Source/revision vigente deve ser visível quando material.

## 26. Process learning / conhecimento tácito

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

Não criar perfil secreto do trabalhador como mecanismo de aprendizagem.

## 27. Governed Learning / Expertise Studio

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

## 28. Workflow / Durable Runtime

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

## 29. Copilot Task

Unidade operacional curta/média backed pelo Durable Workflow Runtime.

Mostra objective/status/progress/pending decisions/results/evidence/entity links/meeting/frontline refs quando aplicável.

## 30. Copilot Case

Unidade de investigação/trabalho prolongado com entity refs, Evidence Board, hypotheses, decisions, actions, Tasks/Workflows, timeline, room ref, artifacts e meeting/frontline refs.

Não substitui source permissions.

## 31. Interaction Rooms

C0 deve inventariar a infraestrutura já existente — incluindo salas do Portal Comercial — antes de decidir `REUSE | EXTEND | ADAPTER | CREATE_REQUIRED`.

Room membership não concede acesso aos sources relacionados.

Meeting artifacts podem ser associados sem duplicar raw media/template biométrico.

## 32. Copilot Inbox

Materializa `waiting_for_user`, `working`, `completed`, `alerts` e meeting candidate actions.

É surface/projection, não outro workflow engine.

## 33. Copilot Watch

```text
OBSERVE
ADVISE
ACT
```

Event/condition-driven quando possível, com dedupe/cooldown/expiry/permission revalidation.

ACT somente em C7 com autonomy policy adequada.

## 34. Simulation

```text
SIMULATE != APPLY
```

Somente modelos/cálculos com owner, premissas e reproducibility. Apply é nova Business Action governada.

## 35. Model Router / Advanced realtime

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

Advanced realtime media/biometric em C7 exige budgets, backpressure, network-degraded behavior, concurrency, privacy/security e cost telemetry.

## 36. Iframe integration

Classes:

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

Bridge é para contexto/experiência. Business Action continua por API/OpenAPI.

## 37. Autonomia

| Nível | Comportamento |
|---|---|
| L0 | explicar |
| L1 | navegar |
| L2 | consultar/analisar |
| L3 | preparar mudança |
| L4 | executar governado |
| L5 | execute explicit allowlist dentro de limites |

L5 OFF por default.

Autonomia empresarial não autoriza atuação física de máquina nem reduz requisitos biométricos/autorizativos.

## 38. Industrial/OT safety

Default:

```text
Copilot → observe/read/explain/recommend
Copilot → prepare governed enterprise action
Copilot -X→ arbitrary physical machine command
```

Qualquer future OT actuation requer gate separado com industrial owner, typed deterministic commands, allowlist, state/preconditions, independent safety PLC/interlocks, human authorization, simulation/test environment, fail-safe e audit.

LLM não substitui safety system.

## 39. Quality/inspection safety

Computer vision pode gerar finding/evidence, mas não aprova/reprova peça por default quando o processo exige medição/tolerância/equipamento/autoridade oficial.

```text
visual finding
→ Evidence/Hypothesis
→ official inspection rule/data
→ authorized decision
```

## 40. Privacy / media / biometric / shared devices

Obrigatório:

- capture e identity-recognition visíveis;
- purpose/consent/policy;
- transcript/raw-audio/raw-video/screen/derived Evidence/biometric templates com lifecycles separados;
- data minimization;
- protected biometric storage;
- shared-device user isolation;
- user identity != device identity;
- biometric candidate != authenticated session;
- no open-world/indiscriminate recognition por default;
- no emotion/personality/trustworthiness/sensitive inference;
- no hidden worker scoring/profiling;
- no automatic employment decision from biometrics.

## 41. Administração/Observabilidade

Governar/observar:

- capabilities/actions;
- OpenAPI sources;
- apps readiness;
- expertise/playbooks;
- knowledge/evidence quality;
- workflows/tasks/cases/watch;
- Meeting/Frontline sessions/artifacts;
- media/biometric providers/retention/budgets;
- enrollment/revocation/template lifecycle;
- biometric false accept/reject/unknown/correction metrics;
- Decision Gates;
- model usage;
- latency/cost/failure/retry;
- rollout/cohorts;
- privacy incidents;
- kill switch;
- audit.

Sem CoT e sem person scoring subjetivo.

## 42. AI-ready onboarding

Níveis conceituais:

```text
L1 discoverable
L2 context-ready
L3 read-ready
L4 write-ready
L5 workflow-ready
```

Checklist: routes/RBAC, API/OpenAPI, EntityRef/deep-link, WorkspaceContext, evidence, sensitivity/Decision, evals, iframe class.

Frontline-ready pode exigir adicionalmente shared-device/media/context/biometric requirements.

## 43. Activity

Mostrar operações e estado, não reasoning privado:

```text
Planejando
Aplicando expertise
Consultando dados
Ouvindo/Transcrevendo
Analisando imagem/vídeo
Reconhecendo participante
Identidade não confirmada
Aguardando decisão
Monitorando evento
Concluído
```

## 44. Erros

Distinguir unauthorized, not found, missing requirement, policy blocked, pending decision, backend unavailable, partial failure, ambiguous outcome, stale evidence, unsupported simulation, waiting/expired workflow, incompatible bridge, unavailable capability, media permission denied, media/provider unavailable, biometric identity unknown/ambiguous, biometric policy blocked, retention/policy blocked, shared-device session invalid e industrial safety blocked.

Nunca narrar success sem verified outcome.

## 45. Não-funcionais

- independent deployment/rollback;
- security by default;
- Clean Architecture/Ports & Adapters;
- accessibility/responsive/large-touch UX;
- observability/auditability;
- data minimization/LGPD;
- biometric template protection;
- versioned contracts;
- idempotency/resilience;
- media/realtime budgets;
- no duplicate authorities;
- generalization tests;
- no Chat runtime dependency;
- explicit industrial safety boundary.

## 46. Fora de escopo/default

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
- hidden audio/video/identity recognition;
- open-world/indiscriminate facial recognition;
- emotion/personality/honesty/character inference from face/voice;
- sensitive-attribute inference;
- hidden person/employee scoring;
- automatic employment decision from biometrics/Human Observation;
- raw-media/template retention sem purpose;
- free-form LLM→PLC/CNC/robot control;
- substituir industrial safety interlocks.

## 47. Reference scenarios

### Contextual read
> “Explique este cliente e compare com o mês passado.”

### Cross-domain
> “Para este item, compare estoque, compras, produção e carteira.”

### Multimodal
> “Analise este desenho e destaque riscos de fabricação.”

### Meeting
> “Copilot, mostre a produção de ontem da Linha 2. Ao final gere a ata e me mostre as ações propostas antes de criá-las.”

### Biometric Meeting
> “Identifique os participantes enrolled desta reunião, associe os speakers quando houver confiança suficiente e me deixe corrigir qualquer associação.”

### Frontline
> “Estou nesta operação, não consigo encaixar o terminal. Mostre a revisão correta, veja se já aconteceu e me ajude a registrar o problema.”

### Process observation
> “Durante esta sessão autorizada, identifique etapas repetidas, esperas e pedidos de ajuda e gere hipóteses de melhoria do processo — não uma avaliação da pessoa.”

### Governed write
> “Crie uma solicitação para Compras revisar este item.”

### Durable investigation
> “Investigue a reclamação, monte um 8D e acompanhe até Engenharia liberar nova revisão.”

## 48. Product Complete

O release completo exige, para o escopo declarado:

- standalone API/MFE/deploy confirmed;
- Chat-offline independence;
- Portal/Core/Gateway integration;
- navigation/context;
- intelligence core;
- reads/evidence;
- multimodal foundations quando incluídas;
- biometric foundation/governance quando incluída;
- writes/Decision Gates conforme release;
- durable work/proactivity conforme release;
- Meeting/Frontline gates quando incluídos;
- media/privacy/shared-device/biometric compliance;
- no sensitive person inference/automatic employment decision;
- industrial safety boundary;
- security/evals/generalization;
- observability/rollback;
- CP coverage;
- no hidden Chat fallback.

Estado real vive no execution ledger.
