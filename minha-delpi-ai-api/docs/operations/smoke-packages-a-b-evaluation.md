# Smoke / avaliação — pacotes A+B (chat generalista)

Validação offline (2026-08-31) — suite unitária dos gaps G1–G5b.

## Comando

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest \
  tests/unit/domain/services/test_chat_turn_analysis_dispatch_service.py \
  tests/unit/application/services/test_common_chat_operational_guidance.py \
  tests/unit/domain/services/test_chat_department_kpi_intent_service.py \
  tests/unit/domain/services/test_external_action_result_presenter_infer_title.py \
  -q
```

Resultado: **52 passed**.

## Pass/fail (comportamento esperado)

| # | Cenário | Pacote | Offline | Live (manual) |
|---|---------|--------|---------|---------------|
| 1 | «como u posso te chamar?» → identity direct + skip RAG | B | PASS (dispatch unit) | Avaliar no chat: sem notice «dados consultados», latência baixa |
| 2 | «qual o rol filial 01» no comum → guidance agente (não só pedir data) | A | PASS | Confirmar chip ativar agente |
| 3 | Resume «agosto de 2026» com pending missing_date → guidance | A | PASS | Confirmar não «reformular» |
| 4 | «ROL filial 01…» com agente → `/financial/rol` (não by-branch) | A | PASS | Só filial 01 na UI |
| 5 | Título listagem ROL ≠ «Estoque do produto» | A | PASS | Conferir título na bolha |
| 6 | `selected=table` não recomenda barras pelo ideal do shape | A | PASS (recommendation) | Sem chip «barras» indevido |

## Próximo

Pacote C (prompt/insights) após live spot-check dos itens 1–4 quando possível.
