# Manutenção API

API dedicada do plugin **Manutenção** (`id`: `maintenance`) — Minha Delpi.

**Estado:** Fase 0 — documentação inicial; código FastAPI na próxima entrega.

## URLs (gateway dev — alvo)

```text
Health:  http://localhost/apps/maintenance-api/health
Módulo:  http://localhost/apps/maintenance-api/maintenance/health
Docs:    http://localhost/apps/maintenance-api/docs
```

## Documentação

| Documento | Conteúdo |
|-----------|----------|
| [docs/README.md](docs/README.md) | Índice técnico |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Camadas `maint_app`, Postgres, gateways |
| [docs/integration-contracts.md](docs/integration-contracts.md) | Contratos com api-delpi |
| [../docs/12-roadmap-e-evolucao/maintenance/](../docs/12-roadmap-e-evolucao/maintenance/) | Produto, roadmap, playbook |

## Desenvolvimento local (quando implementado)

```bash
cd maintenance-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
export MAINT_API_ROOT_PATH=/apps/maintenance-api
export DELPI_API_URL=http://localhost:8000
python -m uvicorn maint_app.main:app --reload --port 8012
```

## Pacote Python

`maint_app` — espelha `tm_app` (Transformômetro) e `si_app` (Strategic Indicators).

## Integração TOTVS

**Somente** via `DelpiApiClient` → api-delpi. Ver [PLAYBOOK-01](../docs/12-roadmap-e-evolucao/maintenance/PLAYBOOK-01-fronteiras-api-delpi.md).
