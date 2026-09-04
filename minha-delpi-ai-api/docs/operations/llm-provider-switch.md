# Troca de provedor LLM — operação

**Seletor único:** `LLM_PROVIDER`. Texto, embeddings e visão **herdam** esse valor quando `EMBEDDING_PROVIDER` / `VISION_LLM_PROVIDER` estão vazios.

Hoje: `openai_compatible` + `KIMI_*` (OpenRouter). Para Ollama local: `LLM_PROVIDER=ollama`. Não apontar `http://ollama:11434` fora dos gateways de infra.

Guia: [tutorial-conectar-llm-externo.md](./tutorial-conectar-llm-externo.md)  
Playbook: [playbook-24-llm-provider-pluggable-jul2026.md](../roadmap/playbook-24-llm-provider-pluggable-jul2026.md)  
Regra Cursor: `llm-stack-centralized.mdc`.

---

## Capacidades independentes

| Eixo | Variável principal | Default |
|------|-------------------|---------|
| Texto (chat) | `LLM_PROVIDER` | herda env; sem valor → `ollama` |
| Embeddings (RAG) | `EMBEDDING_PROVIDER` | **vazio = mesmo eixo do texto** (`LLM_PROVIDER`) |
| Visão (VLM) | `VISION_LLM_PROVIDER` | `ollama` (em prod Kimi: `openai_compatible`) |

Com `LLM_PROVIDER=openai_compatible` (Kimi/OpenRouter), **não** use Ollama para embeddings. Se `EMBEDDING_MODEL` for tag local (`bge-m3`, `nomic-embed-text`, …), o vetor fica **`off`** e o RAG cai em busca por palavra-chave — o turno **não** quebra. Para vetor no mesmo stack: `EMBEDDING_PROVIDER=openai_compatible` + modelo `/v1/embeddings` (ex. `openai/text-embedding-3-small`) e reindex.

Trocar só `LLM_PROVIDER` **alinha** embeddings ao mesmo provedor quando `EMBEDDING_PROVIDER` está vazio. `VISION_LLM_PROVIDER` continua independente até ser setado.

---

## Ollama local (legado)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:3b
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=bge-m3
```

---

## API externa OpenAI-compatible

Funciona com OpenAI, Azure OpenAI, Groq, Together, vLLM remoto, **Kimi/OpenRouter** (mesmo `KIMI_*` das atas), etc.

```env
LLM_PROVIDER=openai_compatible
LLM_TEXT_BASE_URL=https://api.openai.com/v1
LLM_TEXT_MODEL=gpt-4o-mini
LLM_TEXT_API_KEY=sk-...
LLM_TEXT_TIMEOUT_SECONDS=120

# Kimi — herança das atas (LLM_TEXT_* opcional quando vazio):
# KIMI_API_KEY=sk-or-v1-...
# KIMI_BASE_URL=https://openrouter.ai/api/v1
# KIMI_MODEL=moonshotai/kimi-k3
# LLM_PROVIDER=openai_compatible
# Caps cloud (opcional — default em generationLimitsCloud do response_modes.json).
# NÃO use CHAT_RESPONSE_MODE_*_MAX_TOKENS com openai_compatible (só Ollama).
# CHAT_RESPONSE_MODE_CLOUD_NORMAL_MAX_TOKENS=2048
# CHAT_RESPONSE_MODE_CLOUD_THINKER_MAX_TOKENS=4096
# MAX_CONTEXT_CHARS=24000

# Aliases legados (ainda suportados)
# LLM_PROVIDER=vllm
# VLLM_BASE_URL=...
# VLLM_MODEL=...
# VLLM_API_KEY=...

# Embeddings: vazio herda LLM_PROVIDER. Tag local (bge-m3) com Kimi → vetor off (keyword RAG).
# EMBEDDING_PROVIDER=openai_compatible
# EMBEDDING_MODEL=openai/text-embedding-3-small
# EMBEDDING_PROVIDER=ollama
# EMBEDDING_MODEL=bge-m3

# Visão (VLM documentos) — eixo independente do texto
VISION_LLM_PROVIDER=ollama
# Mesma Kimi/OpenRouter do chat (herda KIMI_* se VISION_LLM_* vazio):
# VISION_LLM_PROVIDER=openai_compatible
# Ou OpenAI dedicado:
# VISION_LLM_PROVIDER=openai_compatible
# VISION_LLM_BASE_URL=https://api.openai.com/v1
# VISION_LLM_MODEL=gpt-4o-mini
# VISION_LLM_API_KEY=sk-...
```

**Warmup:** com provider externo o startup **não** aquece modelo local (`LLM_WARMUP_ON_STARTUP` só afeta Ollama).

---

## Deploy

```bash
docker compose restart minha-delpi-ai-api
```

O serviço roda `flask` **sem** `--reload`; restart é obrigatório após mudança de env.

---

## Validação

```bash
cd minha-delpi-ai-api

# Wiring (sem HTTP)
PYTHONPATH=. python scripts/smoke_llm_provider_switch.py

# Gate de acoplamento
.venv/bin/python scripts/audit_llm_provider_coupling.py --check

# Status admin (requer auth)
curl -s -H "Authorization: Bearer $TOKEN" \
  http://delpi-gateway/admin/llm/status | jq .
```

Resposta esperada de `/admin/llm/status`:

- `text.provider` — `ollama` ou `openai_compatible`
- `embedding.provider` — `openai_compatible`, `off` (keyword RAG) ou `ollama` (legado)
- `vision.provider` — `ollama` ou `openai_compatible`

---

## Override por agente (P5)

No metadata do agente (admin), defina:

```json
{
  "intelligence": {
    "llmProviderOverride": "openai_compatible"
  }
}
```

Valores aceitos: `ollama`, `openai_compatible` (aliases `vllm`, `openai` normalizam para `openai_compatible`).

O env global (`LLM_PROVIDER`) continua como default; o override só afeta turnos daquele agente.

**Rate limit API externa:** `RATE_LIMIT_EXTERNAL_LLM_PER_WINDOW` (default `10` por janela de `RATE_LIMIT_WINDOW_SECONDS`).

**Métricas admin** (`GET /admin/metrics/summary` → `advanced`):

- `llmProviderUsage24h` — uso agregado por provider
- `llmRateLimitSnapshot` — buckets `llm_text:*` ativos
- `costBreakdown24h` — custo por provider/modelo

Ver [changelog jul/2026](../changelog/2026-07-playbook-24-llm-provider-pluggable.md).

---

## Rollback

```env
LLM_PROVIDER=ollama
# remover overrides LLM_TEXT_*
```

```bash
docker compose restart minha-delpi-ai-api
```

---

## Troubleshooting

| Sintoma | Causa provável |
|---------|----------------|
| Chat OK, RAG falha / HTTP 500 no turno | Embeddings ainda no Ollama; com Kimi o vetor deve herdar o LLM ou ficar `off` |
| Tools não funcionam | API externa sem suporte a function calling |
| Warmup lento no startup | Normal com `LLM_PROVIDER=ollama`; desligar com `LLM_WARMUP_ON_STARTUP=false` |
| Custo zerado no admin | Configurar `LLM_PROMPT_TOKEN_COST_PER_1K` / tabela no admin |
