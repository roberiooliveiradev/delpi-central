# Minha DELPI Copilot — Arquitetura Standalone da Aplicação

**Status:** `CANONICAL_AUTHORITY` para boundary do produto e ownership de runtime  
**Ordem de execução:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Patterns:** [`49-architecture-and-design-patterns-standard.md`](./49-architecture-and-design-patterns-standard.md)

## 1. Decisão irrevogável desta iniciativa

O **Minha DELPI Copilot é uma aplicação nova**, construída do zero até o produto completo.

Ele **não é**:

- expansão do `minha-delpi-ai-api`;
- expansão do `plugins/minha-delpi-chat`;
- modo novo do Minha DELPI Chat;
- refatoração incremental do Chat;
- camada adicional dentro do Portal;
- feature do Core API.

A arquitetura alvo possui **runtime, API, frontend, persistência, contratos, observabilidade e ciclo de release próprios**.

```text
Minha DELPI Chat                  Minha DELPI Copilot
------------------------------    --------------------------------
plugins/minha-delpi-chat          novo MFE próprio
minha-delpi-ai-api                nova API própria
estado/persistência do Chat       estado/persistência do Copilot
regras/ciclo de release do Chat   regras/ciclo de release do Copilot

                SEM DEPENDÊNCIA DE RUNTIME
```

Chat e Copilot podem coexistir no Portal como aplicações independentes.

## 2. Regra de não dependência

O Copilot não pode depender de módulos internos, tabelas, services, controllers, sessions, agents, prompts, repositories ou migrations do Chat para funcionar.

Proibido no runtime alvo:

```text
Copilot API → importar minha-delpi-ai-api.app.*
Copilot MFE → importar source de plugins/minha-delpi-chat
Copilot DB → reutilizar tabelas de conversa/agente do Chat como authority
Copilot → chamar endpoint do Chat para planejamento/tools/RAG
Copilot → depender de agent_id/chat_mode do Chat
```

O código do Chat pode ser lido **apenas como referência técnica** durante C0 para identificar lições, anti-patterns ou infraestrutura neutra que já tenha sido extraída para componentes realmente compartilhados.

Reuso legítimo exige uma destas condições:

1. componente já é compartilhado e neutro (`plugin-ui`, utilitário/plataforma comum, contrato oficial); ou
2. C0 prova que um código genérico deve ser extraído para package/shared owner independente, sem o Copilot depender do produto Chat.

Copiar dívida técnica ou criar dependência transitiva do Chat é `FAIL` arquitetural.

## 3. Owners físicos alvo

Os nomes finais devem ser confirmados em C0.S1, porém o desenho canônico é:

```text
/minha-delpi-copilot-api/          # backend independente
/plugins/minha-delpi-copilot/      # MFE independente
/docs/.../minha-delpi-copilot/     # documentação canônica já existente
```

Infraestrutura compartilhada permanece em seus owners atuais:

```text
portal/              Shell/host/navegação/contexto global
core-api/            apps/rotas/RBAC/governança/notificações compartilhadas
keycloak              identidade/SSO
gateway/              entrada e roteamento reverso
plugins/plugin-ui/    design system/componentes compartilhados
plugins/vite/         convenções Module Federation
APIs de domínio       dados e regras de negócio
infra/                compose/deploy/env/network
```

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
               Minha DELPI Copilot MFE
                    (federated)
                            │
                 JWT/access token via host
                            │
                            ▼
                     Gateway/Nginx
                            │
                            ▼
              Minha DELPI Copilot API
                  (serviço independente)
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
          Core API      Domain APIs     AI Providers
        apps/RBAC       OpenAPI/use     LLM/RAG/Vision
                           cases
              │             │              │
              └─────────────┼──────────────┘
                            ▼
                 Copilot-owned state
          conversations/work/evidence/etc.
```

## 5. Responsabilidades da Copilot API

A nova API é owner do runtime inteligente do Copilot:

- turn/request understanding;
- conversation/session state do Copilot;
- capability projection e retrieval;
- Action Catalog do Copilot derivado de contratos OpenAPI autorizados;
- planner/orchestrator estruturado;
- argument binding/validation;
- policies específicas do Copilot sem duplicar RBAC;
- Decision Gates;
- generic action execution;
- Expertise Packs;
- Domain Playbooks;
- knowledge retrieval/RAG do Copilot;
- multimodal/document/drawing pipeline;
- Evidence/Provenance;
- Business Graph refs/relationships/index;
- durable workflows;
- Tasks/Cases/Watch/Inbox state;
- model/provider abstraction e Compute Policy;
- audit/tracing/evals do Copilot;
- administration endpoints do Copilot.

A API **não** vira owner de:

- usuários/grupos/roles/permissões corporativas;
- catálogo mestre de apps/rotas;
- regras de negócio de Comercial, Suprimentos, Engenharia etc.;
- dados mestres que pertencem às APIs de domínio;
- navegação real do Portal.

## 6. Responsabilidades do Copilot MFE

Frontend independente, React/Vite/Module Federation, seguindo padrões do monorepo.

Responsabilidades:

- chat/conversation UX do Copilot;
- Task/Case/Inbox/Approval surfaces;
- evidence/provenance presentation;
- artifacts/attachments;
- full-page Copilot experience;
- global side-panel experience quando hospedado pelo Portal;
- administração do Copilot quando autorizada;
- consumir somente Copilot API e contracts de plataforma necessários.

Não contém regra de negócio nem autorização authoritative.

## 7. Integração com o Portal

O Portal é **host**, não runtime do Copilot.

O código atual prova que `AppHost` suporta `renderMode=federated`, carrega `remoteEntry.js`, exige `mount()` e injeta props como:

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

O Copilot deverá usar o mesmo contrato federado, evoluído somente por contrato genérico quando necessário.

### 7.1 Full page

Manifesto do Copilot registra app `microfrontend` com `renderMode=federated` e base path próprio.

Conceitualmente:

```text
/apps/minha-delpi-copilot
```

O path final é congelado em C0/C1 conforme convenção vigente.

### 7.2 Global Copilot surface

Além do app navegável, o Portal poderá oferecer botão/side panel global.

Regra:

```text
Portal Global Copilot Host
→ monta/exibe o mesmo Copilot MFE por contrato
→ publica WorkspaceContext
→ recebe PlatformCommand
```

O Portal não implementa planner, RAG, actions ou prompt do Copilot.

A integração global precisa evitar uma segunda implementação do frontend. O mesmo MFE deve suportar, por contrato, surfaces como:

```text
surface = page | panel
```

se C0/C1 confirmar esse desenho.

## 8. Integração com Core API

Core permanece authority de:

- identidade corporativa materializada;
- apps registrados;
- rotas;
- permissões efetivas;
- manifesto;
- favorites/notifications/presence/app usage quando aplicável.

Copilot API valida JWT e resolve contexto/permissões por contratos oficiais Core, incluindo `/me`, `/me/apps`, `/me/routes` conforme aplicável.

Regra:

```text
JWT = identidade/contexto
Core = autorização efetiva da plataforma
Domain API = autorização/regra final de negócio
Copilot = nunca amplia permission
```

## 9. Integração com APIs de domínio

O Copilot chama APIs owners diretamente através do Gateway/service network conforme contrato aprovado; não usa Chat como proxy.

Pipeline alvo:

```text
intent
→ allowed capability discovery
→ OpenAPI/contract retrieval
→ structured plan
→ argument validation
→ RBAC/policy/Decision Gate
→ generic executor
→ Domain API
→ verified outcome/evidence
```

OpenAPI-first é requisito **nativo do Copilot desde sua fundação**, não dependência de correções do Chat.

## 10. Integração com API DELPI

`api-delpi` já existe como `backend-only`, com JWT e permission contract próprios. O Copilot a trata como uma API de domínio/integração corporativa, respeitando seu manifesto, OpenAPI e permissões; não replica integrações TOTVS dentro da Copilot API.

## 11. Integração com plugin-ui

Os MFEs usam infraestrutura compartilhada `plugins/vite/federation.shared.ts`, que disponibiliza `@delpi/plugin-ui` por Module Federation e mantém React singleton/versionado.

O Copilot MFE deve:

- reutilizar `@delpi/plugin-ui`;
- reutilizar `FEDERATION_SHARED_REACT` e convenções atuais;
- não source-importar componentes do Portal ou do Chat;
- propor extensão do `plugin-ui` somente quando componente for realmente transversal.

## 12. Persistência independente

Copilot terá schema/tabelas/migrations próprias conforme gaps provados.

Pode compartilhar o mesmo cluster PostgreSQL de plugins por decisão de infraestrutura, mas **não compartilhar ownership lógico de tabelas do Chat**.

Conceitos Copilot-owned candidatos:

- conversations/turns;
- user/project preferences do Copilot;
- expertise/playbooks;
- evidence metadata;
- workflow/task/case/checkpoints;
- watch/inbox/decision refs;
- graph relationship/index derivado;
- eval/admin metadata.

C0 congela boundaries antes de migrations.

## 13. Infraestrutura e deploy

A aplicação terá entradas próprias em:

- dev/prod Docker Compose;
- Gateway dev/prod;
- env examples;
- scripts sequenciais/build/start;
- health checks;
- migrations;
- logs/metrics;
- manifesto/registro Core.

Conceitualmente:

```text
service: minha-delpi-copilot-api
MFE: minha-delpi-copilot
API gateway path: /apps/minha-delpi-copilot-api/
MFE path: /apps/minha-delpi-copilot/
```

Nomes/paths finais devem ser congelados antes da implementação e não inferidos por cada etapa.

## 14. Relação com Minha DELPI Chat

Chat é **sistema vizinho**, não legado a migrar dentro do projeto Copilot.

Portanto ficam fora do roadmap do Copilot:

- migrar `AgentSpecializationService`;
- remover `userActivatedAgent` do Chat;
- remover `softAgentHandoff` do Chat;
- converter sessions do Chat;
- fazer cutover de `agent_id` do Chat;
- corrigir runtime/action routing do Chat.

Esses trabalhos pertencem ao produto Chat se forem desejados futuramente.

O Copilot nasce sem essas dependências.

## 15. Regra de construção do zero

“Do zero” não significa ignorar a plataforma.

Significa:

```text
reutilizar contratos e infraestrutura corporativa estáveis
+
criar runtime de produto próprio
+
não herdar dívida/aplicação Chat
```

O Copilot deve reaproveitar:

- SSO/RBAC;
- Gateway;
- Core app model;
- Manifest v2;
- Module Federation;
- plugin-ui;
- padrões Clean Architecture;
- clients/contracts oficiais das APIs;
- event/notification infrastructure quando apropriado.

## 16. Gate de independência

Antes do primeiro release, provar:

```text
COPILOT_API_OWN_RUNTIME = PASS
COPILOT_MFE_OWN_RUNTIME = PASS
NO_CHAT_RUNTIME_IMPORT = PASS
NO_CHAT_DATABASE_AUTHORITY = PASS
NO_CHAT_API_PROXY_DEPENDENCY = PASS
PORTAL_HOST_INTEGRATION = PASS
CORE_RBAC_INTEGRATION = PASS
DOMAIN_API_DIRECT_CONTRACT = PASS
PLUGIN_UI_REUSE = PASS
INDEPENDENT_DEPLOY_ROLLBACK = PASS
```

Qualquer dependência material do produto Chat bloqueia conclusão, salvo uma futura decisão arquitetural explícita.