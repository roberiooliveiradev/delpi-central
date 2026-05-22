# Arquitetura — Strategic Indicators

**Última atualização:** 2026-05-21

## Visão geral

```text
Portal (shell)
  └── MFE plugins/strategic-indicators
        └── GET /apps/strategic-indicators-api/strategic-indicators/*
              └── strategic-indicators-api (FastAPI, si_app)
                    ├── Postgres plugins (catálogo, metas, settings, period_scores)
                    ├── TOTVS / SQL Server (medições operacionais)
                    ├── Google Sheets (Transforma+, etc.)
                    └── Portal RH (quando aplicável)
```

A **api-delpi** não monta mais o router `/strategic-indicators`. Toda leitura e admin do módulo passam pelo serviço dedicado.

## Componentes

| Componente | Container (dev) | Responsabilidade |
|------------|-----------------|------------------|
| MFE | `delpi-strategic-indicators` | UI React (Module Federation) |
| API SI | `delpi-strategic-indicators-api` | Snapshots, cálculo IGD/IDD, admin |
| Gateway | `delpi-gateway` | Proxy `/apps/strategic-indicators-api/` e `/apps/strategic-indicators/` |
| Postgres plugins | `delpi-postgres-plugins` | Schema `strategic_indicators` |

## Pacote `si_app`

Código derivado da api-delpi, podado para o grafo alcançável a partir de `main.py`:

- `interface/http/routes/strategic_indicators_routes.py` — rotas
- `composition/strategic_indicators_composer.py` — DI
- `application/services/strategic_indicators/` — snapshots, warm-up, cache
- `infrastructure/providers/strategic_indicators/` — coletores TOTVS/Sheets/RH
- `infrastructure/persistence/plugins/repositories/strategic_indicators/` — Postgres

Modelos de snapshot (`StrategicIndicatorsPeriodSnapshot`, etc.) ficam em `strategic_indicators_snapshot_models.py` para evitar import circular com `period_scores_serialization`.

## Fluxo de leitura (painel)

1. **Catálogo estrutural** (Postgres): departamentos, indicadores, pesos.
2. **Metas resolvidas** por competência (`list_resolved_goals_map`); fallback para meta ativa mais recente se o ano da competência não tiver meta cadastrada (`list_latest_active_goals_map`).
3. **Medições** (TOTVS/Sheets/RH) por período — paralelo seguro por departamento e, quando aplicável, por período com `measurements_port_factory`.
4. **Cálculo** (`StrategicIndicatorsCalculator`) → scores, IGD, classificação.
5. **Cache** in-process (TTL) + opcional **`si_period_scores`** (Postgres) para séries em trends.

## Ausência de medição vs. zero real

O painel precisa distinguir **“não houve dado no período”** de **“o realizado foi zero”** (relevante para indicadores `lower_is_better`, onde `0` pode ser excelência).

| Situação | `value` na medição | Nota | Classificação | Peso no IGD / departamento |
|----------|-------------------|------|---------------|----------------------------|
| Sem linha/dado no período | `null` | `null` | **Sem dados preenchidos** | Não entra na média ponderada |
| Zero real (ex.: 0% na planilha) | `0.0` | calculada | faixa normal (ex.: Excelência se ≤ meta) | Entra normalmente |
| Indicador no catálogo sem coleta | `null` (sem medição) | `null` | **Sem dados preenchidos** | Não entra na média |

Regras na API de leitura:

- Campo **`has_value`**: `true` quando existe realizado numérico para o recorte.
- **`realized`**: mapa unidade → valor; chaves podem ter `null` (filial sem dado naquele indicador).
- Indicadores **sempre listados** no departamento quando estão no catálogo resolvido, mesmo sem medição.

Implementação principal:

- `StrategicIndicatorsCalculator` — `MISSING_VALUE_CLASSIFICATION`, `MISSING_GOAL_CLASSIFICATION`, `_build_missing_indicator_value`, `_build_indicator_without_goal_for_view`, média de departamento só com indicadores pontuados.
- Financeiro (Sheets) — `_average_sheet_metric` retorna `null` se não houver linhas no intervalo; **não** converte ausência em `0` (api-delpi espelha a mesma regra).
- MFE — `formatIndicatorValue` / `formatIndicatorScore` exibem **Sem dados preenchidos** quando o valor ou a nota são `null`; rótulos da visão em [MFE.md](./MFE.md).

**Produção:** medições sem valor na fonte permanecem `null` no provider (não são convertidas para `0.0` antes do cálculo).

**Pendente de alinhamento nas fontes:** Qualidade (PPM) usa `default_value=0.0` em alguns indicadores. Ver [DATA_SOURCES.md](./DATA_SOURCES.md).

## Filtro por filial (`branch`) vs. escopo do indicador

Documentação completa: [INDICATOR_GOALS_SCOPE.md](./INDICATOR_GOALS_SCOPE.md).

Resumo do `StrategicIndicatorsCalculator` + catálogo resolvido:

1. **Meta:** com `branch` na query, só entra meta com `goal_scope_branch` igual à filial; não há fallback para `''`.
2. **Realizado:** chave `01`/`02` em `unit_values` só pontua por unidade se houver `branch_goals` ou meta resolvida para aquela filial; caso contrário permanece `measurement.value` (consolidado).
3. **Listagem:** indicador sem meta na filial ainda aparece no painel com `goal_label` *Sem meta para filial XX* e nota `null`.

Helpers compartilhados: `si_app/shared/goal_scope.py` (`indicator_uses_branch_unit_measurement`, `uses_strict_branch_goal_resolution`).

## Metas em séries históricas

O seed padrão (V009) cadastra metas para o ano corrente (ex.: 2026). Trends com `months=6` podem incluir competências de 2025.

| Comportamento | Descrição |
|---------------|-----------|
| Meta do `goal_year` da competência | Preferência quando existe |
| Fallback | Meta ativa mais recente do indicador (log `si_goal_year_fallback`) |
| Sem meta alguma (visão consolidado) | Indicador omitido do catálogo resolvido (log `si_goal_missing`) |
| Sem meta na filial (visão `branch=01/02`) | Indicador listado com `has_resolved_goal=false` e rótulo *Sem meta para filial XX* |

Recomendação de negócio: duplicar metas para anos anteriores via admin (`duplicate-year`) em vez de depender só do fallback.

## Cache e invalidação

| Camada | Onde | TTL / notas |
|--------|------|-------------|
| Medições / catálogo in-process | `snapshot_shared_cache.py` | `SI_SNAPSHOT_CACHE_TTL_SECONDS` (default 600s) |
| Coletores (Transforma+, LMP, etc.) | providers | TTL próprio por fonte |
| HTTP leitura | `Cache-Control`, `ETag` | 300s (`si_read_route_support`) |
| `period_scores` | Postgres V010 | Persiste snapshot calculado por competência/escopo |

Mutações em **settings**, **metas** ou estrutura admin chamam `invalidate_strategic_indicators_snapshot_cache()` (limpa cache in-process e apaga `period_scores` + `calculation_snapshots` no Postgres).

## Warm-up

Com `SI_WARMUP_ON_STARTUP=true`, uma thread em background após o boot:

- Executive-summary (competência atual)
- Trends (`SI_WARMUP_TRENDS_MONTHS`, default 6)

Script manual: `scripts/warmup_si_snapshots.py`.

## Paralelismo seguro

```text
SEGURO:
  - 7 departamentos em paralelo dentro de um período
  - N períodos em paralelo COM measurements_port_factory() (instância por thread)

PROIBIDO:
  - N períodos compartilhando o mesmo RealStrategicIndicatorsMeasurementsProvider
```

Detalhes e checklist: [PERFORMANCE_IMPLEMENTATION.md](./PERFORMANCE_IMPLEMENTATION.md).

## Migrations

Runner próprio: `scripts/run_migrations.py`. SQL em `migrations/V001`–`V010`.  
**Não** adicionar novas versões em `api-delpi/migrations/plugins/strategic-indicators/` (apenas referência histórica).
