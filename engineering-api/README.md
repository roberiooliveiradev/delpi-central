# engineering-api

Backend/BFF do Portal Engenharia (EVA — Portal Engenharia DELPI).

## Status

`F2a` — primeira rota de negócio implementada: `GET /v1/home`, composição
autorizada das fontes oficiais comprovadas no inventário G0 (requests-api,
api-delpi). AuthN Keycloak + AuthZ Core via `shared/delpi_auth`.

**Ativação funcional pendente:** a permissão `engineering.access` ainda não
está registrada na Core — a rota existe e falha fechada (403) até o manifest
oficial do aplicativo Engineering registrar a permissão e os grants.

Decisões aprovadas em
`docs/12-roadmap-e-evolucao/engineering/05-f1-g0-architecture-decisions.md`
e contrato/ledgers em `docs/12-roadmap-e-evolucao/engineering/` (ver
`12-f2a-home-contract-and-implementation.md`).

## Estrutura

```text
engineering_app/
├── main.py                  # entrypoint FastAPI (engineering_app.main:app)
├── config.py                # Settings + envs (padrão das APIs maduras)
├── core/responses.py        # envelopes ok()/fail()
├── application/
│   ├── models/home.py       # contrato versionado da Home (schema 1.0)
│   ├── ports/home_sources.py       # HomeSectionSource / SectionFetch
│   └── use_cases/get_engineering_home.py  # composição com fan-out limitado
├── infrastructure/gateways/
│   ├── downstream_client.py # GET oficial (delegação Bearer do usuário)
│   ├── requests_api_gateway.py  # /requests/mine + /requests/work-queue
│   └── api_delpi_gateway.py     # /engineering/lmps
├── composition/home_composer.py   # wiring do use case
├── middleware/              # auth (delpi_auth) + observabilidade
└── interface/http/routes/
    ├── health_routes.py     # /health, /ready
    └── home_routes.py       # GET /v1/home (protegido)
tests/                       # pytest — contrato, segurança, resiliência
```

`domain/` é proibido por contrato: regras de domínio pertencem aos owners
oficiais; a engineering-api apenas compõe e normaliza.

## Configuração

| Env | Default | Uso |
|---|---|---|
| `SERVICE_NAME` | `engineering-api` | identidade em health/logs |
| `ENGINEERING_API_ROOT_PATH` | `/apps/engineering-api` | root path atrás do gateway |
| `PORT` | `8000` | porta interna |
| `APP_ENV` | `production` | ambiente |
| `LOG_LEVEL` | `INFO` | nível de log |
| `KEYCLOAK_*` | — | emissor/audiência/JWKS (delpi_auth) |
| `DELPI_AUTH_CORE_API_URL` | `http://core-api:8000` | resolução RBAC `/me` |
| `DELPI_API_URL` | `http://delpi-api-delpi:8000` | fonte LMPs (api-delpi) |
| `REQUESTS_API_URL` | `http://requests-api:8000` | fonte tasks/requests |
| `ENGINEERING_HOME_SOURCE_TIMEOUT_SECONDS` | `5.0` | timeout por fonte |
| `ENGINEERING_HOME_MAX_SECTION_ITEMS` | `10` | itens máximos por seção |
| `ENGINEERING_HOME_MAX_CONCURRENT_SOURCES` | `3` | fan-out máximo |

## Execução local

```bash
pip install -r requirements.txt
pip install -e "../shared[fastapi]"
python -m uvicorn engineering_app.main:app --host 0.0.0.0 --port 8000
pytest
```

## Deploy

Canônico via `infra/scripts/up-prod-sequential.sh --build engineering-api`
após push em `main` (ver `AGENTS.md`).
