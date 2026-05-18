# Inteligência do chat — Onda 5

**Status:** implementada (maio/2026)  
**Pré-requisitos:** [Ondas 1–4](./inteligencia-chat-onda-1.md)

## Objetivo

Escalar cache de embeddings entre réplicas e permitir tool-calling nativo do provedor LLM, mantendo fallback para heurísticas e loop agentic.

| # | Entrega | Descrição |
|---|---------|-----------|
| 5.1 | Cache distribuído | `EmbeddingCachePort` com Redis (opcional) e fallback em memória |
| 5.2 | Tool-calling nativo | LLM escolhe tools internas via schema OpenAI; fallback para heurísticas |
| 5.3 | Observabilidade | Latência por etapa (`ragMs`, `toolsMs`, `llmMs`) e stats de cache em `intelligence` |

## Variáveis

| Variável | Default |
|----------|---------|
| `EMBEDDING_CACHE_BACKEND` | `memory` (`memory` \| `redis`) |
| `REDIS_URL` | — |
| `CHAT_NATIVE_TOOL_CALLING_ENABLED` | `false` |
| `EMBEDDING_CACHE_ENABLED` | `true` |

Admin: `nativeToolCallingEnabled`, demais flags das ondas anteriores.

## Critérios de aceite

- [x] Com `EMBEDDING_CACHE_BACKEND=redis` e Redis indisponível, usa memória sem quebrar o chat  
- [x] Com tool-calling nativo ligado (admin + env), vLLM/Ollama podem retornar `tool_calls` executadas antes do LLM final  
- [x] Com nativo desligado ou sem suporte, fluxo idêntico à Onda 4  
- [x] Metadados `intelligence.timings` e `intelligence.embeddingCache` nas mensagens  

## Comportamento tool-calling nativo

- Tools elegíveis: `get_current_user`, `get_allowed_apps`, `get_allowed_routes`, `search_knowledge_base`  
- `execute_external_action` permanece no fluxo heurístico/semântico (OpenAPI)  
- Router LLM de tools é ignorado quando o nativo já selecionou ferramentas  
