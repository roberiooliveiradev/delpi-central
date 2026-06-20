# Changelog — Playbook 19: prosa analyser, latência operacional e skip RAG

**Data:** jun/2026  
**Commit:** `6644de410` — `fix(chat): prosa LLM do analyser e latência operacional ~50% menor`  
**Escopo:** qualidade da prosa em rotas analyser/pricing, presets de latência, contexto LLM compacto, pipeline skip RAG em síntese operacional.

---

## Problema observado

Pergunta «me fale do produto 10080024» retornava prosa genérica («Foram retornados 14 registros») com banner `llm_synthesis`, tabela analyser e latência ~67–76 s (LLM ~92% do turno; RAG ~7 s mesmo com tool ok).

---

## Causa raiz — prosa genérica

No `presentation_profiles.json`, os perfis **`analyser`** e **`sale_pricing`** tinham **`commentaryProfileKey` duplicado** no mesmo objeto JSON — a segunda chave (`generic_list`) sobrescrevia a primeira (`analyser` / `sale_pricing`).

Efeito: `ChatDataInsightService` + `ChatOperationalDataCommentaryService` geravam `dataAnswer.summary` genérico de listagem em vez do commentary específico do analyser.

**Correção:** remover a chave duplicada; manter só `commentaryProfileKey: analyser` e `commentaryProfileKey: sale_pricing`.

**Regressão:** `test_build_product_analyser_uses_analyser_commentary_not_generic_list`.

**Armadilha JSON:** chaves duplicadas em perfis declarativos não falham no parse — sempre validar com `--check-commentary-profiles` ou teste de perfil.

---

## Render plan com prosa LLM desacoplada

Quando `llmProseDecoupled: true` (Playbook 19), o segmento `decision` com `source: dataAnswer` **não** entra mais no `renderPlan.lead`.

| Antes | Depois |
|-------|--------|
| Lead misturava `dataAnswer` genérico + stream LLM | Lead = só `assistantMessage` (prosa streamada) |
| Usuário via «14 registros» antes/durante a síntese | Visuais (tabela analyser) + prosa LLM assertiva |

Serviço: `ChatPresentationRenderPlanService._should_include_decision` — retorna `false` se `_is_llm_prose_decoupled(metadata)`.

Fatos estruturados continuam no prompt via `ChatOperationalLlmSynthesisContextService` (não no lead visual).

---

## Contexto LLM — fatos compactos (analyser)

| Mudança | Arquivo / serviço |
|---------|-------------------|
| Tabelas `role=profile` formatadas como `Campo: valor` | `ChatOperationalLlmSynthesisContextService._format_table_row_fact` |
| Limite maior de linhas para tabela profile | `operational_llm_synthesis_context.json` → `maxProfileTableRows: 8` |
| Budget global do bloco de fatos reduzido | `maxChars: 900` (antes 1400); `maxTableRows: 4`; `maxHumanizedLines: 4` |

Motivo: prompt menor → menos tokens → latência menor sem perder campos do perfil técnico do produto.

---

## Latência operacional (~50%)

### Preset global `operational_cpu` como default

| Componente | Antes (typical dev/balanced) | Depois |
|------------|------------------------------|--------|
| `DEFAULT_PROFILE` | `balanced` | **`operational_cpu`** |
| `LLM_MAX_TOKENS` (preset) | 384–1536 | **320** |
| `OLLAMA_NUM_CTX` (preset) | 1536–2048 | **1024** |
| Perfil `balanced` (fallback unknown) | 1536 / 2048 | **768 / 1536** |

Arquivo: `app/infrastructure/config/llm_latency_profile.py`.

Compose dev/prod: `CHAT_LLM_LATENCY_PROFILE=operational_cpu`, `OLLAMA_MODEL=qwen2.5:1.5b`, `LLM_MAX_TOKENS=320`, `OLLAMA_NUM_CTX=1024`.

### Modos composer (presets default em código)

| Modo | Modelo | max_tokens | num_ctx |
|------|--------|------------|---------|
| **Rápida** | `qwen2.5:1.5b` | 160 | 768 |
| **Normal** | `qwen2.5:1.5b` | 320 | 1024 |
| **Pensador** | `qwen2.5:1.5b` | 512 | 1536 |

Serviço: `ChatResponseModeService.resolve()`. Stack mínimo WSL: `infra/docker-compose.minimal.yml` (presets intermediários).

### Skip RAG em síntese LLM operacional

Bug: ao limpar `directAnswer` para forçar síntese LLM, `skip_rag` era zerado e o pipeline executava RAG (~7 s) mesmo com fatos da tool.

Correção: `ChatResponseModeService._resolve_skip_rag_for_llm_synthesis` — preserva `skip_rag=True` existente; se `execute_external_action` com `metadata.ok`, força skip (fatos da tool bastam).

Smoke «me fale do produto 10080024» pós-tuning (CPU WSL):

| Modo | Latência aprox. (antes → depois) |
|------|----------------------------------|
| Rápida | ~15 s |
| Normal | ~31 s (antes ~67 s) |
| Pensador | ~33 s (antes ~72 s) |

Quality gates do smoke permanecem OK (`templateSimilarity`, anti-deflexão, ladder).

---

## Servidor produção CPU (srv-api)

O compose prod injeta defaults enxutos; hosts com `.env` legado (3b, ctx 2048, tokens 1536) **não** herdam automaticamente o tuning jun/2026.

Recomendação explícita no `.env` do servidor:

```env
CHAT_LLM_LATENCY_PROFILE=operational_cpu
OLLAMA_NUM_CTX=1024
LLM_MAX_TOKENS=320
CHAT_RESPONSE_MODE_NORMAL_MAX_TOKENS=320
CHAT_RESPONSE_MODE_NORMAL_NUM_CTX=1024
CHAT_RESPONSE_MODE_FAST_MAX_TOKENS=160
CHAT_RESPONSE_MODE_FAST_NUM_CTX=768
CHAT_RESPONSE_MODE_THINKER_MAX_TOKENS=512
CHAT_RESPONSE_MODE_THINKER_NUM_CTX=1536
```

Manter `OLLAMA_MODEL=qwen2.5:3b` no srv-api se desejado para turnos fora dos modos; modos composer usam `CHAT_RESPONSE_MODE_*_MODEL`.

Após editar: `docker compose -f infra/docker-compose.yml up -d --force-recreate minha-delpi-ai-api`.

---

## Testes

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_response_mode_service.py -q
.venv/bin/python -m pytest tests/unit/infrastructure/config/test_llm_latency_profile.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_presentation_render_plan_service.py -q
.venv/bin/python -m pytest tests/unit/domain/services/test_chat_operational_llm_synthesis_context_service.py -q
SMOKE_SCENARIO=factory_status .venv/bin/python scripts/smoke_llm_universal_prose.py
```

---

## Referências

- [`playbook-19-inferencia-llm-universal.md`](../roadmap/playbook-19-inferencia-llm-universal.md) § 7
- [`chat-response-modes.md`](../architecture/chat-response-modes.md)
- [`rag-context-min-score-calibracao.md`](../roadmap/rag-context-min-score-calibracao.md) § Homologação de latência
- [`chat-assistant-content-presentation.md`](../architecture/chat-assistant-content-presentation.md) § Prosa LLM desacoplada
- Changelog anterior: [`2026-06-playbook-18-prosa-template-llm.md`](./2026-06-playbook-18-prosa-template-llm.md)
