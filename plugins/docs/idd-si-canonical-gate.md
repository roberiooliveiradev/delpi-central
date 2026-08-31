# Gate — Nota IDD canônica via Strategic Indicators

## Inventário (obrigatório wired)

| Plugin | `department_id` | Fonte Nota IDD |
|--------|-----------------|----------------|
| `dashboard-quality` | `quality` | `indicators[].score` |
| `dashboard-commercial` | `commercial` | idem + ROL via `iddScoreLabel` |
| `commercial` (Portal) | `commercial` | idem |
| `dashboard-production` | `production` | idem |
| `dashboard-supplies` | `supplies` | idem |
| `dashboard-financial` | `financial` | idem |
| `dashboard-engineering` | `engineering` | idem |
| `dashboard-hr` | `hr` | idem |

## Checklist PR

1. `python3 plugins/scripts/check_idd_si_canonical_gate.py` → OK
2. Cards / export usam `pickSiIddScoreLabel` / `iddScoreLabel` do SI
3. Sem `calculateIndicatorIddScore` / `resolveConsolidatedIddScoreLabel` nos MFEs do inventário (só no kit `plugin-ui` / testes de fórmula)
4. Build dos MFEs alterados verde

## Comando

```bash
python3 plugins/scripts/check_idd_si_canonical_gate.py
```

## Verify-final (E3.S1) — evidência

Após refresh `period_scores` com `consolidated,01,02` e api-delpi saudável:

| Caso | Resultado | Evidência |
|------|-----------|-----------|
| Qualidade SC 2026-07 card×badge mesmo payload SI | PASS | badge=5,71 · `quality-ppm-external`=9,33 |
| Qualidade SC 2026-08 card×badge mesmo payload SI | PASS | badge=5,91 · `quality-ppm-external`=10,0 |
| Smoke Engenharia ago SC | PASS | badge=6,0 · 2 indicadores |
| Smoke Comercial ago SC | PASS | badge=8,25 · 6 indicadores |
| pytest max-age | PASS | 4 passed |
| Gate dual-path | PASS | script OK |

Jul SC (5,71) vs ago SC (5,91): ambos vêm do SI; sem dual-compute local nos cards. Ops: `SI_PERIOD_SCORES_REFRESH_BRANCHES=consolidated,01,02` e `SI_PERIOD_SCORES_MAX_AGE_SECONDS=3600` no compose/env.
