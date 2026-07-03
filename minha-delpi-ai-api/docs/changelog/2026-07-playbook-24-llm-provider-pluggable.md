# Jul/2026 — Playbook 24: provedores LLM plugáveis (P0–P5)

**Playbook:** [playbook-24-llm-provider-pluggable-jul2026.md](../roadmap/playbook-24-llm-provider-pluggable-jul2026.md)  
**ADR:** [007-llm-provider-ports.md](../architecture/adr/007-llm-provider-ports.md)  
**Operação:** [llm-provider-switch.md](../operations/llm-provider-switch.md)

---

## Resumo

O chat passou a trocar motor de inferência **sem alterar código** — Ollama continua padrão; API OpenAI-compatible é opcional por env ou por agente.

Três eixos independentes:

| Eixo | Porta | Env principal |
|------|-------|---------------|
| Texto (chat) | `LlmGatewayPort` | `LLM_PROVIDER`, `LLM_TEXT_*` |
| Embeddings (RAG) | `EmbeddingGatewayPort` | `EMBEDDING_PROVIDER`, `EMBEDDING_*` |
| Visão (VLM) | `VisionLlmGatewayPort` | `VISION_LLM_PROVIDER`, `VISION_LLM_*` |

Fine-tuning local permanece só com Ollama; com provider externo → `export_only`.

---

## Commits (ordem cronológica)

| Commit | Fase | Escopo |
|--------|------|--------|
| `07e696c91` | P0–P1 | Porta `LlmGatewayPort`, registry, `OpenAiCompatibleLlmGateway`, `llm_text_config`, warmup condicional, status admin texto, gate `audit_llm_provider_coupling.py`, smoke |
| `f16dafc41` | P2–P3 | Embeddings e VLM plugáveis (`make_embedding_gateway`, `make_vision_llm_gateway`), health admin por eixo |
| `fdf8535aa` | P4 | `FineTuningModelGatewayPort`, deploy local só Ollama, textos em `learning_content.json` |
| `34115a31d` | P5 | Override por agente (`llmProviderOverride`), `ContextAwareLlmGateway`, rate limit API externa, métricas admin por provider |

---

## Arquitetura (texto — caminho crítico)

```text
Send/Stream Use Case
  → llm_provider_scope (provider efetivo: env ou override do agente)
  → ContextAwareLlmGateway (injetado via make_llm_gateway)
  → llm_gateway_registry (cache por provider)
  → OllamaLlmGateway | OpenAiCompatibleLlmGateway
```

**Override por agente:** `metadata.intelligence.llmProviderOverride` (ou legado em `metadata`) — resolvido por `ChatAgentLlmProviderPolicyService` no início do turno.

**Metadata do assistente:** campo `provider` no audit grava o provider **efetivo** (`get_active_llm_provider`), não só o env global.

---

## Variáveis novas relevantes

| Variável | Default | Uso |
|----------|---------|-----|
| `LLM_TEXT_BASE_URL` | fallback `OLLAMA_BASE_URL` / `VLLM_BASE_URL` | URL do motor de texto |
| `LLM_TEXT_MODEL` | fallback `OLLAMA_MODEL` / `VLLM_MODEL` | Modelo default |
| `LLM_TEXT_API_KEY` | vazio (Ollama) | Bearer para API externa |
| `EMBEDDING_PROVIDER` | `ollama` | Motor de embedding RAG |
| `VISION_LLM_PROVIDER` | `ollama` | VLM documentos |
| `RATE_LIMIT_EXTERNAL_LLM_PER_WINDOW` | `10` | Rate limit extra para `openai_compatible` por usuário |

---

## Admin — métricas novas (P5)

Em `GET /admin/metrics/summary` → `advanced`:

| Campo | Descrição |
|-------|-----------|
| `llmProviderUsage24h` | Mensagens, tokens e custo agregados **por provider** |
| `llmRateLimitSnapshot` | Uso atual dos buckets `llm_text:{provider}:{userId}` |
| `costBreakdown24h` | Custo por provider/modelo (normaliza `vllm` → `openai_compatible`) |

---

## Gates e validação

```bash
cd minha-delpi-ai-api
.venv/bin/python scripts/audit_llm_provider_coupling.py --check
.venv/bin/python -m pytest tests/unit/infrastructure/llm/ tests/unit/composition/test_llm_composer.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_agent_llm_provider_policy_service.py -q
PYTHONPATH=. python scripts/smoke_llm_provider_switch.py
```

Deploy: `docker compose restart minha-delpi-ai-api` (flask sem `--reload`).

---

## Artefatos principais no código

| Artefato | Caminho |
|----------|---------|
| Policy override agente | `app/domain/services/chat_agent_llm_provider_policy_service.py` |
| Contexto provider/turno | `app/domain/services/chat_llm_generation_context_service.py` |
| Gateway context-aware | `app/infrastructure/llm/context_aware_llm_gateway.py` |
| Cache gateways | `app/infrastructure/llm/llm_gateway_registry.py` |
| Resolver efetivo | `app/application/services/chat_llm_gateway_resolver_service.py` |
| Rate limit externo | `app/application/services/chat_turn/chat_turn_llm_provider_guard_service.py` |
| Registry providers | `app/composition/provider_registry.py` |
| Config texto | `app/infrastructure/config/llm_text_config.py` |
| Status admin | `GetLlmProviderStatusUseCase` |
