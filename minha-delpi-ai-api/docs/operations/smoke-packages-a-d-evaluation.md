# Smoke / avaliação unificada — pacotes A–D

Validação offline (2026-08-31).

## Suite

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest \
  tests/unit/domain/services/test_chat_turn_analysis_dispatch_service.py \
  tests/unit/application/services/test_common_chat_operational_guidance.py \
  tests/unit/domain/services/test_chat_department_kpi_intent_service.py \
  tests/unit/domain/services/test_external_action_result_presenter_infer_title.py \
  tests/unit/domain/services/test_package_c_intelligence.py \
  tests/unit/domain/services/test_chat_grounded_capability_planning_service.py \
  tests/unit/domain/services/test_chat_presentation_recommendation_service.py \
  -q
```

## Pass/fail

| # | Critério | Pacote | Offline |
|---|----------|--------|---------|
| 1 | Typo identity → dispatch direct + skip RAG | B | PASS |
| 2 | Comum operacional → guidance (não missing_date) | A | PASS |
| 3 | Resume período → guidance via mensagem composta | A | PASS |
| 4 | ROL filial → `/financial/rol` | A | PASS |
| 5 | Título ROL ≠ estoque; table sem chip barras indevido | A | PASS |
| 6 | Contexto sessão + assertividade + commentary KPI | C | PASS |
| 7 | Dual previous_period + filial×filial no planner | D | PASS |
| 8 | YoY dual (regressão) | herança | PASS |

## Live (manual)

Spot-check no chat: «como u posso te chamar?», ROL comum, ROL com agente filial 01, «comparar com período anterior», «comparar filial 01 com 02».
