# Minha DELPI Chat (plugin)

Microfrontend React do **Minha DELPI Chat**, carregado pelo Portal via Module Federation.

## Documentação

| Área | Caminho |
|------|---------|
| **Documentação técnica (API)** | [../../minha-delpi-ai-api/docs/README.md](../../minha-delpi-ai-api/docs/README.md) |
| API backend (HTTP) | [../../minha-delpi-ai-api/docs/api/README.md](../../minha-delpi-ai-api/docs/api/README.md) |
| Modelo conceitual (chat, skills, actions…) | [../../minha-delpi-ai-api/docs/api/12-modelo-conceitual.md](../../minha-delpi-ai-api/docs/api/12-modelo-conceitual.md) |
| Inteligência no chat base (agentes herdam) | [../../minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md](../../minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md) |
| Skills (API) | [../../minha-delpi-ai-api/docs/api/11-skills.md](../../minha-delpi-ai-api/docs/api/11-skills.md) |
| Admin (componentes) | [src/ui/components/admin/README.md](src/ui/components/admin/README.md) |
| **Refatoração frontend (roadmap)** | [docs/frontend-refactor-roadmap.md](docs/frontend-refactor-roadmap.md) |
| CSS apresentação rica | [docs/rich-presentation-css.md](docs/rich-presentation-css.md) |
| Roadmap admin | [../../minha-delpi-ai-api/docs/roadmap/admin-minha-delpi-chat.md](../../minha-delpi-ai-api/docs/roadmap/admin-minha-delpi-chat.md) |
| Gestão de agentes | [../../minha-delpi-ai-api/docs/roadmap/agentes-gestao-melhorias.md](../../minha-delpi-ai-api/docs/roadmap/agentes-gestao-melhorias.md) |
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
  state/             # chatStreamHandoff.ts, chatMessageDelivery.ts
  state/hooks/       # useChatSession, useChatAdmin, …
  ui/
    pages/           # ChatPage, ChatAdminPage, ChatAgentsPage
    components/      # chat, admin (abas modulares)
    components/shared/  # primitivos overlay, composer, menus — ver docs/frontend-refactor-roadmap.md
    components/presentation/  # ChatRich* (tabela, gráfico, KPI, árvore, dashboard)
```

Ver roadmap de refatoração frontend: [docs/frontend-refactor-roadmap.md](docs/frontend-refactor-roadmap.md).

## Experiência do usuário (chat)

- Sessões com pin, arquivo e renomear
- Mensagens com streaming, fontes, tool calls e anexos (cards na timeline com `readingStatus`; edição de anexos ao **reenviar** pergunta com preview em card/modal)
- Log de atividade em tempo real (SSE `activity`) com três pontos pulsando durante o carregamento
- Tabelas/gráficos/árvore/KPI via **`ChatAssistantContent`** — ver [Apresentação no chat](../../minha-delpi-ai-api/docs/architecture/chat-assistant-content-presentation.md)
- **Exportação de apresentações:** tabelas, gráficos, árvores, KPIs e dashboards expõem **CSV**, **Excel** e **PDF** na toolbar (`ChatPresentationExportButtons` + `exportUtils.ts`); gráficos mantêm **PNG**; PDF de gráfico usa rasterização SVG quando disponível
- **Lousa (canvas):** card inline na conversa com prévia do markdown + modal para editar/salvar; comando «coloque na lousa/canvas» após uma resposta do assistente
- Playback da resposta após persistência no servidor (efeito de digitação sem perder texto ao recarregar)
- **Handoff stream → histórico:** ao concluir o turno, `chatStreamHandoff` insere a mensagem do assistente na timeline antes de desmontar a bolha de streaming (evita piscar / placeholder `generating` vazio); `loadMessages` em background sincroniza com o servidor
- **Feedback** (thumbs up/down) em respostas do assistente
- Agentes, projetos, fontes e anexos por contexto
- **Corretor de digitação (Playbook 14):** chip pré-envio para typos operacionais (`estouque` → `estoque`); aceitar ou manter original; textos em `message_composer.json` (sync: `npm run sync:message-composer-content`)
- Notificações (sino) quando habilitado na Core API

### Gestão de agentes (plugin)

Fluxo: **Lista de agentes** → **Builder** (configurar) → **Skills** (comportamento) / **Actions** (OpenAPI).

| Recurso | Descrição |
|---------|-----------|
| Builder | Instruções, visibilidade, **quebra-gelos** (antes de Skills; placeholders `{{productCode}}`), **publicar** rascunho, preview, stats colapsáveis, duplicar |
| Skills | Comportamentos de prompt por agente (ex.: Especialista SQL, company-knowledge); badge de execução SQL quando action `/data/sql` habilitada |
| Actions | Providers OpenAPI, rotas, teste e logs |
| Compartilhar | Busca de usuário (sem UUID manual); editar papel viewer/editor |
| Transferir | Dono pode transferir propriedade |
| Export / Import | JSON portável da configuração + actions |
| Duplicate | `copyActions` e `copySources` opcionais |
| Lista | Métricas de uso (7 dias), inativos, badges de papel |
| Preview | Simulação com rascunho (`POST /chat/agents/preview` ou `.../{id}/preview`) antes de publicar |
| Publicar | `POST /chat/agents/{id}/publish` — visitantes só veem versão publicada |

Detalhes: [roadmap agentes](../../minha-delpi-ai-api/docs/roadmap/agentes-gestao-melhorias.md).

## Apresentação rica (desenvolvimento)

| Tópico | Onde |
|--------|------|
| Arquitetura API + MFE | [`chat-assistant-content-presentation.md`](../../minha-delpi-ai-api/docs/architecture/chat-assistant-content-presentation.md) |
| Corretor de digitação (composer) | [Playbook 14](../../minha-delpi-ai-api/docs/roadmap/playbook-14-corretor-digitacao-chat.md) · [changelog](../../minha-delpi-ai-api/docs/changelog/2026-06-playbook-14-corretor-digitacao-composer.md) |
| Playbook 09 (decisão de formato) | [`playbook-09-apresentacao-rica.md`](../../minha-delpi-ai-api/docs/roadmap/playbook-09-apresentacao-rica.md) |
| Novo componente visual | `registerAssistantSegmentRenderer` em `src/ui/components/assistantContentRegistry.tsx` |
| Segmentos / layout | `assistantContentSegments.ts`, `assistantContentLayout.ts`, `assistantContentVisualFormats.ts` |
| Entrada única na UI | `ChatMessageList` → `ChatAssistantContent` (não usar `ChatRichPresentation` — removido) |

## Painel administrativo

Acesso via botão **Admin** na UI (requer `minha-delpi.chat.admin`).

Navegação em **6 seções** (sub-abas por seção). No topo deve aparecer `admin-v2-6secoes` ao lado do título — se ainda vir 10 abas planas (Conhecimento, Métricas, Diretrizes…), o MFE no Docker está desatualizado:

```bash
cd infra
docker compose -f docker-compose.dev.yml up --build -d minha-delpi-chat
```

Depois: hard refresh no browser (Ctrl+Shift+R).

| Seção | Sub-abas | Função |
|-------|----------|--------|
| Painel | — | KPIs e atalhos |
| Conhecimento | Documentos, Diretrizes, Comportamentos | Base global, skills |
| Agentes | Especialização, Simulação | Agentes e sandbox |
| Qualidade | Métricas, Avaliações | Observabilidade e feedback |
| Plataforma | Ferramentas, Inteligência | Tools/LLM e toggles do pipeline |
| Governança | Segurança, Auditoria | RBAC, scan, trilha |

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
