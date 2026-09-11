# J-R1 — R8 threshold canônico

**Status:** COMPLETE_GATE = PASS (`R8_THRESHOLD_CANONICAL`)  
**HEAD_BEFORE:** `446e9a692306911cf9269c9fed22c66e69a8ad37`  
**Bloqueio:** A11-01  
**Authority:** `docs/testing/chat-ai-flow-families.md` §12

## Problema

`run_e9_s11_efficiency_live.py` marcava PASS quando P50/P95 existiam + tokens + provider ≠ ollama, **sem** comparar aos alvos:

| Modo | Alvo total |
|------|------------|
| Rápida / fast | ≤ 3 s |
| Normal | ≤ 5 s |
| Pensador / thinker | ≤ 15 s |

Candidate histórico `782a4972…` registrou P50≈41.5 s / P95≈50.7 s em `normal` e ainda assim `decision=PASS`.

## Correção

Owner canônico: `ChatR8LatencyThresholdService`

```text
responseMode → threshold_ms
→ exige p50 e p95
→ FAIL se p50 > threshold OU p95 > threshold
→ FAIL se mode/threshold inválido
→ INCONCLUSIVE se métrica ausente (nunca PASS)
→ registra provider / tokens / llmCalls / toolCalls
```

Runner live consome o mesmo serviço (única fonte de decisão R8).

## Testes

| Caso | Esperado |
|---|---|
| normal p50/p95 ≤ 5 s | PASS |
| sibling fast/thinker dentro do alvo | PASS |
| histórico 41522/50708 ms normal | FAIL |
| p95 só acima do limite | FAIL |
| mode inválido / vazio | FAIL |
| p95 ausente | INCONCLUSIVE |

```bash
PYTHONPATH=. python3 -m unittest tests.unit.domain.services.test_j_r1_r8_latency_threshold -v
```

## Reavaliação do evidence histórico

```text
stored decision (stale) = PASS
canonical re-eval     = FAIL  (latência acima do threshold canônico)
```

O PASS antigo **não** é aceite vigente. Live R8 no candidate antigo deve falhar até a latência real caber no SLO — **não** se aumenta o threshold.

## Gate

```text
R8_THRESHOLD_CANONICAL = PASS
COMPLETE_GATE (J-R1) = PASS
NEXT = J-R2
```
