# Modos de resposta do chat (Rápida / Normal / Pensador)

Documentação canônica dos modos `responseMode` enviados pelo composer e resolvidos em `ChatResponseModeService`.

Relacionado: [`chat-intelligence-base.md`](./chat-intelligence-base.md), [`chat-admin-platform-settings.md`](../knowledge/chat-admin-platform-settings.md), bundle `assistant/response_modes.json`.

---

## Princípio

Os modos são **perfis de geração LLM** (`LlmGenerationConfig`) com **presets distintos de latência**. Todos os modos usam LLM para síntese narrativa quando a intenção é aberta (ex.: visão geral de produto); consultas factuais (estoque, KPI) permanecem em direct answer.

| Camada | Afetada pelo modo? |
|--------|-------------------|
| Preset LLM (modelo, tokens, ctx, temperatura) | Sim — distinto por modo |
| Direct answer operacional (estoque, KPI, tabela) | Não — `operational_direct` |
| Visão geral de produto («me fale do produto X») | **Sim** — LLM em todos os modos |
| Perguntas abertas / Normas / redação | Sim — `llm_synthesis` |

O composer envia `responseMode` (`fast` | `normal` | `thinker`) em cada mensagem. `llm_generation_scope` propaga o preset a **todas** as chamadas LLM do turno.

Catálogo HTTP: `GET /chat/response-modes`.

---

## Matriz por modo

| Modo | Modelo (env) | max_tokens | num_ctx | temp | Policy product overview |
|------|--------------|------------|---------|------|-------------------------|
| **Rápida** (`fast`) | `CHAT_RESPONSE_MODE_FAST_MODEL` (1.5b) | 320 | 1280 | 0.25 | `product-overview-fast.md` |
| **Normal** (`normal`) | `CHAT_RESPONSE_MODE_NORMAL_MODEL` ou `OLLAMA_MODEL` | 768 | 2048 | 0.35 | `product-overview.md` |
| **Pensador** (`thinker`) | `CHAT_RESPONSE_MODE_THINKER_MODEL` ou fallback | 1536 | 3072 | 0.25 | `product-overview-thinker.md` |

Consultas factuais (estoque, KPI): **direct answer em todos os modos** — sem passagem pelo LLM.

---

## Gate de product overview

Serviço canônico: `ChatResponseModeService.apply_turn_direct_answer_policy` (chamado ao final de `ChatTurnPreparationPostToolResolutionService`).

```
«me fale do produto X» + tool ok
    │
    ├─ fast     → limpa directAnswer, LLM curto  (responseModeEffect: llm_synthesis_brief)
    ├─ normal   → limpa directAnswer, LLM médio  (responseModeEffect: llm_synthesis)
    └─ thinker  → limpa directAnswer, LLM longo  (responseModeEffect: llm_synthesis)
```

Intent: `ChatProductOverviewIntentService` (`should_force_llm_synthesis`, `is_product_overview_message`).

Policy por modo: `ChatProductOverviewIntentService._overview_policy_for_mode`.

---

## Metadata exposta ao MFE

Em `metadata.intelligence.pipeline`:

| Campo | Valores |
|-------|---------|
| `responseModeEffect` | `llm_synthesis` \| `llm_synthesis_brief` \| `operational_direct` |
| `responseModeEffectNotice` | Texto PT de `response_modes.json` → `pipelineEffects.*` |
| `directResponse` | `true` quando há texto direct answer |

---

## Configuração

### Variáveis de ambiente (`infra/.env` / compose)

| Variável | Default | Papel |
|----------|---------|-------|
| `CHAT_RESPONSE_MODES_ENABLED` | `true` | Master — desligado: só preset Normal legado |
| `CHAT_RESPONSE_MODE_FAST_MODEL` | `qwen2.5:1.5b` | Modelo Rápida |
| `CHAT_RESPONSE_MODE_FAST_MAX_TOKENS` | `320` | Limite Rápida (síntese curta) |
| `CHAT_RESPONSE_MODE_FAST_NUM_CTX` | `1280` | Contexto Rápida |
| `CHAT_RESPONSE_MODE_NORMAL_MAX_TOKENS` | `768` | Limite Normal |
| `CHAT_RESPONSE_MODE_NORMAL_NUM_CTX` | `2048` | Contexto Normal |
| `CHAT_RESPONSE_MODE_NORMAL_TEMPERATURE` | `0.35` | Temperatura Normal |
| `CHAT_RESPONSE_MODE_THINKER_MODEL` | vazio → `OLLAMA_MODEL` | Modelo Pensador |
| `CHAT_RESPONSE_MODE_THINKER_MAX_TOKENS` | `1536` | Limite Pensador |
| `CHAT_RESPONSE_MODE_THINKER_NUM_CTX` | `3072` | Contexto Pensador |

Stack mínimo WSL: ver `infra/docker-compose.minimal.yml` (todos em 1.5b; Normal 640 tokens / ctx 1536).

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

Benchmark manual: `scripts/smoke_response_modes_product_overview.py` com `responseMode` no POST.

Referência WSL (stack mínimo, `qwen2.5:1.5b`, product overview `10080045`):

| Modo | Tempo típico | `responseModeEffect` |
|------|--------------|----------------------|
| Rápida | ~25–30 s | `llm_synthesis_brief` |
| Normal | ~30–35 s | `llm_synthesis` |
| Pensador | ~40–45 s | `llm_synthesis` |

Consultas factuais (estoque/KPI) permanecem `operational_direct` em todos os modos.

---

*Última revisão: jun/2026 — LLM nos três modos com presets balanceados por latência.*
