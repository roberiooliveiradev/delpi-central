# E9.S11 — Efficiency live (openai_compatible / Kimi)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** H (plano 09)  
**Runner:** `scripts/run_e9_s11_efficiency_live.py`  
**Evidência:** `evidence/e9-s11-efficiency-live-v1/results.json`

## Veredito

```text
STACK = openai_compatible (Kimi/OpenRouter)
OLLAMA_FALLBACK = ABSENT
TRIALS_OK = 5/5
P50_WALL_MS = 14708
P95_WALL_MS ≈ 19073
TOKENS_IN_METADATA = PENDING (campo ausente no adminDebug deste runtime)
DECISION = PASS
DELETE_AUTHORIZED = false (demais gates ainda PASS_OFFLINE)
GLOBAL_RELEASE_PASS = false (matriz ainda exige PASS pleno nas demais células / política)
```

## Amostra

| Trial | Probe | Wall ms | Tools | Provider |
|-------|-------|--------:|------:|----------|
| 1 | smalltalk | 16291 | 0 | openai_compatible |
| 2 | stock | 12960 | 1 | openai_compatible |
| 3 | stock_sibling | 12327 | 1 | openai_compatible |
| 4 | smalltalk | 19769 | 0 | openai_compatible |
| 5 | stock | 14708 | 1 | openai_compatible |

## Commit LLM

Default/fallback Ollama já removido em `2b8367b72` (já no remote). Este passo **não** mistura diffs de my-requests/production-pulse.

## Próximo

Reavaliar DELETE só quando gates required estiverem em `PASS` / `PASS_OFFLINE_AND_LIVE` / `APPROVED` (hoje vários ainda `PASS_OFFLINE`).
