# Follow-up assertivo — validação live (ROL)

Thread canônica dos prints:

1. `qual o rol desse mês?`
2. `somente da filial 01` → **revise** (`grounded_revise_query`) + `/financial/rol` com `branch=01` + ack
3. `comparar com ano anterior no mesmo periodo` → **YoY** + `start_date` 2025 + `consume_last_action` (sem BOM)
4. `o rol de uma unidade não pode ser igual ao total` → **challenge** sem pedir período / sem tool
5. `rol filail 01 deste mês` → typo → `branch=01`
6. `resuma o resultado` → narrate sem tool
7. `qual o percentual de rol de novos negócios… deste mês?` → KPI `token_and` → `new-business`

## E8.S1 — Verify-final continuidade grounded (2026-08-31)

### Offline

| Gate | Resultado |
|------|-----------|
| `smoke_follow_up_assertivo_gates.py` (FF-FOLLOW-* + FF-CONT-* + continuity) | **PASS** (exit 0) |

### Live send/stream

| Critério | Resultado |
|----------|-----------|
| T0 seed ROL | **PASS** — path `/financial/rol` |
| T1 revise `branch=01` | **PASS** — reexec + `branch=01` + ack (sem `limit`/`granularity` inventados) |
| T1b YoY mesmo período ano anterior | **PASS** — `/financial/rol` + `start_date` 2025 + branch herdada |
| T2 challenge sem missing_date | **PASS** — sem tool |
| T3 typo filail | **PASS** — `/financial/rol` + `branch=01` |
| T4 narrate | **PASS** — sem tool |
| S1 revise via stream | **PASS** — `/financial/rol` + `branch=01` |
| K1 new-business token_and | **PASS** — `/commercial/new-business-rol-pct` |

**Causa raiz dos fails no verify:** (1) match `financeiro`≠`financial` no reexec; (2) `emptyDefault.limit` / schema inventando params → `ok=False` apagava `lastAction`; (3) `text_task.compare` + skip data-interpretation engoliam YoY.

**Ambiente (2026-08-31):** rebuild `minha-delpi-ai-api` + keycloak/gateway; smoke via `http://localhost`.

```bash
./infra/scripts/up-dev-sequential.sh --fase chat --build minha-delpi-ai-api
cd minha-delpi-ai-api && PYTHONPATH=. .venv/bin/python -u scripts/smoke_follow_up_assertivo_live.py
```

## E5.S3 — Verify-final (2026-08-28)

### Offline

| Gate | Resultado |
|------|-----------|
| `smoke_follow_up_assertivo_gates.py` (content, interpretador, merge/reexec, skip-tools, challenge/ack, FF-FOLLOW-*) | **PASS** (exit 0) |
| Fixtures `FF-FOLLOW-REVISE/CHALLENGE/TYPO/NARRATE/CLARIFY/TOPIC-SWITCH/COMPOUND` | **PASS** |

### Live send/stream

| Critério | Resultado |
|----------|-----------|
| T0 seed ROL | **PASS** — path `/financial/rol` |
| T1 revise `branch=01` | **PASS** — reexec + `branch=01` + ack «Consulta filtrada pela filial 01» |
| T2 challenge sem missing_date | **PASS** — sem tool; prosa faithfulness sem pedir período |
| T3 typo filail | **PASS** — `/financial/rol` + `branch=01` |
| T4 narrate | **PASS** — sem tool |
| S1 revise via stream | **PASS** — `/financial/rol` + `branch=01` |

**Ambiente (2026-08-28):** rebuild `minha-delpi-ai-api` + gateway/keycloak/postgres-*/api-delpi; smoke via `http://localhost`.

## Offline (gates)

```bash
cd minha-delpi-ai-api
.venv/bin/python scripts/smoke_follow_up_assertivo_gates.py
```

Cobre content, interpretador, merge/reexec, skip-tools, challenge/ack e fixtures `FF-FOLLOW-*` + `FF-CONT-*`.

## Live

```bash
./infra/scripts/up-dev-sequential.sh --fase core
./infra/scripts/up-dev-sequential.sh --fase chat --build minha-delpi-ai-api

cd minha-delpi-ai-api
PYTHONPATH=. .venv/bin/python -u scripts/smoke_follow_up_assertivo_live.py

# Sem API no ar — só imprime o roteiro:
SMOKE_OFFLINE=1 PYTHONPATH=. .venv/bin/python -u scripts/smoke_follow_up_assertivo_live.py
```

## Asserções

| Turno | Esperado |
|-------|----------|
| T1 revise | path contém `/financial/rol`, `branch=01`, `continuityMode=consume_last_action` |
| T1b YoY | `/financial/rol`, `start_date` com ano anterior, sem path `/structure` |
| T2 challenge | sem tool; prosa **não** pede período |
| T3 typo | `filail 01` → branch `01` |
| T4 narrate | sem tool |
| S1 stream | mesma trajetória do revise |
| K1 | path contém `new-business` |

## Metadata

- script live: `scripts/smoke_follow_up_assertivo_live.py`
- script gates: `scripts/smoke_follow_up_assertivo_gates.py`
- fixtures: `FF-FOLLOW-*` / `FF-CONT-*` em `tests/fixtures/chat_intelligence_regression_cases.py`
- bundle: `app/content/pt-BR/assistant/follow_up_turn.json`
