# Operação, logs e troubleshooting

## Logs

Logger principal: `strategic_indicators.*` (nível via `LOG_LEVEL`).

### HTTP (rotas de leitura)

Via `run_logged_read_route`:

```text
executive-summary ok competence=2026-05 ... duration_ms=10252
trends failed competence=2026-05 months=6 duration_ms=4
```

### Snapshot

| Log | Significado |
|-----|-------------|
| `si_measurements_loaded` | Medições TOTVS/Sheets/RH por competência |
| `si_snapshot_comparative` | Comparativo 2 períodos (tempos por fase) |
| `si_series_snapshot` | Série N meses (trends/presentation) |
| `si_goal_year_fallback` | Meta de outro ano usada em competência histórica |
| `si_goal_missing` | Indicador sem meta — omitido do catálogo |
| `si_warmup_start` / `si_warmup_failed` | Warm-up no boot |

Arquivo dev (se configurado): `strategic-indicators-api/logs/api_YYYYMMDD.log`.

## Warm-up

Automático: `SI_WARMUP_ON_STARTUP=true` — aquece executive + trends (`SI_WARMUP_TRENDS_MONTHS`).

Manual:

```bash
docker exec delpi-strategic-indicators-api python3 scripts/warmup_si_snapshots.py
```

## Benchmark

```bash
python strategic-indicators-api/scripts/bench_si_routes.py --competence 2026-05
```

Baseline documentado: executive ~19s → ~10s após otimizações — ver [PERFORMANCE_IMPLEMENTATION.md](./PERFORMANCE_IMPLEMENTATION.md).

## Health checks

| URL | Esperado |
|-----|----------|
| `GET /apps/strategic-indicators-api/health` | `{"status":"online"}` |
| `GET /apps/strategic-indicators-api/strategic-indicators/health` | Módulo SI |

## Problemas comuns

### Erro padronizado no MFE

Todas as páginas analíticas (executivo, departamentos, indicadores, tendências, alertas, apresentação) exibem o mesmo card:

- **Onde** / **Recorte** (rota, competência, filial)
- **Possíveis causas** e **O que fazer**
- **Detalhe técnico** (mensagem da API, colapsável)

Componente: `StrategicIndicatorsPageError` → `StrategicIndicatorsErrorState`. Parse centralizado em `strategicIndicatorsError.ts` e `buildStrategicIndicatorsApiError` (ver [MFE.md](./MFE.md)).

### 500 — `Falha ao executar fetch_all no banco de plugins`

**Sintoma:** card de erro na UI; detalhe técnico com essa mensagem (às vezes só na visão **por filial**, com consolidado aparentemente normal).

**Causas frequentes:**

| Causa | Log / detalhe técnico | Ação |
|-------|----------------------|------|
| Migrations pendentes | `column ... goal_scope_branch does not exist` | `run_migrations.py up` até V020 |
| Bug ordem de parâmetros SQL (metas por filial) | `operator does not exist: character varying = date` | Deploy da API com fix `list_resolved_goals_map` (`cbc91c5`+) |
| Schema inexistente | `relation "strategic_indicators...." does not exist` | Migrations V001+ |

Em produção, `SI_RUN_MIGRATIONS_ON_STARTUP` costuma estar **desligado** (`false` no `docker-compose.yml`). As migrations precisam rodar **uma vez** manualmente após deploy.

**Diagnóstico no servidor:**

```bash
# Erro SQL real (traceback)
docker logs delpi-strategic-indicators-api 2>&1 | tail -200 | grep -E "fetch_all failed|does not exist|character varying = date|PluginsRepository|ERROR"

# Reproduzir resolução de catálogo por filial
docker exec delpi-strategic-indicators-api python3 -c "
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_resolved_indicators_catalog_repository import PostgresStrategicIndicatorsResolvedIndicatorsCatalogRepository
n = len(PostgresStrategicIndicatorsResolvedIndicatorsCatalogRepository().list_resolved_indicators_catalog(competence='2026-04', branch='01'))
print('OK', n)
"

# Health
curl -s http://localhost/apps/strategic-indicators-api/strategic-indicators/health | jq

# Migrations (credenciais: carregar .env do host ou usar variáveis do compose)
docker exec delpi-strategic-indicators-api python3 scripts/run_migrations.py status
docker exec delpi-strategic-indicators-api python3 scripts/run_migrations.py up
```

**Correção:** após `up` e deploy da API corrigida:

```bash
docker compose -f infra/docker-compose.yml restart strategic-indicators-api
docker exec delpi-strategic-indicators-api python3 -u scripts/refresh_period_scores.py
```

Confirme `period_scores` para a competência (via container da API, sem depender de `.env` no shell):

```bash
docker exec delpi-strategic-indicators-api python3 -c "
from si_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository
for row in PluginBaseRepository().fetch_all('''
  SELECT competence, scope_branch, computed_at::text
  FROM strategic_indicators.period_scores
  WHERE competence = %s ORDER BY scope_branch
''', ('2026-04',)):
    print(row)
"
```

Esperado: linhas com `scope_branch` `''`, `01` e `02`.

**Nota:** datas `start_date=01-05-2026` no log estão no formato esperado pelo SI (DD-MM-YYYY). O 500 neste caso não é formato de data — é falha ao ler catálogo/metas no Postgres.

### Consolidado OK, filial 01/02 com erro

**Causa:** cache `period_scores` só para `scope_branch = ''`; ao abrir filial a API recalcula e falha na query de metas (migrations ou bug de parâmetros acima).

**Ação:** corrigir API + `refresh_period_scores.py` até existirem linhas para `01` e `02`.

### Filtro por filial: meta “Sem meta para filial XX” ou rótulo “Filial 01” na UI

**Comportamento esperado (2026-05):** departamentos com medição consolidada (ex.: Engenharia) mantêm o **realizado consolidado** na visão por filial; a meta só aparece se existir `goal_scope_branch` `01`/`02`. A UI deve mostrar **Filial 01/02** (não “Consolidado”) em Escopo, leitura estratégica e prefixo de valor/gap — ver [INDICATOR_GOALS_SCOPE.md](./INDICATOR_GOALS_SCOPE.md) e [MFE.md](./MFE.md).

**Se ainda aparecer meta consolidada na filial:** redeploy da API (`uses_strict_branch_goal_resolution`) e refresh de `period_scores` para a competência.

### 502 Bad Gateway em todas as rotas

**Causa:** container `strategic-indicators-api` não sobe (crash no import).

**Ação:** `docker logs delpi-strategic-indicators-api` — corrigir `ImportError` (ex.: import circular em `snapshot_models` vs `period_scores_serialization`).

### 500 em trends/presentation com 6 meses

**Causa histórica:** meta não encontrada para competências de ano anterior.

**Estado atual:** fallback `list_latest_active_goals_map`; log `si_goal_year_fallback`.

**Ação de negócio:** duplicar metas para anos anteriores no admin.

### Executive lento na primeira carga (~10–20s)

**Esperado** com cache frio e TOTVS.

**Ação:** warm-up no boot; segunda requisição usa `SI_SNAPSHOT_CACHE_TTL_SECONDS` e/ou `period_scores`.

### 401 / 403

Token JWT inválido ou permissão ausente na Core API.

Verificar manifesto e roles do usuário (`strategic-indicators.view`, etc.).

### Decimal / JSON 500

Resposta deve passar por `to_json_safe` em `si_read_route_support`. Se reaparecer, verificar rota que não usa `json_read_response`.

## Invalidação de cache

Após alterar metas, settings ou estrutura admin, o cache in-process é invalidado nas rotas de escrita. Se dados parecerem “presos”, reiniciar o container ou aguardar TTL (`SI_SNAPSHOT_CACHE_TTL_SECONDS`).

## Monitoramento sugerido

- Latência p95 de `executive-summary` e `trends?months=6`
- Taxa de `*_failed` nos logs HTTP
- `si_warmup_failed` no startup
- Conexões TOTVS pool esgotado (`TOTVS_POOL_MAX_SIZE`)
