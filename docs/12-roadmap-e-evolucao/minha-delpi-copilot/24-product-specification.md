# Minha DELPI Copilot — Especificação Funcional e Técnica Completa

**Status:** especificação canônica de produto  
**Ordem de implantação:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Rastreabilidade:** [`25-requirements-traceability.md`](./25-requirements-traceability.md)

## 1. Definição

O Minha DELPI Copilot é a **camada inteligente operacional da empresa**.

Não é apenas um chatbot e não substitui os Portais. Ele conecta aplicações, dados, pessoas, conhecimento, decisões e trabalho persistente sob as mesmas regras de segurança da Minha DELPI.

North Star:

> Entender o contexto da organização, conectar dados, pessoas, processos e aplicações, investigar problemas, executar trabalho, acompanhar resultados e transformar conhecimento empresarial em ação governada.

Quatro verbos do produto:

```text
PERGUNTAR  → entender, pesquisar, explicar, analisar
FAZER      → abrir, consultar, criar, alterar, aprovar, executar
ACOMPANHAR → monitorar, detectar, lembrar, alertar, reagir
TRABALHAR  → investigar, colaborar, planejar, acompanhar ações, concluir
```

## 2. Princípio do Copilot único

Existe **um único Minha DELPI Copilot**.

Engenharia, Qualidade, Suprimentos, Comercial, Financeiro, RH e demais áreas não criam novos runtimes/agentes de produto. Especialização ocorre por:

- Expertise Packs;
- Domain Playbooks;
- knowledge scopes;
- project preferences;
- capabilities autorizadas;
- multimodal tools.

Workers internos especializados podem existir como detalhe de implementação, sem criar identidades de produto ou authorities paralelas.

## 3. Superfícies

### 3.1 Painel lateral global

- conversa;
- contexto da tela;
- activity;
- evidence/sources;
- decisions/approvals;
- ações “abrir no app”;
- continuidade entre apps quando permitido.

### 3.2 Página completa

- análises longas;
- Tasks;
- Cases;
- artefatos;
- histórico;
- workflows extensos;
- evidence boards;
- comparação multi-domínio.

### 3.3 Entrada contextual MFE

App publica `WorkspaceContext`; Shell abre o Copilot central.

### 3.4 Entrada contextual iframe

Usa `Iframe Copilot Bridge` conforme classe `PORTAL_ONLY | CONTEXTUAL | INTERACTIVE | AI_READY`.

### 3.5 Inbox

Centraliza:

```text
waiting_for_user
working
completed
alerts
```

### 3.6 Case/Room

Investigações/trabalho colaborativo persistente com pessoas + Copilot + arquivos + evidence + decisões + ações.

## 4. Conversa e entendimento

- PT-BR natural;
- pedidos longos/compostos;
- follow-up contextual;
- decomposição em goals/subtasks;
- clarify somente para requisito realmente ausente;
- entity resolution;
- structured memory/reference;
- sem chain-of-thought exposta/persistida.

## 5. Navegação

Capabilities visuais genéricas:

- abrir app;
- abrir rota;
- abrir entidade;
- voltar;
- selecionar aba/view;
- aplicar filtro visual;
- focar entidade/seção;
- deep link resultante.

LLM escolhe target lógico autorizado; Portal resolve URL/rota.

## 6. Workspace Context

Quando disponível:

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

Contexto é bounded, sanitizado e não concede permission.

## 7. Entidades e DELPI Business Graph

O produto usa `EntityRef` canônico e relações com provenance para navegar semanticamente entre domínios.

Exemplo:

```text
reclamação
→ produto
→ desenho/revisão
→ OP/lote
→ matéria-prima
→ fornecedor
→ inspeções
→ não conformidades
→ plano de ação
```

O Business Graph:

- armazena referências/relações, não cópia integral dos dados;
- distingue authoritative vs inferred relationship;
- respeita RBAC;
- busca dados atuais na source API;
- possui depth/cycle budget.

## 8. Business Reads

O Copilot consulta somente Business Actions autorizadas via OpenAPI + Action Catalog.

Abrange, conforme APIs disponíveis:

- comercial;
- suprimentos;
- produção;
- qualidade;
- financeiro;
- engenharia;
- manutenção;
- solicitações;
- demais domínios onboarded.

A lista não é hardcoded no planner.

## 9. Business Writes

Quando o domínio/API/policy permitir:

- criar;
- editar;
- aprovar/rejeitar;
- atribuir;
- comentar;
- cancelar/arquivar;
- iniciar processo;
- demais actions reais.

Fluxo:

```text
intent
→ grounded args
→ schema validation
→ RBAC/policy
→ impact preview
→ Decision Gate
→ revalidation
→ execute
→ verify outcome
→ evidence/audit/deep link
```

Nunca substituir Business Action por DOM automation.

## 10. Decision Gates

Governança proporcional ao risco:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Considera:

- risk/sensitivity;
- value/impact;
- operation type;
- evidence;
- autonomy policy;
- arguments hash;
- expiry;
- approver/RBAC quando aplicável.

## 11. Análise e Epistemic UX

O Copilot deve distinguir visual e semanticamente:

```text
FACT
CALCULATION
HYPOTHESIS
CONCLUSION
RECOMMENDATION
```

Regras:

- fato material aponta source/evidence quando disponível;
- cálculo expõe inputs/método suficiente;
- hipótese não vira certeza;
- conclusão mostra evidências e limitações;
- recomendação não é ação executada.

## 12. Evidence & Provenance

Cada evidence relevante pode carregar:

```text
sourceRef
entityRefs
observedAt/freshness
confidence quando aplicável
page/region/location quando multimodal
limitations
extractor/model version quando material
```

Conflito ou staleness deve aparecer na síntese.

## 13. Expertise Packs

Expertise Pack define conhecimento operacional especializado, não permissão.

Pode fornecer:

- terminologia;
- domain signals;
- analysis guidance;
- evidence expectations;
- preferred playbooks;
- knowledge scope refs sujeitos a ACL;
- multimodal needs;
- output guidance.

Não pode conter endpoint técnico/permission override como authority.

## 14. Domain Playbooks

Representam métodos como:

- 8D;
- causa raiz;
- análise de desenho;
- FMEA;
- análise de atraso;
- outros métodos corporativos versionados.

Playbook fornece stages/evidence/criteria e o planner resolve capabilities autorizadas.

## 15. Multimodalidade

Suportar, conforme tools:

- PDF;
- imagem;
- desenho técnico;
- planilha/documento;
- foto de defeito;
- certificados/relatórios;
- outros formatos futuros.

Pipeline:

```text
attachment
→ native extraction/OCR/VLM conforme necessidade
→ structured evidence + provenance/confidence
→ expertise/playbook
→ optional API/knowledge reads
→ grounded synthesis
```

Percepção não é conclusão de domínio.

## 16. Knowledge

Camadas conceituais:

- Reference Knowledge — normas/manuais/procedimentos;
- Operational Knowledge — como processos funcionam;
- Decision Knowledge — decisões e justificativas auditáveis, sem CoT;
- Experience Knowledge — casos anteriores aprovados;
- Semantic Knowledge — entidades/relações.

Visibility continua sujeita a ACL.

## 17. Governed Learning

Fluxo:

```text
feedback/case resolution
→ candidate improvement
→ review
→ eval
→ version
→ publish
→ canary/rollout
```

Nunca:

```text
user correction → automatic production prompt/model change
```

## 18. Expertise Studio

Administração governada de Expertise Packs, Playbooks e padrões relacionados:

```text
draft
→ review
→ eval
→ published
→ deprecated/rollback
```

Não é “criador de agentes”.

## 19. Workflows

O Copilot pode executar objetivos compostos com `PLAN → ACT → OBSERVE → UPDATE`.

Workflow possui:

- steps;
- dependencies;
- capability refs;
- preconditions;
- expected outcomes;
- decision boundaries;
- budgets/limits;
- checkpoints.

Reads podem ser paralelizados quando seguros. Writes seguem policy/idempotency.

## 20. Durable Workflow Runtime

Para trabalho que cruza request/reload/tempo:

```text
wait_user
wait_approval
wait_event
wait_time
resume
retry seguro
cancel
timeout
checkpoint
```

Deve sobreviver a restart sem repetir write.

## 21. Copilot Task

Unidade operacional curta/média.

Mostra:

- objetivo;
- status/progress;
- steps;
- pending decisions;
- result/evidence refs;
- links para entidades/Case.

Não possui executor próprio: usa Durable Workflow Runtime.

## 22. Copilot Case

Unidade de investigação/trabalho prolongado.

Pode conter:

- objetivo;
- entity refs;
- evidence board;
- hypotheses;
- decisions;
- actions;
- Tasks/Workflows;
- timeline;
- room ref;
- artifacts.

Case não substitui source system nem source permissions.

## 23. Evidence Board

Organiza os mesmos `EvidenceRef` em estados como:

```text
accepted
contested
missing
superseded
```

Não cria outro modelo de evidence.

## 24. Interaction Rooms

Preferir o padrão de salas existente da Minha DELPI.

Funções:

- participantes;
- mensagens;
- arquivos;
- decisões;
- pending actions;
- Copilot contextual;
- resumo grounded;
- Case link.

Membership da sala não concede automaticamente acesso a dados fonte.

## 25. Copilot Inbox

Materializa trabalho que exige atenção:

- decisões/aprovações;
- Tasks esperando usuário;
- Cases relevantes;
- workflows em andamento/concluídos;
- alerts/Watch.

Inbox é superfície, não novo workflow engine.

## 26. Copilot Watch

Três modos:

```text
OBSERVE
ADVISE
ACT
```

Watch pode ser disparado por evento/condição autorizada.

Obrigatório:

- dedupe/cooldown;
- expiry/disable;
- revalidar permission/policy;
- payload não confiável;
- ACT somente com autonomia/policy/Decision Gate adequados.

## 27. Event-driven interaction

Preferir eventos da plataforma quando disponíveis. Não criar polling app-specific no Copilot core quando houver owner/event source melhor.

`EventEnvelope` compartilhado serve para workflow resume, Watch e observabilidade correlacionada.

## 28. What-if / Simulation

Perguntas como:

- “e se esse fornecedor atrasar mais 5 dias?”;
- “se eu priorizar essa OP, o que muda?”

Só podem usar modelo/cálculo com owner e premissas explícitas.

```text
SIMULATE != APPLY
```

Apply é nova Business Action governada.

## 29. Model Router / Compute Policy

Depois de baseline de qualidade/custo/latência, selecionar classes como:

```text
FAST
STANDARD
DEEP_REASONING
MULTIMODAL
LONG_CONTEXT
```

Policy considera:

- task requirements;
- privacy/data policy;
- provider availability;
- output contract;
- latency/cost budget;
- fallback compatibility.

Não espalhar `if model == ...` por features.

## 30. Iframe integration

Fonte: [`26-iframe-copilot-bridge.md`](./26-iframe-copilot-bridge.md).

Classes:

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

Business Action continua por API/OpenAPI.

## 31. Autonomia

| Nível | Comportamento |
|---|---|
| L0 | explicar |
| L1 | navegar |
| L2 | consultar/analisar |
| L3 | preparar mudança |
| L4 | executar com Decision Gate conforme policy |
| L5 | executar capability explicitamente allowlisted dentro de limites |

L5 OFF por default.

## 32. Administração

Observar/governar:

- capabilities/actions;
- apps AI-ready;
- iframe classes;
- expertise/playbooks;
- evidence quality;
- Tasks/Cases/Workflows;
- Inbox/Watch;
- Decision Gates;
- knowledge lifecycle;
- model routing;
- latency/cost;
- failures/retries;
- safe execution rate;
- rollout/cohorts;
- kill switch;
- audit.

Administração não concede business permission fora do Core/RBAC.

## 33. Onboarding AI-ready

Níveis:

```text
L1 discoverable
L2 context-ready
L3 read-ready
L4 write-ready
L5 workflow-ready
```

Novo app deve entrar por contrato sem patch central.

Checklist inclui:

- routes/RBAC;
- APIs/use cases;
- OpenAPI quality;
- EntityRef/deep-link;
- Workspace Context;
- evidence/provenance quando relevante;
- sensitivity/Decision Gate;
- evals;
- iframe class quando aplicável.

## 34. Activity e explicabilidade operacional

Pode mostrar:

```text
Planejando
Aplicando conhecimento de Engenharia e Qualidade
Consultando produção
Analisando desenho
Aguardando aprovação
Monitorando nova revisão
Concluído
```

Não mostrar chain-of-thought. Mostrar actions, sources, state, policy decisions relevantes e limitações.

## 35. Erros

Distinguir:

- unauthorized;
- not found;
- missing requirement;
- pending decision;
- policy blocked;
- backend unavailable;
- partial failure;
- ambiguous outcome;
- stale evidence;
- unsupported simulation;
- workflow waiting/expired;
- bridge incompatible;
- capability unavailable.

Nunca narrar sucesso quando outcome não foi confirmado.

## 36. Observabilidade

Deve responder:

- o que foi pedido?;
- contexto/entidades?;
- capabilities disponíveis/selecionadas?;
- expertise/playbooks usados?;
- sources/evidence?;
- policy/Decision Gate?;
- workflow/task/case state?;
- outcome real?;
- latency/cost/retries?;
- rollback/failure?.

Sem CoT.

## 37. Não-funcionais

- security by default;
- Clean Architecture;
- baixo acoplamento;
- accessibility;
- responsive UX;
- performance budgets;
- auditability;
- data minimization;
- LGPD;
- versioned contracts;
- incremental rollout;
- idempotency/resilience;
- no duplicate authorities;
- generalization tests.

## 38. Fora de escopo por padrão

- unrestricted desktop/browser control;
- DOM automation como substituto de API;
- cross-origin hacks;
- eval/script injection;
- superuser Copilot identity;
- global L5 autonomy;
- automatic production learning from user data;
- source data access por visibility em outro sistema;
- automatic endpoint creation;
- JWT/refresh token via iframe bridge;
- multi-agent departmental UX como arquitetura principal.

## 39. Cenários de referência

### Contextual read
> “Explique este cliente e compare com o mês passado.”

### Cross-domain analysis
> “Para este item, compare estoque, compras, produção e carteira.”

### Multimodal
> “Analise este desenho e destaque riscos de fabricação.”

### Governed write
> “Crie uma solicitação para Compras revisar este item.”

### Durable investigation
> “Investigue a reclamação, monte um 8D e acompanhe até Engenharia liberar nova revisão.”

### Proactive
> “Me avise quando a nova revisão chegar e reanalise o caso.”

### Simulation
> “Se esse fornecedor atrasar mais cinco dias, quais pedidos entram em risco?”

## 40. Anchor scenario

```text
reclamação cliente
→ Case
→ Business Graph
→ multimodal drawing analysis
→ Evidence Board
→ Engineering + Quality Expertise
→ 8D Playbook
→ Task/Durable Workflow
→ wait_event
→ Watch/Inbox
→ nova revisão
→ reanalysis
→ Decision Gate
→ Business Action
→ Outcome/Evidence/Audit
→ Experience candidate
```

Sem troca manual de agente.

## 41. Product Complete

O release só pode ser chamado completo quando o escopo declarado possuir:

- foundations congeladas;
- navegação/contexto;
- Copilot único + expertise;
- reads/evidence;
- writes/Decision Gates;
- durable work quando no release;
- security/evals;
- generalization;
- observabilidade;
- rollout/rollback;
- requisitos CP correspondentes `PASS` ou `OUT_OF_SCOPE_WITH_DECISION` justificável;
- nenhum fallback material escondido.

O estado de execução real é registrado no ledger, não inferido desta especificação.