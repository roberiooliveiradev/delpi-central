# Minha DELPI Copilot — Especificação Funcional e Técnica Completa

**Status:** especificação canônica de produto  
**Produto:** aplicação standalone nova  
**Boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Ordem:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Rastreabilidade:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)

## 1. Definição

O Minha DELPI Copilot é a **camada inteligente operacional da empresa implementada como aplicação independente dentro da Minha DELPI**.

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

> Entender o contexto da organização, conectar dados, pessoas, processos e aplicações, investigar problemas, executar trabalho, acompanhar resultados e transformar conhecimento empresarial em ação governada.

```text
PERGUNTAR  → entender, pesquisar, explicar, analisar
FAZER      → abrir, consultar, criar, alterar, aprovar, executar
ACOMPANHAR → monitorar, detectar, alertar, reagir
TRABALHAR  → investigar, colaborar, planejar, acompanhar, concluir
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
→ inteligência/orquestração/trabalho/evidence
```

O Portal é host, não runtime inteligente. Core é authority de permissões, não banco do Copilot. Domain APIs continuam donas do negócio.

## 3. Superfícies

### Full page

Aplicação registrada como MFE federado para:

- conversas longas;
- Tasks/Cases;
- artifacts;
- evidence boards;
- administration;
- workflows extensos.

### Global side panel

Portal hospeda o mesmo MFE/runtime para acesso contextual de qualquer app.

O painel não é segundo frontend nem segundo estado do produto.

### Contextual app/iframe

MFEs/iframes podem publicar `WorkspaceContext` e receber Platform Commands tipados.

### Inbox / Case / Room

Surfaces de trabalho persistente, sempre usando a mesma Copilot API.

## 4. Copilot único

Existe um único Copilot. Domínios especializam o runtime por:

- Expertise Packs;
- Domain Playbooks;
- Knowledge scopes;
- project/preferences;
- authorized capabilities;
- multimodal tools.

Não existe agent runtime por departamento.

## 5. Conversa e entendimento

- PT-BR natural;
- pedidos longos/compostos;
- follow-up contextual;
- goal decomposition;
- entity resolution;
- clarify somente quando necessário;
- structured references/memory;
- sem chain-of-thought persistida/exposta.

Conversations/turns são Copilot-owned e não usam sessions/agent_id do Chat.

## 6. Workspace Context

```text
appId
routeId
entityRefs
filters
selection
dateRange
visibleDataRefs
source
```

Bounded/sanitized. Não concede permission.

## 7. Navegação / Platform Commands

- abrir app;
- abrir rota;
- abrir entidade;
- back/history;
- select/focus view;
- aplicar filtro visual quando app declarar suporte.

LLM escolhe target lógico; Portal resolve rota autorizada. URL arbitrária é proibida.

## 8. Capability architecture

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

## 9. Business Reads

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

## 10. Business Writes

Quando Domain API/policy permitir:

- criar;
- editar;
- aprovar/rejeitar;
- atribuir;
- comentar;
- cancelar/arquivar;
- iniciar processo;
- demais operations reais.

Nunca usar DOM automation como substituto de API.

## 11. Decision Gates

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Consideram risk, sensitivity, impact, evidence, arguments hash, expiry, autonomy e approver requirements.

## 12. Entity model e DELPI Business Graph

`EntityRef` e `RelationshipRef` conectam semanticamente domínios:

```text
reclamação
→ produto
→ desenho/revisão
→ OP/lote
→ material
→ fornecedor
→ inspeções
→ não conformidade
→ plano de ação
```

Graph guarda refs/relationships/provenance, não master copies dos dados.

## 13. Evidence / Epistemic UX

Distinguir:

```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

Evidence pode carregar source, entity refs, freshness, page/region, confidence, limitations, extractor/model version.

## 14. Expertise Packs

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

## 15. Domain Playbooks

Métodos versionados como:

- 8D;
- root cause;
- drawing review;
- FMEA;
- shortage/delay analysis;
- outros processos corporativos.

Playbook orienta stages/evidence/criteria. Planner resolve capabilities reais.

## 16. Knowledge

- Reference Knowledge;
- Operational Knowledge;
- Decision Knowledge;
- Experience Knowledge;
- Semantic Knowledge.

Knowledge/RAG runtime é próprio do Copilot e respeita ACL/source provenance.

## 17. Multimodalidade

Suportar conforme tools:

- PDF;
- imagens;
- desenhos técnicos;
- planilhas/documentos;
- fotos de defeito;
- certificados/relatórios.

```text
attachment
→ native extraction/OCR/Vision
→ structured Evidence
→ Expertise/Playbook
→ optional API/Knowledge reads
→ grounded synthesis
```

A implementação é nova na Copilot API. O pipeline existente do Chat pode ser estudado, mas não é runtime dependency.

## 18. Governed Learning / Expertise Studio

```text
feedback/case outcome
→ candidate
→ expert review
→ eval
→ version
→ publish
→ canary/rollback
```

Nunca auto-publicar comportamento de produção a partir de correção do usuário.

Expertise Studio gerencia Packs/Playbooks, não agents.

## 19. Workflow / Durable Runtime

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

## 20. Copilot Task

Unidade operacional curta/média backed pelo Durable Workflow Runtime.

Mostra objective/status/progress/pending decisions/results/evidence/entity links.

## 21. Copilot Case

Unidade de investigação/trabalho prolongado com:

- entity refs;
- Evidence Board;
- hypotheses;
- decisions;
- actions;
- Tasks/Workflows;
- timeline;
- room ref;
- artifacts.

Não substitui source permissions.

## 22. Interaction Rooms

C0 deve inventariar a infraestrutura já existente — incluindo salas do Portal Comercial — antes de decidir `REUSE | EXTEND | ADAPTER | CREATE_REQUIRED`.

Room membership não concede acesso aos sources relacionados.

## 23. Copilot Inbox

Materializa:

```text
waiting_for_user
working
completed
alerts
```

É surface/projection, não outro workflow engine.

## 24. Copilot Watch

```text
OBSERVE
ADVISE
ACT
```

Event/condition-driven quando possível, com dedupe/cooldown/expiry/permission revalidation.

ACT somente em C7 com autonomy policy adequada.

## 25. Simulation

```text
SIMULATE != APPLY
```

Somente modelos/cálculos com owner, premissas e reproducibility. Apply é nova Business Action governada.

## 26. Model Router

Introduzido somente após baseline de quality/cost/latency.

Classes possíveis:

```text
FAST
STANDARD
DEEP_REASONING
MULTIMODAL
LONG_CONTEXT
```

Provider/model selection segue Compute Policy e data policy.

## 27. Iframe integration

Classes:

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

Bridge é para contexto/experiência. Business Action continua por API/OpenAPI.

## 28. Autonomia

| Nível | Comportamento |
|---|---|
| L0 | explicar |
| L1 | navegar |
| L2 | consultar/analisar |
| L3 | preparar mudança |
| L4 | executar governado |
| L5 | execute explicit allowlist dentro de limites |

L5 OFF por default.

## 29. Administração/Observabilidade

Governar/observar:

- capabilities/actions;
- OpenAPI sources;
- apps readiness;
- expertise/playbooks;
- knowledge/evidence quality;
- workflows/tasks/cases/watch;
- Decision Gates;
- model usage;
- latency/cost/failure/retry;
- rollout/cohorts;
- kill switch;
- audit.

Sem CoT.

## 30. AI-ready onboarding

Níveis conceituais:

```text
L1 discoverable
L2 context-ready
L3 read-ready
L4 write-ready
L5 workflow-ready
```

Checklist: routes/RBAC, API/OpenAPI, EntityRef/deep-link, WorkspaceContext, evidence, sensitivity/Decision, evals, iframe class.

## 31. Activity

Mostrar operações e estado, não reasoning privado:

```text
Planejando
Aplicando expertise
Consultando dados
Analisando documento
Aguardando decisão
Monitorando evento
Concluído
```

## 32. Erros

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
- unavailable capability.

Nunca narrar success sem verified outcome.

## 33. Não-funcionais

- independent deployment/rollback;
- security by default;
- Clean Architecture/Ports & Adapters;
- accessibility/responsive UX;
- observability/auditability;
- data minimization/LGPD;
- versioned contracts;
- idempotency/resilience;
- no duplicate authorities;
- generalization tests;
- no Chat runtime dependency.

## 34. Fora de escopo

- transformar Chat em Copilot;
- migrar Chat agents/sessions;
- depender do Chat API;
- unrestricted desktop/browser control;
- DOM automation as business integration;
- superuser Copilot identity;
- global L5 autonomy;
- automatic production learning;
- automatic endpoint creation;
- multi-agent departmental product UX.

## 35. Reference scenarios

### Contextual read
> “Explique este cliente e compare com o mês passado.”

### Cross-domain
> “Para este item, compare estoque, compras, produção e carteira.”

### Multimodal
> “Analise este desenho e destaque riscos de fabricação.”

### Governed write
> “Crie uma solicitação para Compras revisar este item.”

### Durable investigation
> “Investigue a reclamação, monte um 8D e acompanhe até Engenharia liberar nova revisão.”

### Proactive
> “Me avise quando a nova revisão chegar e reanalise o caso.”

## 36. Anchor scenario

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

## 37. Product Complete

O release completo exige:

- standalone API/MFE/deploy confirmed;
- Chat-offline independence;
- Portal/Core/Gateway integration;
- navigation/context;
- intelligence core;
- reads/evidence;
- writes/Decision Gates conforme release;
- durable work/proactivity conforme release;
- security/evals/generalization;
- observability/rollback;
- CP coverage;
- no hidden Chat fallback.

Estado real vive no execution ledger.