# 92 — CP5: verificação independente do governed stage resume e remediação dirigida

**Data:** 2026-10-22 · **Tarefa:** `DELIA-C3-GOVERNED-STAGE-RESUME-INDEPENDENT-VERIFICATION-01`
**Base de verificação:** `origin/main = 7a043525b4` (reancoragem; SHAs CP4 `a2d6576e37` e revisão `5f09a7156a` tratados como referência histórica)
**Escopo:** R1–R4 do doc 91 §6 — reprodução independente, correção mínima dos defeitos reproduzidos, regressão, avaliação real. Sem redesenho de orquestração; limites aprovados preservados (`MAX_GOVERNED_ATTEMPTS=2`, `INTERACTION_TOTAL_BUDGET_SECONDS=60`, `PER_ATTEMPT_MAX_SECONDS=30`).

---

## 1. Veredicto

`ACCEPT_WITH_REMEDIATION` — o mecanismo CP4 é correto na arquitetura (replay tipado, fronteira material, terminal único, cancelamento por ContextVar). **Dois defeitos reais foram reproduzidos e corrigidos minimamente; um terceiro foi refinado.** Nenhuma autorização foi inventada; onde não há contrato de revalidação separado, a dependência é registrada honestamente.

| Resíduo | Classificação | Resultado |
|---|---|---|
| R1 — outcome em cache vs. autorização live | **PARCIALMENTE DEFEITO** — outcome parcial/incompleto era checkpointável | Corrigido: só outcome `COMPLETED`+`is_complete` entra no checkpoint |
| R2 — âncora do orçamento de 60s | **DEFEITO REPRODUZIDO** — `interaction_end` era computado dentro de `attempt()`, ignorando tempo já consumido na interação | Corrigido no owner (`TurnDeadline.started_at`), sem orçamento paralelo |
| R3 — cancelamento mid-attempt | **DEFEITO REPRODUZIDO** — `cancel_check` só era consultado na fronteira de tentativas; novos estágios/invokes podiam iniciar após disconnect | Corrigido: sondas de cancelamento nos seams de modelo, surface-list, relist e invoke |
| R4 — MCP autenticado real | `TEST_NOT_RUN` — bloqueio de credencial | Nenhum `DEV_PORTAL_*` provisionado; não declarado PASS |

---

## 2. R1 — autorização e reutilização de outcomes

### Onde a autorização vive (inventariado, não presumido)

- **AuthZ é remota e por chamada wire.** `McpSpecialistAdapter._connect()` resolve `credential_provider.credential_for(profile)` — o bearer delegado do sujeito — e constrói o transporte. `list_remote_tools` **e** `invoke` passam por `_connect`, logo **a surface-list já é uma verificação AuthZ user-scoped**: uma delegação revogada falha o relist com `MCP_AUTHORIZATION_DENIED`/`MCP_AUTHENTICATION_FAILED` (fail-closed, `_invalidate_on_auth_failure` descarta a credencial rejeitada).
- Não existe contrato de "AuthZ probe" separado do invoke — nenhuma revalidação foi inventada.

### O que o replay realmente garante

Na segunda tentativa, antes de qualquer replay de outcome: (a) a superfície é **relistada ao vivo com o bearer delegado** (AuthZ de list = AuthZ de invoke, mesmo canal); (b) a capability é re-resolvida do grupo fresco (remoção/schema-change → terminal ou re-validação de argumentos); (c) o outcome em cache só retorna para `invoke_key` idêntico (grupo+remote+argumentos byte-idênticos) — **mesma capability, mesmos argumentos, mesma interação, mesmo sujeito, janela ≤60s**.

### Defeito reproduzido e correção

**R1.D:** outcome **parcial/incompleto** era gravado no checkpoint e replayado como evidência concluída. Reproduzido: `RemoteToolOutcome(is_complete=False)` era congelado e replayado na tentativa 2 sem nova leitura. Correção mínima em `_invoke`: o registro exige `outcome.is_complete and outcome.status is COMPLETED` — resultado degradado provoca **releitura legítima** da mesma chamada não-mutante (nunca replay).

### Casos obrigatórios — classificação

| Caso | Resultado |
|---|---|
| READ concluído → timeout posterior → replay sem duplicar | PASS — teste CP4 `test_completed_read_outcome_is_replayed_not_duplicated` revalidado no SHA corrigido |
| Autorização revogada → não apresentar | PASS — revogação falha o relist autenticado → terminal honesto (`test_surface_authorization_failure_between_attempts_is_terminal`) |
| Capability removida entre tentativas | PASS — re-resolução do grupo fresco falha fechado (teste CP4 revalidado) |
| Schema alterado entre tentativas | PASS — `test_schema_change_between_attempts_revalidates_arguments`: argumentos revalidados contra o contrato fresco; invoke bloqueado; terminal não-SUCCESS |
| Argumentos alterados/inválidos | PASS — fingerprint byte-idêntico do `invoke_key` impede replay de argumentos diferentes |
| Evidência expirada | **Dependência de contrato registrada** — não há TTL de outcome no contrato `SpecialistOutcome`; a janela de reuso é a própria interação (≤60s, mesmo sujeito). Sem contrato de expiry, nenhuma política foi inventada |
| Resultado incompleto/sem postcondition | CORRIGIDO — `is_complete`+`COMPLETED` exigidos no checkpoint (`test_partial_outcome_is_refetched_not_replayed`) |
| PREPARE iniciado → timeout → sem 2ª invocação | PASS — fronteira material preservada (teste CP4 revalidado) |
| ACT iniciado → timeout → sem repetição | PASS — idem |
| Classe desconhecida → fail-closed | PASS — `_RESUMABLE_OPERATION_CLASSES` allowlist-only |

**Resíduo honesto:** uma revogação que não afete `tools/list` mas negasse `invoke` é indetectável sem re-invocar — não existe contrato de probe separado. Limitado à janela de uma interação (≤60s, mesmo sujeito, mesmos argumentos). `CHECKPOINT_NEVER_PARALLEL_AUTHORITY=PROVEN`.

## 3. R2 — orçamento end-to-end

**Defeito reproduzido:** `interaction_end = first_deadline.clock() + 60` dentro de `attempt()` mede a partir da entrada do orquestrador, não do início da interação. Com 5s consumidos antes de `attempt()` e 26s na tentativa 1, a tentativa 2 recebia 30s (total 61s) — `test_interaction_budget_counts_time_before_the_orchestrator` falhou em RED.

**Correção no owner:** `TurnDeadline.start()` agora registra `started_at` (o instante real do relógio da interação, criado em `handle_interactive_turn.execute`). `interaction_end = first_deadline.started_at + total_budget`. Deadlines construídos diretamente (sem `started_at`) mantêm o comportamento anterior — sem mecanismo paralelo de orçamento.

**Verificado:** teto de 60s end-to-end incluindo tempo pré-orquestrador; `per_attempt = min(30s, remaining)`; janela < 2s viável → sem retry; sem terceira tentativa; modo legado inalterado. A stream-eval de 60s mostra a 2ª tentativa recebendo **29.6s** (não 30) — a âncora correta em evidência real.

## 4. R3 — cancelamento e transporte NDJSON

**Defeito reproduzido:** `cancel_check` só era avaliado na fronteira de tentativas — um disconnect observado **dentro** de uma tentativa não impedia que o próximo estágio de modelo ou invoke iniciasse. Reproduzido: cancelamento sinalizado durante o relist da tentativa 2 ainda permitia uma nova chamada de modelo.

**Correção:** `_CANCEL_CHECK` ContextVar + `_TurnCancelled` internos, sondados nos seams que iniciam trabalho real: `_model_stage_proposal`, `_invoke`, `list_groups` de superfície e `_fresh_group` — nenhum novo estágio/invoke após cancelamento observado; a tentativa desenrola para o terminal honesto (`PROCESSING_TIMEOUT`, `error_code=cancelled`). Chamadas já em curso **não são interrompidas** (limitação honesta: `GeneratorExit` não cancela I/O em andamento; o retorno é descartado).

**Stream real de ~60s (container, rota NDJSON real):** `scripts/cp5_stream_budget_eval.py` — handler composto real + orquestrador real; apenas o adapter de modelo honra o deadline concedido como o adapter HTTP real. Resultado medido: `elapsed=60.4s`, tentativa 1 grant `30.0s` → TIMEOUT → `CONTINUING` (1×, entregue no stream vivo) → tentativa 2 grant `29.6s` → TIMEOUT → `turn_result` único; fases `REQUEST_RECEIVED→CONTEXTUALIZING→CONTINUING→CONTEXTUALIZING→BLOCKED`; sem eventos pós-terminal. `STREAM_60S_TEST=PASS`.

**Disconnect real no transporte:** `test_stream_disconnect_signals_cancel_and_worker_finishes_bounded` — `response.close()` mid-turn → worker observa `cancel_check()` → finaliza bounded, resultado descartado. `CONTINUING` entregue no stream vivo (`test_continuing_phase_is_delivered_on_the_live_stream`). Checkpoint/cancel são ContextVar — `test_checkpoint_state_never_leaks_between_interactions` prova isolamento entre interações no mesmo orquestrador.

**Infraestrutura:** gunicorn `--threads 4` (gthread — request em voo não é morto pelo `--timeout`), nginx `proxy_read_timeout` por-gap (eventos contínuos), Cloudflare ~100s > 60s+terminal — config do CP4 revalidada, sem alteração.

## 5. R4 — MCP real autenticado

`TEST_NOT_RUN` — **bloqueio:** nenhuma credencial de usuário delegada provisionada neste ambiente (`DEV_PORTAL_USERNAME`/`DEV_PORTAL_PASSWORD` ausentes do shell e de `infra/.env`). Os scripts reais existentes (`real_governed_read_eval.py`, `real_provider_neutral_eval.py`) exigem esse grant de senha; credenciais administrativas não foram usadas como substituto silencioso do usuário. A invocação MCP autenticada pós-resume segue pendente antes de qualquer decisão de produção.

## 6. Reprodução dos incidentes P1/P2 (modelo real, container dev)

`scripts/cp5_incident_repro_eval.py` — handler composto real + LLM real + adapters MCP reais:

| Caso | Pergunta | Estágios de modelo | Resultado |
|---|---|---|---|
| P1 | `qual o ultimo processo cadastrado no transformometro?` | admission×1, select_group×1, turn×1 — 23.2s | `NON_GROUNDED`, COMPLETED, resposta honesta de insuficiência (modelo não selecionou capability) |
| P2 | `quais oa ultimos processos cadastrados?` (typo preservado) | admission×1, select_group×1, turn×1 — 13.2s | `NON_GROUNDED`, COMPLETED, resposta honesta de insuficiência |

Classificação honesta: a cadeia orquestrada real executou e a resposta respeita a fronteira factual (não inventa último processo). O incidente original exigia invoke MCP autenticado — mesmo bloqueio de R4. `P1/P2=MODEL_PATH_EXERCISED,INVOKE_LEG=TEST_NOT_RUN`.

## 7. Avaliação real com modelo (dev container, SHA corrigido)

`cp4_governed_resume_eval.py` (cap de estágio reduzido 3.0→2.0s — o modelo real ficou mais rápido; 2.0s é o mínimo viável):

- **Resume ON + cap 2s:** `interaction_admission×2 + select_group×2` (admission estourou o cap nas duas tentativas — retentativa correta do estágio falho), `CONTINUING=1`, fases `REQUEST_RECEIVED→CONTEXTUALIZING→CONTINUING→CONTEXTUALIZING→BLOCKED`, terminal único com copy honesta de timeout.
- **Legado OFF + cap 2s:** 1 tentativa, `CONTINUING=0`, `BLOCKED` — sem mudança de comportamento.
- **Caminho normal:** resposta real em ~15s, `CONTINUING=0`.

## 8. Regressão

| Suíte | Resultado |
|---|---|
| `test_cp5_governed_resume_verification.py` (novo) | 11 PASS — R1 parcial/relist-AuthZ/schema, R2 âncora, R3 cancel/stream/leak |
| `test_governed_stage_resume.py` (CP4) | 15 PASS — incl. teste de cancelamento rescrito para a semântica nova correta |
| `test_c3_ephemeral_continuity_characterization.py` (CP3) | PASS |
| Ceiling/CP2 timeout (`test_execution_ceiling_turn_budget.py`) | PASS |
| Orquestração, interaction, activity/streaming, CRI, presentation | 318 testes no recorte — PASS |
| **Suíte backend completa** | **PASS — sem exclusões ocultas** |
| Frontend `tsc -p tsconfig.app.json` | PASS — após fix mínimo de narrowing em `conversationQueue.test.ts` (defeito pré-existente no HEAD, commit upstream `cff65bb63b`, não relacionado ao CP5) |
| Frontend vitest | **322 PASS** (27 arquivos) |

## 9. Arquivos alterados

- `delia-api/app/application/interaction/turn_budget.py` — `started_at` (âncora do orçamento no início real da interação).
- `delia-api/app/application/capability_provision/orchestration.py` — `_CANCEL_CHECK`/`_TurnCancelled` + sondas nos seams de modelo/surface/invoke; `interaction_end` ancorado em `started_at`; checkpoint só de outcomes `COMPLETED`+`is_complete`.
- `delia-api/tests/test_cp5_governed_resume_verification.py` — novo, 11 testes.
- `delia-api/tests/test_governed_stage_resume.py` — teste de cancelamento rescrito (a semântica nova bloqueia corretamente a 1ª chamada quando já cancelada) + caso novo `test_cancellation_from_the_start_runs_no_model_call`.
- `delia-api/scripts/cp4_governed_resume_eval.py` — cap de estágio 3.0→2.0s (mínimo viável) para o timeout real do modelo.
- `delia-api/scripts/cp5_stream_budget_eval.py` — novo, stream NDJSON real de ~60s.
- `delia-api/scripts/cp5_incident_repro_eval.py` — novo, reprodução P1/P2.
- `plugins/delia/src/queue/conversationQueue.test.ts` — fix de narrowing `never` pré-existente no HEAD (unblock do gate de typecheck; `let first!:` idiom já usado no mesmo arquivo).

## 10. Resíduos

**Materiais:** (1) `REAL_MCP_EVALUATION=TEST_NOT_RUN` — invocação autenticada pós-resume pendente de credencial delegada legítima; (2) revogação invisível ao relist (negar invoke sem negar list) não é detectável sem re-invocação — não existe contrato de probe; dependência registrada, não inventada.

**Não bloqueantes:** chamadas modelo/MCP já em curso não são interrompidas pelo disconnect (o resultado é descartado — caracterizado honestamente); sem TTL contratual de outcome (a janela de reuso é a interação ≤60s).

**Produção:** `DELIA_MAX_GOVERNED_ATTEMPTS` permanece `:-1` (OFF) — ativação não autorizada nesta tarefa.

`CP5_VERIFICATION=EXECUTED` · `R1=REMEDIATED(partial-outcome checkpoint)` · `R2=REMEDIATED(interaction-start anchor)` · `R3=REMEDIATED(mid-attempt cancel seams)` · `R4=TEST_NOT_RUN(credential blocker)` · `PRODUCTION_ENABLED=NO` · `I04_ACCEPTED=NO` · `C3_EXECUTED=YES`
