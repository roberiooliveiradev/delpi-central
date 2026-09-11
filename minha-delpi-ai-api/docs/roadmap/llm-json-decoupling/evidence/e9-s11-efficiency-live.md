# E9.S11 — Efficiency live (openai_compatible / Kimi)

**Status:** `ATENDIDO` (revalidado 2026-09-11 — tokens metadata)  
**Onda:** H (plano 09)  
**Runner:** `scripts/run_e9_s11_efficiency_live.py`  
**Evidência:** `evidence/e9-s11-efficiency-live-v1/results.json`

## Veredito

```text
STACK = openai_compatible (Kimi/OpenRouter)
OLLAMA_FALLBACK = ABSENT
TRIALS_OK = ≥3
P50_WALL / P95_WALL = medidos
TOKENS_IN_METADATA = PASS (totalTokens ← *TokensEstimated + aliases)
DECISION = PASS
```

## Correção 2026-09-11

Harness lia `promptTokens`/`totalTokens` enquanto o runtime publica `*TokensEstimated`.  
Fix: extractor aceita Estimated + aliases canônicos em `ChatAdminDebugService` (`promptTokens`/`completionTokens`/`totalTokens`).

## Próximo

Débito tokens fechado. Release já com `globalReleasePass=true`.
