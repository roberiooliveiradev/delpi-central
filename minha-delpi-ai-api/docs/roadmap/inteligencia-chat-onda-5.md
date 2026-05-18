# Inteligência do chat — Onda 5

**Status:** em implementação (5.1 em andamento)  
**Pré-requisitos:** [Ondas 1–4](./inteligencia-chat-onda-1.md)

## Objetivo

Escalar cache de embeddings entre réplicas e avaliar tool-calling nativo do provedor LLM, mantendo fallback para o loop agentic atual.

| # | Entrega | Descrição |
|---|---------|-----------|
| 5.1 | Cache distribuído | `EmbeddingCachePort` com Redis (opcional) e fallback em memória |
| 5.2 | Tool-calling nativo | Quando o gateway suportar `tools`, delegar seleção ao LLM com schema OpenAPI reduzido |
| 5.3 | Observabilidade | Métricas de hit/miss do cache e latência por etapa no metadata `intelligence` |

## Ordem sugerida

1. **5.1** Port + adapter Redis para embeddings (em andamento)  
2. **5.2** Feature flag `CHAT_NATIVE_TOOL_CALLING_ENABLED`  
3. **5.3** Instrumentação admin/métricas  

### 5.1 — entregue parcialmente

- `EmbeddingCachePort` + `RedisEmbeddingCache` com fallback para memória  
- `EMBEDDING_CACHE_BACKEND` (`memory` \| `redis`) e `REDIS_URL`  
- Gateway singleton compartilhado + `embeddingCache` nos metadados `intelligence`  

## Variáveis (proposta)

| Variável | Default |
|----------|---------|
| `EMBEDDING_CACHE_BACKEND` | `memory` (`memory` \| `redis`) |
| `REDIS_URL` | — |
| `CHAT_NATIVE_TOOL_CALLING_ENABLED` | `false` |

## Fora de escopo

- Troca de modelo LLM padrão  
- Mudanças de contrato HTTP no plugin (salvo exibir novos campos em `intelligence`)
