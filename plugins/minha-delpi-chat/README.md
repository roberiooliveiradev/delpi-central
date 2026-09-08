# Minha DELPI Chat

Microfrontend React do **Minha DELPI Chat**, carregado pelo Portal via Module Federation.

## Fontes técnicas vigentes

| Área | Fonte |
|------|-------|
| Arquitetura do chat | [chat-intelligence-base.md](../../minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md) |
| Actions OpenAPI | [04-actions-openapi.md](../../minha-delpi-ai-api/docs/api/04-actions-openapi.md) |
| Nova API/action | [new-api-route-checklist.md](../../minha-delpi-ai-api/docs/architecture/new-api-route-checklist.md) |
| Evals R1–R11 | [chat-ai-flow-families.md](../../minha-delpi-ai-api/docs/testing/chat-ai-flow-families.md) |
| API HTTP | [api/README.md](../../minha-delpi-ai-api/docs/api/README.md) |
| Modelo conceitual | [12-modelo-conceitual.md](../../minha-delpi-ai-api/docs/api/12-modelo-conceitual.md) |
| Skills | [11-skills.md](../../minha-delpi-ai-api/docs/api/11-skills.md) |
| Admin do plugin | [src/ui/components/admin/README.md](src/ui/components/admin/README.md) |
| Exportação | [docs/export.md](docs/export.md) |
| Estrutura frontend | [docs/component-structure.md](docs/component-structure.md) |

Roadmaps e changelogs não são fonte de arquitetura para este plugin.

## Identificação

| Campo | Valor |
|-------|-------|
| Manifesto | `delpi.manifest.json` |
| `basePath` | `/apps/minha-delpi-chat` |
| API | `/apps/minha-delpi-ai/api` |

## Desenvolvimento

```bash
cd plugins/minha-delpi-chat
npm install
npm run dev
```

Build:

```bash
npm run build
```

O gateway serve os assets do MFE em `/apps/minha-delpi-chat/assets/`.

## Estrutura principal

```text
src/
  export/
  data/api/
  state/
  state/hooks/
  ui/pages/
  ui/components/
  ui/components/presentation/
  ui/components/composer/
  ui/components/message/
  ui/components/workspace/
```

## Responsabilidade do frontend

O MFE é cliente da inteligência da API. Ele deve:

- enviar mensagens e consumir send/stream;
- renderizar `presentationDecision`/`renderPlan`;
- exibir tabelas, gráficos, árvores, KPIs e demais segmentos declarados;
- preservar estados de loading, activity, playback e feedback;
- aplicar a UI de agentes, projetos, fontes, anexos e admin;
- não recriar routing, RBAC, policy ou decisão operacional localmente.

Fluxo de apresentação:

```text
API: schema-driven presentation
→ presentationDecision
→ renderPlan
→ ChatAssistantContent
→ renderizadores registrados no MFE
```

O frontend não deve conhecer path/provider/operationId para decidir a apresentação de uma Action.

## Experiência do chat

- sessões e histórico;
- streaming SSE/activity/playback;
- agentes, projetos, fontes e anexos;
- Actions OpenAPI autorizadas pelo agente;
- RAG e pesquisa web quando habilitados;
- lousa/canvas;
- feedback de respostas;
- apresentação estruturada e exportação;
- painel administrativo.

## Gestão de agentes

Fluxo:

```text
Lista de agentes
→ Builder
→ Skills / Knowledge / Actions
→ Preview
→ Publicação
```

Actions são operations importadas de providers OpenAPI. O MFE administra configuração/binding; o backend mantém seleção, validação, policy e execução.

## Permissões

Consulte `delpi.manifest.json`. Principais permissões incluem:

- `minha-delpi.chat.access`
- `minha-delpi.chat.ask`
- `minha-delpi.chat.admin`
- `minha-delpi.chat.tools.manage`

O frontend usa capabilities/RBAC efetivos da plataforma e não deriva autorização completa apenas do JWT.

## Clientes HTTP

- `chatApi.ts` — `/chat/*`
- `adminApi.ts` — `/admin/*`

Base pública da API:

```text
/apps/minha-delpi-ai/api
```

## Regra de implementação

Mudança de comportamento inteligente deve ser implementada no chat base e validada pelo protocolo R1–R11. Mudança apenas visual permanece no MFE, respeitando `renderPlan` e o design system.
