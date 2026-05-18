# Minha DELPI Chat (plugin)

Microfrontend React do **Minha DELPI Chat**, carregado pelo Portal via Module Federation.

## Documentação

| Área | Caminho |
|------|---------|
| API backend | [../../minha-delpi-ai-api/docs/api/README.md](../../minha-delpi-ai-api/docs/api/README.md) |
| Admin (componentes) | [src/ui/components/admin/README.md](src/ui/components/admin/README.md) |
| Roadmap admin | [../../minha-delpi-ai-api/docs/roadmap/admin-minha-delpi-chat.md](../../minha-delpi-ai-api/docs/roadmap/admin-minha-delpi-chat.md) |
| Status da plataforma | [../../docs/12-roadmap-e-evolucao/minha-delpi-chat/status-atual.md](../../docs/12-roadmap-e-evolucao/minha-delpi-chat/status-atual.md) |

## Identificação

| Campo | Valor |
|-------|--------|
| Manifesto | `delpi.manifest.json` |
| `basePath` | `/apps/minha-delpi-chat` |
| API | `/apps/minha-delpi-ai/api` |

## Desenvolvimento

```bash
cd plugins/minha-delpi-chat
npm install
npm run dev
```

Build para o gateway:

```bash
npm run build
```

O Nginx serve `dist/` em `/apps/minha-delpi-chat/assets/`.

## Estrutura do código

```text
src/
  data/api/          # chatApi.ts, adminApi.ts, tipos
  state/hooks/       # useChatSession, useChatAdmin, …
  ui/
    pages/           # ChatPage, ChatAdminPage, ChatAgentsPage
    components/      # chat, admin (abas modulares)
```

## Experiência do usuário (chat)

- Sessões com pin, arquivo e renomear
- Mensagens com streaming, fontes, tool calls e anexos
- **Feedback** (thumbs up/down) em respostas do assistente
- Agentes, projetos, fontes e anexos por contexto
- Notificações (sino) quando habilitado na Core API

## Painel administrativo

Acesso via botão **Admin** na UI (requer `minha-delpi.chat.admin`).

| Aba | Função |
|-----|--------|
| Conhecimento | Ingestão global, upload, metadados curadoriais, pré-visualização de pipeline |
| Métricas | Resumo operacional, janela 24h/7d/30d, tabela de custo LLM editável, série histórica |
| Diretrizes | CRUD, versões, publicação, teste RAG |
| Simulação | Prompt final, RAG, diretrizes, tools; histórico de sessão; sandbox de tools |
| Avaliações | Nota 1–5, sugestões automáticas e opcionais via LLM |
| Agentes | Especialização (escopo RAG, diretrizes, tools) |
| Segurança | Config, eventos, scan de entrada |
| Ferramentas | Health consolidado, providers/actions, LLM |
| Auditoria | Filtros, timeline, export CSV, trace id |

## Permissões (manifesto)

Consulte `delpi.manifest.json`. Principais:

- `minha-delpi.chat.access` — uso geral
- `minha-delpi.chat.ask` — enviar mensagens
- `minha-delpi.chat.admin` — painel administrativo
- `minha-delpi.chat.tools.manage` — agentes e actions próprios

O frontend usa `GET /chat/capabilities` e `GET /admin/rbac/summary`; não infere permissões só pelo JWT.

## Clientes HTTP

- `chatApi.ts` — rotas `/chat/*`
- `adminApi.ts` — rotas `/admin/*`

Base: `const API_BASE_URL = "/apps/minha-delpi-ai/api"`.
