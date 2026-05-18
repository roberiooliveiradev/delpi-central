# Strategic Indicators API

Serviço **FastAPI** dedicado ao módulo **Indicadores Estratégicos** (`/strategic-indicators/*`).

## Documentação completa

**Índice:** [docs/README.md](docs/README.md)

| Guia | Link |
|------|------|
| Visão geral | [docs/OVERVIEW.md](docs/OVERVIEW.md) |
| Arquitetura | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| API HTTP | [docs/API.md](docs/API.md) |
| Banco de dados | [docs/DATABASE.md](docs/DATABASE.md) |
| Fontes de dados | [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) |
| Código (`si_app`) | [docs/CODE_STRUCTURE.md](docs/CODE_STRUCTURE.md) |
| MFE | [docs/MFE.md](docs/MFE.md) |
| Desenvolvimento | [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) |
| Deploy | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| Operação | [docs/OPERATIONS.md](docs/OPERATIONS.md) |
| Performance | [docs/PERFORMANCE_IMPLEMENTATION.md](docs/PERFORMANCE_IMPLEMENTATION.md) |

## URLs (gateway)

```text
/apps/strategic-indicators-api/strategic-indicators/*
/apps/strategic-indicators-api/docs
/apps/strategic-indicators-api/health
```

A **api-delpi** não expõe mais o painel SI. Dados diretos (ROL, etc.) permanecem em `/apps/api-delpi/finacial/financial/*`.

## Início rápido (Docker)

```bash
cd infra
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d strategic-indicators-api gateway
curl -s http://localhost/apps/strategic-indicators-api/health
```

## Migrations

```bash
python strategic-indicators-api/scripts/run_migrations.py up
```

Ver [migrations/README.md](migrations/README.md).

## Desenvolvimento local

Ver [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
