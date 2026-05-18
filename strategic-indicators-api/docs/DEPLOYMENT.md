# Deploy e infraestrutura

## Docker

| Item | Valor |
|------|-------|
| Dockerfile | `strategic-indicators-api/Dockerfile` (contexto = raiz do monorepo) |
| Container dev | `delpi-strategic-indicators-api` |
| Porta interna | `8000` |
| `root-path` uvicorn | `/apps/strategic-indicators-api` |

Build:

```bash
docker build -f strategic-indicators-api/Dockerfile -t strategic-indicators-api:dev .
```

## Compose

Serviço em `infra/docker-compose.yml` e overrides em `infra/docker-compose.dev.yml`:

- Volume dev: `../strategic-indicators-api:/app`
- `depends_on`: keycloak, postgres-plugins
- Gateway inclui `strategic-indicators-api` no `depends_on`

## Gateway (Nginx)

```nginx
location ^~ /apps/strategic-indicators-api/ {
  proxy_pass http://strategic-indicators-api:8000/;
}
```

MFE:

```nginx
location ^~ /apps/strategic-indicators/ {
  proxy_pass http://delpi-strategic-indicators:80/;
}
```

Ver [gateway-nginx.md](../../docs/02-infraestrutura/gateway-nginx.md).

## Variáveis de ambiente

### SI / performance

| Variável | Default | Descrição |
|----------|---------|-----------|
| `SI_API_ROOT_PATH` | `/apps/strategic-indicators-api` | Prefixo OpenAPI e links |
| `SI_SNAPSHOT_CACHE_TTL_SECONDS` | `600` | Cache in-process medições/catálogo |
| `SI_WARMUP_ON_STARTUP` | `false` (`true` no Compose dev) | Warm-up em thread no boot |
| `SI_WARMUP_TRENDS_MONTHS` | `6` | Meses aquecidos no warm-up |
| `SI_PERIOD_SCORES_ENABLED` | `true` | Grava/lê `period_scores` |
| `SI_RUN_MIGRATIONS_ON_STARTUP` | `false` (`true` dev) | Migrations antes do warm-up |
| `TOTVS_POOL_ENABLED` | `true` | Pool pyodbc |
| `TOTVS_POOL_MAX_SIZE` | `8` | Conexões máx. no pool |
| `LOG_LEVEL` | `INFO` | Logs `strategic_indicators.*` |

Exemplo: [infra/env.strategic-indicators.example](../../infra/env.strategic-indicators.example)

### Autenticação

| Variável | Descrição |
|----------|-----------|
| `JWT_SECRET` / `API_DELPI_JWT_SECRET` | Fallback HS256 |
| `KEYCLOAK_JWKS_URL`, `KEYCLOAK_ISSUER`, `KEYCLOAK_AUDIENCE` | Validação JWT |
| `JWT_ALGORITHMS` | Ex.: `RS256` |

### Bancos

| Grupo | Variáveis |
|-------|-----------|
| Postgres plugins | `PLUGINS_DB_HOST`, `PLUGINS_DB_PORT`, `PLUGINS_DB_NAME`, `PLUGINS_DB_USER`, `PLUGINS_DB_PASSWORD` |
| TOTVS | `TOTVS_DB_*` → mapeadas para `DB_*` no container |
| Portal RH | `PORTAL_RH_DB_*` |
| Google Sheets | `GOOGLE_SHEETS_*`, `*_SHEET_ID`, `*_GID` (ver `config.py`) |

## Ordem de subida (dev)

```text
postgres-plugins, keycloak
  → strategic-indicators-api (migrations opcionais + warm-up)
  → strategic-indicators (MFE build)
  → gateway
```

## Produção — checklist

1. `SI_RUN_MIGRATIONS_ON_STARTUP=false` — rodar migrations em pipeline ou job
2. `SI_WARMUP_ON_STARTUP=true` se aceitar carga no boot; ou cron com `warmup_si_snapshots.py`
3. Ajustar `TOTVS_POOL_MAX_SIZE` conforme filiais × paralelismo
4. Logs em stdout do container; arquivo opcional em `logs/` no volume dev
5. Health: `GET /apps/strategic-indicators-api/health`

## Migrations em produção

```bash
docker exec delpi-strategic-indicators-api python3 scripts/run_migrations.py status
docker exec delpi-strategic-indicators-api python3 scripts/run_migrations.py up
```
