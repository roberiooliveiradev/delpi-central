# Inteligência do chat — Onda 3

**Status:** implementada (maio/2026)  
**Pré-requisitos:** [Onda 1](./inteligencia-chat-onda-1.md), [Onda 2](./inteligencia-chat-onda-2.md)

## Objetivo

Melhorar recall do RAG, reduzir latência de embeddings e permitir rodadas extras de tools antes da resposta final.

| # | Entrega | Descrição |
|---|---------|-----------|
| 3.1 | RAG híbrido | Busca vetorial + keyword (BM25-like) com fusão e rerank |
| 3.2 | Cache de embeddings | TTL em memória para texto de actions e queries repetidas |
| 3.3 | Loop agentic | Até N rodadas extras de seleção/execução de tools via LLM |

## Ordem de implementação

1. **3.2** Cache de embeddings  
2. **3.1** RAG híbrido em `SearchKnowledgeUseCase`  
3. **3.3** `ChatAgenticToolLoopService` integrado ao fluxo de mensagem  

## Variáveis de ambiente

| Variável | Default |
|----------|---------|
| `CHAT_RAG_HYBRID_ENABLED` | `true` |
| `CHAT_RAG_HYBRID_VECTOR_WEIGHT` | `0.7` |
| `CHAT_RAG_HYBRID_KEYWORD_WEIGHT` | `0.3` |
| `CHAT_RAG_HYBRID_CANDIDATE_MULTIPLIER` | `4` |
| `EMBEDDING_CACHE_ENABLED` | `true` |
| `EMBEDDING_CACHE_TTL_SECONDS` | `3600` |
| `EMBEDDING_CACHE_MAX_ENTRIES` | `500` |
| `CHAT_AGENTIC_LOOP_ENABLED` | `false` |
| `CHAT_AGENTIC_LOOP_MAX_STEPS` | `2` |

Admin (`chat_intelligence_settings`): `ragHybridEnabled`, `agenticLoopEnabled`, `agenticLoopMaxSteps`.

## Critérios de aceite

- [x] Pergunta com termo exato no documento recupera chunk mesmo com score vetorial baixo  
- [x] Re-embed da mesma action não chama Ollama dentro do TTL  
- [x] Com `CHAT_AGENTIC_LOOP_ENABLED=true`, planner LLM pode disparar tools extras  
- [x] Com loop desligado, comportamento idêntico à Onda 2  

## Próxima onda

[Onda 4](./inteligencia-chat-onda-4.md)
