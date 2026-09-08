# Documentação técnica — Minha DELPI Chat AI

**Status:** vigente  
**Produto:** assistente conversacional corporativo da Minha DELPI

Este documento é um ponto de entrada. A fonte arquitetural principal é [`minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md`](../../../minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md).

## Componentes

```text
Portal / Gateway
  ├─ plugins/minha-delpi-chat
  └─ minha-delpi-ai-api
       ├─ Core API / Keycloak
       ├─ PostgreSQL + pgvector
       ├─ LLM provider
       ├─ RAG
       └─ providers OpenAPI / api-delpi
```

| Componente | Responsabilidade |
|------------|------------------|
| `plugins/minha-delpi-chat` | UI, streaming, composer, agentes/projetos, renderização |
| `minha-delpi-ai-api` | Inteligência, contexto, tools, RAG, policies, apresentação |
| `api-delpi` | Contratos/dados corporativos e integração TOTVS |
| Core API | RBAC/permissões efetivas |
| Keycloak | Identidade SSO OAuth2/OIDC |

## Pipeline do chat

```text
mensagem
→ workspace context
→ entendimento/decomposição
→ contexto/memória estruturados
→ direct / no-tool / Actions / RAG / mixed
→ Actions autorizadas + Action Catalog
→ retrieval top-K
→ planner estruturado
→ validação OpenAPI
→ RBAC/policy/confirmation
→ executor genérico
→ RAG quando necessário
→ schema-driven presentation
→ síntese
→ persistência/metadata/observabilidade
→ send/stream
```

Agentes e projetos especializam o mesmo pipeline; não possuem routing paralelo.

## Actions OpenAPI

```text
OpenAPI
→ import/index
→ Action Catalog
→ agent binding + allowed_action_ids
→ retrieval/planner/validator
→ policy
→ HTTP executor
```

Uma API externa nova não exige cadastro técnico por endpoint no core do chat.

Não criar:

- `if path/provider/operationId` no motor genérico;
- intent/selector por endpoint;
- markers ou parameter strategy que dupliquem OpenAPI;
- catálogo técnico paralelo;
- presenter dedicado obrigatório.

Referências:

- [Actions OpenAPI](../../../minha-delpi-ai-api/docs/api/04-actions-openapi.md)
- [Checklist nova API/action](../../../minha-delpi-ai-api/docs/architecture/new-api-route-checklist.md)

## Apresentação

```text
response schema + payload + metadata
→ schema-driven presentation
→ presentationDecision
→ renderPlan
→ MFE render-only
```

O MFE não deve redecidir regras de negócio, routing ou autorização com base em endpoint/provider.

## Backend — Clean Architecture

```text
interfaces/http
→ application/use_cases + application/services
→ domain/services + ports
→ infrastructure adapters
→ composition root
```

Regras:

- domain não depende de infrastructure/interfaces;
- use cases orquestram, não concentram regra transversal;
- dependências concretas são ligadas em composition;
- linguagem/UX configurável fica em conteúdo declarativo;
- contrato técnico de Actions vem do OpenAPI/Action Catalog.

## Frontend

```text
plugins/minha-delpi-chat/src/
  data/api/
  state/
  ui/pages/
  ui/components/
  ui/components/message/
  ui/components/presentation/
  ui/components/composer/
  ui/components/workspace/
  export/
```

Responsabilidades principais:

- consumir API/stream SSE;
- renderizar mensagens e `renderPlan`;
- administrar agentes/projetos/actions;
- exibir activity/loading/feedback;
- exportar apresentações;
- respeitar design system e RBAC retornado pela plataforma.

## Segurança e autorização

- identidade: Keycloak OAuth2/OIDC;
- JWT não é catálogo completo de permissões;
- RBAC efetivo é resolvido pela plataforma/Core API;
- `allowed_action_ids` limita Actions do agente;
- writes/admin/destructive respeitam confirmation/policy;
- conteúdo de RAG/tool não substitui policy;
- tokens/secrets não entram em prompt/log/resposta.

## Avaliação da inteligência

Toda alteração de inteligência segue [`chat-ai-flow-families.md`](../../../minha-delpi-ai-api/docs/testing/chat-ai-flow-families.md).

```text
BASELINE
→ bug + sibling + negative
→ implementação canônica
→ CANDIDATE no mesmo corpus/config
→ R1–R11
→ live/surfaces
→ decisão
```

Mudança no motor de tools exige API externa desconhecida e teste metamórfico.

## Fontes vigentes

- [Índice técnico da API](../../../minha-delpi-ai-api/docs/README.md)
- [Arquitetura do chat](../../../minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md)
- [Actions OpenAPI](../../../minha-delpi-ai-api/docs/api/04-actions-openapi.md)
- [Nova API/action](../../../minha-delpi-ai-api/docs/architecture/new-api-route-checklist.md)
- [Protocolo R1–R11](../../../minha-delpi-ai-api/docs/testing/chat-ai-flow-families.md)
- [Fluxos](../../../minha-delpi-ai-api/docs/flows/README.md)
- [README do MFE](../../../plugins/minha-delpi-chat/README.md)

Roadmaps/changelogs datados não são fonte de arquitetura. Histórico técnico permanece no Git.
