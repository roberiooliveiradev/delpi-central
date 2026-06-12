# Manutenção API

API dedicada do plugin **Manutenção** (`id`: `maintenance`) — Minha Delpi.

**Estado:** Fases 0–2 concluídas — CRUD operacional, preventiva, gateways TOTVS e listagens paginadas server-side (jun/2026).

## URLs (gateway dev)

```text
Health:  http://localhost/apps/maintenance-api/health
Módulo:  http://localhost/apps/maintenance-api/maintenance/health
Docs:    http://localhost/apps/maintenance-api/docs
```

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [docs/README.md](docs/README.md) | Índice técnico, listagens paginadas, filtro 3019 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Camadas `maint_app`, Postgres, gateways |
| [docs/integration-contracts.md](docs/integration-contracts.md) | Contratos com api-delpi |
| [../docs/12-roadmap-e-evolucao/maintenance/](../docs/12-roadmap-e-evolucao/maintenance/) | Produto, roadmap, playbook |

## Desenvolvimento local

```bash
cd maintenance-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
export MAINT_API_ROOT_PATH=/apps/maintenance-api
export DELPI_API_URL=http://localhost:8000
python -m uvicorn maint_app.main:app --reload --port 8012
```

## Testes

```bash
./scripts/ci-maintenance-api.sh   # 37 testes
```

## Pacote Python

`maint_app` — espelha `tm_app` (Transformômetro) e `si_app` (Strategic Indicators).

## Integração TOTVS

**Somente** via `DelpiApiClient` → api-delpi. Ver [PLAYBOOK-01](../docs/12-roadmap-e-evolucao/maintenance/PLAYBOOK-01-fronteiras-api-delpi.md).
