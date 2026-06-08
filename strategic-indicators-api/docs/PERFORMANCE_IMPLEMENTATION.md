# Plano de implementação — performance API Strategic Indicators

Documento de referência para implementação incremental. Atualizar **Status** e **Checklist** a cada entrega.

**Última atualização:** 2026-05-28 (mapa de gargalos api-delpi)

**Mapa de gargalos (refresh / api-delpi):** `docs/SI_BOTTLENECK_MAP.md`  
**Baseline medido:** `GET /strategic-indicators/executive-summary?competence=2026-05` ≈ **19s** → **~10s** (2 períodos em paralelo com providers isolados).  
**Trends (3 meses):** ~28s (série sequencial por dept) → **~9–10s** (períodos em paralelo com factory, até 3 workers).

---

## 1. Objetivo

Reduzir latência das rotas de **leitura do painel** (grupo A/B), mantendo correção dos dados e **sem repetir** o erro de paralelismo inseguro entre períodos.

Rotas **admin/escrita** (grupo C) são secundárias — já são rápidas (Postgres).

---

## 2. Mapa de arquivos (onde mexer)

| Responsabilidade | Caminho |
|------------------|---------|
| Rotas HTTP | `si_app/interface/http/routes/strategic_indicators_routes.py` |
| Log/cache HTTP leitura | `si_app/interface/http/si_read_route_support.py` |
| Cache TTL compartilhado | `si_app/application/services/strategic_indicators/snapshot_shared_cache.py` |
| TTL genérico | `si_app/infrastructure/cache/ttl_cache.py` |
| Composição DI | `si_app/composition/strategic_indicators_composer.py` |
| Snapshot (núcleo) | `si_app/application/services/strategic_indicators/strategic_indicators_snapshot_service.py` |
| Modelos de snapshot | `strategic_indicators_snapshot_models.py` |
| Metas fallback (série) | `postgres_resolved_indicators_catalog_repository.py`, `list_latest_active_goals_map` |
| Medições (TOTVS/Sheets/RH) | `si_app/infrastructure/providers/strategic_indicators/real_indicator_measurements_provider.py` |
| Coletores por dept | `si_app/infrastructure/providers/strategic_indicators/*_indicators_snapshot_provider.py` |
| Catálogo + metas (Postgres) | `si_app/infrastructure/persistence/plugins/repositories/strategic_indicators/postgres_resolved_indicators_catalog_repository.py` |
| Metas em lote | `postgres_indicator_goals_repository.py` (`list_resolved_goals_map`) |
| Benchmark | `scripts/bench_si_routes.py` |
| Migrations Postgres | `migrations/`, `scripts/run_migrations.py` |
| JSON `Decimal` → resposta HTTP | `si_app/shared/json_encoding.py` (`to_json_safe`) |
| MFE (commit separado) | `plugins/strategic-indicators/src/data/cache/` |

---

## 3. Rotas por grupo

### Grupo A — comparativo (2 períodos: atual + anterior)

| Rota | Use case | Carga |
|------|----------|-------|
| `GET /executive-summary` | `GetStrategicIndicatorsExecutiveSummaryRealUseCase` | `get_current_and_previous_snapshot` |
| `GET /departments` | `GetStrategicIndicatorsDepartmentsRealUseCase` | idem |
| `GET /departments/{id}` | `GetStrategicIndicatorsDepartmentDetailsRealUseCase` | idem + filtro `department_id` |
| `GET /alerts` | `GetStrategicIndicatorsAlertsRealUseCase` | idem (catálogo via `comparative.catalog`) |

### Grupo B — período único ou série

| Rota | Use case | Carga |
|------|----------|-------|
| `GET /indicators` | `GetStrategicIndicatorsUseCase` | `get_period_snapshot` |
| `GET /trends?months=N` | `GetStrategicIndicatorsTrendsRealUseCase` | `get_series_snapshot_optimized` + séries consolidadas 7 deptos |
| `GET /presentation?include=` | `GetStrategicIndicatorsPresentationUseCase` | comparativo + trends (split no MFE) |

### Grupo C — admin

`settings`, `change-requests`, `admin/*`, `indicator-goals/*` — invalidam cache via `invalidate_strategic_indicators_snapshot_cache()`.

---

## 4. O que já foi feito

- [x] Metas em lote (`list_resolved_goals_map`)
- [x] Logs `si_catalog_loaded`, `si_measurements_loaded`, `si_snapshot_comparative`, `si_series_snapshot`
- [x] Logs HTTP rotas A/B (`run_logged_read_route`)
- [x] Script `scripts/bench_si_routes.py`
- [x] Alerts sem `get_catalog_snapshot` duplicado
- [x] Cache TTL in-process (`SI_SNAPSHOT_CACHE_TTL_SECONDS`, default 600s)
- [x] `Cache-Control` + `ETag` nas GET de leitura
- [x] Séries consolidadas: 7 deptos em paralelo em `get_indicator_measurements_series` quando `department_id` é null
- [x] `get_series_snapshot_optimized`: departamentos/metas executivos uma vez por série
- [x] Presentation `?include=` + MFE carrega overview e trends em 2 requests
- [x] Provider com `threading.Lock` no cache interno
- [x] Comparativo: 2 períodos em paralelo com `measurements_port_factory` (instâncias isoladas)
- [x] Trends: períodos da série em paralelo (`_load_measurements_by_period_parallel`, max 3 workers)
- [x] Fix `Decimal` não serializável em `JSONResponse` (`to_json_safe` + normalização na rota `/indicators`)
- [x] MFE: stale-while-revalidate, prefetch e presentation split (plugin)

---

## 4.1 Incidentes resolvidos

| Incidente | Causa | Correção |
|-----------|--------|----------|
| 500 em `/indicators`, `/presentation`, `/trends` com use case OK no log | `JSONResponse` + `Decimal` do Postgres após introdução de `si_read_route_support` | `to_json_safe()` antes de serializar |
| Executive ~30s → erro com 2 períodos paralelos no mesmo provider | Race em cache TOTVS/pyodbc | Medições sequenciais; depois factory por thread |
| 500 trends/presentation 6 meses: meta não encontrada | Metas só no `goal_year` da competência (seed 2026; série inclui 2025) | Fallback `list_latest_active_goals_map`; omitir indicador sem meta |
| 502 em todas as rotas | Import circular `snapshot_service` ↔ `period_scores_serialization` | Modelos em `strategic_indicators_snapshot_models.py` |

---

## 5. Regra de ouro — paralelismo

```
SEGURO:
  - 7 deptos em paralelo dentro de um período
  - 2 períodos em paralelo COM measurements_port_factory() (uma instância por thread)

PROIBIDO:
  - 2 períodos no MESMO RealStrategicIndicatorsMeasurementsProvider
```

---

## 6. Fases e checklist

### Fase 0 — Observabilidade

- [x] Log HTTP rotas A/B
- [x] Log `si_series_snapshot`
- [x] Script `scripts/bench_si_routes.py`

### Fase 1 — Quick wins backend

- [x] 1.1 Alerts → `comparative.catalog`
- [x] 1.2 Cache TTL + invalidação em mutações de metas/settings
- [x] 1.3 `Cache-Control` / `ETag`
- [x] 1.4 Bench `departments/{id}` no script

### Fase 2 — Séries

- [x] 2.1 Séries consolidadas (7 deptos) em `real_indicator_measurements_provider.py`
- [x] 2.2 Catálogo estrutural uma vez em `get_series_snapshot_optimized`
- [x] 2.3 Tabela `period_scores` (Postgres) + leitura em executive/departments/indicators
- [x] 2.3b Job periódico (`period_scores_refresh`) a cada 5 min + `refresh_state` (V011)
- [x] 2.4 Presentation `?include=` (API); trends-only sem comparativo
- [x] 2.4b MFE split trends

### Fase 3 — Raiz das medições

- [x] 3.1 Lock no cache do provider
- [x] 3.2 Períodos paralelos com factory
- [x] 3.3 Pool pyodbc TOTVS no SI — **removido jun/2026** ([LEGACY_CLEANUP.md](./LEGACY_CLEANUP.md)); pool permanece na api-delpi
- [x] 3.4 Coletores thin — produção consolidada (`get_consolidated_snapshot` → passagem única)
- [x] 3.4b Transforma+ — cache TTL de `load_raw_data` (6 abas)
- [x] 3.4c Financial — `list_rol_by_branch` (1 query TOTVS por período)
- [x] 3.4d LMP — `GET /engineering/lmps/dashboard/summary` via api-delpi (SI sem cálculo local)
- [x] 3.5 Warm-up — `scripts/warmup_si_snapshots.py` + `SI_WARMUP_ON_STARTUP` (legado se refresh desligado)
- [x] 3.6 Materialização — `scripts/refresh_period_scores.py` + `SI_PERIOD_SCORES_REFRESH_*`

### Fase 4 — MFE (`plugins/strategic-indicators`)

- [x] 4.1 Stale-while-revalidate (executive, departments, trends, indicators, alerts, presentation)
- [x] 4.2 Prefetch departments + trends após executive
- [x] 4.3 Presentation: overview primeiro, trends em segundo request + `trendsLoading` na UI

### Fase 5 — Admin

- [x] Invalidar cache em writes de metas/settings
- [x] Metas admin: `monthly_targets` em lote (`_attach_monthly_targets`)
- [x] Change-requests: paginação `limit`/`offset` + `total` (índices já em V007)

---

## 7. Variáveis de ambiente

| Variável | Default | Uso |
|----------|---------|-----|
| `SI_SNAPSHOT_CACHE_TTL_SECONDS` | `300` no Compose | TTL cache in-process entre requests |
| `LOG_LEVEL` | `INFO` | Logs `strategic_indicators.*` |
| `TOTVS_POOL_*` (api-delpi) | — | Pool ODBC só na api-delpi; removido do SI |
| `SI_WARMUP_ON_STARTUP` | `false` no Compose | Warm-up legado (só se `SI_PERIOD_SCORES_REFRESH_ENABLED=false`) |
| `SI_WARMUP_TRENDS_MONTHS` | `6` | Meses no warm-up legado |
| `SI_PERIOD_SCORES_ENABLED` | `true` | Lê/grava `period_scores` nas rotas de leitura |
| `SI_PERIOD_SCORES_REFRESH_ENABLED` | `true` | Scheduler recalcula scores a cada N segundos |
| `SI_PERIOD_SCORES_REFRESH_INTERVAL_SECONDS` | `300` | Intervalo do job (mín. 60s) |
| `SI_PERSIST_CALCULATION_SNAPSHOTS_ON_READ` | `false` | Em leituras HTTP, grava só `period_scores` (refresh materializa `calculation_snapshots`) |
| `SI_PERIOD_SCORES_REFRESH_TRENDS_MONTHS` | `3` | Meses materializados (consolidado) |
| `SI_PERIOD_SCORES_REFRESH_PER_DEPARTMENT` | `false` | Materializa linha por departamento (não lida pela exibição; leitura usa sempre a base global) |
| `SI_PERIOD_SCORES_REFRESH_INCLUDE_PREVIOUS` | `true` | Garante comparativo mês anterior |
| `SI_PERIOD_SCORES_REFRESH_BRANCHES` | vazio | Filiais extras (CSV); vazio = consolidado |

---

## 8. Benchmark

```bash
# Local (monorepo)
export PYTHONPATH="$(pwd)/strategic-indicators-api:$(pwd)/shared"
python strategic-indicators-api/scripts/bench_si_routes.py --competence 2026-05

# Container
docker exec delpi-strategic-indicators-api python3 -c "..."  # ver histórico no doc ou script
```

---

## 9. Pendências opcionais (pós fases 0–5)

| Item | Prioridade | Notas |
|------|------------|-------|
| Backfill `period_scores` / `calculation_snapshots` | Média | `refresh_period_scores.py` (materializa ambos) |
| `catalog_inputs_hash` (V014) | Feito | Detectar divergência catálogo vs materializado |
| Meta ativa única por ano (V013) | Feito | Índice parcial + dedupe na migration |
| Vigência `valid_from`/`valid_to` | Feito | Filtro SQL na resolução de metas |
| Metas por ano (2025, etc.) | Baixa | Admin `duplicate-year`; hoje há fallback automático |
| Paginação admin extra | Baixa | Ex.: histórico de metas se volume crescer |
| Unificar migrations | Housekeeping | Remover duplicata legada em `api-delpi/migrations/plugins/strategic-indicators/` |
| Refresh por filial | Baixa | `SI_PERIOD_SCORES_REFRESH_BRANCHES` com códigos TOTVS |

---

## 10. Histórico

| Data | Nota |
|------|------|
| 2026-05-18 | Criação do plano |
| 2026-05-18 | Implementação fases 0–2 e 3.1–3.2 (API); executive ~10s com paralelo seguro |
| 2026-05-18 | Fix serialização `Decimal`; trends com períodos paralelos; roadmap atualizado |
| 2026-05-18 | MFE: cache leitura, prefetch, split presentation, SWR em todas as páginas do painel |
| 2026-05-18 | Pool pyodbc TOTVS com release no `BaseRepository` e discard em erro |
| 2026-05-18 | Produção consolidada: elimina N×`get_unit_snapshot` por filial (thin SI) |
| 2026-05-18 | Financial: `list_rol_by_branch` substitui N×`get_rol` no snapshot SI |
| 2026-05-18 | LMP: cache TTL do dashboard summary; SI ignora avg lead time |
| 2026-05-18 | Warm-up executive + trends (`warmup_si_snapshots.py`, `SI_WARMUP_ON_STARTUP`) |
| 2026-05-18 | Admin: batch monthly_targets; change-requests paginado; bench alerts |
| 2026-05-18 | `period_scores` (V010): trends lê scores do Postgres quando todos os meses existem |
| 2026-05-19 | `refresh_state` (V011) + scheduler 5 min: executive/departments/indicators leem Postgres; TOTVS só no job |
| 2026-05-18 | Fallback metas + `snapshot_models` (fix série 6m e boot 502) |
| 2026-05-18 | Documentação completa SI: OVERVIEW, DATABASE, MFE, DEPLOYMENT, DEVELOPMENT, OPERATIONS, CODE_STRUCTURE, DATA_SOURCES |
| 2026-05-25 | api-delpi: refatoração LMP com batch queries (temp tables em batch único pyodbc) + connection pooling |
| 2026-05-26 | api-delpi: fix pool max=4→10 (burst ~30 req do snapshot causava TimeoutError → 500) |
