# F1-G0 — Decisões de Arquitetura — engineering-api

> **Documento:** `05-f1-g0-architecture-decisions.md`
> **Fase:** F1-G0 — Architecture Decision Gate (somente documentação)
> **BASE_HEAD de inspeção:** `486831a025bfad52694a5aa0a0711dffc2340f95` (`origin/main`)
> **Escopo:** ADR-REQ-05 (framework/estrutura) + ADR-REQ-10 (gateway/Docker/deploy). Core AuthZ em `06-f1-g0-core-authz-contract.md`.
> **Status das decisões:** `PROPOSED` — nada aqui está implementado; aguardam aprovação da Coordenação.

---

## 0. Contexto

F0 (`ACCEPT_WITH_RESIDUAL`) registrou dois bloqueios de implementação: ADR-REQ-05 e ADR-REQ-10 (`04-f0-implementation-readiness.md` §7). Este documento resolve ambos com evidência verificável no SHA acima.

**Correção factual à F0 (residual search):** `02-f0-factual-inventory.md` §2.5 classificou `commercial-api`, `requests-api`, `strategic-indicators-api` e `transformometro-api` como Flask. **Isso está errado** — os quatro são **FastAPI + uvicorn** (ver `requirements.txt` de cada um e os entrypoints `<svc>_app/main.py`). A distribuição real:

| Framework | Serviços |
|---|---|
| **FastAPI** (18; 17 com pacote `*_app` + `api-delpi` com `app/`) | `api-delpi`, `commercial-api`, `requests-api`, `strategic-indicators-api`, `transformometro-api`, `tv-dashboard-api`, `purchase-requests-api`, `helpdesk-api`, `controllership-finance-api`, `cipa-api`, `customer-experience-api`, `production-control-api`, `delpi-mes-api`, `financial-api`, `travel-expenses-api`, `production-pulse-api`, `maintenance-api`, `comite-etica-conduta-api` |
| **Flask** (5) | `core-api`, `minha-delpi-ai-api`, `supplies-api`, `external-data-api`, `delia-api` |

Evidência: `*/requirements.txt` (`fastapi`/`uvicorn[standard]` vs `Flask==3.x`/`gunicorn`) e entrypoints `*_app/main.py` (`FastAPI(...)`) vs `app/create_app.py` (Flask factory). Verificado em `486831a025`.

---

## 1. ADR-REQ-05 — Framework, naming e estrutura

### 1.1. Evidência do padrão dominante

Todas as APIs de domínio criadas na geração atual da plataforma seguem o mesmo bootstrap (verificado arquivo a arquivo):

| Aspecto | Padrão provado | Evidência |
|---|---|---|
| Framework | FastAPI + `uvicorn[standard]` | `commercial-api/requirements.txt`; idem requests/si/tm/tv/cf/cipa/cx/pc/mes/financial/travel/pulse/maint/cec |
| Pacote | `<svc>_app/` snake do service name | `commercial_app`, `requests_app`, `si_app`, `tm_app`, `tv_app`, `cx_app`, `maint_app`, `cec_app`, `delpi_mes_app`, `production_control_app`, `controllership_finance_app`, `purchase_requests_app`, `financial_app`, `travel_expenses_app`, `production_pulse_app`, `helpdesk_app` |
| Entrypoint | `<pkg>_app/main.py` → `app = FastAPI(...)` | `si_app/main.py:75`, `commercial_app/main.py:105` |
| FastAPI init | `root_path=settings.<SVC>_API_ROOT_PATH`, `lifespan`, `redirect_slashes=False` | `commercial_app/main.py:105-115` (comentário inline: evita 307 com `Location: http://` atrás de TLS) |
| Lifespan | `check_credentials()` → `run_migrations_on_startup()` → schedulers → cleanup | `commercial_app/main.py:75-99`; `si_app/main.py:50-68` |
| Config | `config.py` classe `Settings` + `_get_env(*names, default)` + `settings` singleton | `commercial_app/config.py:1-114` |
| Auth | `middleware/auth_middleware.py` wrapper de `delpi_auth.middleware.fastapi_auth.jwt_middleware` + public path allowlist (`/health`, `/ready`, root-path variants) | `commercial_app/middleware/auth_middleware.py:1-30`; `si_app/middleware/auth_middleware.py:1-33` |
| Erros | `core/responses.py` `fail(msg, status)` + exception handlers `RequestValidationError→422`, `Exception→500` | `commercial_app/main.py:117-131` |
| Health | `@app.get("/health")` + `@app.get("/ready")` (ready = degraded-aware) | `commercial_app/main.py:144-176`; `commercial-api/tests/test_health.py` |
| Middleware extra | `GZipMiddleware` + `CORSMiddleware` com `build_allowed_origins(public_base_url, keycloak_url)` | `commercial_app/main.py:133-141` |
| Observabilidade | request log estruturado + `X-Operation-Id`/`X-Response-Time-Ms` + contextvars | `api-delpi/app/middleware/request_observability_middleware.py` + `app/infrastructure/observability/request_context.py` (app-local) |
| Estrutura interna | `domain/`, `application/{use_cases,services,ports}`, `infrastructure/{gateways,persistence,providers,schedulers}`, `interface/http/{routes,schemas}`, `composition/`, `middleware/`, `startup/`, `core/` | `commercial-api/commercial_app/` tree |
| Testes | `pytest.ini` (`pythonpath=.`, `testpaths=tests`), `tests/test_health.py` com `TestClient` | `requests-api/pytest.ini`, `commercial-api/tests/` |
| Shared deps | `pip install -e "/shared[fastapi]"` (extra `fastapi` em `shared/pyproject.toml:24`) | `commercial-api/Dockerfile`, `shared/pyproject.toml` |

### 1.2. Alternativas consideradas

| Alternativa | Prós | Contras | Veredito |
|---|---|---|---|
| **A. FastAPI + `engineering_app/`** (padrão dominante) | 17 serviços idênticos; `delpi_auth` FastAPI middleware canônico; OpenAPI-first nativo; async favorece fan-out do BFF; `redirect_slashes`/`root_path` já resolvidos; WS nativo (ver §1.4) | exige async discipline nos gateways | **RECOMENDADA** |
| B. Flask + `app/` (família delia/core/chat) | delia-api mostra bootstrap simples; gunicorn+threads | minoria (5, legados/specialistas); quebra `delpi_auth.middleware.fastapi_auth`; sem OpenAPI nativo; WS exigiria Flask-SocketIO (só core-api usa) | rejeitada |
| C. FastAPI + `app/` (naming híbrido) | — | quebra convenção `<svc>_app` dos 17; herda ambiguidade com `api-delpi/app` | rejeitada |
| D. Flask + `engineering_app/` | — | pior dos dois mundos | rejeitada |

**Nota de drift documental:** `ARCHITECTURE.md` §4 propõe `engineering-api/engineering_app/` (naming correto) e domain "sem Flask", mas §9 (linha ~219) exige "tecnologia realtime compatível com Flask" — pressupõe Flask como framework do serviço. Os docs foram escritos antes da convergência FastAPI ser visível (17 APIs `*_app` FastAPI + api-delpi vs 5 Flask legados/specialistas). **Registrado como divergência; a decisão segue o código vigente, e `ARCHITECTURE.md` deve ser atualizado na F1** (não silenciosamente — a Coordenação deve sancionar a correção documental).

### 1.3. Realtime (futura Sala) sob FastAPI

A preocupação original de P-05 ("realtime Flask-compatible") desaparece: FastAPI tem WebSocket nativo e **já está provado** — `commercial-api` expõe `/commercial/realtime/ws` com `commercial_realtime_hub` (`bind_loop` + worker asyncio, `commercial_app/main.py:77-91`), e `si_app`/`tm_app` possuem padrão equivalente (middleware de `commercial-api` cita "como o Transformômetro"). A Sala futura herda um padrão real, não uma incógnita.

### 1.4. Decisão proposta — ADR-REQ-05

| Item | Decisão `PROPOSED` |
|---|---|
| Framework | **FastAPI + uvicorn[standard]** |
| Pacote | `engineering-api/engineering_app/` |
| Entrypoint | `engineering_app/main.py` → `app = FastAPI(title="Engineering API", root_path=settings.ENGINEERING_API_ROOT_PATH, redirect_slashes=False, lifespan=lifespan)`; CMD `python -m uvicorn engineering_app.main:app --host 0.0.0.0 --port 8000 --root-path /apps/engineering-api` |
| Estrutura | `engineering_app/{domain,application,infrastructure,interface,composition,middleware,startup,core}` — espelhando `commercial_app` reduzido ao mínimo; `interface/http/{routes,schemas}`; `infrastructure/{gateways,observability}` |
| Composition root | `engineering_app/composition/` (factories); wiring explícito em `main.py`/`lifespan`; DI leve — sem framework de DI novo |
| Config | `engineering_app/config.py` `Settings` + `_get_env` + `settings` singleton (padrão `commercial_app/config.py`) |
| Middleware | `engineering_app/middleware/auth_middleware.py` — wrapper `delpi_auth.middleware.fastapi_auth.jwt_middleware` com allowlist `/health`,`/ready` (+ variantes com root_path); **nenhuma** rota service-token em F1 |
| Erros | `engineering_app/core/responses.py` `ok()/fail()` + handlers `RequestValidationError→422`, `Exception→500`; sem stack/SQL/hostname em resposta |
| Observabilidade | `engineering_app/middleware/request_observability_middleware.py` (adaptação mínima do padrão api-delpi: operation_id, `X-Response-Time-Ms`, request id, log estruturado) |
| OpenAPI | FastAPI nativo; `docs_url=None, redoc_url=None` (padrão `si_app/main.py:80-82`) mantendo `/openapi.json` para consumidores de contrato; decisão sobre Swagger público pode ser revista |
| Health | `GET /health` (público, `{"status":"online","service":"engineering-api"}`) + `GET /ready` (degraded-aware; F1 sem DB → readiness sobre config/auth plumbing, não migração) |
| Deps | `requirements.txt` com pins explícitos (precedente `delpi-mes-api` `fastapi==0.118.0`); `pip install -e "/shared[fastapi]"` |
| Testes mínimos | `pytest.ini` (`pythonpath=.`, `testpaths=tests`); `tests/test_health.py`; `tests/test_auth_middleware.py` (401/403/503 com Core mockado); `tests/test_no_cross_context_imports.py` (arch test) |
| CI compat | `scripts/ci/audit_backend_boundaries.py`, `audit_fastapi_authz.py`, `audit_openapi_contracts.py`, `audit_architecture_phase3.py` — paths `**/*.py` já cobrem; verificar em F1 se algum gate exige registro explícito do serviço |

### 1.5. O que NÃO entra no bootstrap (anti-Abstraction-Gate)

- Nenhum `PLUGINS_DB_*`/`migrations/` em F1 (sem persistência — Sala é F-futura);
- nenhum scheduler/outbox/realtime hub (só quando existir consumer);
- nenhum gateway downstream concreto além do port/interface de `Core` (necessário ao `/ready`) — `api-delpi` adapters chegam em F2a (`/v1/home`);
- nenhum `service_token` bypass path (não há integração server-to-server em F1).

---

## 2. ADR-REQ-10 — Gateway, Docker e deployment

### 2.1. Evidência do padrão de infra

| Aspecto | Padrão provado | Evidência |
|---|---|---|
| Public path | `/apps/<svc>-api/` | `gateway/nginx.conf:465` (`/apps/commercial-api/`), `REQUESTS_API_ROOT_PATH=/apps/requests-api`, `TM_API_ROOT_PATH=/apps/transformometro-api` |
| Service name (compose) | `<svc>-api` | `commercial-api:`, `requests-api:`, `delia-api:` em `infra/docker-compose.yml` |
| Container name | `delpi-<svc>-api` | `delpi-commercial-api`, `delpi-requests-api`, `delpi-delia-api`, `delpi-transformometro-api` |
| Dockerfile | `<svc>-api/Dockerfile`, `python:*-slim`, `COPY shared /shared` + `pip install -e "/shared[fastapi]"`, `WORKDIR /app`, `EXPOSE 8000`, CMD uvicorn `--root-path` | `commercial-api/Dockerfile:1-19` |
| Compose block | `env_file: .env` + `environment:` explícito + `depends_on` condições + `healthcheck` python urllib `/health` + `logging json-file 10m/3` + `delpi-network` | `infra/docker-compose.yml` `requests-api:` |
| Healthcheck | `["CMD","python","-c","import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]`, interval 10s, timeout 5s, retries 6, start_period 30s | `infra/docker-compose.yml` requests-api block |
| Depends_on | `keycloak: service_started`, `postgres-plugins: service_healthy` (quando há DB), `core-api: service_started`, `api-delpi: service_healthy` (quando chama api-delpi) | commercial-api/requests-api blocks |
| Env vars | `PORT=8000`, `<SVC>_API_ROOT_PATH`, `PUBLIC_BASE_URL`, `JWT_SECRET: ${API_DELPI_JWT_SECRET}`, `KEYCLOAK_REALM/AUDIENCE/JWKS_URL/ISSUER`, `JWT_ALGORITHMS`, `LOG_LEVEL`, `TZ`, `CORE_API_URL: http://core-api:8000`, `DELPI_AUTH_CORE_API_URL`, `DELPI_API_CALLER_APP` | requests-api/commercial-api blocks |
| Nginx block | `location ^~ /apps/<svc>-api/ { limit_req zone=api_zone burst=50 nodelay; set $upstream_<svc>_api <svc>-api:8000; rewrite ^/apps/<svc>-api/?(.*)$ /$1 break; proxy_pass http://$upstream_<svc>_api; proxy_http_version 1.1; Upgrade/Connection; Host/X-Real-IP/X-Forwarded-For/X-Forwarded-Proto $delpi_proto; proxy_read_timeout 86400; proxy_buffering off; no-store cache headers; }` | `gateway/nginx.conf:465-486`; mesmo padrão em `gateway/nginx.dev.conf:358` |
| Dev compose | `<<: *plugin-profile` + mounts `../<svc>-api:/app` + `../shared:/shared` (live source) + mesmos env | `infra/docker-compose.dev.yml` `requests-api:` |
| Deploy | `./infra/scripts/up-prod-sequential.sh --build <svc>`; fases `core→chat→remote→mfe→api`; `FASE_API` é lista hardcoded de 21 serviços (`up-prod-sequential.sh:164-185`) | `infra/scripts/up-prod-sequential.sh` |
| Gateway reload | `infra/scripts/gateway-static-upstreams.sh` recarrega `delpi-gateway` após recriar serviço com `proxy_pass` estático; upstreams em variável (`set $upstream_*`) resolvem DNS em runtime mas o script continua sendo o mecanismo canônico de refresh | `infra/scripts/gateway-static-upstreams.sh` |
| DNS interno | services resolvem por service name (`commercial-api:8000`) e container name (`delpi-api-delpi:8000` — usado em `DELPI_API_URL`); ambos válidos na `delpi-network`, mas a convenção env→URL usa container name em alguns serviços e service name em outros — **inconsistência registrada** | `DELPI_API_URL: http://delpi-api-delpi:8000` vs `CORE_API_URL: http://core-api:8000` |

### 2.2. Decisão proposta — ADR-REQ-10

| Item | Decisão `PROPOSED` |
|---|---|
| Caminho público | `/apps/engineering-api/` (rewrite strip → `/`) |
| Service name (compose) | `engineering-api` |
| Container name | `delpi-engineering-api` |
| Dockerfile | `engineering-api/Dockerfile` — `python:3.11-slim` (convenção commercial/requests), `COPY shared /shared` → `pip install -e "/shared[fastapi]"`, CMD uvicorn com `--root-path /apps/engineering-api` |
| Nginx | novo bloco `location ^~ /apps/engineering-api/` em `gateway/nginx.conf` e `gateway/nginx.dev.conf`, espelhando o bloco commercial (upstream variável `engineering-api:8000`) |
| Compose prod | bloco `engineering-api:` em `infra/docker-compose.yml` — `env_file: .env`, envs canônicas, `depends_on: keycloak(started) + core-api(started)` (sem `postgres-plugins` em F1 — sem DB), healthcheck urllib `/health`, `delpi-network`, logging json-file |
| Compose dev | bloco espelhado em `infra/docker-compose.dev.yml` com `<<: *plugin-profile` + mounts `../engineering-api:/app` + `../shared:/shared` |
| Env vars previstas | `PORT=8000`, `ENGINEERING_API_ROOT_PATH=/apps/engineering-api`, `PUBLIC_BASE_URL`, `JWT_SECRET`, `KEYCLOAK_REALM/AUDIENCE/JWKS_URL/ISSUER`, `JWT_ALGORITHMS`, `LOG_LEVEL`, `TZ`, `CORE_API_URL=http://core-api:8000` (+ `DELPI_AUTH_CORE_API_URL` se o shared esperar esse nome — confirmar em F1), `SERVICE_NAME=engineering-api`, `CORE_API_TIMEOUT`. Futuras (não em F1): `ENGINEERING_RUN_MIGRATIONS_ON_STARTUP`, `DELPI_API_URL`, `PLUGINS_DB_*` |
| Health/readiness | `/health` liveness pública; `/ready` = degraded-aware sem DB em F1 (valida config carregada + auth plumbing); ambas no allowlist público do middleware |
| Init deps | `keycloak` (JWKS), `core-api` (effective RBAC) — `service_started`; sem `postgres-plugins` até DB existir |
| Deploy | adicionar `engineering-api` ao array `FASE_API` em `infra/scripts/up-prod-sequential.sh`; comando canônico `git pull --ff-only && ./infra/scripts/up-prod-sequential.sh --build engineering-api` em `srv-api` |
| Rollback | `git revert` do commit + rebuild/redeploy do serviço (imagem reconstruída do SHA anterior); sem migration/DB em F1 → rollback trivial; manifest Core: `POST /admin/apps/<id>/rollback` se registro existir |
| Smoke pós-deploy | `GET /apps/engineering-api/health` → 200 `{"status":"online"}`; `GET /apps/engineering-api/ready` → 200/degraded explícito; `GET /apps/engineering-api/` sem token → 401; `docker logs delpi-engineering-api` sem secret leak |

### 2.3. Arquivos exatos envolvidos (quando F1 for autorizada)

| Arquivo | Ação |
|---|---|
| `engineering-api/` (novo, todo) | criar |
| `gateway/nginx.conf` | + bloco `location ^~ /apps/engineering-api/` |
| `gateway/nginx.dev.conf` | + bloco espelhado |
| `infra/docker-compose.yml` | + service `engineering-api` |
| `infra/docker-compose.dev.yml` | + service espelhado |
| `infra/scripts/up-prod-sequential.sh` | + `engineering-api` em `FASE_API` |
| `infra/env.*.example` (se existir convenção) | documentar envs novas sem valores secretos — **verificar necessidade em F1** (serviços FastAPI não mantêm `env.example` local; só `delia-api` tem) |

Sem modificação nesta tarefa — tabela é contrato de execução futura.

---

## 3. Consequências

1. **FastAPI padroniza**: engineering-api entra na família de 18 serviços — middleware, CI audits (`audit_fastapi_authz`), observabilidade e OpenAPI saem quase de graça.
2. **`ARCHITECTURE.md` diverge** (pressupõe Flask): atualização documental proposta para F1 — não silenciosa.
3. **Sala futura destravada**: WS FastAPI provado em commercial-api elimina a dúvida P-05 do ponto de vista de framework (decisões funcionais P-01..P-04 continuam abertas).
4. **BFF assíncrono**: fan-out do `/v1/home` (F2a) favorece `httpx` async — já presente nas deps de commercial-api.
5. **Sem DB em F1**: readiness é sobre config+auth, não migration; `postgres-plugins` entra em `depends_on` só quando persistência existir.

## 4. Trade-offs aceitos

| Trade-off | Aceite |
|---|---|
| Assíncrono exige disciplina em gateways futuros | compensa pelo padrão dominante + BFF fan-out |
| `engineering.access` não existirá até manifest ser registrado | F1 prova AuthZ por harness (mocked Core), como delia-api — ver doc 06 |
| `docs_url=None` esconde Swagger | `/openapi.json` continua disponível para consumidores; decisão reversível |
| Inconsistência de naming interno (`delpi-api-delpi` vs service names) | engineering-api segue convenção container `delpi-engineering-api`, service `engineering-api`; URLs internas futuras devem preferir service name (consistente com `CORE_API_URL`) |

## 5. Responsáveis pela aprovação

- **EVA — Architecture / Coordination**: veredicto do gate (framework/naming/infra).
- **Product Owner**: confirmação para início de F1 (por `IMPLEMENTATION-PLAN.md`: nenhuma etapa é autorização automática).

## 6. Pendências

| ID | Item | Estado |
|---|---|---|
| ADR-REQ-05 | framework/estrutura | `PROPOSED` — aguarda aprovação |
| ADR-REQ-10 | gateway/Docker/deploy | `PROPOSED` — aguarda aprovação |
| DRIFT-01 | `ARCHITECTURE.md` pressupõe Flask | `DOCUMENTED` — corrigir em F1 com sancionar da Coordenação |
| ADR-REQ-02 | registro `engineering.access` / backend-only `engineering` | `PROPOSED` — ver doc 06 §6 |
| ADR-REQ-04 | contratos downstream `/v1/home` | `TO_INVENTORY` — F2a |
| ADR-REQ-03/09 | MCP/EVA | `NOT_READY` — fora de escopo G0 |
