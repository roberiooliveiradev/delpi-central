# Troca de provedor LLM — operação

Guia para alternar o motor de inferência do chat mantendo **Ollama como padrão** em dev/homolog.

**Playbook:** [playbook-24-llm-provider-pluggable-jul2026.md](../roadmap/playbook-24-llm-provider-pluggable-jul2026.md)

---

## Capacidades independentes

| Eixo | Variável principal | Default |
|------|-------------------|---------|
| Texto (chat) | `LLM_PROVIDER` | `ollama` |
| Embeddings (RAG) | `EMBEDDING_PROVIDER` | `ollama` |
| Visão (VLM) | `VISION_LLM_PROVIDER` | `ollama` |

Trocar só `LLM_PROVIDER` **não** altera RAG nem visão de documentos.

---

## Ollama local (padrão)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:3b
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=bge-m3
```

---

## API externa OpenAI-compatible

Funciona com OpenAI, Azure OpenAI, Groq, Together, vLLM remoto, etc.

```env
LLM_PROVIDER=openai_compatible
LLM_TEXT_BASE_URL=https://api.openai.com/v1
LLM_TEXT_MODEL=gpt-4o-mini
LLM_TEXT_API_KEY=sk-...
LLM_TEXT_TIMEOUT_SECONDS=120

# Aliases legados (ainda suportados)
# LLM_PROVIDER=vllm
# VLLM_BASE_URL=...
# VLLM_MODEL=...
# VLLM_API_KEY=...

# Embeddings: Ollama local ou API externa
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=bge-m3
# EMBEDDING_PROVIDER=openai_compatible
# EMBEDDING_BASE_URL=https://api.openai.com/v1
# EMBEDDING_API_KEY=sk-...

# Visão (VLM documentos)
VISION_LLM_PROVIDER=ollama
# VISION_LLM_PROVIDER=openai_compatible
# VISION_LLM_BASE_URL=https://api.openai.com/v1
# VISION_LLM_MODEL=gpt-4o-mini
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
- `embedding.provider` — `ollama` (até P2)
- `vision.provider` — `ollama` (até P3)

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
| Chat OK, RAG falha | `EMBEDDING_PROVIDER=ollama` mas serviço Ollama indisponível |
| Tools não funcionam | API externa sem suporte a function calling |
| Warmup lento no startup | Normal com `LLM_PROVIDER=ollama`; desligar com `LLM_WARMUP_ON_STARTUP=false` |
| Custo zerado no admin | Configurar `LLM_PROMPT_TOKEN_COST_PER_1K` / tabela no admin |
