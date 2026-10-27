# engineering-api

Backend/BFF do Portal Engenharia (EVA — Portal Engenharia DELPI).

## Status

`F1.S1` — bootstrap mínimo: FastAPI + Uvicorn, `GET /health`, `GET /ready`,
OpenAPI técnico. **Nenhuma rota de negócio, autenticação ou autorização foi
implementada nesta etapa** — AuthN/AuthZ chega em F1.S2 via `shared/delpi_auth`.

Decisões aprovadas em
`docs/12-roadmap-e-evolucao/engineering/05-f1-g0-architecture-decisions.md`
(ADR-REQ-05/10) e contrato de execução em
`docs/12-roadmap-e-evolucao/engineering/07-f1-implementation-contract.md`.

## Estrutura

```text
engineering_app/
├── main.py                  # entrypoint FastAPI (engineering_app.main:app)
├── config.py                # Settings + envs (padrão das APIs maduras)
├── core/responses.py        # envelope fail()
└── interface/http/routes/
    └── health_routes.py     # /health, /ready
tests/                       # pytest (health, config, boundaries)
```

`domain/`, `application/` e `infrastructure/` serão criados quando existirem
casos de uso e adapters reais (F2a em diante) — sem pastas antecipadas.

## Configuração

| Env | Default | Uso |
|---|---|---|
| `SERVICE_NAME` | `engineering-api` | identidade em health/logs |
| `ENGINEERING_API_ROOT_PATH` | `/apps/engineering-api` | root path atrás do gateway |
| `PORT` | `8000` | porta interna |
| `APP_ENV` | `production` | ambiente |
| `LOG_LEVEL` | `INFO` | nível de log |

Sem secrets nesta etapa; `KEYCLOAK_*`/`CORE_API_URL` entram em F1.S2.

## Execução local

```bash
pip install -r requirements.txt
python -m uvicorn engineering_app.main:app --host 0.0.0.0 --port 8000
pytest
```

## Deploy

Não aplicável em F1.S1 — gateway/Compose/FASE_API entram em F1.S5
(`infra/scripts/up-prod-sequential.sh --build engineering-api`).
