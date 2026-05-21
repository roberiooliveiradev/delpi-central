# Fontes de dados — medições do painel

**Última atualização:** 2026-05-21

O painel SI **não** armazena valores realizados no Postgres (exceto cache `period_scores`). Os realizados vêm de fontes operacionais por `source_key` / departamento.

## Ausência vs. zero nas fontes

| Comportamento esperado | Quem implementa |
|------------------------|-----------------|
| Sem registro no período → medição com `value: null` | Coletor / `FinancialMetricsSnapshotService` |
| Registro com 0 na fonte → `value: 0.0` | Coletor (zero é realizado válido) |
| UI e API expõem **Sem dados preenchidos** | `StrategicIndicatorsCalculator` + MFE |

| Departamento | Status (2026-05) |
|--------------|------------------|
| Financeiro (Sheets EBITDA / custos fixos) | Alinhado — `null` sem linhas no período |
| RH | Parcial — satisfação/PDI só entram no snapshot se existirem; demais métricas usam `null` na resolução |
| Comercial | Repassa `null` do snapshot quando aplicável |
| Qualidade | PPM ainda pode usar `default_value=0.0` quando falta dado |
| Produção | `_build_measurement` ainda converte ausência em `0.0` |
| Suprimentos / Engenharia | Depende do snapshot upstream |

## Resumo por departamento

| Departamento | Fontes principais | Coletor (si_app) |
|--------------|-------------------|------------------|
| Financeiro | TOTVS (ROL), Google Sheets (EBITDA e custo fixo já em %; filial vazia = consolidado; filial preenchida = por unidade), recebíveis (PMR). Sem linhas no período → `ebitda_over_rol_pct` / `fixed_cost_over_rol_pct` / `pmr_days` = `null` (não `0`). | `financial_indicators_snapshot_provider` |
| Comercial | TOTVS: ROL matriz/filial, taxa fechamento, % ROL novos clientes (provisório para *novos negócios*). **Pendente:** OTD pedidos venda, % ROL novos negócios (curva). Catálogo V015. | `commercial_indicators_snapshot_provider` |
| Produção | TOTVS (OTD, OEE), Sheets (MO, custo, depreciação) | `production_indicators_snapshot_provider` |
| Qualidade | TOTVS (PPM, NC), Sheets (Kaizen, 5S) | `quality_indicators_snapshot_provider` |
| Suprimentos | TOTVS (CPV, giro, OTD, estoque) | `supplies_indicators_snapshot_provider` |
| Engenharia | TOTVS (LMP), Transforma+ (Sheets) | `engineering_indicators_snapshot_provider` |
| RH | Portal RH (Postgres) | `hr_indicators_snapshot_provider` |

Composição: `real_indicator_measurements_provider.py` — paraleliza departamentos na visão consolidada.

## TOTVS (SQL Server)

- Variáveis: `DB_*` no container (mapeadas de `TOTVS_DB_*` no Compose)
- Pool: `TOTVS_POOL_ENABLED`, `TOTVS_POOL_MAX_SIZE`
- Otimizações SI: produção consolidada (uma passagem), financial `list_rol_by_branch`

## Google Sheets

Variáveis em `si_app/config.py` (prefixos `QUALITY_*`, `TRANSFORMA_MAIS_*`, `FINANCIAL_*`, `PRODUCTION_*`, etc.).

Transforma+: cache TTL de `load_raw_data` no coletor de engenharia.

## Portal RH

`PORTAL_RH_DB_*` — métricas de absenteísmo, turnover, treinamento, PDI.

## Dados diretos na api-delpi

Consultas pontuais (ex.: **ROL** bruto) permanecem em:

```text
GET /apps/api-delpi/finacial/financial/rol
```

Essas rotas **não** substituem o painel SI; servem integrações e outros módulos.

## Metas e catálogo

Sempre **Postgres** (`strategic_indicators.*`). Alterações em admin invalidam cache in-process (`invalidate_strategic_indicators_snapshot_cache`).
