# 102 — ADR/CONTRACT: orçamentos ampliados de LLM e continuidade governada

**Data:** 2026-10-23
**TASK_ID:** `DELIA-C3-BUDGET-CONTINUITY-CONTRACT-DECISION-01` (Task 1 do roadmap doc 101)
**Status:** `PROPOSED_CONTRACT` — documento de decisão; **nenhum código, runtime ou deploy alterado**. `CODE_CHANGE=NONE`.
**Autoridade de entrada:** decisão PO doc 100 (`PRODUCT_DIRECTION=APPROVED`), roadmap doc 101, evidência de atribuição doc 99/Etapa 6, incidentes de 22/10/2026, policy Ollama-only.

---

## 1. Contexto e decisão de produto

O PO aprovou (doc 100):

- Até **60 s de trabalho semântico do LLM por tentativa** (o teto anterior de 30 s/attempt é insuficiente em casos operacionais complexos).
- Até **3 tentativas governadas** dentro da mesma interação original.
- **B+D**: reserva de tempo para execução operacional (B) e encerramento honesto quando não houver condição de continuar em segurança (D).
- Comunicação real de continuidade/cancelamento ao usuário, sem chain-of-thought.
- Sem heurísticas lexicais (regex/keywords/aliases/branches por provider); autoridade das Domain APIs inalterada.
- **TO_DECIDE:** duração total da interação e valor da reserva operacional — proposta concreta abaixo (§5, §6), não aprovada ainda.
- R4 revogação intra-turno: `REVOCATION_RISK=OPEN`, `REVOCATION_REMEDIATION=DEFERRED_BY_PO`; produção multi-attempt permanece bloqueada até gate canônico.

## 2. Inventário de mecanismos existentes

| Responsabilidade | Owner canônico | EXISTING_EQUIVALENT | REUSE_DECISION | Notas |
|---|---|---|---|---|
| Deadline monotônico do turno | `turn_budget.py` `TurnDeadline` (ends_at, clock, started_at, remaining_seconds, stage_timeout clamp, check) | YES | EXTEND | `stage_timeout()` já implementa "min(cap, remaining)"; `started_at` ancora o orçamento monotônico real |
| Budgets | `orchestration.py` consts: `GOVERNED_ATTEMPT_MAX_SECONDS=30`, `MAX_GOVERNED_ATTEMPTS=2`, `DEFAULT_INTERACTION_TOTAL_BUDGET_SECONDS=60`, `MODEL_STAGE_TIMEOUT_SECONDS=10`, `MIN_VIABLE_MODEL_STAGE_SECONDS=2`, `CONVERSATIONAL_FALLBACK_RESERVE_SECONDS=8`, `INTERACTION_ADMISSION_STAGE_CAP=6` | YES | EXTEND | precedente de reserva já existe (CONVERSATIONAL_FALLBACK_RESERVE); teto 30s/attempt é constante |
| Loop de tentativas | `orchestration.attempt()` — monotonic `interaction_end`, `min(GOVERNED_ATTEMPT_MAX_SECONDS, remaining)`, boundary reasons `model_timeout/turn_budget_exhausted/cancelled`, bloqueio se `mutating_invoke_started` | YES | EXTEND | fronteira 1ª/2ª tentativa já emite classificação; estende-se a 3ª |
| Resume/checkpoint | `_RESUME_STATE` ContextVar; replay só de estágios comprovadamente concluídos; `mutating_invoke_started` bloqueia novas tentativas | YES | REUSE | invariantes de replay já codificados |
| Model Invocation | `ModelInvocation` adapter (`execute`, timeout por estágio, usage provider-reported) | YES | REUSE | timeout por chamada já é parâmetro; quota é débito de soma, não novo engine |
| Progresso/atividade | `ActivityPhase.CONTINUING` (RUNNING), ActivityEvent v1, emissão via `activity_channel` | YES | EXTEND | fase CONTINUING já existe e mapeia para RUNNING |
| NDJSON stream | `interaction_routes._stream_interaction_turn` — fila bounded 64+2, preflight antes de headers, disconnect.set() → cancel_check, terminal único, sentinel | YES | REUSE | disconnect já impede nova tentativa; in-flight termina bounded |
| Cancelamento | `cancel_check` + `_CANCEL_CHECK` ContextVar consultado em seams de estágio e fronteira de tentativa | YES | REUSE | sinal imediato; chamada em curso termina bounded |
| Observabilidade | `turn_observability` (Etapa 6): `elapsed_ms{model,operational,composition,other}`, `operational_calls[]`, `calls[].budget_remaining_ms`, `timeout_source`, tokens provider-reported | YES | REUSE | métricas separadas A/B/C já serializadas |
| MCP/Domain | `McpSpecialistAdapter`, `HttpOpenApiInvoker`; `DELIA_MCP_TIMEOUT_SECONDS=15`, `DELIA_OPENAPI_TIMEOUT_SECONDS=15` | YES | REUSE | timeouts de fonte são parâmetro do cálculo de reserva |
| Core AuthZ | live Core AuthZ + Domain authority (backend-first) | YES | REUSE | inalterado |
| CRI/composição | `compose_cri_response` determinístico; composition_mode {cri,deterministic,model} | YES | REUSE | tempo de composição já medido |
| Gateway/proxy | `gateway/nginx.conf` delia-api `proxy_read_timeout 86400`; Cloudflare edge ~100 s (comentário canon. no compose) | YES | REUSE | proxy não é gargalo; idle-time entre bytes é o risco real |
| Client | `interactionClient` AbortSignal, NDJSON consume, `observability` parseado por allowlist | YES | REUSE/EXTEND (Task 3) | estados de progresso já têm vocabulário |

`EXISTING_EQUIVALENT=YES` em todas as responsabilidades; **nenhum novo scheduler/deadline-engine/telemetry/registry** será criado — toda semântica nova é estendida aos owners acima.

## 3. Definições do contrato (proposta)

### 3.1 Unidades

- **Janela semântica por tentativa** — `llm_quota_seconds`: soma do tempo medido de chamadas de modelo (wall-clock real por `ModelInvocation.execute`) dentro de uma tentativa. **NÃO** é tempo por chamada nem tempo de wall-clock do attempt; é quota acumulada de decisão.
- **Janela de wall-clock por tentativa** — `attempt_wall_seconds`: teto de wall-clock de uma tentativa, proteção contra stalls não-modelo.
- **Reserva operacional** — `operational_reserve_seconds`: wall-clock que nenhum estágio semântico pode consumir, reservado à execução operacional + verificação + composição.
- **Envelope global** — `interaction_total_budget_seconds`: teto monotônico end-to-end ancorado em `TurnDeadline.started_at` (início real da interação), proteção última; nunca reinicia entre tentativas.

### 3.2 Regras de débito

1. Um estágio de modelo só inicia se `llm_quota_remaining ≥ MIN_VIABLE_MODEL_STAGE_SECONDS` **e** `wall_remaining > operational_reserve_seconds` (guard B).
2. Timeout de uma chamada de modelo = `min(stage_cap, llm_quota_remaining, wall_remaining − operational_reserve_seconds, per_call_cap_provider)`.
3. Estágio interrompido por timeout: debita do quota o tempo efetivamente decorrido (nunca o cap); tokens de chamadas com falha permanecem ausentes (não fabricados).
4. Replay de checkpoint: estágios comprovadamente concluídos são reproduzidos sem nova chamada — **não debitam quota** (cache/replay não é trabalho novo do modelo).
5. Execução operacional (discovery/AuthZ/invoke/postcondition) e composição **não** debitam o quota semântico; debitam apenas wall-clock global.
6. Quota esgotado em estágio ⇒ `semantic_quota_exhausted` (classificação honesta; nunca rotulado como falha de fonte).

### 3.3 Tentativas governadas

- `max_governed_attempts ≤ 3` (cap de código; valor efetivo por flag).
- Nova tentativa só se: checkpoint existe, `attempts < max_governed_attempts`, `mutating_invoke_started == false`, `cancel_check` livre, e `wall_remaining > operational_reserve + MIN_VIABLE_MODEL_STAGE_SECONDS`.
- Cada nova tentativa recebe **quota semântico próprio de 60 s** e deadline `min(attempt_wall_seconds, envelope_remaining)`.
- Fronteira de tentativa emite `ActivityPhase.CONTINUING` (RUNNING) com `attempt_index` — evento real, não mensagem ornamental.
- READ/DISCOVERY concluído pode ser replayed dentro da mesma interação (mesmo sujeito/args/autorização); PREPARE/ACT/unknown nunca reexecutam — invariante existente preservado.

### 3.4 Encerramento honesto (D)

Terminal quando: tentativas esgotadas, envelope esgotado, reserva impossível de garantir, cancelamento, ou invoke mutante já iniciado. Classificação via `timeout_source` (model/provider/budget/cancelled) + `error_code` (`semantic_quota_exhausted`, `turn_budget_exhausted`, `operational_reserve_guard`, `cancelled`, `model_timeout`). Nunca mascarar como `SOURCE_UNAVAILABLE`.

### 3.5 Progresso user-facing

- `ActivityPhase.CONTINUING` na fronteira de tentativa com `attempt_index` e cópia honesta tipo "Ainda estou analisando…".
- Evento de progresso de estágio longo: quando um estágio de modelo excede ~15 s, emitir no máximo 1 evento `RUNNING` de progresso a cada ≤15 s (mesmo phase corrente, sem avanço falso, sem chain-of-thought) — serve também de **keep-alive** para edges ~100 s idle-timeout.
- Cancelamento: `disconnect.set()`/cancel_check — sinal imediato, in-flight termina bounded, terminal único descartado se desconectado.

## 4. Proposta de valores (TO_DECIDE → recomendação concreta)

| Parâmetro | Atual | Proposta | Fundamento |
|---|---|---|---|
| `DELIA_LLM_ATTEMPT_QUOTA_SECONDS` | — (novo) | **60** | decisão PO; medido como soma de durações reais de chamadas por tentativa |
| `DELIA_ATTEMPT_WALL_SECONDS` | 30 (`GOVERNED_ATTEMPT_MAX_SECONDS`) | **90** | cobre quota 60 + execução operacional (~25) + folga; proteção contra stalls não-modelo |
| `DELIA_MAX_GOVERNED_ATTEMPTS` | 2 (dev) / 1 (prod) | **≤3 dev** / 1 prod | decisão PO ≤3; produção segue OFF até gate R4 |
| `DELIA_OPERATIONAL_RESERVE_SECONDS` | — (novo; precedente CONVERSATIONAL_FALLBACK_RESERVE=8) | **25** | pior caso: timeout de fonte 15s (MCP/OpenAPI configurado) + AuthZ ~1s + pós-condição ~2s + CRI ~1s + descoberta refetch + margem; ≥×1.6 do timeout de fonte |
| `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS` | 60 | **150 (streamed) / 60 (buffered)** | ver §5 |

## 5. END_TO_END_LIMIT_PROPOSAL = 150 s (streamed)

Fundamento aritmético (não "3×60=180"):

- Caminho legítimo típico: A1 esgota quota aos ~60 s → CONTINUING → A2 completa com invoke+composição em ~60–85 s → total ≈ 125–145 s.
- 3 tentativas **completas** (3×60 quota + ops) ≈ 255 s — deliberadamente **não** coberto: o envelope é teto protetor, não orçamento de design. A 3ª tentativa só é elegível quando tentativas anteriores terminaram cedo (erros de estágio terminam em 5–20 s típico); 150 s cobre dois ciclos completos + início significativo do terceiro.
- Limite de transporte: Cloudflare edge ~100 s é *idle-time*, não duração total — NDJSON emite bytes cedo (REQUEST_RECEIVED/CONTEXTUALIZING) e a cadência de keep-alive ≤15 s (§3.5) mantém o stream aberto. Gateway nginx já é `proxy_read_timeout 86400`.
- Fallback não-NDJSON (JSON buffered): mantém envelope **60 s** — cliente buffered não pode aguardar com segurança além do edge; comportamento legado preservado.
- Alternativas consideradas: 90 s (cobre só ~1.3 tentativa — sem continuidade real), 180 s/255 s (cobre o máximo teórico mas converte teto em orçamento de design — rejeitado como convite a UX de espera extrema), 60 s (status quo — sufoca a decisão PO).

## 6. OPERATIONAL_RESERVE_PROPOSAL = 25 s

- Bound real: timeouts de fonte configurados (`DELIA_MCP_TIMEOUT_SECONDS=15`, `DELIA_OPENAPI_TIMEOUT_SECONDS=15`) + AuthZ ~1 s + pós-condição/outcome ~2 s + CRI ~1 s + margem para um re-fetch de catálogo (~4 s).
- Garantias: nenhum estágio semântico inicia com `wall_remaining ≤ reserve + MIN_VIABLE`; se seleção pronta e invoke pendente com `wall_remaining > reserve`, o invoke executa com seu próprio timeout autoritativo (15s fonte) protegido pela reserva.
- Alternativas: reserva dinâmica por capability (timeout declarado por provider — complexidade sem ganho na v1; pode virar refinamento), reserve=8s atual do fallback conversacional (insuficiente para pior caso de fonte), reserve=40s (conservador demais, rouba janela semântica).

## 7. Erros e vocabulário de encerramento (aditivos)

| error_code | Significado | timeout_source |
|---|---|---|
| `semantic_quota_exhausted` | quota LLM 60s da tentativa esgotado | model |
| `model_timeout` | chamada individual excedeu seu timeout | model |
| `operational_reserve_guard` | encerrado para proteger a reserva | budget |
| `turn_budget_exhausted` | envelope global esgotado | budget |
| `provider_timeout` / `provider_error` | falha/timeout da fonte autoritativa | provider |
| `cancelled` | cancelamento/desconexão | cancelled |

Compatibilidade: códigos existentes mantidos; novos são aditivos e mapeiam para o terminal honesto existente (PROCESSING_TIMEOUT/CANCELLED), nunca para `SOURCE_UNAVAILABLE`.

## 8. Invariantes (não negociáveis)

1. Envelope monotônico único ancorado em `TurnDeadline.started_at`; nunca reinicia entre tentativas.
2. `mutating_invoke_started` ⇒ nenhuma nova tentativa. PREPARE/ACT/unknown nunca reexecutados. READ replay só dentro da mesma interação/sujeito/args/autorização.
3. Core AuthZ e Domain authority avaliam cada invoke real; credencial revogada não ganha autoridade (gate R4 segue OPEN).
4. Terminal único por interação; events intermediários ≤64; nenhum chain-of-thought/prompt/payload cru em eventos/observabilidade.
5. Seleção permanece decisão do modelo — zero regex/keyword/alias/branch por provider.
6. `timeout_source` nunca relabela falha de API como timeout de modelo (e vice-versa).
7. Flags: `DELIA_MAX_GOVERNED_ATTEMPTS` cap 3 (prod default 1), `DELIA_LLM_ATTEMPT_QUOTA_SECONDS` default 60, `DELIA_ATTEMPT_WALL_SECONDS` default 90, `DELIA_INTERACTION_TOTAL_BUDGET_SECONDS` proposta 150-streamed/60-buffered, `DELIA_OPERATIONAL_RESERVE_SECONDS` default 25 — dev-only até gates de produção.

## 9. Matriz de testes (para Task 2/4)

| # | Cenário | Esperado |
|---|---|---|
| T1 | estágio lento esgota quota 60s | `semantic_quota_exhausted`, CONTINUING, tentativa 2 inicia |
| T2 | 2 tentativas esgotam quota | 3ª elegível só se wall+reserve ok |
| T3 | wall_remaining ≤ reserve+MIN_VIABLE antes de invoke | terminal `operational_reserve_guard`/`budget`, invoke protegido ou não iniciado |
| T4 | replay de estágio concluído | zero débito de quota, zero nova chamada |
| T5 | PREPARE/ACT concluído + timeout posterior | nenhuma nova tentativa (mutating_invoke_started) |
| T6 | cancel mid-stage | sinal imediato, terminal CANCELLED único, sem nova tentativa |
| T7 | disconnect NDJSON | disconnect.set → sem nova tentativa; terminal descartado; stream fecha |
| T8 | estágio >15s | evento de progresso ≤15s cadência, sem fake progress |
| T9 | timeout de fonte 15s | classificado provider, não model; invoke dentro da reserva |
| T10 | envelope 150s estoura em 3ª tentativa | terminal turn_budget_exhausted honesto |
| T11 | JSON buffered (sem NDJSON) | envelope 60s legado |
| T12 | wire sanitizado | sem prompt/CoT/provider-private/payload em events/observability |
| T13 | Ollama real: modelo lento + API rápida; API lenta + modelo rápido | classificação correta em ambos; outcome autoritativo preservado |
| T14 | tokens de chamadas falhas | ausentes, nunca fabricados; usage agregado = soma provider |

## 10. Alternativas rejeitadas

- Envelope 180 s+ "para caber tudo": converte proteção em orçamento de design e convida UX de espera extrema — rejeitado.
- Quota como timeout por chamada: permitiria N chamadas de 60 s por tentativa — não implementa "60s de trabalho semântico".
- Novo deadline engine separado para quota: duplicaria `TurnDeadline`; rejeitado — quota é débito medido sobre o owner existente.
- Regex/keyword fallback quando seleção é lenta: viola invariante de decisão do modelo — proibido.
- Reserva dinâmica por capability na v1: mais complexidade sem ganho medido; refinamento futuro possível.

## 11. DECISION_LOG

- `CONTRACT=PROPOSED` (este documento) — aguardando aprovação de coordenação.
- `LLM_ATTEMPT_QUOTA=60s` (PO-approved direção); `ATTEMPT_WALL=90s` (proposta); `MAX_ATTEMPTS≤3` dev/prod-flag.
- `END_TO_END_LIMIT_PROPOSAL=150s streamed / 60s buffered` — **TO_DECIDE**.
- `OPERATIONAL_RESERVE_PROPOSAL=25s` — **TO_DECIDE**.
- `REVOCATION_RISK=OPEN`, `REVOCATION_REMEDIATION=DEFERRED_BY_PO`, `PRODUCTION_RETRY=BLOCKED`.
- `CODE_CHANGE=NONE`, `RUNTIME_CHANGE=NONE`, `RELEASE=NONE`.
- Próximo passo (doc 101 Task 2): implementação dev-only do contrato aprovado nos owners existentes, com RED/GREEN determinísticos da matriz §9.
