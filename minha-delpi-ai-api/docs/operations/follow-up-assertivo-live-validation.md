# Follow-up assertivo — validação live (ROL)

Thread canônica dos prints:

1. `qual o rol desse mês?`
2. `somente da filial 01` → **revise** (`grounded_revise_query`) + `/financial/rol` com `branch=01` + ack
3. `o rol de uma unidade não pode ser igual ao total` → **challenge** sem pedir período / sem tool
4. `rol filail 01 deste mês` → typo → `branch=01`
5. `resuma o resultado` → narrate sem tool

## Offline (gates)

```bash
cd minha-delpi-ai-api
.venv/bin/python scripts/smoke_follow_up_assertivo_gates.py
```

Cobre content, interpretador, merge/reexec, skip-tools, challenge/ack e fixtures `FF-FOLLOW-*`.

## Live

```bash
# Stack (quando Docker disponível)
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

## Metadata

- script live: `scripts/smoke_follow_up_assertivo_live.py`
- script gates: `scripts/smoke_follow_up_assertivo_gates.py`
- fixtures: `FF-FOLLOW-*` em `tests/fixtures/chat_intelligence_regression_cases.py`
- bundle: `app/content/pt-BR/assistant/follow_up_turn.json`
