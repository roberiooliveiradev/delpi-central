# Tutorial — conectar outros LLMs ao chat DELPI

Passo a passo para usar **APIs externas** (OpenAI, Azure, Groq, Together, vLLM remoto, etc.) mantendo **Ollama como padrão** em dev.

**Público:** operação, DevOps e desenvolvedores que configuram ambiente — **sem alterar código**.

**Referências:** [playbook-24](../roadmap/playbook-24-llm-provider-pluggable-jul2026.md) · [llm-provider-switch.md](./llm-provider-switch.md) · [changelog jul/2026](../changelog/2026-07-playbook-24-llm-provider-pluggable.md)

---

## 1. Antes de começar

### 1.1 O que o chat suporta hoje

| Capacidade | Providers | Protocolo |
|------------|-----------|-----------|
| **Texto** (prosa, tools) | `ollama`, `openai_compatible` | Ollama `/api/chat` ou OpenAI `/v1/chat/completions` |
| **Embeddings** (RAG) | `ollama`, `openai_compatible` | Ollama `/api/embeddings` ou OpenAI `/v1/embeddings` |
| **Visão** (VLM documentos) | `ollama`, `openai_compatible` | Chat multimodal com imagem |
| **Fine-tuning local** | só `ollama` | Com API externa → modo `export_only` |

Aliases aceitos e normalizados internamente:

| Você configura | Vira internamente |
|----------------|-------------------|
| `vllm`, `openai` | `openai_compatible` |
| `LLM_PROVIDER=vllm` + `VLLM_*` | `openai_compatible` + `LLM_TEXT_*` (fallback legado) |

**Não suportado nativamente (backlog):** Anthropic Messages API, Gemini API sem camada OpenAI-compatible. Use um proxy/gateway compatível ou aguarde gateway dedicado.

### 1.2 Pré-requisitos da API externa

Para o **chat completo** (consultas operacionais com tools):

- [ ] Endpoint **chat completions** (`POST .../v1/chat/completions`)
- [ ] **Function calling** / tools (`tools` + `tool_choice`)
- [ ] Latência aceitável para modo Normal/Pensador
- [ ] API key com cota suficiente

Para **só prosa** (sem tools nativos): qualquer completion API basta; o pipeline pode degradar para texto simples.

### 1.3 Onde editar variáveis

| Ambiente | Arquivo típico |
|----------|----------------|
| Dev local (Compose) | `infra/.env` ou `infra/.env.dev` |
| Produção | `infra/.env` no servidor |
| Referência | `infra/.env.prod.example`, `infra/.env.dev.example` |

Serviço afetado: **`minha-delpi-ai-api`**. Após qualquer mudança → **restart obrigatório** (Flask sem `--reload`).

```bash
cd ~/projetos/delpi-central
docker compose -f infra/docker-compose.dev.yml restart minha-delpi-ai-api
# produção:
# docker compose -f infra/docker-compose.yml restart minha-delpi-ai-api
```

---

## 2. Cenários recomendados

Escolha um perfil antes de configurar:

| Cenário | Texto | Embeddings | Visão | Quando usar |
|---------|-------|------------|-------|-------------|
| **A — Híbrido (recomendado)** | API externa | Ollama local | Ollama local | Melhor custo: só prosa na nuvem; RAG/VLM no CPU local |
| **B — Tudo externo** | API externa | API externa | API externa | Sem Ollama no Compose; exige reindex se trocar modelo embedding |
| **C — Só um agente externo** | Ollama global + override no agente | Ollama | Ollama | Piloto com um assistente premium |
| **D — Ollama padrão** | Ollama | Ollama | Ollama | Dev/homolog atual (nada a fazer) |

---

## 3. Tutorial A — Híbrido (texto externo, RAG local)

Cenário mais comum: **GPT/Groq para chat**, **Ollama para RAG e visão**.

### Passo 1 — Obter credenciais

Exemplo OpenAI: crie API key em [platform.openai.com](https://platform.openai.com/api-keys).

### Passo 2 — Configurar env

Edite `infra/.env` (ou o env do Compose):

```env
# --- Texto: API externa ---
LLM_PROVIDER=openai_compatible
LLM_TEXT_BASE_URL=https://api.openai.com/v1
LLM_TEXT_MODEL=gpt-4o-mini
LLM_TEXT_API_KEY=sk-SUA_CHAVE_AQUI
LLM_TEXT_TIMEOUT_SECONDS=120

# --- Embeddings: manter Ollama (RAG) ---
EMBEDDING_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
EMBEDDING_MODEL=bge-m3
EMBEDDING_DIMENSIONS=1024

# --- Visão: manter Ollama ---
VISION_LLM_PROVIDER=ollama
# CHAT_DOCUMENT_VISION_OLLAMA_MODEL=qwen2.5vl:7b  # se já existir no compose

# --- Custo no admin (opcional mas recomendado) ---
LLM_PROMPT_TOKEN_COST_PER_1K=0.00015
LLM_COMPLETION_TOKEN_COST_PER_1K=0.0006
LLM_COST_CURRENCY=USD

# --- Rate limit API externa (P5) ---
RATE_LIMIT_EXTERNAL_LLM_PER_WINDOW=10
```

### Passo 3 — Restart e validar

```bash
docker compose -f infra/docker-compose.dev.yml restart minha-delpi-ai-api

# Status dos três eixos (com token admin)
curl -s -H "Authorization: Bearer $TOKEN" \
  http://delpi-gateway/admin/llm/status | jq .

# Smoke de wiring
cd minha-delpi-ai-api
PYTHONPATH=. python scripts/smoke_llm_provider_switch.py
```

Resposta esperada em `/admin/llm/status`:

```json
{
  "text": { "provider": "openai_compatible", "model": "gpt-4o-mini", ... },
  "embedding": { "provider": "ollama", "model": "bge-m3", ... },
  "vision": { "provider": "ollama", ... }
}
```

### Passo 4 — Testar no chat

1. Abra o chat e envie: *«Qual o estoque do produto 90123456?»* (ou pergunta operacional do seu agente).
2. Confirme que tools/actions executam (requer function calling na API).
3. No admin → métricas: `advanced.llmProviderUsage24h` deve mostrar `openai_compatible`.

---

## 4. Exemplos por provedor (texto)

Todos usam `LLM_PROVIDER=openai_compatible` e variam só URL, modelo e key.

### 4.1 OpenAI

```env
LLM_PROVIDER=openai_compatible
LLM_TEXT_BASE_URL=https://api.openai.com/v1
LLM_TEXT_MODEL=gpt-4o-mini
LLM_TEXT_API_KEY=sk-...
```

Modelos úteis: `gpt-4o-mini` (custo), `gpt-4o` (qualidade + visão se usar mesmo modelo no VLM).

### 4.2 Azure OpenAI

```env
LLM_PROVIDER=openai_compatible
LLM_TEXT_BASE_URL=https://SEU-RECURSO.openai.azure.com/openai/deployments/SEU-DEPLOYMENT
LLM_TEXT_MODEL=SEU-DEPLOYMENT
LLM_TEXT_API_KEY=SUA_AZURE_KEY
```

Notas:

- A URL deve incluir o **deployment**; o campo `model` no payload usa o nome do deployment.
- Alguns deployments exigem header `api-key` — o gateway envia `Authorization: Bearer`; confira compatibilidade do seu endpoint Azure.

### 4.3 Groq

```env
LLM_PROVIDER=openai_compatible
LLM_TEXT_BASE_URL=https://api.groq.com/openai/v1
LLM_TEXT_MODEL=llama-3.3-70b-versatile
LLM_TEXT_API_KEY=gsk_...
```

Verifique na documentação Groq se o modelo escolhido suporta **tools**.

### 4.4 Together / Fireworks / outros OpenAI-compatible

```env
LLM_PROVIDER=openai_compatible
LLM_TEXT_BASE_URL=https://api.together.xyz/v1
LLM_TEXT_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo
LLM_TEXT_API_KEY=...
```

### 4.5 vLLM local ou remoto (GPU)

```env
LLM_PROVIDER=openai_compatible
LLM_TEXT_BASE_URL=http://vllm:8000/v1
LLM_TEXT_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_TEXT_API_KEY=minha-delpi-local-vllm
```

Aliases legados ainda funcionam:

```env
LLM_PROVIDER=vllm
VLLM_BASE_URL=http://vllm:8000/v1
VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct
VLLM_API_KEY=minha-delpi-local-vllm
```

### 4.6 Ollama (voltar ao padrão)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:3b
```

---

## 5. Tutorial B — Embeddings na API externa

Use quando **não** houver Ollama no ambiente ou quiser embeddings na mesma conta OpenAI.

```env
EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=sk-...
EMBEDDING_DIMENSIONS=1536
```

### ⚠ Reindex obrigatório

Trocar modelo ou dimensão de embedding **invalida** vetores existentes no pgvector.

1. Anote o modelo/dimensão antigos.
2. Após mudar env e restart, **reindexe** documentos de conhecimento (admin → fontes / job de indexação).
3. Valide busca RAG com pergunta que dependa de uma fonte conhecida.

---

## 6. Tutorial C — Visão (VLM) externa

Para análise de PDF/imagem sem Ollama VLM:

```env
VISION_LLM_PROVIDER=openai_compatible
VISION_LLM_BASE_URL=https://api.openai.com/v1
VISION_LLM_MODEL=gpt-4o-mini
VISION_LLM_API_KEY=sk-...
```

Com `VISION_LLM_PROVIDER=ollama`, o pipeline usa fallback Tesseract quando VLM falha — comportamento documentado na Onda 13.

Teste: anexe um PDF ou imagem legível e peça *«resuma o documento anexado»*.

---

## 7. Tutorial D — Só um agente com LLM externo

Útil para piloto: ambiente continua Ollama, **um agente** usa API paga.

### Passo 1 — Env global (Ollama)

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:3b
```

### Passo 2 — Credenciais da API externa (mesmo com Ollama global)

O override do agente usa o gateway `openai_compatible`, que lê `LLM_TEXT_*`:

```env
LLM_TEXT_BASE_URL=https://api.openai.com/v1
LLM_TEXT_MODEL=gpt-4o-mini
LLM_TEXT_API_KEY=sk-...
```

### Passo 3 — Metadata do agente (admin)

No cadastro do agente, campo `metadata` (JSON):

```json
{
  "intelligence": {
    "llmProviderOverride": "openai_compatible"
  }
}
```

Também aceito no legado: `"llmProviderOverride": "openai_compatible"` direto em `metadata`.

### Passo 4 — Validar

- Turno com **esse agente** → audit/metadata da resposta: `"provider": "openai_compatible"`.
- Turno com **outro agente** → `"provider": "ollama"`.
- Rate limit: bucket `llm_text:openai_compatible:{userId}` no admin (`llmRateLimitSnapshot`).

---

## 8. Custo e métricas no admin

### 8.1 Tabela de custo

Opção 1 — env:

```env
LLM_COST_TABLE_JSON=[{"provider":"openai_compatible","model":"gpt-4o-mini","promptCostPer1k":0.00015,"completionCostPer1k":0.0006,"currency":"USD"}]
```

Opção 2 — painel admin (persistido em `ai_admin_runtime_settings`).

### 8.2 Métricas (`GET /admin/metrics/summary`)

| Campo | Uso |
|-------|-----|
| `advanced.costBreakdown24h` | Custo por provider **e** modelo |
| `advanced.llmProviderUsage24h` | Resumo por provider |
| `advanced.llmRateLimitSnapshot` | Uso do rate limit de API externa |

---

## 9. Checklist pós-configuração

- [ ] `GET /admin/llm/status` — três eixos com provider esperado
- [ ] Pergunta operacional com **tools** (action api-delpi executada)
- [ ] Pergunta com **RAG** (fonte recuperada) — se `EMBEDDING_PROVIDER=ollama`, Ollama up
- [ ] Anexo com **visão** — se `VISION_LLM_PROVIDER=ollama`, modelo VLM puxado no Ollama
- [ ] `scripts/smoke_llm_provider_switch.py` verde
- [ ] Métricas admin mostram provider correto em `llmProviderUsage24h`

---

## 10. Troubleshooting

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| `401` / `403` na resposta | API key inválida ou URL errada | Conferir `LLM_TEXT_API_KEY` e `LLM_TEXT_BASE_URL` |
| Chat responde, tools não rodam | Modelo sem function calling | Trocar modelo (ex.: `gpt-4o-mini`) |
| RAG vazio / erro embedding | Ollama down com `EMBEDDING_PROVIDER=ollama` | Subir `ollama` ou mudar para `openai_compatible` + reindex |
| `Rate limit exceeded for external LLM` | `RATE_LIMIT_EXTERNAL_LLM_PER_WINDOW` | Aumentar env ou aguardar janela |
| Custo zerado no admin | Tabela de custo não configurada | `LLM_COST_TABLE_JSON` ou admin cost table |
| Warmup lento no startup | Normal com Ollama | Com externo, warmup é ignorado; se ainda lento, verificar health Ollama para RAG |
| Agente não usa API externa | Override ausente ou typo | `metadata.intelligence.llmProviderOverride` = `openai_compatible` |

### Rollback rápido

```env
LLM_PROVIDER=ollama
# Remover ou comentar LLM_TEXT_* overrides
```

```bash
docker compose -f infra/docker-compose.dev.yml restart minha-delpi-ai-api
```

Remova `llmProviderOverride` dos agentes se tiver configurado override.

---

## 11. Matriz rápida de variáveis

| Variável | Eixo | Obrigatória quando |
|----------|------|-------------------|
| `LLM_PROVIDER` | Texto | Sempre (`ollama` ou `openai_compatible`) |
| `LLM_TEXT_BASE_URL` | Texto | Provider externo |
| `LLM_TEXT_MODEL` | Texto | Provider externo |
| `LLM_TEXT_API_KEY` | Texto | Provider externo (exceto vLLM local sem auth) |
| `EMBEDDING_PROVIDER` | RAG | Sempre (default `ollama`) |
| `EMBEDDING_BASE_URL` | RAG | `EMBEDDING_PROVIDER=openai_compatible` |
| `EMBEDDING_API_KEY` | RAG | `EMBEDDING_PROVIDER=openai_compatible` |
| `EMBEDDING_DIMENSIONS` | RAG | Deve bater com modelo; reindex se mudar |
| `VISION_LLM_PROVIDER` | VLM | Sempre (default `ollama`) |
| `VISION_LLM_BASE_URL` | VLM | Provider externo |
| `VISION_LLM_MODEL` | VLM | Provider externo |
| `RATE_LIMIT_EXTERNAL_LLM_PER_WINDOW` | Texto externo | Opcional (default `10`) |

---

## 12. Próximos passos

- Arquitetura completa: [playbook-24](../roadmap/playbook-24-llm-provider-pluggable-jul2026.md)
- Referência rápida operacional: [llm-provider-switch.md](./llm-provider-switch.md)
- Variáveis de infra: `infra/README-ambiente.md`
- Adicionar provider **não** OpenAI-compatible: exige novo gateway em `infrastructure/llm/` + entrada em `provider_registry.py` (desenvolvimento — ver playbook §3.4)
