# Modos de resposta do chat (Rápida / Normal / Pensador)

Documentação canônica dos modos `responseMode` enviados pelo composer e resolvidos em `ChatResponseModeService`.

Relacionado: [`chat-intelligence-base.md`](./chat-intelligence-base.md), [`chat-admin-platform-settings.md`](../knowledge/chat-admin-platform-settings.md), bundle `assistant/response_modes.json`.

---

## Princípio

Os modos são **perfis de geração LLM** (`LlmGenerationConfig`), não um atalho para todo o pipeline.

| Camada | Afetada pelo modo? |
|--------|-------------------|
| Preset LLM (modelo, tokens, ctx, temperatura) | Sim |
| Direct answer operacional (estoque, KPI, tabela) | Não — `operational_direct` |
| Visão geral de produto («me fale do produto X») | **Sim** — ver matriz abaixo |
| Perguntas abertas / Normas / redação | Sim — `llm_synthesis` |

O composer envia `responseMode` (`fast` | `normal` | `thinker`) em cada mensagem. `llm_generation_scope` propaga o preset a **todas** as chamadas LLM do turno.

Catálogo HTTP: `GET /chat/response-modes`.

---

## Matriz por modo

| Modo | Modelo (env) | max_tokens | num_ctx | temp | Visão geral produto | Operacional (estoque/KPI) |
|------|--------------|------------|---------|------|---------------------|---------------------------|
| **Rápida** (`fast`) | `CHAT_RESPONSE_MODE_FAST_MODEL` | `FAST_MAX_TOKENS` (384) | 1536 | 0.3 | Relatório **direto** do presenter | Direct answer |
| **Normal** (`normal`) | `OLLAMA_MODEL` | `LLM_MAX_TOKENS` | `OLLAMA_NUM_CTX` | `LLM_TEMPERATURE` | **Síntese LLM** com policy `product-overview.md` | Direct answer |
| **Pensador** (`thinker`) | `CHAT_RESPONSE_MODE_THINKER_MODEL` ou fallback `OLLAMA_MODEL` | `THINKER_MAX_TOKENS` | `THINKER_NUM_CTX` | 0.25 | **Síntese LLM** (ctx maior) | Direct answer |

---

## Gate de product overview

Serviço canônico: `ChatResponseModeService.apply_turn_direct_answer_policy` (chamado ao final de `ChatTurnPreparationPostToolResolutionService`).

```
«me fale do produto X» + tool ok
    │
    ├─ fast  → mantém directAnswer / markdown do presenter  (responseModeEffect: presenter_direct)
    └─ normal / thinker → limpa directAnswer, skip_rag=false  (responseModeEffect: llm_synthesis)
                              └─ LLM + product-overview.md + dados da tool
```

Intent: `ChatProductOverviewIntentService` (`should_force_llm_synthesis`, `is_product_overview_message`).

---

## Metadata exposta ao MFE

Em `metadata.intelligence.pipeline`:

| Campo | Valores |
|-------|---------|
| `responseModeEffect` | `llm_synthesis` \| `presenter_direct` \| `operational_direct` |
| `responseModeEffectNotice` | Texto PT de `response_modes.json` → `pipelineEffects.*` |
| `directResponse` | `true` quando há texto direct answer |

---

## Configuração

### Variáveis de ambiente (`infra/.env` / compose)

| Variável | Default | Papel |
|----------|---------|-------|
| `CHAT_RESPONSE_MODES_ENABLED` | `true` | Master — desligado: só preset Normal |
| `CHAT_RESPONSE_MODE_FAST_MODEL` | `qwen2.5:1.5b` | Modelo Rápida |
| `CHAT_RESPONSE_MODE_FAST_MAX_TOKENS` | `384` | Limite Rápida |
| `CHAT_RESPONSE_MODE_THINKER_MODEL` | vazio → `OLLAMA_MODEL` | Modelo Pensador (recomendado: `qwen2.5:3b` com GPU) |
| `CHAT_RESPONSE_MODE_THINKER_NUM_CTX` | `4096` | Contexto Pensador |

Stack mínimo WSL: ver `infra/docker-compose.minimal.yml` (Normal e Pensador em 1.5b; Pensador com ctx 4096).

### Admin

Painel **Plataforma → Modos de resposta**: toggle `responseModesEnabled` (runtime em `chat_response_mode_settings`). Parâmetros técnicos permanecem na env.

### Textos PT

Bundle: `app/content/pt-BR/assistant/response_modes.json`  
Loader: `ChatResponseModeContentService`

---

## Testes de regressão

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_response_mode_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_response_mode_content_service.py -q
.venv/bin/python -m pytest tests/unit/application/services/test_chat_turn_preparation_response_mode.py -q
```

Benchmark manual (3 conversas, mesma pergunta): script efêmero ou smoke operacional com `responseMode` no POST.

---

*Última revisão: jun/2026 — gate product overview + metadata `responseModeEffect`.*
