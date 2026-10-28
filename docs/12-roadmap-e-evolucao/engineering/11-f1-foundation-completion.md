# F1-FINAL — Engineering API Foundation Completion — Registro de Execução

> **Documento:** `11-f1-foundation-completion.md`
> **Escopo autorizado:** F1.S4 (segurança/testes) + F1.S5 (infra) + F1.S6 (integração) + F1.S7 (fechamento)
> **BASE_HEAD:** `93ded7d59355b2265fcb08d257e146a3e34ed739` (`origin/main` na reancoragem)
> **Baseline de referência:** `c862172662` (F1.S3, ancestral ✓)
> **Estado anterior:** F1.S3 — implementada; F1.S2R1 `ACCEPT_WITH_RESIDUAL` (residual resolvido nesta fase)

---

## 1. Resumo executivo

| Gate | Resultado |
|---|---|
| S4 — Segurança e observabilidade | **PASS** |
| S5 — Infraestrutura canônica | **PASS** |
| S6 — Build, integração e smoke | **PASS** (Docker/nginx/compose validados com daemon real) |
| S7 — Documentação e evidências | **PASS** |
| Deploy produtivo | executado via fluxo canônico `AGENTS.md` (evidência §9) ou `PENDING` conforme relatório |

## 2. F1.S4 — Segurança consolidada

### 2.1. Residual S2R1 resolvido — sem mutação de `scope["path"]`

`shared/delpi_auth` evoluída com extensão neutra e backward-compatible:

```python
async def jwt_middleware(request, call_next,
                         public_path_checker: Callable[[str], bool] | None = None):
    is_public = public_path_checker if public_path_checker is not None else is_public_path
```

- `None` → política default canônica da lib — **zero mudança** para os ~16 consumidores existentes (todos chamam `jwt_middleware(request, call_next)` posicional).
- Engineering passa `_is_engineering_public_path` (frozenset exact-match pós `normalize_path`) — a política ampla do shared nunca se aplica e o request nunca é mutado. Wrapper agora tem 4 linhas efetivas.
- Testes shared novos (`test_jwt_middleware_public_path_checker.py`): default intacto, checker restringe paths amplos → 401, `scope["path"]` nunca alterado, contrato global `is_public_path` preservado.

### 2.2. Allowlist final (contrato público)

`/health`, `/ready`, `/apps/engineering-api/health`, `/apps/engineering-api/ready`, `/docs`, `/redoc`, `/openapi.json` — somente exatos. Todos os negativos S2R1 + novos (`/foo/docs`, `/x/openapi.json`, `/apps/commercial-api/health`, prefixos falsos, `/v1/health`) → **401**, provando exigência de JWT (não 404).

### 2.3. Core AuthZ preservada

Sem nenhuma alteração em resolução `/me`, cache (fresh/stale/`force_refresh`), decorators ou autoridade. `engineering.access` permanece permission code alvo **não registrado** — registro pertence ao manifest futuro governado pela Core.

### 2.4. Service principals

Contrato canônico `delpi_auth` mantido: `principal_type="service"` vs `"user"`. Novos testes provam: service token válido → `principal_type=service`, `email=service@delpi.internal` (nunca confundido com humano); header arbitrário sem env configurada → 401. Writes futuras exigem `principal_type="user"` — documentado, sem rota de negócio criada.

### 2.5. Observabilidade — logging seguro e 500s

- **`path` do log = template da rota resolvida** (`/probe/items/{item_id}`), nunca o path real — identificadores de recursos e paths arbitrários têm cardinalidade zero em logs; unmatched → `unmatched_route`.
- **500s instrumentados:** exceções não capturadas por boundaries internos (rotas públicas, pré-roteamento) eram convertidas pelo `ServerErrorMiddleware` — fora do middleware, sem headers. Agora o middleware de observabilidade converte exceções propagadas em resposta 500 com envelope canônico `fail()` + `X-Request-Id` + `X-Operation-Id` + `X-Response-Time-Ms`, logando `error_class` + traceback server-side (`exc_info`). Exceções dentro do boundary de auth continuam no contrato `{"detail": ...}` do `delpi_auth` — ambos instrumentados.
- **Concorrência real:** `httpx.AsyncClient` + `asyncio.gather` com requests sobrepostos (`await asyncio.sleep` no handler) — request ids, emails e `principal_type` isolados; contexto limpo após o lote e após exceção.

## 3. F1.S5 — Infraestrutura canônica

| Arquivo | Mudança |
|---|---|
| `gateway/nginx.conf` | bloco `location ^~ /apps/engineering-api/` — upstream `engineering-api:8000`, rewrite strip prefix, headers X-Forwarded-*, `proxy_read_timeout 300`, no-store, `limit_req api_zone` |
| `gateway/nginx.dev.conf` | bloco equivalente dev (`$scheme`) |
| `infra/docker-compose.yml` | serviço `engineering-api` / container `delpi-engineering-api`: build local, envs auth canônicos via `.env`, `DELPI_AUTH_*` tunables, healthcheck `urllib /health` (10s/5s/6/30s), `depends_on` keycloak+core-api (`service_started`), logging json-file, `delpi-network`. Sem DB, volumes, workers |
| `infra/docker-compose.dev.yml` | mesmo serviço + `<<: *plugin-profile`, mounts `../engineering-api:/app` e `../shared:/shared`, `APP_ENV: development` |
| `infra/scripts/up-prod-sequential.sh` | `engineering-api` incluído em `FASE_API` |

Sem secrets em código/config — somente referências `${VAR}` governadas pelo `.env` da plataforma.

## 4. F1.S6 — Validação executada (evidência real)

| Verificação | Comando / evidência | Resultado |
|---|---|---|
| Suíte engineering | `python -m pytest` @ SHA final | **128 passed** (113 anteriores + 15 novos) |
| Shared lib | `pytest shared/delpi_auth/tests` | **94 passed** (inclui 4 novos do checker) |
| Consumidores | travel-expenses `test_auth_middleware` 3✓, cec 3✓, api-delpi observability 1✓ | **PASS**; transformometro/controllership: `TEST_NOT_RUN` (venv local sem `psycopg` — limitação de ambiente, não regressão) |
| Compose | `docker compose -f docker-compose.yml config --quiet` = 0; idem dev = 0 | **PASS** |
| Docker build | `docker build -f engineering-api/Dockerfile` | **PASS** (imagem construída) |
| Container startup | `docker run` + envs dev → `engineering_api_started`, `/health` 200 via urllib | **PASS** |
| Nginx | `nginx -t` (imagem nginx:alpine, rede com aliases) prod + dev | **PASS** |
| Gateway smoke E2E | nginx prod real → `/apps/engineering-api/health` 200 + `x-request-id` + `x-operation-id`; `/ready` JSON; `/v1/nonexistent` → 401 sem JWT; `/apps/fake/engineering-api/health` → 404 | **PASS** |
| Fail-closed | path protegido sem JWT → 401 através do gateway | **PASS** |
| Keycloak/Core reais | sem ambiente autorizado / permissão `engineering.access` não registrada | **PENDING** — plumbing provado com JWT RS256 real (suite) |

## 5. Contratos HTTP finais

- `GET /apps/engineering-api/health` → `{"status":"online","service":"engineering-api"}` + headers de observabilidade.
- `GET /apps/engineering-api/ready` → ready + `auth_configured`.
- Qualquer outro path sem JWT válido → `401` (`{"detail":"Unauthorized"}`).
- `openapi.json` público expõe somente `/health` e `/ready`.

## 6. Residuais e pendências

- `engineering.access` sem registro na Core → autorização efetiva `PENDING` até manifest do app `engineering`.
- Métricas/tracing (Prometheus/OTel) — `TO_INVENTORY`, não autorizado nesta fase.
- Propagação downstream de `X-Request-Id` quando domain gateways forem criados (`get_request_id()` disponível).
- Dois envelopes de 500 coexistem por boundary (delpi `{"detail"}` interno vs `fail()` canônico na borda) — ambos instrumentados e documentados; uniformização exigiria decisão transversal.

## 7. Próximo bounded step

F2 conforme roadmap — rotas de negócio/manifest `engineering` sob nova autorização da Coordenação. Não iniciada automaticamente.
