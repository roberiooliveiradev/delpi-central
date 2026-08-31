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
