# Follow-up assertivo — validação live (ROL)

Thread canônica dos prints:

1. `qual o rol desse mês?`
2. `somente da filial 01` → **revise** (`grounded_revise_query`) + `/financial/rol` com `branch=01` + ack
3. `o rol de uma unidade não pode ser igual ao total` → **challenge** sem pedir período / sem tool
4. `rol filail 01 deste mês` → typo → `branch=01`
5. `resuma o resultado` → narrate sem tool

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

```bash
./infra/scripts/up-dev-sequential.sh --fase core
./infra/scripts/up-dev-sequential.sh --fase chat --build minha-delpi-ai-api
# se preciso: gateway, keycloak, postgres-plugins, postgres-core, api-delpi
cd minha-delpi-ai-api && PYTHONPATH=. .venv/bin/python -u scripts/smoke_follow_up_assertivo_live.py
```

## Offline (gates)

```bash
cd minha-delpi-ai-api
.venv/bin/python scripts/smoke_follow_up_assertivo_gates.py
```

Cobre content, interpretador, merge/reexec, skip-tools, challenge/ack e fixtures `FF-FOLLOW-*`.

## Live

```bash
./infra/scripts/up-dev-sequential.sh --fase core
./infra/scripts/up-dev-sequential.sh --fase chat --build minha-delpi-ai-api

cd minha-delpi-ai-api
PYTHONPATH=. .venv/bin/python -u scripts/smoke_follow_up_assertivo_live.py

# Sem API no ar — só imprime o roteiro:
SMOKE_OFFLINE=1 PYTHONPATH=. .venv/bin/python -u scripts/smoke_follow_up_assertivo_live.py
```

O live também abre uma segunda sessão e reexecuta o revise via `stream`.

## Asserções

| Turno | Esperado |
|-------|----------|
| T1 revise | path contém `/financial/rol`, `branch=01`, não cai em «Com base no último resultado» sem tool |
| T2 challenge | sem tool; prosa **não** pede período |
| T3 typo | `filail 01` → branch `01` |
| T4 narrate | sem tool |
| S1 stream | mesma trajetória do revise |

## Commits desta rodada

- E1.S1 — Vocabulário follow-up + typos filial
- E2.S1 — Interpretador revise/challenge/clarify/switch
- E3.S1 — Reexec lastAction + merge imutável
- E3.S2 — Skip-tools / turn_analysis / missing_date
- E4.S1 — Challenge faithfulness + ack pós-revise
- E5.S1 — Fixtures FF-FOLLOW-*
- E5.S2 — Smoke + doc ops

## Metadata

- script live: `scripts/smoke_follow_up_assertivo_live.py`
- script gates: `scripts/smoke_follow_up_assertivo_gates.py`
- fixtures: `FF-FOLLOW-*` em `tests/fixtures/chat_intelligence_regression_cases.py`
- bundle: `app/content/pt-BR/assistant/follow_up_turn.json`
