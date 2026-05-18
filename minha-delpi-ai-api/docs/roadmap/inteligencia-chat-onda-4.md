# Inteligência do chat — Onda 4

**Status:** em implementação  
**Pré-requisitos:** [Ondas 1–3](./inteligencia-chat-onda-1.md)

## Objetivo

Refinar qualidade do RAG e do loop agentic sem exigir tool-calling nativo do provedor LLM.

| # | Entrega | Descrição |
|---|---------|-----------|
| 4.1 | Rerank pós-híbrido | Re-score dos candidatos fusionados antes do corte final |
| 4.2 | Loop agentic incremental | Novas tools mesmo quando heurísticas já rodaram; sem duplicar execução |
| 4.3 | FTS no keyword RAG | `plainto_tsquery` no Postgres quando disponível, fallback ILIKE |
| 4.4 | Metadados de inteligência | `intelligence` no metadata da mensagem (flags, scores, passos agentic) |

## Variáveis

| Variável | Default |
|----------|---------|
| `CHAT_RAG_RERANK_ENABLED` | `true` |
| `CHAT_RAG_RERANK_KEYWORD_BOOST` | `0.15` |
| `CHAT_RAG_FTS_ENABLED` | `true` |

Admin: `ragRerankEnabled`, `ragFtsEnabled`.
