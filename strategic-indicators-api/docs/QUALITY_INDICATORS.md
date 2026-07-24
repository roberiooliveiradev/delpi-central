# Departamento Qualidade — metas por unidade

**Migration:** `V018__quality_branch_goals_2026.sql`

Indicadores permanecem `scope_type = consolidated` (medição consolidada no painel), com **metas distintas por filial** (`goal_scope_branch` `01` e `02`), exceto indicadores cadastrados como `per_unit` (ex.: plugues e custo de refugo × ROL).

## Perdas — custo × ROL (admin + código)

| `indicator_id` | `source_key` | Fonte HTTP | Escopo típico |
|----------------|--------------|------------|---------------|
| `quality-scrap-cost-pct` | `quality_scrap_cost_pct` | `GET /quality/scrap-cost-pct` | Por unidade |
| `quality-rework-cost-pct` | `quality_rework_cost_pct` | `GET /quality/rework-cost-pct` | Consolidado |

Cálculo: mesmo das rotas `/refugos/scrap_cost_pct` e `/retrabalhos/rework_cost_pct` (custo / ROL com IPI × 100). Snapshot SI preenche `unit_values` 01/02 e consolidado sem `branch`.

## Metas 2026 (após V018)

| Indicador | Filial 01 | Filial 02 |
|-----------|-----------|-----------|
| PPM Interno | 1.400 PPM | 2.300 PPM |
| PPM Externo | 1.100 PPM | 290 PPM |
| Ideias Kaizen | 8 ideias/mês | 8 ideias/mês |
| Nota 5S | 80% | 80% |
| Ganhos financeiros Kaizen | Modo **Curva** (12 pontos): R$ 4.500 (jan–jun), R$ 9.000 (jul–dez) | Modo **Padrão**: R$ 4.500/mês |

**Ganhos financeiros (cálculo):** a `api-delpi` deriva `daily_savings` de cada kaizen a partir da planilha Google Sheets (`segundos_por_ocorrencia × ocorrencias_por_dia / 3600 × custo_hora`). Para cada kaizen com status *implantado*, o SI soma `daily_savings × dias ativos` no mês da competência. A data de implantação define o início da contagem; kaizens implantados em meses anteriores continuam gerando ganho nos dias do mês filtrado (não exige nova implantação no mês). O indicador *Ideias Kaizen* continua contando apenas implantações cuja data cai no período.

> **Evolução (cadastro Postgres):** quando `GET /quality/kaizens/summary` migrar para PostgreSQL (Fase 6), o cálculo usará **revisões temporais** (`quality.kaizen_revisions`) para preservar status e economia vigentes em cada mês — ver [ESPECIFICACAO-REVISOES.md](../../docs/12-roadmap-e-volucao/cadastro-kaizen/ESPECIFICACAO-REVISOES.md).

Detalhes da planilha e fórmulas: `api-delpi/docs/api/06-modulos-departamentais.md` (§ `GET /quality/kaizens/summary`).

Metas consolidadas (`goal_scope_branch = ''`) do seed V009 são **inativadas**; a leitura por filial usa `branch=01` ou `02` na API (sem fallback para meta consolidada na query).

Na UI, filtro por filial exibe rótulo **Filial 01/02** — [MFE.md](./MFE.md).

Na visão **Consolidado** (`aggregation_mode = average_of_units`):

- Nota de cada indicador = média das notas das filiais `01` e `02`.
- Meta, valor atual e gap exibem `01: … | 02: …`.
- **Nota IDD da Qualidade** = média entre o IDD da filial `01` e o IDD da filial `02`.

## Deploy

```bash
docker exec delpi-strategic-indicators-api python3 scripts/run_migrations.py up
docker exec delpi-strategic-indicators-api python3 -u scripts/refresh_period_scores.py
```

Após incluir scrap/rework no snapshot (sem migration nova), basta o **refresh** de `period_scores` para o cache refletir os novos `indicator_id`.

Produção (metas por filial 01/02 em indicadores `per_unit`): ver migration `V021__per_unit_branch_goals.sql` e [INDICATOR_GOALS_SCOPE.md](./INDICATOR_GOALS_SCOPE.md).
