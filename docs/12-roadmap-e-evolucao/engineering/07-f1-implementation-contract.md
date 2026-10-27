# F1 — Implementation Contract — engineering-api foundation

> **Documento:** `07-f1-implementation-contract.md`
> **Fase:** F1-G0 → contrato de execução para a futura F1 (nada implementado aqui)
> **BASE_HEAD:** `486831a025bfad52694a5aa0a0711dffc2340f95`
> **Requisito:** RQ-ENG-001 / AC-ENG-001
> **Precondição:** aprovação de ADR-REQ-05, ADR-REQ-10 e decisão Core AuthZ (docs 05 e 06) + pedido explícito do PO.

---

## 1. Escopo exato da F1

### Dentro

- Scaffold `engineering-api/` (FastAPI, `engineering_app` — ADR-REQ-05 `PROPOSED`).
- Bootstrap, configuração segura (`check_credentials`, `Settings`+envs).
- `GET /health` + `GET /ready` (públicas; ready = degraded-aware, **sem DB**).
- Autenticação JWT Keycloak via `delpi_auth` (middleware compartilhado).
- Integração efetiva Core AuthZ (plumbing `/me` + harness de teste com Core mockado).
- Tratamento padronizado de erros (`fail()` envelope; 401/403/422/500/503-semântica).
- Correlation/request id + logging estruturado (request observability mínimo).
- OpenAPI mínimo (`/openapi.json`; docs UI desabilitado — decisão ADR-REQ-05).
- Rota probe de autorização **TEST-only** (se aprovada) para provar 401/403/200 sem rotas de negócio.
- Infra: Dockerfile, bloco compose prod+dev, bloco nginx prod+dev, entrada em `FASE_API`.
- Correção documental de `ARCHITECTURE.md` (Flask→FastAPI) — sancionada pela Coordenação.

### Fora (não antecipar)

`GET /v1/home` e qualquer rota de negócio; DB próprio/migrations; Sala; LMPs; produtos/BOM; desenhos; IA/LLM; MCP; frontend; escritas; deploy de funcionalidades de negócio; registro Core de manifest (ver doc 06 §2.3); service tokens; realtime.

**Reconciliação com `01-foundation`:** o plano original (§4-F1, linhas 71–77) incluía port/gateway para primeira fonte + contrato read-only do Início já em F1. A Coordenação estreitou F1 ao bootstrap puro (este documento) — a composição do Início fica para F2a conforme `04-f0-implementation-readiness.md` §2. Registrado como decisão de escopo, não drift.

---

## 2. RQ/AC

**RQ-ENG-001 — Foundation engineering-api.**

**AC-ENG-001 (aceite):**
1. Serviço inicializável via compose (`docker compose up engineering-api` → healthy).
2. `GET /apps/engineering-api/health` → `200 {"status":"online","service":"engineering-api"}` público.
3. `GET /ready` → 200/`degraded` explícito conforme config carregada.
4. Rota protegida probe: sem token → 401; token inválido → 401; token válido sem permission → 403; Core mock → 200.
5. Erros em envelope `fail()`; sem stack/SQL/hostname/path físico.
6. Request log estruturado + `X-Operation-Id`/`X-Response-Time-Ms`.
7. `pytest` verde (health, auth ±, config, boundaries).
8. `audit_backend_boundaries`, `audit_fastapi_authz`, `audit_openapi_contracts`, `audit_architecture_phase3` limpos no diff.
9. Nenhuma chamada/import a `api-delpi`, `commercial_app`, `requests_app`, `delia`, `minha_delpi` (teste estrutural).
10. Zero rotas de negócio — OpenAPI expõe apenas health/ready (+probe TEST-only, se aprovada).

---

## 3. Estrutura proposta (ADR-REQ-05)

```text
engineering-api/
├── Dockerfile
├── README.md
├── env.example                      # placeholders públicos, sem secrets
├── pytest.ini                       # pythonpath=. / testpaths=tests
├── requirements.txt                 # pins explícitos (precedente delpi-mes-api)
├── engineering_app/
│   ├── main.py                      # FastAPI(), lifespan, routers, middleware, handlers
│   ├── config.py                    # Settings + _get_env + settings
│   ├── core/
│   │   └── responses.py             # ok()/fail() envelope
│   ├── middleware/
│   │   ├── auth_middleware.py       # wrapper delpi_auth + public allowlist
│   │   └── request_observability_middleware.py
│   ├── interface/http/
│   │   └── routes/
│   │       ├── health_routes.py     # /health, /ready
│   │       └── probe_routes.py      # TEST-only authz probe (se aprovada)
│   ├── application/                 # (ports quando necessário — não inflar)
│   ├── domain/                      # (vazio ou mínimo — sem regra ainda)
│   ├── infrastructure/
│   │   └── observability/
│   │       └── request_context.py   # contextvars (padrão api-delpi)
│   ├── composition/
│   │   └── root_composer.py         # wiring explícito
│   └── startup/
│       └── __init__.py              # (run_migrations só quando DB existir)
└── tests/
    ├── conftest.py                  # TestClient + mocks Core /me
    ├── test_health.py
    ├── test_auth_middleware.py      # 401/403/200/503-ish ±
    ├── test_config.py
    └── test_no_cross_context_imports.py
```

`domain/` e `application/` nascem quase vazios: F1 não tem regra de negócio; criar pastas completas sem conteúdo seria inflação de estrutura — incluir apenas `__init__.py` + README curto ou diferir até F2a (decisão de estilo, não de arquitetura).

## 4. Arquivos a criar / modificar

| Arquivo | Ação |
|---|---|
| `engineering-api/**` | criar (§3) |
| `gateway/nginx.conf` | + `location ^~ /apps/engineering-api/` (espelho commercial) |
| `gateway/nginx.dev.conf` | + bloco espelhado |
| `infra/docker-compose.yml` | + `engineering-api:` (ver doc 05 §2.2) |
| `infra/docker-compose.dev.yml` | + bloco com `<<: *plugin-profile` + mounts `/app`+`/shared` |
| `infra/scripts/up-prod-sequential.sh` | + `engineering-api` em `FASE_API` |
| `docs/12-roadmap-e-evolucao/engineering/ARCHITECTURE.md` | corrigir Flask→FastAPI (DRIFT-01) |
| `docs/12-roadmap-e-evolucao/engineering/04-f0-implementation-readiness.md` | atualizar ADR-REQ-05/10 → `READY_CONFIRMED` |

Não modificar: qualquer arquivo de `api-delpi`, Core, plugins, manifests, migrations, secrets.

## 5. Sequência de execução (bounded steps)

```text
F1.S1 scaffold + health        → engineering-api/{Dockerfile,requirements,engineering_app/main,config,core/responses,health_routes} + test_health
F1.S2 auth plumbing            → middleware/auth_middleware + delpi_auth + test_auth_middleware (401/403/mock)
F1.S3 erros + observabilidade  → responses/handlers + request_observability + context
F1.S4 probe TEST-only authz    → rota protegida de teste + positive/negative/sibling (se aprovada pela Coordenação; caso contrário evidência por harness puro)
F1.S5 infra wiring             → Dockerfile final + compose prod/dev + nginx prod/dev + FASE_API
F1.S6 smoke local              → compose up + /health via gateway dev + logs sem secrets
F1.S7 docs + gates             → ARCHITECTURE.md fix + CI audits + residual search
```

Cada `F1.S*` segue `plan-execution.mdc` — revalidar antes de executar; drift interrompe o subgrafo.

## 6. Testes

| Camada | Testes |
|---|---|
| Unit | config defaults; `check_credentials` fail-closed; envelope `fail()` |
| Middleware | public paths; 401 sem token; 401 token inválido; 200 token válido (mock validator+Core); 403 sem permission (probe); Core-down → fail-closed |
| Smoke | `/health` 200; `/ready` 200/degraded; OpenAPI schema gera |
| Boundaries | `test_no_cross_context_imports` (AST scan) |
| Contrato | `/openapi.json` válido; operationIds `get_engineering_health`, `get_engineering_ready` |
| CI | `audit_backend_boundaries`, `audit_fastapi_authz`, `audit_openapi_contracts`, `audit_architecture_phase3`, `audit_platform_guardrails` |

## 7. Gates

- [ ] ADR-REQ-05 + ADR-REQ-10 aprovados (este G0)
- [ ] PO autoriza F1 explicitamente
- [ ] Decisão doc 06 §2.3 (registro: adiar a F3a **ou** backend-only `engineering` v0.1.0)
- [ ] `DELPI_AUTH_CORE_API_URL` vs `CORE_API_URL` confirmado no shared antes do compose
- [ ] Status Core-down exato confirmado em `fastapi_auth.py`
- [ ] Probe TEST-only aprovada ou substituída por harness

## 8. Segurança

- Sem secrets no repo; `env.example` só placeholders; `.env` real em `infra/` (já existente, não commitado).
- `check_credentials()` fail-fast no lifespan.
- JWT: sem validação local ad-hoc — só `delpi_auth`.
- Nenhuma rota de negócio → superfície = health/ready (+probe gated).
- Erros não vazam internals; logs não incluem Bearer.
- `redirect_slashes=False` + `root_path` correto atrás do gateway (precedente commercial).

## 9. Observabilidade

- `logging.basicConfig` padrão (`%(asctime)s [%(levelname)s] %(name)s: %(message)s`).
- Startup log: `engineering_api_started service=engineering-api version=... env=...` (padrão delia-api).
- Request log: `engineering_api_request method=... path=... status=... operation_id=... duration_ms=...` + `X-Response-Time-Ms`.
- Request/correlation id propagado se presente (`X-Request-Id` ou equivalente — confirmar convenção exata do repo em F1.S3).

## 10. Deploy / rollback

- Deploy: `ssh srv-api` → `git pull --ff-only` → `./infra/scripts/up-prod-sequential.sh --build engineering-api` (adicionar a `FASE_API` antes).
- Gateway: `gateway-static-upstreams.sh` cuida do reload de `delpi-gateway`.
- Rollback: `git revert` + rebuild do serviço no SHA anterior (sem DB → trivial); manifest Core não existe ainda → nada a reverter lá.
- Smoke pós-deploy: health/ready via `/apps/engineering-api/*`; 401 sem token em qualquer rota não pública.

## 11. Residuals de F1 previstos

| Residual | Tratamento |
|---|---|
| `engineering.access` inexistente até registro do manifest | probe/harness prova plumbing; registro na decisão doc 06 §2.3 |
| Status Core-down (401 vs 503) | confirmar no código; alinhar com fail-closed canônico |
| Naming URL interna (`delpi-api-delpi` vs service name) | seguir service name em envs novas |
| `domain/`/`application/` quase vazias em F1 | intencional — crescem com F2a |
| Sem persistência/scheduler/outbox | intencional — Sala/state futuras |

## 12. Postconditions de F1 (quando executada)

1. `origin/main` contém `engineering-api/` + diffs de infra documentados.
2. `docker compose up engineering-api` → healthy; `/apps/engineering-api/health` 200 via gateway.
3. `pytest` verde; CI audits limpos no diff.
4. Nenhuma rota de negócio; nenhum manifest/permission criado; nenhum bypass de Domain API.
5. `EVA EXECUTION REPORT` da F1 com SHA, outcome evidence, residuals.

## 13. Próximo bounded step

`F1.S1` — scaffold + health — **somente** após: veredicto `ACCEPT`/`ACCEPT_WITH_RESIDUAL` deste G0 + autorização explícita do PO + decisão doc 06 §2.3. Este documento não autoriza execução.
