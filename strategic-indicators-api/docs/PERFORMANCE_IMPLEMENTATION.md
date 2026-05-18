# Plano de implementação — performance API Strategic Indicators

Documento de referência para implementação incremental. Atualizar **Status** e **Checklist** a cada entrega.

**Última atualização:** 2026-05-18  
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
| Medições (TOTVS/Sheets/RH) | `si_app/infrastructure/providers/strategic_indicators/real_indicator_measurements_provider.py` |
| Coletores por dept | `si_app/infrastructure/providers/strategic_indicators/*_indicators_snapshot_provider.py` |
| Catálogo + metas (Postgres) | `si_app/infrastructure/persistence/plugins/repositories/strategic_indicators/postgres_resolved_indicators_catalog_repository.py` |
| Metas em lote | `postgres_indicator_goals_repository.py` (`list_resolved_goals_map`) |
| Benchmark | `scripts/bench_si_routes.py` |
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
- [ ] 2.3 Tabela `si_period_scores` (opcional, não implementado)
- [x] 2.4 Presentation `?include=` (API); trends-only sem comparativo
- [x] 2.4b MFE split trends

### Fase 3 — Raiz das medições

- [x] 3.1 Lock no cache do provider
- [x] 3.2 Períodos paralelos com factory
- [x] 3.3 Pool pyodbc TOTVS (`connection_pool.py`, `TOTVS_POOL_*`)
- [x] 3.4 Coletores thin — produção consolidada (`get_consolidated_snapshot` → passagem única)
- [x] 3.4b Transforma+ — cache TTL de `load_raw_data` (6 abas)
- [ ] 3.4c Financial N×ROL / LMP agregado SQL (pendente)
- [ ] 3.5 Warm-up cron (pendente)

### Fase 4 — MFE (`plugins/strategic-indicators`)

- [x] 4.1 Stale-while-revalidate (executive, departments, trends, indicators, alerts, presentation)
- [x] 4.2 Prefetch departments + trends após executive
- [x] 4.3 Presentation: overview primeiro, trends em segundo request + `trendsLoading` na UI

### Fase 5 — Admin

- [x] Invalidar cache em writes de metas/settings
- [ ] Índices/paginação listas grandes (pendente)

---

## 7. Variáveis de ambiente

| Variável | Default | Uso |
|----------|---------|-----|
| `SI_SNAPSHOT_CACHE_TTL_SECONDS` | `600` | TTL cache medições/catálogo entre requests |
| `LOG_LEVEL` | `INFO` | Logs `strategic_indicators.*` |
| `TOTVS_POOL_ENABLED` | `true` | Reutiliza conexões pyodbc entre queries |
| `TOTVS_POOL_MAX_SIZE` | `8` | Máx. conexões simultâneas (7 deptos + margem) |

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

## 9. Ordem restante sugerida

1. Coletores thin (3.4)
3. `si_period_scores` (2.3) se trends ainda > 25s
4. Paginação admin (5)

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
