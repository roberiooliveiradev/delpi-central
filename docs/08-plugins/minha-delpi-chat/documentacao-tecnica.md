# Documentação técnica — Minha DELPI Chat AI

> **Status:** documentação oficial (jun/2026)  
> **Público:** desenvolvimento backend, frontend, DevOps e arquitetura  
> **Produto:** assistente conversacional corporativo da plataforma Minha DELPI

---

## 1. Objetivo

Este documento é o **ponto de entrada** da documentação técnica do **Minha DELPI Chat AI**. Ele descreve a arquitetura macro, os componentes, os fluxos principais e aponta para a documentação detalhada já existente no monorepo.

Para contratos HTTP endpoint a endpoint, use a referência da API. Para regras de inteligência transversal (pipeline, tools, RAG, apresentação), use a arquitetura do chat base.

---

## 2. Visão geral do produto

O **Minha DELPI Chat** é um assistente conversacional integrado ao portal corporativo. Permite:

- conversas com histórico, streaming e feedback;
- consulta a dados operacionais (via **api-delpi**) com apresentação rica (tabela, gráfico, árvore, KPI);
- base de conhecimento documental (RAG com pgvector);
- **agentes** configuráveis (prompt, skills, actions OpenAPI);
- **projetos** com instruções, ícone e conversas agrupadas (sem colaboração multiusuário por enquanto);
- anexos, lousa (canvas), pesquisa web e painel administrativo.

### Princípio arquitetural central

O **chat** é o núcleo de inteligência. **Agentes**, **projetos** e simulação admin **herdam** o mesmo pipeline — não reimplementam lógica paralela.

| Conceito | Papel |
|----------|--------|
| **Chat (sessão)** | Pipeline de mensagens, histórico, tools, RAG, LLM |
| **Agente** | `system_prompt`, skills, actions permitidas, escopo RAG |
| **Projeto** | Agrupamento de sessões, prompt de projeto, agente default |
| **Skill** | Comportamento injetado no prompt (ex.: SQL, normas, visão documental) |
| **Action** | Rota OpenAPI executável (ex.: estoque, estrutura, `/data/sql`) |

Detalhes: [`minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md`](../../../minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md).

---

## 3. Componentes no monorepo

```text
┌─────────────────────────────────────────────────────────────────┐
│                         Usuário (browser)                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Gateway Nginx                                                   │
│  /apps/minha-delpi-chat/*     → plugin MFE (assets)             │
│  /apps/minha-delpi-ai/api/*   → minha-delpi-ai-api              │
└───────────────┬─────────────────────────────┬───────────────────┘
                │                             │
                ▼                             ▼
┌───────────────────────────┐   ┌─────────────────────────────────┐
│  plugins/minha-delpi-chat │   │  minha-delpi-ai-api (Flask)     │
│  React + Module Federation│   │  Clean Architecture             │
└───────────────────────────┘   └───────────┬─────────────────────┘
                                            │
              ┌─────────────────────────────┼─────────────────────────┐
              │                             │                         │
              ▼                             ▼                         ▼
   ┌──────────────────┐        ┌──────────────────┐      ┌──────────────────┐
   │  postgres-plugins │        │  Ollama / vLLM   │      │  api-delpi       │
   │  (pgvector)       │        │  (LLM)           │      │  (dados TOTVS)   │
   └──────────────────┘        └──────────────────┘      └──────────────────┘
              │
              ▼
   ┌──────────────────┐
   │  Core API        │  JWT, RBAC, /me, consentimentos LGPD
   │  Keycloak        │  SSO
   └──────────────────┘
```

### Identificação e URLs

| Campo | Valor |
|-------|--------|
| Plugin ID | `minha-delpi-chat` |
| `basePath` | `/apps/minha-delpi-chat` |
| API backend | `/apps/minha-delpi-ai/api` |
| Container Docker (dev) | `delpi-minha-delpi-chat` / `minha-delpi-ai-api` |
| Manifesto | [`plugins/minha-delpi-chat/delpi.manifest.json`](../../../plugins/minha-delpi-chat/delpi.manifest.json) |

---

## 4. Backend — minha-delpi-ai-api

### 4.1 Stack e requisitos

| Item | Tecnologia |
|------|------------|
| Runtime | Python 3.12+, Flask |
| Banco | PostgreSQL 15+ com **pgvector** (`postgres-plugins`) |
| Auth | JWT Keycloak (mesmo padrão issuer/JWKS da plataforma) |
| LLM (dev) | Ollama |
| LLM (prod) | vLLM (opcional) |
| Embeddings | Serviço interno + cache configurável |

Setup local: [`minha-delpi-ai-api/README.md`](../../../minha-delpi-ai-api/README.md).

### 4.2 Clean Architecture

```text
interfaces/http/routes/     → handlers finos (< 40 linhas)
application/use_cases/      → orquestração (Send, Stream, Admin…)
application/services/       → serviços de turno, RAG, tools, stream
domain/services/            → regras de negócio, presenter, intent
domain/prompt_policies/     → policies Markdown globais
infrastructure/             → Postgres, gateways HTTP, LLM, loaders JSON
composition/                → factories (DI / composition root)
```

**Regras obrigatórias:**

- `domain` **não** importa `infrastructure` nem `interfaces`;
- textos PT-BR para usuário ficam em `app/content/pt-BR/assistant/*.json`;
- send e stream compartilham os mesmos serviços de preparação e conclusão do turno.

Playbook: [`minha-delpi-ai-api/docs/roadmap/playbook-11-clean-architecture-chat-api.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-11-clean-architecture-chat-api.md).

ADRs: [`minha-delpi-ai-api/docs/architecture/adr/README.md`](../../../minha-delpi-ai-api/docs/architecture/adr/README.md).

### 4.3 Estrutura de código

```text
minha-delpi-ai-api/
  app/
    application/
      use_cases/              # SendChatMessage, StreamChatMessage, …
      services/
        chat_turn/            # ChatTurnPreparationService, Completion…
    domain/
      services/               # Intent, presenter, SQL, memória…
      prompt_policies/        # *.md (analysis_mode, web-search…)
    content/pt-BR/assistant/  # Bundles JSON (textos de UI)
    infrastructure/           # Repositories, gateways, settings
    interfaces/http/routes/   # /chat, /admin, /knowledge, /tools
    composition/              # make_* composers
  migrations/                 # Alembic
  tests/unit/                 # pytest
  docs/                       # Documentação técnica da API
```

### 4.4 Blueprints HTTP

| Prefixo | Responsabilidade |
|---------|------------------|
| `/health` | Health check |
| `/chat` | Sessões, mensagens, agentes, projetos, anexos, capabilities |
| `/knowledge` | Ingestão e busca RAG |
| `/tools` | Execução direta de tools internas |
| `/admin` | Painel admin, métricas, auditoria, simulação |

Referência completa: [`minha-delpi-ai-api/docs/api/README.md`](../../../minha-delpi-ai-api/docs/api/README.md).

---

## 5. Pipeline de inteligência (turno de mensagem)

Fluxo simplificado de um turno (`POST .../messages/stream` ou send síncrono):

```text
Mensagem do usuário
  │
  ├─► Segurança de entrada (sanitização, anti-injection)
  │
  ├─► ChatWorkspaceContextService
  │     projeto + agente + capabilities + consentimento LGPD
  │
  ├─► ChatSimpleTurnGateService (opcional short-circuit)
  │     identidade, small talk, utilidades, pedido vago → resposta direta
  │
  ├─► ChatTurnPreparationService
  │     ├─ RAG (escopo agente/projeto/anexos)
  │     ├─ Seleção de tools/actions (ExternalActionSelectionService)
  │     ├─ Execução de tools (ChatToolContextService)
  │     └─ Direct answers (SQL, operacional, web, e-mail, texto…)
  │
  ├─► ChatPromptBuilderService + prompt_policies
  │
  ├─► LLM (stream ou send) — quando necessário
  │
  └─► ChatTurnCompletionService
        metadata, persistência, memória, adminDebug, feedback context
```

**Serviços centrais** (não duplicar lógica nos use cases):

| Serviço | Função |
|---------|--------|
| `ChatIntelligencePipelineService` | Decisões pré/pós-tools compartilhadas |
| `ChatTurnPreparationService` | Preparação unificada send/stream |
| `ChatTurnCompletionService` | Conclusão pós-LLM unificada |
| `ChatToolContextService` | Seleção e execução de tools/actions |
| `ExternalActionSelectionService` | Roteamento heurístico api-delpi |
| `ExternalActionResultPresenter` | Apresentação rica (`humanizedSummary`, tabelas, gráficos) |

Documentação completa: [`chat-intelligence-base.md`](../../../minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md).

Camadas pré-LLM (modelo alvo): [`chat-pre-llm-layers.md`](../../../minha-delpi-ai-api/docs/architecture/chat-pre-llm-layers.md).

### 5.1 Streaming SSE

Eventos principais no stream:

| Evento | Significado |
|--------|-------------|
| `status` | Conexão estabelecida |
| `user_persisted` | Mensagem do usuário gravada (id real) |
| `activity` | Etapa do pipeline (headline humanizado + detail técnico) |
| `assistant_pending` | Placeholder do assistente (`delivery=generating`) |
| `playback` | Texto final para animação de digitação |
| `canvas_open` | Abertura/atualização da lousa |
| `done` | Turno concluído |

Variável: `CHAT_PERSIST_BEFORE_PLAYBACK=true` (default) — persiste antes do playback.

Doc HTTP: [`02-chat-sessoes-mensagens.md`](../../../minha-delpi-ai-api/docs/api/02-chat-sessoes-mensagens.md).

### 5.2 Respostas diretas (sem LLM)

Atalhos determinísticos para reduzir latência e custo:

| Categoria | Serviço exemplo | Gatilho |
|-----------|-----------------|---------|
| Identidade do assistente | `ChatAssistantIdentityService` | «quem é você?» |
| Perfil do usuário | `ChatUserContextService` | «quem sou eu?» |
| Small talk | `ChatSmallTalkService` | saudação, agradecimento |
| Utilidades | `ChatUtilityDirectAnswerService` | hora, data, dia da semana |
| Capacidades | `ChatCapabilitiesService` | «consegue buscar por grupo?» |
| Operacional | `ChatOperationalParameterService` | estoque sem código de produto |
| Interpretação de dados | `ChatDataInterpretationAnswerService` | «explique os dados acima» |
| Web search | `ChatWebSearchDirectAnswerService` | pesquisa com poucas fontes |

---

## 6. Frontend — plugin minha-delpi-chat

### 6.1 Stack

| Item | Tecnologia |
|------|------------|
| Framework | React + TypeScript |
| Build | Vite + Module Federation |
| Integração | Portal carrega `remoteEntry.js` |
| HTTP | `chatApi.ts`, `adminApi.ts` |

Setup: [`plugins/minha-delpi-chat/README.md`](../../../plugins/minha-delpi-chat/README.md).

### 6.2 Estrutura de código

```text
plugins/minha-delpi-chat/src/
  data/api/           # chatApi, adminApi, tipos
  state/
    hooks/            # useChatSession, useChatStreaming, …
    chatStreamHandoff.ts
  ui/
    pages/            # ChatPage, ChatAdminPage, ChatAgentsPage
    components/       # ChatAssistantContent, admin, apresentação
  content/            # Cópias espelhadas de bundles JSON (sync)
```

### 6.3 Módulos canônicos de UI (não duplicar)

| Domínio | Módulo canônico |
|---------|-----------------|
| Prosa/markdown/streaming | `assistantProseRendering.ts`, `chatMarkdown.ts` |
| Apresentação rica | `ChatAssistantContent`, `chatPresentation.ts` |
| Segmentos visuais | `assistantContentSegments.ts`, `renderPlanSegmentBuilder.ts` |
| Ativação de agente | `chatAgentActivation.ts` |
| Log de atividade SSE | `streamingActivityLog.ts`, `ChatStreamingActivityPanel` |
| Overlays/menus composer | `shared/overlay/AnchoredMenuPortal`, `shared/composer/ComposerOptionSelector` |

Doc apresentação: [`chat-assistant-content-presentation.md`](../../../minha-delpi-ai-api/docs/architecture/chat-assistant-content-presentation.md).

**Refatoração frontend (componentes compartilhados, CSS, tokens):** [`frontend-refactor-roadmap.md`](../../../plugins/minha-delpi-chat/docs/frontend-refactor-roadmap.md) · mapa de pastas: [`component-structure.md`](../../../plugins/minha-delpi-chat/docs/component-structure.md).

### 6.4 Painel administrativo

6 seções (admin v2): Painel, Conhecimento, Agentes, Qualidade, Plataforma, Governança.

Requer permissão `minha-delpi.chat.admin`. O frontend consulta `GET /chat/capabilities` — **não** infere permissões só pelo JWT.

Doc: [`08-admin.md`](../../../minha-delpi-ai-api/docs/api/08-admin.md).

### 6.5 Workspace — projetos, agentes e composer (jun/2026)

Entregas da sessão **17–18/06/2026**. Detalhes: [changelog workspace](../../../minha-delpi-ai-api/docs/changelog/2026-06-workspace-projetos-agentes-ui.md).

| Área | Destaques |
|------|-----------|
| **Projetos** | Create (nome + ícone), `ChatProjectSettingsModal`, «Gerenciar projeto», drag-and-drop conversa→projeto na sidebar |
| **Agentes** | `ChatLucideIconPickerModal` (catálogo Lucide); `ChatAgentIcon` + `lucideIconResolver.ts` |
| **Composer** | `ChatComposerContextBadges`; menus `@`/`+` ancorados no caret |
| **Modais** | Botões canônicos `mdc-chat-modal-icon-btn` / `mdc-chat-modal-tool-btn` em `chat-modal.css` |
| **Colaboração** | Desativada (`PROJECT_COLLABORATION_ENABLED`); roadmap em `projetos-colaborativos-futuro.md` |

API correlata: `PATCH /chat/sessions/{id}` com `projectId`; `UpdateChatSessionUseCase`.

---

## 7. Modelo conceitual

```text
Usuário
  └── Sessão de chat
        ├── Mensagens (user / assistant)
        ├── Fontes, anexos, artefatos
        ├── Projeto (opcional)
        └── Agente (opcional)
              ├── Skills (comportamento no prompt)
              └── Actions (rotas OpenAPI via providers)
                    └── api-delpi, providers externos
```

Entidades e relações: [`12-modelo-conceitual.md`](../../../minha-delpi-ai-api/docs/api/12-modelo-conceitual.md).

### Publicação de agente

- Rascunho editável no builder;
- **Publicar** (`POST /chat/agents/{id}/publish`) gera `published_version` / `published_config`;
- Visitantes só veem versão publicada (`published_version >= 1`).

Doc: [`03-agentes.md`](../../../minha-delpi-ai-api/docs/api/03-agentes.md).

---

## 8. Integrações externas

| Sistema | Uso no chat |
|---------|-------------|
| **Core API** | `/me`, perfil RBAC, consentimentos LGPD, busca de usuários |
| **api-delpi** | Dados operacionais TOTVS via actions OpenAPI |
| **Ollama / vLLM** | Geração de texto, síntese web, visão documental (opcional) |
| **Provedores web** | Tavily, Serper, Bing, SearXNG, DuckDuckGo (configurável) |
| **SearXNG** | Instância self-hosted no compose dev (profile `chat`) |

Mapa intenção → rota api-delpi: [`api-delpi-rotas-agente.md`](../../../minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md).

Contrato de respostas api-delpi → presenter: [`playbook-10-contrato-respostas-api-delpi.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md).

---

## 9. Banco de dados

| Item | Valor |
|------|--------|
| Serviço Docker | `postgres-plugins` |
| Imagem | `pgvector/pgvector:pg15` |
| Porta host (dev) | `5433` |
| Migrations | Automáticas no boot (`docker-entrypoint.sh` → `flask db upgrade`) |

Tabelas principais:

```text
ai_chat_sessions, ai_chat_messages, ai_chat_message_feedback
ai_chat_session_memory, ai_chat_agents, ai_chat_agent_actions
ai_knowledge_documents, ai_knowledge_chunks
ai_external_action_providers, ai_external_actions
ai_audit_logs, ai_admin_runtime_settings
```

Schema e deploy: [`09-deploy-migrations-schema.md`](../../../minha-delpi-ai-api/docs/api/09-deploy-migrations-schema.md).

Memória de sessão: [`session-memory.md`](../../../minha-delpi-ai-api/docs/architecture/session-memory.md).

---

## 10. Conteúdo e internacionalização

Textos exibidos ao usuário (títulos, mensagens, rótulos, erros, chips) ficam em:

```text
minha-delpi-ai-api/app/content/pt-BR/assistant/*.json
```

Carregados por serviços `*ContentService` — **proibido** hardcode de frases PT em Python/TypeScript.

Catálogo: [`assistant-content-catalog.md`](../../../minha-delpi-ai-api/docs/architecture/assistant-content-catalog.md).

No MFE, bundles espelhados em `plugins/minha-delpi-chat/src/content/` (sync documentado nos READMEs).

---

## 11. Permissões RBAC

| Permissão | Finalidade |
|-----------|------------|
| `minha-delpi.chat.access` | Acesso geral ao módulo |
| `minha-delpi.chat.ask` | Enviar mensagens, fontes, anexos |
| `minha-delpi.chat.history.view` | Histórico autorizado |
| `minha-delpi.chat.knowledge.manage` | Gestão de conhecimento |
| `minha-delpi.chat.tools.use` | Uso de tools/actions |
| `minha-delpi.chat.tools.manage` | Agentes e actions próprios |
| `minha-delpi.chat.admin` | Administração e agentes oficiais |

Resolução em runtime: `GET /chat/capabilities`.

---

## 12. Desenvolvimento local

### Subir stack completa

```bash
cd infra
docker compose -f docker-compose.dev.yml up -d
```

Profile chat (SearXNG, Ollama): ver `infra/README-ambiente.md`.

### Backend isolado

```bash
cd minha-delpi-ai-api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
set -a && source ../infra/.env && set +a
export DATABASE_URL="postgresql+psycopg://${PLUGINS_DB_USER}:${PLUGINS_DB_PASSWORD}@localhost:5433/${PLUGINS_DB_NAME}"
flask --app app.main:app db upgrade
flask --app app.main:app run --debug
```

### Frontend isolado

```bash
cd plugins/minha-delpi-chat
npm install
npm run dev
```

Build antes de commitar alterações de UI:

```bash
npm run build
```

### Testes

```bash
# Unitários backend
cd minha-delpi-ai-api && pytest tests/unit -q

# Regressão de inteligência (amostra)
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  pytest tests/unit/domain/services/test_chat_intelligence_regression.py -q
```

Smokes manuais: [`smoke-operacional-manual.md`](../../../minha-delpi-ai-api/docs/testing/smoke-operacional-manual.md).

---

## 13. Variáveis de ambiente (seleção)

Lista completa: `app/infrastructure/config/settings.py` e `infra/.env.dev.example`.

| Variável | Papel |
|----------|--------|
| `DATABASE_URL` | PostgreSQL + pgvector |
| `LLM_PROVIDER` | `ollama` ou `vllm` |
| `OLLAMA_MODEL` | Modelo default (ex.: `qwen2.5:1.5b`) |
| `RAG_CONTEXT_MIN_SCORE` | Score mínimo de chunk no contexto |
| `CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED` | Identidade sem LLM (default `true`) |
| `CHAT_PERSIST_BEFORE_PLAYBACK` | Persistência antes da animação (default `true`) |
| `CHAT_AGENTIC_LOOP_ENABLED` | Loop agentic de tools (default `false`) |
| `CHAT_WEB_SEARCH_ENABLED` | Pesquisa web |
| `CHAT_DOCUMENT_VISION_ENABLED` | OCR PDF/imagem |
| `CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL` | Skill global no chat comum |

Perfis dev/prod documentados: [`chat-intelligence-settings-profiles.md`](../../../minha-delpi-ai-api/docs/knowledge/chat-intelligence-settings-profiles.md).

---

## 14. Índice da documentação existente

### Dentro do pacote API (recomendado para backend)

| Doc | Conteúdo |
|-----|----------|
| [docs/README.md](../../../minha-delpi-ai-api/docs/README.md) | **Índice mestre** da API |
| [development/guia-desenvolvimento.md](../../../minha-delpi-ai-api/docs/development/guia-desenvolvimento.md) | Guia do desenvolvedor |
| [architecture/README.md](../../../minha-delpi-ai-api/docs/architecture/README.md) | Índice de arquitetura |
| [testing/README.md](../../../minha-delpi-ai-api/docs/testing/README.md) | Testes e smokes |

### API HTTP

| Doc | Conteúdo |
|-----|----------|
| [README](../../../minha-delpi-ai-api/docs/api/README.md) | Índice geral |
| [00-visao-geral](../../../minha-delpi-ai-api/docs/api/00-visao-geral.md) | Auth, erros, SSE |
| [02-chat-sessoes-mensagens](../../../minha-delpi-ai-api/docs/api/02-chat-sessoes-mensagens.md) | Sessões, stream, pin |
| [03-agentes](../../../minha-delpi-ai-api/docs/api/03-agentes.md) | CRUD, publicar, preview |
| [04-actions-openapi](../../../minha-delpi-ai-api/docs/api/04-actions-openapi.md) | Providers e rotas |
| [05-projetos-fontes-anexos](../../../minha-delpi-ai-api/docs/api/05-projetos-fontes-anexos-artefatos.md) | Projetos, anexos |
| [08-admin](../../../minha-delpi-ai-api/docs/api/08-admin.md) | Painel admin |
| [10-referencia-rapida-endpoints](../../../minha-delpi-ai-api/docs/api/10-referencia-rapida-endpoints.md) | Tabela consolidada |
| [12-modelo-conceitual](../../../minha-delpi-ai-api/docs/api/12-modelo-conceitual.md) | Entidades |

### Arquitetura

| Doc | Conteúdo |
|-----|----------|
| [chat-intelligence-base](../../../minha-delpi-ai-api/docs/architecture/chat-intelligence-base.md) | Pipeline, serviços, roteamento |
| [chat-pre-llm-layers](../../../minha-delpi-ai-api/docs/architecture/chat-pre-llm-layers.md) | Fases A/B/C antes do LLM |
| [chat-assistant-content-presentation](../../../minha-delpi-ai-api/docs/architecture/chat-assistant-content-presentation.md) | Apresentação rica API+MFE |
| [assistant-content-catalog](../../../minha-delpi-ai-api/docs/architecture/assistant-content-catalog.md) | Bundles JSON |
| [session-memory](../../../minha-delpi-ai-api/docs/architecture/session-memory.md) | Memória e assertividade |
| [intent-routing](../../../minha-delpi-ai-api/docs/architecture/intent-routing.md) | Roteamento de intenção |
| [adr/](../../../minha-delpi-ai-api/docs/architecture/adr/README.md) | Decisões arquiteturais |

### Roadmap e status

| Doc | Conteúdo |
|-----|----------|
| [status-atual](../../12-roadmap-e-evolucao/minha-delpi-chat/status-atual.md) | Estado funcional jun/2026 |
| [roadmap inteligência](../../../minha-delpi-ai-api/docs/roadmap/README.md) | Ondas 1–14 |
| [admin roadmap](../../../minha-delpi-ai-api/docs/roadmap/admin-minha-delpi-chat.md) | Painel admin (concluído) |
| [agentes roadmap](../../../minha-delpi-ai-api/docs/roadmap/agentes-gestao-melhorias.md) | Gestão de agentes |
| [changelog workspace jun/2026](../../../minha-delpi-ai-api/docs/changelog/2026-06-workspace-projetos-agentes-ui.md) | Projetos, agentes, composer, modais |
| [projetos colaborativos (futuro)](../../../minha-delpi-ai-api/docs/roadmap/projetos-colaborativos-futuro.md) | Share editor/viewer — backlog |
| [frontend refactor roadmap](../../../plugins/minha-delpi-chat/docs/frontend-refactor-roadmap.md) | Componentes shared, CSS, tokens, modais |
| [component structure](../../../plugins/minha-delpi-chat/docs/component-structure.md) | Pastas feature (shared, presentation, message, …) |

### Testes e homologação

| Doc | Conteúdo |
|-----|----------|
| [smoke-operacional-manual](../../../minha-delpi-ai-api/docs/testing/smoke-operacional-manual.md) | Checklist manual |
| [perguntas-teste-chat-jun2026](../../../minha-delpi-ai-api/docs/testing/perguntas-teste-chat-jun2026.md) | Casos de teste |
| [homologacao-mvp](../../12-roadmap-e-evolucao/minha-delpi-chat/homologacao-mvp.md) | Homologação MVP |

### Plataforma

| Doc | Conteúdo |
|-----|----------|
| [arquitetura-geral](../../01-arquitetura/arquitetura-geral.md) | Visão macro Minha DELPI |
| [08-plugins README](../README.md) | Inventário de plugins |

---

## 15. Checklist para contribuir

Antes de abrir PR com alteração no chat:

- [ ] A regra está no **módulo canônico** (não patch local no MFE ou use case)?
- [ ] Send e stream usam o **mesmo serviço** para a mesma regra?
- [ ] Texto novo PT-BR está em `assistant/*.json`?
- [ ] Existe teste unitário ou caso em `chat_intelligence_regression_cases.py`?
- [ ] Build do plugin passa (`npm run build`)?
- [ ] `pytest tests/unit` relevante passa?

Regras Cursor (obrigatórias no repo): `.cursor/rules/chat-intelligence-base.mdc`, `clean-architecture-chat-api.mdc`, `centralized-rules-first.mdc`.

---

## 16. Próximas seções (a expandir)

Documentação técnica adicional planejada — indicar prioridade ao time:

| Seção | Escopo |
|-------|--------|
| **Diagramas de sequência** | Turno stream completo (SSE evento a evento) |
| **Guia de novo agente** | Do zero à publicação com actions e RAG |
| **Guia de nova action** | Import OpenAPI → roteamento → presenter |
| **Guia de nova skill** | Policy, registro, injeção no prompt |
| **Runbook produção** | vLLM, scaling, monitoramento, backup pgvector |
| **Troubleshooting** | Erros comuns (RAG vazio, action errada, stream travado) |

---

*Última atualização: jun/2026. Mantenedor: equipe Minha DELPI Chat.*
