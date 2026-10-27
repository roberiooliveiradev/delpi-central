# F1.S1 — Engineering API Scaffold + Health — Registro de Execução

> **Documento:** `08-f1-s1-engineering-api-bootstrap.md`
> **Fase:** F1.S1 — implementação real (scaffold mínimo autorizado)
> **BASE_HEAD:** `5bd8ca1e3a18960c9e95b43d4bc65182cd52d78d` (`origin/main` na reancoragem)
> **Autorização:** Coordenação EVA — F1.S1 ONLY (escopo: scaffold, bootstrap, config, health/ready, testes, boundaries, docs)
> **Decisões consumidas:** ADR-REQ-05/10 (`05-f1-g0-architecture-decisions.md`), contrato F1 (`07-f1-implementation-contract.md`)

---

## 1. O que foi criado

```text
engineering-api/
├── Dockerfile                     # python:3.11-slim, uvicorn --root-path
├── README.md                      # status, estrutura, config, execução
├── pytest.ini                     # pythonpath=. / testpaths=tests
├── requirements.txt               # pins explícitos (padrão delpi-mes-api)
├── engineering_app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI(), lifespan, handlers, router
│   ├── config.py                  # Settings + _get_env + settings
│   ├── core/
│   │   ├── __init__.py
│   │   └── responses.py           # fail() envelope
│   └── interface/http/routes/
│       ├── __init__.py
│       └── health_routes.py       # GET /health, GET /ready
└── tests/
    ├── conftest.py                # TestClient
    ├── test_health.py             # 7 testes
    ├── test_config.py             # 4 testes
    └── test_architecture.py       # 3 testes (boundaries)
```

Estrutura mínima deliberada: **sem** `domain/`, `application/`, `infrastructure/`, `composition/`, `middleware/` — criados quando houver casos de uso/adapters reais (guardado por `test_no_premature_layer_directories`).

## 2. Contratos HTTP implementados

| Rota | operationId | Resposta |
|---|---|---|
| `GET /health` | `get_engineering_health` | `200 {"status":"online","service":"engineering-api"}` |
| `GET /ready` | `get_engineering_ready` | `200 {"status":"ready","service":"engineering-api","root_path":...}` |
| `GET /openapi.json` | (FastAPI interno) | schema com apenas `/health` + `/ready` |

- `docs_url=None`, `redoc_url=None` (padrão `si_app/main.py`) — `/docs` e `/redoc` → 404.
- `redirect_slashes=False` — `/health/` → 404 (sem 307 com `Location: http://` atrás de TLS; precedente `commercial_app/main.py`).
- Handlers: `RequestValidationError`→`422 fail(...)`, `Exception`→`500 fail("Erro interno do servidor.")` — sem stack/SQL/hostname.
- Sem rotas de negócio, sem auth middleware (F1.S2), sem service tokens, sem allowlist custom.

## 3. Configuração

Padrão `Settings` + `_get_env` (espelho `commercial_app/config.py`), singleton `settings`:

| Env | Default |
|---|---|
| `SERVICE_NAME` | `engineering-api` |
| `ENGINEERING_API_ROOT_PATH` | `/apps/engineering-api` |
| `PORT` | `8000` |
| `APP_ENV` | `production` |
| `LOG_LEVEL` | `INFO` |

Sem secrets/credenciais nesta etapa → `check_credentials()` do `delpi_auth` **não** é usado ainda (dependência `shared/` entra em F1.S2 junto com o middleware JWT — Dockerfile deliberadamente não instala `shared` para não criar dependência artificial).

## 4. Readiness — semântica honesta

`/ready` reflete apenas o que existe: bootstrap concluído + config local válida. Não há DB, downstream nem Core AuthZ nesta etapa — **nenhuma validação simulada foi adicionada**. Não declara autorização nem integração corporativa.

## 5. Testes executados

Ambiente: venv Python 3.12 (WSL) com pins exatos de `requirements.txt` (fastapi 0.118.0, uvicorn 0.37.0, pydantic 2.11.9, httpx 0.28.1, pytest 8.4.2).

```text
$ python -m pytest -v
13 passed in 0.05s
```

| Teste | Verifica |
|---|---|
| `test_health_returns_online` | `/health` 200 + contrato exato |
| `test_ready_returns_ready` | `/ready` 200 + status/service |
| `test_openapi_exposes_stable_operation_ids` | operationIds no schema |
| `test_no_business_routes_exposed` | paths == `{/health, /ready}` |
| `test_docs_ui_disabled` | `/docs`, `/redoc` → 404 |
| `test_trailing_slash_not_redirected` | `/health/` → 404 sem redirect |
| `test_defaults` / `test_env_override` / `test_invalid_log_level_falls_back_to_info` | config defaults/override/fallback |
| `test_settings_expose_no_secrets` | nenhum atributo com secret/password/token/key |
| `test_no_cross_context_imports` | sem import de `app`, `commercial_app`, `requests_app`, `si_app`, `tm_app`, `delia_app`, `minha_delpi`, `core_app`… |
| `test_no_forbidden_dependencies` | sem `psycopg`/`sqlalchemy`/`openai`/`mcp`/`flask`/`delpi_mcp` etc. |
| `test_no_premature_layer_directories` | sem `domain/`/`application/`/`infrastructure/`/`composition/`/`middleware/` antecipados |

## 6. Smoke real (uvicorn, stack pinned)

```text
$ python -m uvicorn engineering_app.main:app --host 127.0.0.1 --port 8137 --root-path /apps/engineering-api
INFO ... engineering_api_started service=engineering-api env=production root_path=/apps/engineering-api
GET /health        → 200 {"status":"online","service":"engineering-api"}
GET /ready         → 200 {"status":"ready","service":"engineering-api","root_path":"/apps/engineering-api"}
GET /openapi.json  → paths: ['/health','/ready'], title: "Engineering API"
```

Observação de roteamento (verificada, consistente com o padrão do monorepo): o app responde em paths **internos** (`/health`); o gateway faz `rewrite ^/apps/engineering-api/?(.*)$ /$1 break` antes do proxy — request direto a `/apps/engineering-api/health` no container retorna 404 por design (mesmo comportamento de `commercial-api`).

## 7. CI audits executados

```text
python scripts/ci/audit_backend_boundaries.py  --check --base 5bd8ca1e3a → OK (0 findings)
python scripts/ci/audit_fastapi_authz.py       --check --base 5bd8ca1e3a → OK (0 findings)
python scripts/ci/audit_openapi_contracts.py   --check --base 5bd8ca1e3a → OK (0 findings)
python scripts/ci/audit_architecture_phase3.py --check --base 5bd8ca1e3a → OK
python scripts/ci/audit_platform_guardrails.py --check --base 5bd8ca1e3a → OK (0 findings)
```

## 8. Correção documental sancionada — `ARCHITECTURE.md`

- §4: "sem Flask" → "sem dependência de framework HTTP" (layer purity).
- §9: premissa "tecnologia realtime compatível com Flask" → FastAPI + Uvicorn conforme ADR-REQ-05; escolha da tecnologia realtime da Sala permanece **aberta e não implementada** (WebSocket nativo registrado apenas como precedente em `commercial-api`).

## 9. Limitações e gaps (honestos)

| Item | Estado |
|---|---|
| AuthN JWT / Core AuthZ | **ausente por escopo** — F1.S2 |
| Rotas de negócio | nenhuma — F2a+ |
| `engineering.access` | não registrado — decisão doc 06 §2.3 |
| Persistência/DB/migrations | nenhuma — decisão futura |
| Gateway/Compose/`FASE_API` | não modificado — F1.S5; serviço **não** é implantável ainda |
| Deploy | não executado — sem runtime produtivo |
| Observabilidade estruturada de request | mínima (log de startup); middleware de request log entra com auth em F1.S2/S3 |
| Versão local de teste | evidência principal no stack pinned via venv WSL; run adicional em Python 3.14/fastapi 0.148 também passou (13/13) — não é o alvo de produção |
| Dockerfile | estrutura verificada contra padrão `commercial-api`; **build da imagem não executado** (sem daemon Docker no ambiente) — `TEST_NOT_RUN` |

## 10. Próximo bounded step

`F1.S2` — auth plumbing: `middleware/auth_middleware.py` com `delpi_auth.middleware.fastapi_auth.jwt_middleware`, allowlist `/health`+`/ready` (+variantes root_path), `check_credentials()` no lifespan, `COPY shared` no Dockerfile, envs `KEYCLOAK_*`/`CORE_API_URL`, testes 401/403/mock-Core — **somente mediante autorização explícita da Coordenação**.
