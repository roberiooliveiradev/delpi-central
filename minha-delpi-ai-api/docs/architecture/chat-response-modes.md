# Modos de resposta do chat (Rápida / Normal / Pensador)

Documentação canônica dos modos `responseMode` enviados pelo composer e resolvidos em `ChatResponseModeService`.

Relacionado: [`chat-intelligence-base.md`](./chat-intelligence-base.md), [`chat-assistant-content-presentation.md`](./chat-assistant-content-presentation.md), bundle `assistant/response_modes.json`, `assistant/operational_narrative_synthesis.json`.

---

## Princípio

Os modos são **perfis de geração LLM** (`LlmGenerationConfig`) com **presets distintos de latência**. Síntese LLM é **pontual** — overview de produto e perfis `summary_then_evidence` (estoque/fábrica narrativos); consultas factuais estreitas permanecem em direct answer.

| Camada | Afetada pelo modo? |
|--------|-------------------|
| Preset LLM (modelo, tokens, ctx, temperatura) | Sim — distinto por modo |
| Direct answer operacional factual estreito | Não — `operational_direct` |
| Visão geral de produto | Sim — LLM em todos os modos |
| Stack `summary_then_evidence` (estoque/fábrica narrativos) | Sim — LLM em todos os modos |
| Perguntas abertas / Normas / redação | Sim — `llm_synthesis` |

Gate canônico: `ChatOperationalNarrativeSynthesisService` + `ChatResponseModeService.apply_turn_direct_answer_policy`.

O composer envia `responseMode` (`fast` | `normal` | `thinker`). `llm_generation_scope` propaga o preset a **todas** as chamadas LLM do turno.

Catálogo HTTP: `GET /chat/response-modes`.

---

## Matriz por modo (presets default)

| Modo | Modelo | max_tokens | num_ctx | temp | Policy overview | Policy operacional |
|------|--------|------------|---------|------|-----------------|-------------------|
| **Rápida** | `FAST_MODEL` (1.5b) | 256 | 1024 | 0.2 | `product-overview-fast.md` | `operational-synthesis-fast.md` |
| **Normal** | `NORMAL_MODEL` ou `OLLAMA_MODEL` | 512 | 1536 | 0.3 | `product-overview.md` | `operational-synthesis.md` |
| **Pensador** | `THINKER_MODEL` ou fallback | 896 | 2560 | 0.25 | `product-overview-thinker.md` | `operational-synthesis-thinker.md` |

---

## Gate de síntese LLM

```
Tool ok + intenção narrativa
    │
    ├─ product overview («me fale do produto X»)
    ├─ summary_then_evidence (stack estoque/fábrica/produção/expedição)
    │     └─ metadata: presentationMode ou stack + profileKey/path
    │
    ├─ fast     → llm_synthesis_brief
    ├─ normal   → llm_synthesis
    └─ thinker  → llm_synthesis

Consulta factual estreita (filial + quantidade, sem marcador narrativo)
    └─ operational_direct (sem LLM)
```

Serviços:

| Serviço | Papel |
|---------|-------|
| `ChatOperationalNarrativeSynthesisService` | Detecta kind + policy + `should_force_llm_synthesis` |
| `ChatResponseModeService.apply_turn_direct_answer_policy` | Limpa `directAnswer`, seta `responseModeEffect` |
| `ChatTurnCompletionService` | `skip_replacement` quando `responseModeEffect` é síntese LLM |

Bundle declarativo: `assistant/operational_narrative_synthesis.json`.

---

## Metadata exposta ao MFE

Em `metadata.intelligence.pipeline`:

| Campo | Valores |
|-------|---------|
| `responseModeEffect` | `llm_synthesis` \| `llm_synthesis_brief` \| `operational_direct` |
| `responseModeEffectNotice` | Texto PT de `response_modes.json` |
| `directResponse` | `true` apenas quando há direct answer final |

---

## Configuração

### Variáveis de ambiente

| Variável | Default | Papel |
|----------|---------|-------|
| `CHAT_RESPONSE_MODE_FAST_MAX_TOKENS` | `256` | Síntese curta |
| `CHAT_RESPONSE_MODE_FAST_NUM_CTX` | `1024` | Contexto Rápida |
| `CHAT_RESPONSE_MODE_NORMAL_MAX_TOKENS` | `512` | Síntese Normal |
| `CHAT_RESPONSE_MODE_NORMAL_NUM_CTX` | `1536` | Contexto Normal |
| `CHAT_RESPONSE_MODE_THINKER_MAX_TOKENS` | `896` | Síntese Pensador |
| `CHAT_RESPONSE_MODE_THINKER_NUM_CTX` | `2560` | Contexto Pensador |

Stack mínimo WSL: `infra/docker-compose.minimal.yml` (Normal 448 tokens / ctx 1280).

---

## Validação de qualidade (smoke/regressão)

Serviço: `ChatResponseModeSynthesisQualityService`  
Bundle: `assistant/response_mode_synthesis_quality.json`

O smoke **não** basta checar metadata — valida por turno:

| Critério | O que falha |
|----------|-------------|
| Pipeline | `directResponse=true` ou efeito errado |
| Template | similaridade com `textPresentation` / markdown autorizado ≥ limite |
| Contexto | código do produto + overlap mínimo com tokens dos dados da tool |
| Assertividade | frases evasivas («preciso acessar», «não tenho acesso», …) |
| Modo | Rápida mais curta/rápida que Normal; conteúdos distintos entre modos |

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_response_mode_synthesis_quality_service.py -q
SMOKE_SCENARIO=factory_status .venv/bin/python scripts/smoke_response_modes_product_overview.py
```

---

## Testes de regressão

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_operational_narrative_synthesis_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_response_mode_service.py -q
.venv/bin/python -m pytest tests/unit/application/services/test_chat_turn_preparation_response_mode.py -q
.venv/bin/python scripts/smoke_response_modes_product_overview.py
```

---

*Última revisão: jun/2026 — gate summary_then_evidence + presets acelerados + skip authorized replacement.*
