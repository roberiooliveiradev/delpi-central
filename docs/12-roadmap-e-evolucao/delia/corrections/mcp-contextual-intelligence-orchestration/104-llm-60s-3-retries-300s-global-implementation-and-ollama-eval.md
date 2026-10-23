# 104 — Implementação doc 103: 60s/chamada LLM, até 3 tentativas, 300s globais — backend, frontend e eval Ollama GPU

**Data:** 2026-10-23. **Task:** `DELIA-C3-LLM-60S-3RETRIES-300S-FULL-IMPLEMENTATION-AND-LOCAL-EVAL-01` (Task 2 do doc 101). **Status:** IMPLEMENTATION=DEV_VERIFIED; PRODUCTION_CHANGED=NO; PRODUCTION_RETRY=OFF; EXTERNAL_LLM_CALLS=0.

## Escopo executado

Implementação integral da política aprovada no doc 103 sobre os owners canônicos já inventariados no doc 102 — sem engine/scheduler/fila/registry novo:

| Responsabilidade | Owner | Mudança |
|---|---|---|
| Teto por chamada real do LLM | `model_invocation/invoke_model.py` | `MAX_TIMEOUT_SECONDS` 30→**60** — era o corte efetivo escondido que invalidava qualquer chamada >30s com `invalid_request` |
| Limite de estágio por chamada | `config/settings.py` + `orchestration.py` | `MODEL_STAGE_TIMEOUT` default 30→**60**; `call_timeout = min(stage_timeout, deadline.remaining_seconds())` recalculado por invocação |
| Retry por chamada lógica | **novo** `model_invocation/governed_retries.py` | `LLM_CALL_MAX_ATTEMPTS=3`; elegíveis `TIMEOUT`, `PROVIDER_UNAVAILABLE`, `INVALID_STRUCTURED_OUTPUT`; definitivas (`invalid_request`, `unsupported_model`, `policy_denied`, `provider_rejected`, `evaluation_failure`) não repetem |
| Loops de retry | `orchestration.py::_model_stage_proposal`, `handle_interactive_turn.py` (conversacional) | até 3 invocações reais; cancel-check antes de cada retry; `CONTINUING` emitido quando retry realmente inicia; ledger registra falhas reais sem fabricar usage; 4ª invocação impossível por construção |
| Deadline global | `turn_budget.py` + settings | `DEFAULT_TURN_BUDGET_SECONDS`/`INTERACTION_TOTAL` → **300** monotônico, ancorado no início da interação, nunca reinicia |
| Cancelamento | `errors.py` + ambos os loops | `CANCELLED` explícito; cancelamento entre retries impede a próxima invocação real |
| Continuidade user-facing | `activity/activityView.ts` | `CONTINUING` → “Preciso de mais tempo para concluir esta análise. Vou continuar…” (emitido só quando retry/resume real começa — sem aviso falso, sem porcentagem, sem CoT) |
| Painel Contexto (residual UX aprovado) | `ConversationThreeRegionLayout`, `DeliaConversationPage`, `App.tsx`, `index.css` | `rightOpen` opcionalmente controlado (default uncontrolled preservado); “Ver contexto” seleciona+abre em um clique; fechar limpa o realce; barra azul substituída por tint/outline discreto |

### Separação retry-de-chamada × resume-de-turno

Decisão semântica registrada: `model_timeout` que já consumiu as 3 invocações da chamada lógica é **terminal** — um resume de turno criaria uma 4ª invocação proibida da mesma chamada. O governed resume (CP4) fica reservado a `turn_budget_exhausted` com trabalho checkpointado, e só dispara de estágios que propagam a exaustão (o estágio de arguments converte exaustão em clarificação/projeção, comportamento existente preservado). MCP/Domain invocations e operações materiais nunca são repetidas por retry de LLM.

## Configuração efetiva

| Variável | Código (default) | dev compose | prod compose |
|---|---|---|---|
| `DELIA_LLM_TIMEOUT_SECONDS` | 30 | **60** | 30 (frozen) |
| `DELIA_MODEL_STAGE_TIMEOUT_SECONDS` | **60** | 60 | 30 (frozen) |
| `DELIA_TURN_BUDGET_SECONDS` | **300** | 300 | 30 (frozen) |
| `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS` | **300** | 300 | 60 (frozen) |
| `DELIA_MAX_GOVERNED_ATTEMPTS` | 1 | 2 | 1 (frozen) |

Produção verificada congelada em todos os cinco valores; `mcp_timeout=15s` e demais timeouts de fonte intactos; rollback = reverter este diff (valores anteriores já estão no histórico).

## Evidência determinística (suite backend)

**1986 testes coletados — exit 0** (3 skips pré-existentes). Novos/ajustados cobrem a matriz doc 103:

- Timeout em 1ª/2ª tentativa com sucesso subsequente; exaustão de timeout → `model_timeout` terminal honesto
- 3 falhas elegíveis → terminal; **4ª invocação nunca criada** (assertivo sobre o stub)
- `INVALID_STRUCTURED_OUTPUT` e `PROVIDER_UNAVAILABLE` elegíveis; `invalid_request`/`policy_denied` sem retry
- Cancelamento entre retries → zero novas chamadas reais no re-attempt
- Per-call grant ≤60s e clamped pelo deadline remanescente
- Governed resume a partir de `turn_budget_exhausted` em estágio propagante; schema/capability/AuthZ revalidados; owner reads completados não duplicam; PREPARE/ACT sem replay
- `CONTINUING` emitido somente em início real de retry/resume
- Ledger: durações reais por invocação, `budget_remaining_ms` honesto, erros sem usage fabricado

Testes de caracterização atualizados para a política aprovada (valores 30s→60s/300s, gatilhos de resume movidos do estágio de arguments para estágios propagantes) — nenhuma assertiva de segurança enfraquecida: no-read-após-falha, no-provider-call-após-cancel, no-material-action-sem-confirmação permanecem.

## Eval real Ollama — CPU fallback + GPU

Harness: `delia-api/scripts/doc103_budget_continuity_eval.py` — adapter real, egress fail-closed (`OLLAMA_ONLY`), 26 cenários (G1–G5 gerais, D1–D11 DELPI, V1–V7 variações semânticas, M1 follow-up multi-turn, C1a/C1b concorrência bounded). Artefatos locais: `~/doc103-eval-artifacts/{doc103_eval,doc103_eval_gpu}.{json,log}`.

| Métrica | CPU (watchdog caiu, fallback) | GPU 100% (`ollama ps`) |
|---|---|---|
| Cenários | 26 | 26 |
| Chamadas reais | 116 | 123 |
| Latência chamada p50 / p95 / max | 3.44s / 10.06s / 26.61s | **0.78s / 2.96s / 5.31s** |
| Latência turno p50 / p95 / max | 14.95s / 47.75s / 67.49s | **5.98s / 11.48s / 17.49s** |
| `invalid_structured_output` | 25 | 13 |
| `timeout` | **0** | **0** |
| Eventos `CONTINUING` | 17 | 9 |
| EXCEPTIONs (terminal honesto) | 5 | 4 |
| Tokens (usage real) | — | in 85.921 / out 4.365 |

Ambas as execuções: **nenhuma chamada ≥60s, nenhum turno ≥300s, zero timeout** — os tetos aprovados nunca foram atingidos na amostra. `model=qwen2.5:3b`, RTX 3050 6GB, `100% GPU` confirmado via `ollama ps` antes e durante a bateria.

### Diagnóstico por cenário (GPU)

- **G1/C1a (saudação, classe `conversation`):** estágio `turn` produziu JSON malformado 3× → exatamente 3 invocações, terminal EXCEPTION honesto. O retry funcionou conforme o contrato; a falha é aderência-JSON do 3B no estágio conversacional (residual conhecido docs 96/97 — velocidade ≠ qualidade estrutural).
- **M1_followup:** anáfora resolvida — `arguments` extraiu `{'code': '10080043'}` do contexto de turno anterior. Continuidade contextual funcional.
- **D9 `use o DAVI`:** seleção semântica preferiu `openapi:delpi`/`delpi.search_products` sobre `mcp:davi`; args incompletos → clarificação honesta. Residual de qualidade semântica do 3B, não de contrato.
- **D8 `terminal bala`:** admission classificou como `hypothetical` → resposta conversacional. Miss-classificação do modelo, sem degradação de governança.
- **D7/V2/V6/M1 invoke:** “acesso à fonte autoritativa necessária negado” — fail-closed correto: o harness não porta bearer delegado, então o invoke é negado e a resposta é honesta (não inventa dado). Governança READ/AuthZ íntegra.
- **V4 troca de especialista:** seleção retornou `remote_name=None` → fallback conversacional com limitação honesta.
- **C1a/C1b concorrência bounded:** executadas em paralelo; resultados independentes (1 EXCEPTION honesta, 1 sucesso).

## Frontend

- delia: `tsc` limpo, **336 vitest verdes**, build Vite + `verify:federation` OK
- plugin-ui: **2315 testes verdes**
- `BROWSER_QA=TEST_NOT_RUN` — o Portal serve build MFE anterior; QA real no portal permanece pendente de deploy autorizado

## Resíduos materiais

1. `invalid_structured_output` do `qwen2.5:3b` no estágio conversacional (G1/G3/D2/C1a) — 4 terminais EXCEPTION no GPU run; classe recuperável exercitada corretamente, mas a taxa do modelo 3B limita a qualidade de saudações/ambíguas. Não é regressão: evidenciado desde o doc 93.
2. Seleção semântica 3B: D8 miss-class (hypothetical vs operational), D9 escolha de grupo subótima. Qualidade de modelo, não contrato.
3. `BROWSER_QA=TEST_NOT_RUN` (MFE stale no portal).
4. R4 revogação intra-turno: `DEFERRED_BY_PO`, risco `OPEN` — inalterado; retry produtivo continua bloqueado por esse gate.

## DECISION_LOG

`LLM_CALL_TIMEOUT_EFFECTIVE=60s`; `LEGACY_10S_AND_30S_CUTOFFS=REMOVED_NO_OWNER`; `LLM_CALL_MAX_ATTEMPTS=3`; `FOURTH_ATTEMPT_BLOCKED=BY_CONSTRUCTION`; `GLOBAL_INTERACTION_CAP=300s_MONOTONIC`; `OPERATIONAL_TIMEOUTS_PRESERVED=mcp15+sources`; `NEW_MODULE=governed_retries (policy only, no engine)`; `PRODUCTION_CHANGED=NO`; `RELEASE=NOT_AUTHORIZED`; `EXTERNAL_LLM_CALLS=0`; `I04_ACCEPTED=NO`.
