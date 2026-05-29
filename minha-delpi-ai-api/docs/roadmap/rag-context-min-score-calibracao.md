# Calibração — `RAG_CONTEXT_MIN_SCORE`

Guia da **Onda 7.4** para ajustar o score mínimo de chunks no contexto do chat.

## O que a variável faz

Após a busca RAG (FTS e/ou vetor), chunks com score abaixo do limiar são **descartados** antes de montar o prompt. Isso reduz ruído e alucinação em perguntas documentais.

- **Código:** `RagContextService.build_context(..., min_score=)` + `Settings.RAG_CONTEXT_MIN_SCORE`
- **Admin:** pode sobrescrever via runtime `ragContextMinScore` (`ChatIntelligenceSettingsService`)
- **Fallback:** se `RAG_CONTEXT_MIN_SCORE` não estiver no `.env`, usa `RAG_ASSERTIVENESS_MIN_SCORE` (default `0.35`)

### Perguntas de identidade do assistente (exceção)

«Quem te criou?», «o que você é?» usam limiar **próprio**, não o global:

| Variável | Default | Quando |
|----------|---------|--------|
| `RAG_IDENTITY_QUESTION_MIN_SCORE` | `0.22` | `ChatAssistantIdentityService` detectou pergunta sobre o assistente em `ChatTurnPreparationService` |

Motivo: embeddings de perguntas meta costumam pontuar ~0.25–0.35 em documentos de arquitetura; com `ragContextMinScore` 0.35+ o contexto vinha vazio e o modelo respondia sem base documental.

A query usa `ChatAssistantIdentityService.build_rag_query` (foco em chat/plataforma; **sem** sufixo `empresa` que puxa normas técnicas). Chunks passam por `is_identity_relevant_chunk` antes de montar o prompt. Ver [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md#identidade-do-assistente-maio2026).

## Valores recomendados por ambiente

| Ambiente | `RAG_CONTEXT_MIN_SCORE` | Observação |
|----------|-------------------------|------------|
| **Dev** | `0.30` | Mais contexto para depurar; aceita chunks medianos |
| **Homologação** | `0.35` | Ponto de partida; calibrar com admin **Teste RAG** |
| **Produção CPU (operacional)** | `0.40`–`0.45` | Com fast path ligado, RAG entra menos; score mais alto evita texto fraco |
| **Produção (agente documental)** | `0.35`–`0.40` | Agentes só RAG: não subir demais ou perde cobertura |
| **GPU + hybrid on** | `0.32`–`0.38` | Com rerank/hybrid, scores mudam escala — revalidar após ligar `CHAT_RAG_HYBRID_ENABLED` |

## Procedimento de calibração (homologação)

1. Admin → **Diretrizes** → **Teste RAG** com 10–15 perguntas reais do domínio do agente.
2. Anotar para cada pergunta: chunks retornados, score do top-1 e se a resposta do chat citou fonte correta.
3. Se muitas perguntas **sem chunk** útil → **baixar** 0.02 (ex.: `0.35` → `0.33`).
4. Se respostas **inventam** a partir de trechos fracos → **subir** 0.02–0.05.
5. Persistir no runtime admin ou `.env` e registrar data/valor em `status-atual.md`.

## Combinação com outras flags (CPU)

Para agentes **operacionais** (api-delpi), priorize pipeline de actions; RAG é complemento:

```env
CHAT_OPERATIONAL_FAST_PATH_ENABLED=true
CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED=true
CHAT_RAG_HYBRID_ENABLED=false
CHAT_RAG_PREFER_KEYWORD_SEARCH=true
EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED=false
RAG_CONTEXT_MIN_SCORE=0.40
```

Para agentes **documentais** (RH, políticas):

```env
CHAT_RAG_HYBRID_ENABLED=false
CHAT_RAG_PREFER_KEYWORD_SEARCH=true
RAG_CONTEXT_MIN_SCORE=0.35
MAX_CONTEXT_CHUNKS=4
```

## Homologação de latência (Onda 7.5 / 11.2.2)

### Preset por ambiente

Use `CHAT_LLM_LATENCY_PROFILE` quando não quiser calibrar `LLM_MAX_TOKENS` e `OLLAMA_NUM_CTX` manualmente. Variáveis explícitas **sempre** têm prioridade.

| Perfil | `LLM_MAX_TOKENS` | `OLLAMA_NUM_CTX` | Quando |
|--------|------------------|------------------|--------|
| `operational_cpu` | 384 | 1536 | Homologação / produção CPU operacional (meta p95 &lt; 15s) |
| `balanced` | 1536 | 2048 | Dev local (default) |
| `documental` | 768 | 4096 | Agentes só RAG ou GPU/16GB+ |

Exemplo homologação:

```env
CHAT_LLM_LATENCY_PROFILE=operational_cpu
CHAT_OPERATIONAL_FAST_PATH_ENABLED=true
CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED=true
```

Status do perfil ativo: campo `latencyProfile` em `GET /chat/llm/status` (admin).

### Checklist manual CPU

| Pergunta | Meta p95 | Pipeline esperado |
|----------|----------|-------------------|
| Estoque do produto `10080047` | &lt; 15 s | Fast path → action → resposta direta |
| Descrição do mesmo código | &lt; 20 s | Action ou RAG mínimo + LLM curto |
| CPV / valor total estoque | &lt; 25 s | Action suprimentos → direta ou LLM |
| Política interna (só RAG) | &lt; 30 s | FTS + LLM |

Registrar em `docs/12-roadmap-e-evolucao/minha-delpi-chat/status-atual.md` após medição.

## Referências

- [inteligencia-chat-onda-7.md](./inteligencia-chat-onda-7.md)
- [variaveis-de-ambiente.md](../../../docs/02-infraestrutura/variaveis-de-ambiente.md)
