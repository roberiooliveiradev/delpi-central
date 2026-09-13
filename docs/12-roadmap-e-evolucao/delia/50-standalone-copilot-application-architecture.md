# DÉLIA — Arquitetura Standalone da Aplicação

**Status:** `CANONICAL_AUTHORITY` para boundary do produto e ownership de runtime  
**Ordem de execução:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)  
**Baseline factual:** [`51-platform-integration-baseline.md`](./51-platform-integration-baseline.md)  
**Naming:** [`68-delia-product-identity-and-naming.md`](./68-delia-product-identity-and-naming.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

> Este documento define a **arquitetura alvo**. Ele não prova que runtime, serviço, rota, contrato, infraestrutura ou capability da DÉLIA já exista no HEAD. Fatos de plataforma são registrados em `51` com escopo de evidência e revalidados em `C0.S0`.

## 1. Decisão irrevogável desta iniciativa

A **DÉLIA é uma aplicação nova**, construída do zero até o produto completo.

Ela **não é**:

- expansão do `minha-delpi-ai-api`;
- expansão do `plugins/minha-delpi-chat`;
- modo novo do Minha DELPI Chat;
- refatoração incremental do Chat;
- camada adicional dentro do Portal;
- feature do Core API.

A arquitetura alvo possui **runtime, API, frontend, persistência, contratos, observabilidade e ciclo de release próprios**.

```text
Minha DELPI Chat                  DÉLIA
------------------------------    --------------------------------
plugins/minha-delpi-chat          novo MFE próprio
minha-delpi-ai-api                nova API própria
estado/persistência do Chat       estado/persistência da DÉLIA
regras/ciclo de release do Chat   regras/ciclo de release da DÉLIA

                SEM DEPENDÊNCIA DE RUNTIME
```

Chat e DÉLIA podem coexistir no Portal como aplicações independentes.

## 2. Regra de não dependência

A DÉLIA não pode depender de módulos internos, tabelas, services, controllers, sessions, agents, prompts, repositories ou migrations do Chat para funcionar.

Proibido no runtime alvo:

```text
API da DÉLIA → importar minha-delpi-ai-api.app.*
MFE da DÉLIA → importar source de plugins/minha-delpi-chat
DB da DÉLIA → reutilizar tabelas de conversa/agente do Chat como authority
DÉLIA → chamar endpoint do Chat para planejamento/tools/RAG
DÉLIA → depender de agent_id/chat_mode do Chat
```

O código do Chat pode ser lido **apenas como referência técnica** durante C0 para identificar lições, anti-patterns ou infraestrutura neutra que já tenha sido extraída para componentes realmente compartilhados.

Reuso legítimo exige uma destas condições:

1. componente já é compartilhado e neutro (`plugin-ui`, utilitário/plataforma comum, contrato oficial), com owner e consumers reais; ou
2. C0 prova que um código genérico deve ser extraído para package/shared owner independente, sem a DÉLIA depender do produto Chat.

Copiar dívida técnica ou criar dependência transitiva do Chat é `FAIL` arquitetural.

## 3. Owners físicos alvo

Os nomes finais de API/MFE/serviços/paths devem ser confirmados em C0.S1. Até lá, os namespaces técnicos planejados permanecem temporários:

```text
/minha-delpi-copilot-api/          # backend independente; namespace técnico temporário
/plugins/minha-delpi-copilot/      # MFE independente; namespace técnico temporário
/docs/12-roadmap-e-evolucao/delia/ # documentação canônica atual
```

A pasta documental `delia/` já é o path vigente no HEAD e não depende do freeze de naming técnico de API/MFE.

Infraestrutura compartilhada permanece em seus owners canônicos:

```text
portal/              Shell/host/navegação/published context
core-api/            apps/rotas/RBAC/governança
Keycloak             identidade/SSO
gateway/              entrada e roteamento reverso
plugins/plugin-ui/    design system/componentes compartilhados
plugins/vite/         convenções Module Federation, se revalidadas
Domain APIs           dados e regras de negócio
infra/                compose/deploy/env/network
Automation Hub        execução técnica de automações
```

C0.S0 revalida quais assets/contratos estão disponíveis no HEAD de execução e seu estado real; ownership normativo não é evidência de implementação.

## 4. Arquitetura macro

```text
                         USUÁRIO
                            │
                            ▼
                    Portal React Shell
              ┌─────────────┴─────────────┐
              │                           │
       rota/full page                surface global
              │                           │
              └─────────────┬─────────────┘
                            ▼
                      MFE da DÉLIA
                    (federated target)
                            │
                 JWT/access token via host
                            │
                            ▼
                     Gateway/Nginx
                            │
                            ▼
                       API da DÉLIA
                  (serviço independente)
        ┌───────────────────┼────────────────────┐
        ▼                   ▼                    ▼
     Core API           Domain APIs           AI/Media
 apps/routes/RBAC       data/rules/        LLM/RAG/Vision/
   governance            actions          STT/TTS/Realtime
        │                   │                    │
        └───────────────────┼────────────────────┘
                            ▼
                   DÉLIA-owned state
       conversations/work/evidence/media refs/etc.
```

Execução técnica de automações materiais usa o Automation Hub por contrato quando aplicável; a DÉLIA permanece owner de intelligence/context, Evidence, Policy, Decision, Work/orquestração e coordenação da verificação de Outcome.

## 5. Surfaces sobre o mesmo runtime

A DÉLIA deve suportar diferentes experiências sem criar produtos/runtimes paralelos:

```text
GLOBAL      → painel contextual no Portal
WORKSPACE   → página completa
MEETING     → reunião assistida multimodal
FRONTLINE   → operador/posto/máquina
```

Invariante:

```text
4 surfaces
→ same DÉLIA API
→ same product identity
→ same Policy/Decision/Work semantics
→ same Evidence contracts
→ no second planner/workflow authority
```

RBAC não pertence à DÉLIA; cada surface preserva as authorities Keycloak/Core/Domain.

## 6. Responsabilidades da API da DÉLIA

A nova API é owner do runtime inteligente e de Work/orchestration da DÉLIA:

- turn/request understanding;
- conversation/session state da DÉLIA;
- capability projection e retrieval;
- Action Catalog derivado de contratos OpenAPI autorizados;
- planner/orchestrator estruturado;
- argument binding/validation;
- policies específicas da DÉLIA sem duplicar RBAC ou regras de domínio;
- Decision Gates;
- orchestration de ações governadas via contratos de executor;
- Expertise Packs;
- Domain Playbooks;
- knowledge retrieval/RAG da DÉLIA;
- multimodal/document/drawing/image/audio/video intelligence pipeline;
- speech/transcription/synthesis adapters quando implementados;
- media session orchestration quando necessário;
- Evidence/Provenance;
- Business Graph refs/relationships/index;
- durable workflows;
- Tasks/Cases/Watch/Inbox state;
- Meeting artifacts/session semantics da DÉLIA;
- Frontline assistance/session semantics da DÉLIA;
- model/provider abstraction e Compute Policy;
- audit/tracing/evals da DÉLIA;
- administration endpoints da DÉLIA.

A API **não** vira owner de:

- identidade/SSO corporativos;
- apps/rotas/RBAC/governança Core;
- regras de negócio de Comercial, Suprimentos, Engenharia etc.;
- dados mestres que pertencem às Domain APIs;
- navegação real do Portal;
- execução técnica de automações que pertence ao Automation Hub;
- regras certificadas de segurança de máquinas;
- interlocks/PLC safety logic;
- qualificação/certificação oficial de operador;
- critérios de inspeção que pertencem a sistemas/process owners.

`Work/orchestration != technical executor runtime`.

## 7. Responsabilidades do MFE da DÉLIA

Frontend independente, React/Vite/Module Federation quando esse contrato for confirmado no baseline vigente.

Responsabilidades:

- conversation UX da DÉLIA;
- Task/Case/Inbox/Approval surfaces;
- Evidence/provenance presentation;
- artifacts/attachments;
- media capture controls quando surface/device suportar;
- Meeting Mode UX;
- Frontline Mode UX;
- full-page DÉLIA experience;
- global side-panel experience quando hospedado pelo Portal;
- administração da DÉLIA quando autorizada;
- consumir somente API da DÉLIA e contracts de plataforma necessários.

Não contém regra de negócio nem autorização authoritative. Permission state recebido no frontend serve UX/contexto e nunca substitui enforcement backend.

## 8. Integração com o Portal

O Portal é **host**, não runtime da DÉLIA.

O snapshot de evidência em `51` registra como `PROVEN` o `AppHost` federado atual, incluindo `remoteEntry`, `mount()/unmount()` e host props como:

```text
getAccessToken
basePath
pathname
search
appRoutes
routeLabel
permissions
isSuperadmin
```

Essa evidência vale para o SHA/blob registrado em `51` e deve ser revalidada no HEAD de C0.S0. Revalidação futura não transforma evidência já observada em `TO_INVENTORY`; apenas impede tratá-la como eterna ou suficiente para compatibilidade DÉLIA.

DÉLIA deve reutilizar/evoluir contrato genérico de host somente após contract check em C0/C1.

### 8.1 Full page

**TARGET:** manifesto da DÉLIA registra app federado com base path próprio se a convenção vigente for confirmada.

Conceitualmente, mantendo namespace técnico temporário:

```text
/apps/minha-delpi-copilot
```

O path final é congelado em C0.S1/C1.

### 8.2 Global DÉLIA surface

Além do app navegável, o Portal poderá oferecer botão/side panel global.

Regra alvo:

```text
Portal Global DÉLIA Host
→ monta/exibe o mesmo MFE da DÉLIA por contrato
→ publica bounded WorkspaceContext
→ recebe PlatformCommand
```

O Portal não implementa planner, RAG, Policy, business actions, media intelligence ou prompts da DÉLIA.

A integração global precisa evitar uma segunda implementação do frontend. O mesmo MFE deve suportar, por contrato, surfaces como:

```text
surface = page | panel | meeting | frontline
```

quando cada surface for liberada.

## 9. Meeting e Frontline não são novos backends

Meeting/Frontline são experiências da DÉLIA standalone.

```text
Meeting MFE surface ─┐
Frontline MFE surface├→ API da DÉLIA
Global/Page surface ─┘
```

Não criar:

```text
meeting-ai-api
frontline-ai-api
operator-agent-runtime
```

sem gap arquitetural real e ADR. Serviços auxiliares de media/Edge podem existir por boundary real, mas não como segunda authority de intelligence/Policy/Decision/Work.

## 10. Workspace Context operacional

Portal publica contexto de host/workspace conforme seu contrato. DÉLIA constrói contexto operacional/inteligente bounded a partir de refs autorizadas; nenhum deles vira segundo sistema de verdade industrial.

OP, operação, máquina, produto, lote, material, ferramenta e posto devem usar preferencialmente `EntityRef` dentro do `WorkspaceContext`, quando esses contracts forem confirmados/criados no owner correto.

```text
WorkspaceContext
├─ app/route
├─ EntityRefs
│  ├─ productionOrder
│  ├─ machine
│  ├─ product
│  └─ operation
└─ bounded device/session metadata
```

Context/data vindo de Portal, MFE, provider ou event é untrusted para permission. Device/session metadata nunca concede autorização.

## 11. Integração com Keycloak e Core API

Separar authority explicitamente:

```text
Keycloak = identidade corporativa / SSO
Core API = apps / rotas / RBAC / governance
```

Core pode materializar/projetar user context necessário aos seus contratos, mas não substitui Keycloak como identity/SSO authority.

A API da DÉLIA valida identidade/JWT conforme foundation aprovada e resolve contexto/permissões de plataforma por contratos Core confirmados. Endpoints concretos devem ser revalidados em C0.S0 antes de virarem dependência de implementação.

Regra:

```text
JWT = identidade/contexto, não permission final
Core = autorização efetiva da plataforma
Domain API = autorização/regra final de negócio
DÉLIA = nunca amplia permission
```

## 12. Shared devices

Terminal de produção, tablet, kiosk ou sala podem ser devices compartilhados.

A arquitetura deve separar:

```text
user identity
≠
device identity
≠
operational context
```

Obrigatório quando aplicável:

- user atual explícito;
- session timeout/lock;
- troca de usuário sem state leak;
- limpeza de cache/mídia/contexto local;
- logout seguro;
- device scopes limitados.

## 13. Integração com APIs de domínio

A DÉLIA chama APIs owners diretamente através do Gateway/service network conforme contrato aprovado; não usa Chat como proxy.

Pipeline alvo:

```text
intent / event / signal
→ allowed semantic capability discovery
→ authoritative contract retrieval
→ structured plan
→ argument validation
→ live AuthZ + Policy/Decision Gate
→ governed execution request
→ Domain API / Automation Hub / approved provider adapter
→ authoritative postcondition verification
→ Outcome/Evidence
```

OpenAPI-first é requisito **nativo da DÉLIA quando aplicável**, não dependência de correções do Chat. OpenAPI não elimina Domain authorization nem concede permission.

## 14. Integração com API DELPI

`api-delpi/` está `PROVEN` em `51` como componente presente no monorepo. Seus owners funcionais, manifesto, OpenAPI, JWT/permission semantics, integrações e suitability para capabilities específicas permanecem `TO_INVENTORY` até inspeção factual de contrato.

Se `api-delpi` for owner de integração/regra necessária, DÉLIA consome o contrato aprovado; não replica a integração dentro da API da DÉLIA.

## 15. Integração com plugin-ui

O snapshot `51` registra `plugins/vite/federation.shared.ts` como `PROVEN` para configuração compartilhada atual de federation/`@delpi/plugin-ui`.

Se C1 confirmar compatibilidade do contrato, o MFE da DÉLIA deve:

- reutilizar `@delpi/plugin-ui`;
- reutilizar convenções de federation compartilhadas vigentes;
- não source-importar componentes do Portal ou do Chat;
- propor extensão shared somente com 2+ consumers reais, owner, contrato pequeno e testes;
- preservar accessibility e large-touch/responsive needs de Meeting/Frontline.

## 16. Media architecture

A DÉLIA é owner da inteligência/orquestração e dos contracts de media necessários ao seu produto; providers, transport, storage e device integrations concretos ficam atrás de boundaries e preservam seus próprios owners.

Possíveis ports somente quando C0/Abstraction Gate provar necessidade:

```text
SpeechToTextPort
TextToSpeechPort
MediaIngestPort
VisionAnalysisPort
RealtimeMediaSessionPort
MediaStoragePort
DeviceContextPort
```

Não criar todos antecipadamente.

Meeting, câmera, vídeo e voz usam adapters aprovados; não chamam runtime do Chat.

## 17. MediaRef / Evidence

C0 deve decidir se `MediaRef` é primitive compartilhado necessário e quem o owns.

Evidence não deve duplicar mídia bruta; referencia source/location quando necessário.

Candidate semantics, não schema congelado:

```text
media ref
kind
source
capturedAt
session/owner refs
retention class
consent/policy ref
hash/version
storage ref if persisted
```

## 18. Persistência independente

A DÉLIA terá schema/tabelas/migrations próprias somente conforme gaps/lifecycles e owned durable state forem provados.

Pode compartilhar infraestrutura PostgreSQL por decisão explícita, mas **não compartilhar ownership lógico de tabelas do Chat**.

Conceitos DÉLIA-owned candidatos:

- conversations/turns;
- user/project preferences quando DÉLIA owns a classe;
- expertise/playbooks;
- Evidence/media metadata;
- Work/task/case/checkpoints;
- watch/inbox/decision refs;
- meeting artifact/session metadata quando persistência for necessária;
- frontline session metadata quando policy exigir;
- graph relationship/index derivado;
- eval/admin metadata;
- correlation/projection refs necessários para execution/Outcome, sem duplicar technical executor state do Automation Hub.

Raw audio/video não é automaticamente DÉLIA-owned durable state. Retention precisa de purpose/policy explícitos.

C0 congela boundaries antes de migrations.

## 19. Privacy/consent boundary

Audio/video/camera/screen capture exige estado explícito e policy.

Separar:

```text
transient capture
transcript
raw audio
raw video
screen capture
derived Evidence
meeting artifact
```

Essas classes podem ter retention/access diferentes.

Default: data minimization.

## 20. Industrial/OT boundary

DÉLIA não é safety controller.

Default permitido:

```text
observe
consult
explain
recommend
prepare governed enterprise action
```

Governed enterprise ACT não concede physical authority.

Default proibido:

```text
arbitrary LLM/model/vision/voice-generated machine command
AI replacing/bypassing interlock or safety PLC
implicit OT permission from enterprise autonomy
```

Qualquer futura machine actuation exige arquitetura/gate industrial separado com deterministic command contract/schema, allowlist, industrial owner, machine-state validation, independent safety interlocks, test environment, fail-safe, human authorization quando aplicável e audit.

Autonomia L5 empresarial da DÉLIA não habilita OT automaticamente.

## 21. Infraestrutura e deploy

A aplicação terá, quando implementada, entradas próprias conforme contratos e padrões confirmados em C0/C1:

- dev/prod deployment mechanism aprovado;
- Gateway dev/prod;
- env/config conventions;
- scripts/build/start quando necessários;
- health checks;
- migrations;
- logs/metrics;
- manifesto/registro Core.

Conceitualmente, usando namespace técnico temporário:

```text
service: minha-delpi-copilot-api
MFE: minha-delpi-copilot
API gateway path: /apps/minha-delpi-copilot-api/
MFE path: /apps/minha-delpi-copilot/
```

Media/realtime support pode exigir tuning de Gateway/infra, mas não cria outro product boundary.

Nomes/paths finais devem ser congelados antes da implementação e não inferidos por cada etapa.

## 22. Relação com Minha DELPI Chat

Chat é **sistema vizinho e reference-only para esta iniciativa**, não legado a migrar dentro do projeto DÉLIA.

Portanto ficam fora do roadmap da DÉLIA:

- migrar `AgentSpecializationService`;
- remover `userActivatedAgent` do Chat;
- remover `softAgentHandoff` do Chat;
- converter sessions do Chat;
- fazer cutover de `agent_id` do Chat;
- corrigir runtime/action routing do Chat;
- reutilizar voice/vision/media runtime do Chat como dependency.

Esses trabalhos pertencem ao produto Chat se forem desejados futuramente.

A DÉLIA nasce sem essas dependências.

## 23. Regra de construção do zero

“Do zero” não significa ignorar a plataforma.

Significa:

```text
reutilizar contratos e infraestrutura corporativa estáveis e comprovados
+
criar runtime de produto próprio
+
não herdar dívida/aplicação Chat
```

Candidates de platform reuse, sempre sujeitos ao inventário/contrato real:

- Keycloak SSO;
- Core RBAC/apps/routes;
- Gateway;
- manifest/app model;
- Module Federation;
- plugin-ui;
- padrões Clean Architecture;
- clients/contracts oficiais das Domain APIs;
- event/notification infrastructure quando apropriado e provado;
- device/media infrastructure neutra se C0 provar owner compartilhado;
- Automation Hub quando sua implementação/contrato for provada.

## 24. Gate de independência

Antes do primeiro release, provar:

```text
COPILOT_API_OWN_RUNTIME = PASS       # technical gate id temporary
COPILOT_MFE_OWN_RUNTIME = PASS       # technical gate id temporary
NO_CHAT_RUNTIME_IMPORT = PASS
NO_CHAT_DATABASE_AUTHORITY = PASS
NO_CHAT_API_PROXY_DEPENDENCY = PASS
PORTAL_HOST_INTEGRATION = PASS
CORE_RBAC_INTEGRATION = PASS
DOMAIN_API_DIRECT_CONTRACT = PASS
PLUGIN_UI_REUSE = PASS
INDEPENDENT_DEPLOY_ROLLBACK = PASS
```

Os tokens `COPILOT_*` permanecem temporariamente como identificadores técnicos legados do planejamento até C0.S1; não são nome de produto.

Antes de Meeting/Frontline production scope, provar também conforme aplicável:

```text
MEDIA_POLICY = PASS
CONSENT_VISIBILITY = PASS
RETENTION_CLASSES = PASS
SHARED_DEVICE_ISOLATION = PASS
OPERATIONAL_CONTEXT = PASS
OT_SAFETY_BOUNDARY = PASS
NO_HIDDEN_SURVEILLANCE = PASS
```

Qualquer dependência material do produto Chat, captura sem governance, bypass de safety/RBAC ou duplicate execution authority bloqueia conclusão.

## 25. Estado de execução

Este documento define boundary/target; não prova implementação da DÉLIA.

```text
PROGRAM = PLANNED / NOT_STARTED
NEXT = C0.S0
```

Qualquer claim de runtime deve vir do ledger/evidence para o SHA/config avaliados.
