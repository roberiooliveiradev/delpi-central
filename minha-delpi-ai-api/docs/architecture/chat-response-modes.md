# Modos de resposta do chat (Rápida / Normal / Pensador)

Documentação canônica dos modos `responseMode` enviados pelo composer e resolvidos em `ChatResponseModeService`.

Relacionado: [`chat-intelligence-base.md`](./chat-intelligence-base.md), [`chat-assistant-content-presentation.md`](./chat-assistant-content-presentation.md), bundle `assistant/response_modes.json`, `assistant/operational_narrative_synthesis.json`.

---

## Princípio

Os modos são **perfis de geração LLM** (`LlmGenerationConfig`) com presets distintos de latência. Com **Playbook 19** (`llmProseEverywhere`), toda prosa operacional passa por síntese LLM; visuais permanecem nativos no MFE.

| Camada | Afetada pelo modo? |
|--------|-------------------|
| Preset LLM (modelo, tokens, ctx, temperatura) | Sim — distinto por modo |
| Prosa operacional (playbook, KPI, SQL, narrativa) | Sim — `llm_synthesis*` |
| Visuais (tabela, KPI, árvore, gráfico) | Não — metadata + render-only |
| Rollback template offline | Só com `allowTemplateProseFallback` + modos OFF |

Gate canônico: `ChatPresentationProseDeliveryService` (`template` \| `llm` \| `direct`) → intenção em `ChatOperationalNarrativeSynthesisService` + `ChatResponseModeService.apply_turn_direct_answer_policy`.

Playbooks: [`playbook-18`](../roadmap/playbook-18-prosa-template-llm-desacoplamento.md), [`playbook-19`](../roadmap/playbook-19-inferencia-llm-universal.md).

O composer envia `responseMode` (`fast` | `normal` | `thinker`). `llm_generation_scope` propaga o preset a **todas** as chamadas LLM do turno.

Catálogo HTTP: `GET /chat/response-modes`.

---

## Metadata v2 (Playbook 19)

Contrato pós-inferência universal — **sem prosa template na UI**:

| Campo tool metadata | Valor / regra |
|---------------------|---------------|
| `proseDeliveryMode` | `llm` |
| `dataOnlyPresentation`, `llmProseDecoupled` | `true` |
| `humanizedSummary.linhas` | `[]` (fatos em `templateProseArchive` ou `dataAnswer`) |
| `textPresentation.markdown` | vazio após pipeline |
| `renderPlan` lead | `source: assistantMessage` |
| `responseModeEffect` | `llm_synthesis` ou `llm_synthesis_brief` — nunca `operational_direct` |

Rollback template (dev/offline): `presentation_prose_delivery.json` → `allowTemplateProseFallback: true`, `llmProseEverywhere: false`, modos de resposta desligados.

---

## Matriz por modo (presets default — jun/2026)

Defaults calibrados para CPU operacional (~50% menos latência vs presets anteriores). Compose dev/prod alinha `OLLAMA_MODEL` e modos em `qwen2.5:1.5b`; srv-api prod pode manter `OLLAMA_MODEL=3b` para turnos fora dos modos.

| Modo | Modelo | max_tokens | num_ctx | temp | Policy overview | Policy operacional |
|------|--------|------------|---------|------|-----------------|-------------------|
| **Rápida** | `CHAT_RESPONSE_MODE_FAST_MODEL` (default `qwen2.5:1.5b`) | 160 | 768 | 0.2 | `product-overview-fast.md` | `operational-synthesis-fast.md` |
| **Normal** | `CHAT_RESPONSE_MODE_NORMAL_MODEL` ou `OLLAMA_MODEL` (default `1.5b`) | 320 | 1024 | 0.3 | `product-overview.md` | `operational-synthesis.md` |
| **Pensador** | `CHAT_RESPONSE_MODE_THINKER_MODEL` ou fallback (default `1.5b`) | 512 | 1536 | 0.25 | `product-overview-thinker.md` | `operational-synthesis-thinker.md` |

Preset global quando variáveis explícitas não estão no `.env`: `CHAT_LLM_LATENCY_PROFILE=operational_cpu` → `LLM_MAX_TOKENS=320`, `OLLAMA_NUM_CTX=1024` (`llm_latency_profile.py`). Ver [`rag-context-min-score-calibracao.md`](../roadmap/rag-context-min-score-calibracao.md).

---

## Gate de síntese LLM

```
Tool execute_external_action (ok ou falha)
    │
    ├─ llmProseEverywhere → proseDeliveryMode=llm + pipeline data-only
    ├─ fast     → llm_synthesis_brief
    ├─ normal   → llm_synthesis
    └─ thinker  → llm_synthesis

Rollback template (offline)
    └─ modos OFF + allowTemplateProseFallback + llmProseEverywhere=false
```

Serviços:

| Serviço | Papel |
|---------|-------|
| `ChatOperationalNarrativeSynthesisService` | Detecta kind + policy + intenção narrativa (interno ao prose gate) |
| `ChatPresentationProseDeliveryService` | Gate único no turno: `template` \| `llm` \| `direct`; chama decouple quando LLM |
| `ChatPresentationLlmProseDecouplingService` | Remove markdown template do metadata; `renderPlan.lead` → `assistantMessage` |
| `ChatResponseModeService.apply_turn_direct_answer_policy` | Limpa `directAnswer`, seta `responseModeEffect`, resolve `skip_rag` |
| `ChatResponseModeService._resolve_skip_rag_for_llm_synthesis` | Preserva skip operacional; força skip quando `execute_external_action` ok (evita RAG ~7 s redundante) |
| `ChatTurnCompletionService` | `skip_replacement` quando `responseModeEffect` é síntese LLM |

Bundle declarativo: `assistant/operational_narrative_synthesis.json`.

### Desacoplamento template × LLM

Quando síntese LLM está ativa (`CHAT_RESPONSE_MODES_ENABLED` + gate narrativo):

1. `ChatPresentationLlmProseDecouplingService` arquiva o markdown do presenter em `templateProseArchive`, zera `textPresentation.markdown` e seta `llmProseDecoupled`.
2. `renderPlan` mantém slots visuais (tabela, árvore, KPI, gráfico) e aponta o **lead** para `assistantMessage` — prosa vem da resposta LLM streamada.
3. `should_prefer_authorized_answer_over_llm` e `should_persist_authorized_tool_answer` retornam `false` quando decoupled.
4. Fatos para o prompt LLM continuam em `dataAnswer`, tabelas, KPI e `humanizedSummary` (`ChatOperationalLlmSynthesisContextService`).

---

## Metadata exposta ao MFE

Em `metadata.intelligence.pipeline`:

| Campo | Valores |
|-------|---------|
| `responseModeEffect` | `llm_synthesis` \| `llm_synthesis_brief` (P19: nunca `operational_direct` com everywhere) |
| `responseModeEffectNotice` | Texto PT de `response_modes.json` |
| `directResponse` | `true` apenas quando há direct answer final |

---

## Configuração

### Variáveis de ambiente

| Variável | Default | Papel |
|----------|---------|-------|
| `CHAT_LLM_LATENCY_PROFILE` | `operational_cpu` | Preset global `LLM_MAX_TOKENS` + `OLLAMA_NUM_CTX` quando não explícitos |
| `LLM_MAX_TOKENS` | `320` (via preset) | Teto tokens turno geral |
| `OLLAMA_NUM_CTX` | `1024` (via preset) | Contexto Ollama global |
| `CHAT_RESPONSE_MODE_FAST_MAX_TOKENS` | `160` | Síntese curta |
| `CHAT_RESPONSE_MODE_FAST_NUM_CTX` | `768` | Contexto Rápida |
| `CHAT_RESPONSE_MODE_NORMAL_MAX_TOKENS` | `320` | Síntese Normal |
| `CHAT_RESPONSE_MODE_NORMAL_NUM_CTX` | `1024` | Contexto Normal |
| `CHAT_RESPONSE_MODE_THINKER_MAX_TOKENS` | `512` | Síntese Pensador |
| `CHAT_RESPONSE_MODE_THINKER_NUM_CTX` | `1536` | Contexto Pensador |

Compose: `infra/docker-compose.dev.yml` e `infra/docker-compose.yml` injetam os defaults acima.

Stack mínimo WSL: `infra/docker-compose.minimal.yml` (presets intermediários — Normal 448 / ctx 1280).

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

*Última revisão: jun/2026 — preset `operational_cpu` default, modos 160/320/512 tokens, skip RAG em síntese LLM com tool ok, render plan sem lead `dataAnswer` quando decoupled.*
