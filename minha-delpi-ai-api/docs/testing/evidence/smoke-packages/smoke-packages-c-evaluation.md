# Smoke / avaliação — pacote C

Validação offline (2026-08-31).

## Suite

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest tests/unit/domain/services/test_package_c_intelligence.py -q
```

## Pass/fail

| # | Critério | Offline |
|---|----------|---------|
| 1 | Prompt sessão com focus + lastAction + limite chat comum | PASS |
| 2 | Assertividade do turno anterior vira diretiva | PASS |
| 3 | Commentary/dataAnswer path para KPI sem rows (sem crash) | PASS |
| 4 | Policy síntese com continuidade (operational-synthesis.md) | PASS (revisão) |

## Live (manual)

Pedido operacional com agente: conferir adminDebug com bloco de contexto/diretivas; `dataAnswer` presente; prosa não inventa formato divergente do `presentationDecision`.
