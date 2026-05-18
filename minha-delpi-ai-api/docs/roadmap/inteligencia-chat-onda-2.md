# Inteligência do chat — Onda 2

**Status:** implementada (maio/2026)  
**Pré-requisito:** [Onda 1](./inteligencia-chat-onda-1.md)

## Objetivo

Reduzir latência e aumentar precisão do roteamento de ferramentas/actions, com governança via admin.

| # | Entrega | Descrição |
|---|---------|-----------|
| 2.1 | Embeddings em `ai_external_actions` | Coluna `embedding`, geração no import OpenAPI e backfill admin |
| 2.2 | Busca vetorial de actions | `search_similar_actions` — ranker usa pgvector antes de re-embed on-the-fly |
| 2.3 | Config runtime admin | `GET/PUT /admin/chat/intelligence-settings` em `ai_admin_runtime_settings` |
| 2.4 | Resumo de histórico | `ChatHistorySummaryService` quando sessão > `CHAT_HISTORY_SUMMARY_TRIGGER_MESSAGES` |
| 2.5 | Router LLM | `ChatToolRouterService` — JSON com tools/actionId autorizados |

## Migration

```bash
flask --app app.main:app db upgrade
# f7a8b9c0d1e2 — embedding em ai_external_actions
```

Após import de providers existentes:

```http
POST /admin/tools/actions/reindex-embeddings
{ "providerKey": "opcional" }
```

## Variáveis de ambiente

| Variável | Default |
|----------|---------|
| `CHAT_TOOL_ROUTER_ENABLED` | `true` |
| `CHAT_TOOL_ROUTER_MAX_ACTIONS` | `20` |
| `CHAT_HISTORY_SUMMARY_ENABLED` | `true` |
| `CHAT_HISTORY_SUMMARY_TRIGGER_MESSAGES` | `16` |
| `CHAT_HISTORY_SUMMARY_MAX_CHARS` | `1500` |
| `EXTERNAL_ACTION_EMBEDDING_ON_IMPORT` | `true` |

Limiares RAG/actions podem ser sobrescritos pelo admin (`ragContextMinScore`, etc.).

## Onda 3 (futuro)

- Tool-calling nativo em loop agentic
- RAG híbrido BM25 + vetor + rerank
- Cache de embeddings de actions em memória/Redis
