# Banco de dados — schema `strategic_indicators`

Banco: **postgres-plugins** (`PLUGINS_DB_*`).  
Migrations: `strategic-indicators-api/migrations/` (runner próprio).

## Versões

| Versão | Objeto principal |
|--------|------------------|
| V001 | Schema `strategic_indicators`, extensões |
| V002 | `module_settings` |
| V003 | `settings_audit` |
| V004 | `departments` |
| V005 | `department_indicators` |
| V006 | `indicator_goals`, `indicator_goal_monthly_targets` |
| V007 | `settings_change_requests` |
| V008 | `settings_change_request_comments` |
| V009 | Seed estrutura admin + metas ano corrente |
| V010 | `period_scores` (indicadores materializados) |
| V011 | `refresh_state` (estado do job de refresh) |
| V012 | `calculation_snapshots` (insumos materializados do cálculo) |

Detalhes dos arquivos: [../migrations/README.md](../migrations/README.md).

## Tabelas principais

### Estrutura e governança

- **`departments`** — departamentos do painel (id, nome, peso, ativo)
- **`department_indicators`** — indicadores ligados ao departamento (peso, source_key, formatação)
- **`module_settings`** — JSON de parâmetros e governança
- **`settings_audit`** — trilha de alterações em settings
- **`settings_change_requests`** / **`settings_change_request_comments`** — fluxo de solicitação de mudança

### Metas

- **`indicator_goals`** — metas versionadas por `indicator_id` + `goal_year`
- **`indicator_goal_monthly_targets`** — metas mensais quando `goal_mode` exige

Resolução em runtime: `list_resolved_goals_map` (ano da competência) com fallback `list_latest_active_goals_map` para séries históricas.

### Performance (V010–V011)

- **`period_scores`** — snapshot serializado por `(competence, scope_branch, scope_department_id)`

Colunas relevantes: `igd`, `igd_exact`, `classification`, `calculated_departments` (JSONB), `calculated_indicators` (JSONB), `measurement_errors`, `computed_at`.

Rotas de leitura (`executive-summary`, `departments`, `indicators`, `trends`) consultam esta tabela quando o período é mês calendário padrão e o registro existe. O job `SI_PERIOD_SCORES_REFRESH_*` recalcula e grava a cada 5 minutos (padrão).

- **`refresh_state`** — `last_started_at`, `last_completed_at`, `last_duration_ms`, `last_periods_upserted`, `last_error` do último ciclo de materialização.

### Insumos do cálculo (V012)

- **`calculation_snapshots`** — snapshot dos **inputs** usados pelo `StrategicIndicatorsCalculator`, por `(competence, scope_branch, scope_department_id)`:

| Coluna JSONB | Conteúdo |
|--------------|----------|
| `departments_catalog` | Departamentos ativos, pesos, modo de agregação |
| `indicators_catalog` | Indicadores com metas resolvidas para a competência |
| `goals_by_department` | Resumos executivos por departamento |
| `measurements` | Realizados coletados (TOTVS, Sheets, RH) |
| `measurement_errors` | Erros de coleta por indicador/fonte |

Atualizado pelo mesmo job de `period_scores` (padrão: a cada 5 min, `SI_PERIOD_SCORES_REFRESH_INTERVAL_SECONDS=300`). Flag: `SI_CALCULATION_SNAPSHOTS_ENABLED` (default `true`).

Diferença em relação a **`period_scores`**: `period_scores` guarda o **resultado** (IGD, scores, classificação); `calculation_snapshots` guarda o que entrou no cálculo.

## Comandos

```bash
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
python strategic-indicators-api/scripts/run_migrations.py status
python strategic-indicators-api/scripts/run_migrations.py up
```

Container:

```bash
docker exec delpi-strategic-indicators-api python3 scripts/run_migrations.py up
```

Startup: `SI_RUN_MIGRATIONS_ON_STARTUP=true` (dev Compose).

## Reset (somente dev)

```bash
python strategic-indicators-api/scripts/run_migrations.py reset
```

Remove o schema inteiro.

## Relação com api-delpi

**Não** executar migrations SI via `api-delpi/scripts/run_plugins_migrations.py`. O diretório `api-delpi/migrations/plugins/strategic-indicators/` foi removido do monorepo.
