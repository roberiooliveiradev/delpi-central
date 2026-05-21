# Departamento Qualidade — metas por unidade

**Migration:** `V018__quality_branch_goals_2026.sql`

Indicadores permanecem `scope_type = consolidated` (medição consolidada no painel), com **metas distintas por filial** (`goal_scope_branch` `01` e `02`).

## Metas 2026 (após V018)

| Indicador | Filial 01 | Filial 02 |
|-----------|-----------|-----------|
| PPM Interno | 1.400 PPM | 2.300 PPM |
| PPM Externo | 1.100 PPM | 290 PPM |
| Ideias Kaizen | 8 ideias/mês | 8 ideias/mês |
| Nota 5S | 80% | 80% |
| Ganhos financeiros Kaizen | Curva mensal: R$ 4.500 (jan–jun), R$ 9.000 (jul–dez) | R$ 4.500/mês (padrão) |

Metas consolidadas (`goal_scope_branch = ''`) do seed V009 são **inativadas**; a leitura por filial usa `branch=01` ou `02` na API.

Na visão **Consolidado** (`aggregation_mode = average_of_units`):

- Nota de cada indicador = média das notas das filiais 01 e 02.
- **Nota IDD da Qualidade** = média entre o IDD da filial 01 e o IDD da filial 02.

## Deploy

```bash
docker exec delpi-strategic-indicators-api python3 scripts/run_migrations.py up
docker exec delpi-strategic-indicators-api python3 -u scripts/refresh_period_scores.py
```
