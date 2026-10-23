# 105 — GATE 1 isolamento de retry produtivo + GATE 2 validação local de stream 300s

**Data:** 2026-10-23. **Task:** `DELIA-C3-MODEL-RETRY-ISOLATION-AND-300S-STREAMING-VERIFICATION-01`.
**Base:** `origin/main` = `941544bda741ba3f7c8189d059f519076998509c` (reanciado). **Escopo:** os dois blockers do parecer de coordenação anexado ao doc 104 — (1) retry por chamada lógica sem isolamento de configuração, (2) stream NDJSON longo/cancelamento sem prova local real.
**Veredicto:** `GATE1=PASS`, `GATE2=PASS_LOCAL`, `PRODUCTION_CHANGED=NO`, `RELEASE=NOT_AUTHORIZED`.

## GATE 1 — isolamento `MODEL_CALL_ATTEMPTS` ≠ `TURN_RESUME_ATTEMPTS`

### Mudança

- `settings.py`: novo `DELIA_LLM_CALL_MAX_ATTEMPTS` (env `DELIA_LLM_CALL_MAX_ATTEMPTS`), parse com convenção canônica `*_config_source` / `*_config_invalid`. **Default fail-closed = 1** (OFF). Teto PO = 3; fora de [1,3] (zero/negativo/acima/não-numérico) → **inválido → fallback 1** + warning de configuração (fail-closed, nunca habilitação involuntária).
- `governed_retries.py`: `LLM_CALL_MAX_ATTEMPTS` permanece como teto PO do predicado; a política recebe agora o limite efetivo (`call_retry_eligible(code, attempt, max_attempts=1)` — default 1). Nenhuma classe nova de erro; elegíveis seguem `TIMEOUT`, `PROVIDER_UNAVAILABLE`, `INVALID_STRUCTURED_OUTPUT`.
- `orchestration.py` e `handle_interactive_turn.py`: novo parâmetro injetado `llm_call_max_attempts`, clampeado a `[1,3]` no ctor; o retry loop consulta o limite efetivo, `cancel_check` e o `TurnDeadline` remanescente **antes de cada tentativa**. `max_governed_attempts` (resume de turno) inalterado e ortogonal.
- `root_composer.py`: propaga `settings.llm_call_max_attempts` para ambos os consumers e loga política efetiva com fail-closed warning (`config_invalid` → OFF).
- `infra/docker-compose.dev.yml`: `DELIA_LLM_CALL_MAX_ATTEMPTS=3` (dev autorizado). `infra/docker-compose.yml`: `DELIA_LLM_CALL_MAX_ATTEMPTS=1` (prod explícito OFF).

### Provas

- OFF (default/prod): timeout, `invalid_structured_output` e provider-unavailable → **1 invocação**, zero `CONTINUING`, terminal honesto — testes novos em ambos consumers (`test_governed_stage_resume.py` GATE-1 matrix; `test_turn_observability.py` OFF default).
- ON (dev): falha×2→sucesso na 3ª prova 3 calls reais + `CONTINUING` por retry; 3 falhas → terminal honesto; 4ª chamada impossível por construção (`attempt<3` no predicado) e por teste (`adapter.calls==3`).
- Cancel entre retries → nenhuma chamada nova; deadline remanescente respeitado (`min(call_cap, deadline.remaining)` re-derivado por invocação); não-recuperável → sem retry; **zero replay MCP/Domain/material** (retry nunca re-invoca estágios operacionais).
- Config inválida: `0`, `-2`, `9`, `abc`, ausente → effective `1` + `config_source`/`config_invalid` corretos (testes em `test_config.py`).
- Fio real: probe server real (`scripts/gate2_stream_probe.py`, WSGI real, adapter de borda com TIMEOUT controlado) — `DELIA_LLM_CALL_MAX_ATTEMPTS=3` → `CONTINUING`×2 na wire + `adapter_calls`>1; `=1` → `adapter_calls=1`, zero `CONTINUING`, `turn_error` honesto `model_timeout`.

## GATE 2 — stream NDJSON longo, keepalive, cancelamento, terminal único

### Mudança

- `interaction_routes.py`: `_INTERACTION_KEEPALIVE_SECONDS=15.0`; `items.get(timeout=...)` no generator; em `queue.Empty` (e turno vivo) emite `{"type":"keepalive","version":"1"}` — **registro de transporte**, sem `event_id`/`sequence`/`phase`, nunca conta como `activity_event`. `X-Accel-Buffering: no` já presente; fila bounded inalterada (`put_nowait`, terminal nunca dropado); um único `turn_result`/`turn_error`; `GeneratorExit`→`disconnect.set()` + join bounded do worker.

### Provas

- **Wire real (socket HTTP real, container eval `infra-delia-api`, Ollama-only):** silêncio de 2.5s → keepalives fluem a cada intervalo, depois evento real + terminal único. Turno real end-to-end (`:18000`, JWT Keycloak real via Core `/me`, `qwen2.5:3b` **100% GPU**) → 3 `activity_event` + `turn_result` único em ~4.4s.
- **Disconnect real:** kill do cliente a ~6.5s durante a 2ª tentativa (modo `always_timeout`) → `adapter_calls=2` no drop e +8s depois — **nenhuma chamada nova pós-cancelamento**, worker bounded (in-flight termina dentro do deadline; nenhuma tentativa adicional inicia).
- **Determinístico:** 47 testes `test_activity_streaming` verdes — keepalive nunca impersona progresso, janela silenciosa longa com keepalives bounded, disconnect durante silêncio cancela e para trabalho novo, saturação de fila preserva terminal (60 intermediários + terminal), dedup/sequência, um só terminal.
- **Teto 300s:** fake clock (`TurnDeadline.start(300.0, clock=...)`) prova grant ≤60s por chamada e exaustão global determinística — sem wall-clock de 5min.
- **Frontend:** parser ignora `keepalive` e tipos desconhecidos (teste novo: keepalives ×2 + `future_record_kind` + terminal → 1 evento, resultado OK). `tsc` limpo; 337 vitest verdes; build+federation OK.

## Configuração efetiva avaliada

| Setting | dev | prod |
|---|---|---|
| `DELIA_LLM_TIMEOUT_SECONDS` | 60 | 30 (congelado) |
| `DELIA_MODEL_STAGE_TIMEOUT_SECONDS` | 60 | 30 (congelado) |
| `DELIA_TURN_BUDGET_SECONDS` | 300 | 30 (congelado) |
| `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS` | 300 | 60 (congelado) |
| `DELIA_LLM_CALL_MAX_ATTEMPTS` | **3** | **1 (OFF explícito)** |
| `DELIA_MAX_GOVERNED_ATTEMPTS` | 2 | 1 (resume, inalterado) |

## Resíduos materiais

1. `EDGE_300S_VERIFICATION=TEST_NOT_RUN` — edge externa (Cloudflare/produção) não testável localmente; gate de release preservado. Dev gateway `/apps/delia-api/`: `proxy_read_timeout 120s` **por gap** — keepalive ≤15s satisfaz com folga; `proxy_buffering` não desabilitado na rota, mas `X-Accel-Buffering: no` upstream instrui flush imediato.
2. `GATEWAY_LIVE_NDJSON=TEST_NOT_RUN` — o container dev em execução roda o código de `main` (sem keepalive) e aponta para OpenRouter (pago): provar NDJSON via gateway teria consumido LLM externo pago. Prova real feita em container eval dedicado com a mesma stack WSGI real.
3. `BROWSER_QA=TEST_NOT_RUN` — Portal serve build MFE stale (residual do doc 104, inalterado).
4. Keepalive é transport-only: o MFE o ignora por design; se futuro MFE quiser exibir "ainda processando", novo contrato precisaria de aprovação.
5. R4 revogação intra-turno: `OPEN/DEFERRED_BY_PO` — inalterado; retry produtivo continua bloqueado por esse gate.

## Rollback

- `git revert` do commit desta task restaura: `governed_retries` com limite fixo 3, consumers sem `llm_call_max_attempts`, stream sem keepalive, composes sem o novo pin. Produção intocada (nada a reverter lá).
- Para ativação futura de retry produtivo (após gates + R4): apenas `DELIA_LLM_CALL_MAX_ATTEMPTS=3` no env prod — nenhuma mudança de código.

## DECISION_LOG

`MODEL_CALL_RETRY_CONFIG=DELIA_LLM_CALL_MAX_ATTEMPTS`; `TURN_RESUME_CONFIG=DELIA_MAX_GOVERNED_ATTEMPTS (intocado)`; `CONFIG_FAIL_CLOSED=YES (default/absent/invalid→1; >3 inválido→1)`; `DEV_MODEL_CALL_RETRIES=3`; `PROD_MODEL_CALL_RETRIES=1`; `RETRY_OFF_NEGATIVE_TESTS=PASS (ambos consumers)`; `RETRY_ON_TESTS=PASS`; `THIRD_ATTEMPT_PROOF=PASS (wire+unit)`; `FOURTH_ATTEMPT_BLOCKED=BY_CONSTRUCTION+TEST`; `CANCEL_BETWEEN_RETRIES=PASS (unit+wire)`; `NO_MATERIAL_REPLAY=PASS`; `GLOBAL_CAP_300S=PASS_DETERMINISTIC (fake clock)`; `NDJSON_LONG_STREAM=PASS_LOCAL_REAL_HTTP`; `KEEPALIVE_BEHAVIOR=PASS (transport-only, ≠progresso)`; `BACKPRESSURE=PASS (bounded queue, terminal nunca dropado)`; `DISCONNECT_CANCEL=PASS (wire: adapter_calls congelou)`; `ORPHAN_WORKERS=NONE_OBSERVED (join bounded)`; `SINGLE_TERMINAL=PASS`; `GATEWAY_LOCAL=CONFIG_VERIFIED+REAL_HTTP_DIRECT`; `EDGE_300S_VERIFICATION=TEST_NOT_RUN`; `BROWSER_QA=TEST_NOT_RUN`; `FRONTEND_CONTINUITY=PASS`; `OLLAMA_MODEL=qwen2.5:3b`; `GPU_OFFLOAD=100%`; `EXTERNAL_LLM_TEST_CALLS=0`; `PAID_FALLBACK=DISABLED`; `BACKEND_REGRESSION=2036 tests exit 0`; `FRONTEND_REGRESSION=337 delia vitest + tsc + build + federation OK`; `PRODUCTION_CHANGED=NO`; `PRODUCTION_RETRY_STATUS=OFF (env=1, R4 gate aberto)`; `REVOCATION_RISK=OPEN/DEFERRED_BY_PO`; `PHASE_ADVANCE=NO`.


## Parecer de coordenação — 2026-10-23

**REVIEW_VERDICT=ACCEPT_WITH_RESIDUAL (GATE1 + GATE2 LOCAL)**. Verificados no GitHub o HEAD `24d230eb15f2d2e090829d9396c25fe1836e44d3`, o relatório 105 e o registro na trilha. Evidências de testes e HTTP real foram executadas pelo Cursor, não reproduzidas independentemente nesta revisão (`INDEPENDENT_RUNTIME_REEXECUTION=TEST_NOT_RUN`).

**Gate 1 — ACCEPT_LOCAL:** `DELIA_LLM_CALL_MAX_ATTEMPTS` separado de `DELIA_MAX_GOVERNED_ATTEMPTS`, default e config inválida fail-closed para uma chamada, prod compose explicitamente 1, dev 3; testes negativos nos dois consumers, terceira tentativa e proibição da quarta, cancelamento e não repetição material reportados. A configuração produtiva ativa ainda precisa ser verificada no deploy; arquivo compose não prova runtime remoto.

**Gate 2 — ACCEPT_LOCAL_WITH_RESIDUAL:** keepalive transport-only no NDJSON, sem ActivityEvent falso; teste de fluxo HTTP local, client disconnect e frozen adapter-call-count, single terminal, bounded queue e teto 300s via fake clock. O limite máximo e transporte de cinco minutos não foram exercidos integralmente via navegador+edge; `GATEWAY_LIVE_NDJSON=TEST_NOT_RUN`, `EDGE_300S_VERIFICATION=TEST_NOT_RUN`, `BROWSER_QA=TEST_NOT_RUN`. Não usar teste unitário/fake clock para alegar Cloudflare end-to-end validado. 

**Risco e liberação:** R4 revogação intra-turno permanece OPEN/DEFERRED_BY_PO. `PRODUCTION_CALL_RETRY=OFF` e `PRODUCTION_TURN_RESUME=OFF` até aprovação aplicável; não declarar release produtivo autorizado com base neste aceite local. `SEMANTIC_MODEL_QUALITY` e `BUSINESS_OUTCOME` continuam escopos de avaliação separados. Próximo passo delimitado: QA real de browser/gateway com build atual e modelo/identidade autorizados, sem executar bateria paga de LLM externo. `I04_ACCEPTED=NO` até decisão canônica.
