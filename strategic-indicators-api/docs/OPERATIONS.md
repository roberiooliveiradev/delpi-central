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
