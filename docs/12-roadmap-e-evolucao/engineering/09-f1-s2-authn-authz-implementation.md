# F1.S2 — Engineering API AuthN/AuthZ — Registro de Execução

> **Documento:** `09-f1-s2-authn-authz-implementation.md`
> **Fase:** F1.S2 — fundação de autenticação/autorização corporativa
> **BASE_HEAD:** `5c70eed4dbe2edc9d5a82ab2ee2c06f83e162b43` (`origin/main` na reancoragem;
> `origin/main` avançou para `d0ba78f5e9b2` antes do commit — rebase + revalidação registrados)
> **Autorização:** Coordenação EVA — F1.S2 ONLY (Keycloak + Core AuthZ + `delpi_auth`; sem F1.S3/S5, Portal ou MCP)
> **Decisões consumidas:** `05-f1-g0-architecture-decisions.md`, `06-f1-g0-core-authz-contract.md`,
> `07-f1-implementation-contract.md`, scaffold de `08-f1-s1-engineering-api-bootstrap.md`

---

## 1. Objetivo

Integrar `engineering-api` ao mecanismo oficial de autenticação/autorização da plataforma:

- **Keycloak** emite e assina o JWT — `engineering-api` valida assinatura, issuer, audience e claims mínimos via `delpi_auth.jwt_validator` (JWKS, RS256).
- **Core API** permanece autoridade efetiva: permissões do usuário vêm de `GET /me` na Core — nunca de claims do JWT.
- **`shared/delpi_auth`** é a única implementação de middleware, resolução de contexto, cache RBAC e decoradores de autorização.
- **`engineering-api`** apenas consome: wrapper de allowlist pública + `require_any_permission` nas operações futuras.

Nenhum sistema paralelo de permissões foi criado. Nenhuma tabela, catálogo ou endpoint de RBAC foi adicionado.

## 2. Ownership — invariante preservada

| Responsabilidade | Owner | Implementação nesta etapa |
|---|---|---|
| Identidade, SSO, emissão de JWT | Keycloak | validação via JWKS/issuer/audience (`delpi_auth`) |
| Catálogo de apps, permissões, vínculos, RBAC | Core API | `GET {CORE_API_URL}/me` com Bearer do usuário |
| Middleware e mecanismos compartilhados | `shared/delpi_auth` | `middleware/fastapi_auth.py`, `jwt_validator.py`, `authorization.py`, `credential_guard.py`, `service_token.py` |
| Autorização das operações de Engenharia | owner da operação | `require_any_permission(["engineering.access"])` — provado no harness de testes |
| Composição de dados do Portal | `engineering-api` | nenhuma rota de negócio nesta fase |

`engineering.access` segue **TARGET aprovado, ainda não registrado** — decisão de registro via manifest futuro de `plugins/engineering` permanece (doc 06 §2.3). O código aparece somente como constante de contrato nos testes.

## 3. O que foi implementado

### 3.1. Middleware (`engineering_app/middleware/auth_middleware.py`)

Wrapper mínimo no padrão `commercial_app/middleware/auth_middleware.py`:

```python
async def jwt_middleware(request, call_next):
    if _is_engineering_public_path(request.url.path):
        return await call_next(request)
    return await _base_jwt_middleware(request, call_next)
```

Allowlist pública — idêntica em intenção ao padrão commercial:

- `is_public_path(path)` do `delpi_auth` (`/health`, `/apps/<svc>/health`, `/docs`, `/redoc`, `/openapi.json`);
- `/ready` e `/ready` com root_path (`/apps/engineering-api/ready`) — adição explícita como no commercial;
- variante `/apps/engineering-api/health` — já coberta pelo `_is_root_health_path` da lib e reforçada localmente.

Todo o resto delega para `delpi_auth.middleware.fastapi_auth.jwt_middleware`, que:

1. verifica service token interno (`X-Delpi-Service-Token`/`Authorization` vs `API_DELPI_INTERNAL_SERVICE_TOKEN`) — mecanismo canônico server-to-server;
2. exige `Authorization: Bearer <jwt>` — ausente/malformado → `401 {"detail":"Unauthorized"}`;
3. `validate_token()` — assinatura JWKS, issuer, audience, expiração; claims `sub`/`email` obrigatórios;
4. `load_user_rbac(token)` — `GET {CORE_API_URL}/me` com o Bearer do usuário;
5. falha na Core → fallback `_rbac_from_claims(..., rbac_unavailable=True)` com `permissions=[]`;
6. publica `SimpleNamespace` em `request.state.user` + `ContextVar` (`request_context`);
7. `map_authz_exception` traduz exceções canônicas: `"Unauthorized"→401`, `"Forbidden"→403`, `"Service Unavailable"→503`.

### 3.2. Lifespan (`engineering_app/main.py`)

```python
missing = settings.missing_auth_envs()        # KEYCLOAK_ISSUER, KEYCLOAK_AUDIENCE
if missing:
    raise RuntimeError("engineering-api auth configuration incomplete — ...")
check_credentials()                            # LGPD Art. 46 — strict em APP_ENV=production
```

Fail-fast no startup: sem `KEYCLOAK_ISSUER`/`KEYCLOAK_AUDIENCE` o processo não sobe. Credenciais fracas em produção abortam o boot.

### 3.3. Configuração (`engineering_app/config.py`)

Envs expostos para readiness/boot — **a `delpi_auth` lê os mesmos nomes diretamente** (não há config paralela):

| Env | Default | Uso real na `delpi_auth` |
|---|---|---|
| `KEYCLOAK_ISSUER` | — (obrigatório) | `jwt_validator` — `iss` |
| `KEYCLOAK_AUDIENCE` | — (obrigatório) | `jwt_validator` — `aud` |
| `KEYCLOAK_JWKS_URL` | OIDC discovery via `KEYCLOAK_URL`/`KEYCLOAK_REALM` | `jwt_validator._get_jwks` |
| `KEYCLOAK_URL` / `KEYCLOAK_REALM` | `http://keycloak:8080/auth` / `delpi` | discovery fallback |
| `JWT_ALGORITHMS` | `RS256` | `jwt_validator` |
| `DELPI_AUTH_CORE_API_URL` → `CORE_API_URL` | `http://core-api:8000` | `load_user_rbac` (precedência na ordem) |
| `DELPI_AUTH_RBAC_TIMEOUT_SECONDS` | `5.0` | timeout do GET /me |
| `DELPI_AUTH_RBAC_CACHE_TTL_SECONDS` | `60` | fresh cache |
| `DELPI_AUTH_RBAC_STALE_TTL_SECONDS` | `900` | janela stale |

### 3.4. Readiness (`health_routes.py`)

`GET /ready` agora inclui `"auth_configured": bool` — presença das envs obrigatórias, **sem** chamada à Core/Keycloak (healthcheck não deve custar round-trip nem vazar segredos). Semântica honesta: autoridade indisponível se manifesta por request, fail-closed no middleware.

### 3.5. Dependências e Dockerfile

- `requirements.txt`: `+ python-jose[cryptography]==3.5.0`, `requests==2.34.2`, `pytest-asyncio==1.4.1`.
- `Dockerfile`: `COPY shared /shared` + `pip install -e "/shared[fastapi]"` — mecanismo canônico do monorepo (mesmo padrão das APIs que consomem `delpi_auth`); contexto de build = raiz do repo.
- Sem Redis/Postgres/infra adicional.

## 4. Cache RBAC e política de indisponibilidade (contrato real observado)

`load_user_rbac` (`delpi_auth.middleware.fastapi_auth`):

- Chave de cache: `sha256(token)` — nunca o token em claro.
- Fresh TTL 60s; stale TTL 900s; lock por token evita thundering herd.
- **Stale fallback:** se a Core falha (timeout/erro HTTP/5xx→`RuntimeError`) dentro da janela stale, o último `/me` em cache é servido — política oficial de disponibilidade degradada.
- **`force_refresh=True`** (disponível para escritas sensíveis futuras): desativa fresh+stale — falha propaga (fail-closed para autorização material).
- Cache miss + Core indisponível → exceção → middleware cai no fallback `rbac_unavailable=True` com `permissions=[]` → `require_*` mapeia para `503 {"detail":"Authorization service unavailable"}` via `map_authz_exception`.

## 5. Semântica de erros observada

| Cenário | Resposta real | Mecanismo |
|---|---|---|
| Sem `Authorization` | `401 {"detail":"Unauthorized"}` | middleware |
| Header malformado / `Bearer` vazio / não-JWT | `401` | middleware |
| JWT expirado | `401 {"detail":"Invalid token"}` | `jwt_validator` |
| Assinatura inválida (chave errada) | `401` | `jwt_validator` + retry de JWKS |
| `iss`/`aud` incompatível | `401` | `jwt_validator` |
| `sub`/`email` ausentes | `401 {"detail":"Invalid token claims"}` | middleware |
| Claims JWT carregando `permissions`/`is_superadmin`/`roles` | ignorados para autorização | `_rbac_from_claims` zera permissions |
| Identidade válida, sem permissão efetiva | `403 {"detail":"Forbidden"}` | `require_any_permission` + `map_authz_exception` |
| Permissão de app irmão (`dashboard-*.view`) | `403` | idem |
| `is_superadmin` da Core = true | acesso concedido | bypass oficial |
| Core indisponível sem cache | `503 {"detail":"Authorization service unavailable"}` | `rbac_unavailable` → `_deny_missing_permission` |
| Core indisponível com stale válido | último `/me` conhecido | política oficial stale |
| Erro inesperado autenticado | `500 {"detail":"Internal server error"}` | middleware |

Nenhum status HTTP foi forçado localmente — o comportamento é o da biblioteca compartilhada.

## 6. Harness de testes (isolamento garantido)

`tests/conftest.py` monta um `FastAPI` **separado** com `/probe` e `/probe/whoami` protegidos por `require_any_permission(["engineering.access"])` — o mesmo mecanismo das rotas futuras. A rota:

- não existe no app produtivo;
- não aparece no `openapi.json` de produção (teste dedicado);
- não vai para gateway/manifest.

JWT de teste: par RSA gerado em runtime, JWKS fake injetado via monkeypatch em `_get_jwks` — o decode percorre o caminho real do `python-jose` (assinatura real, issuer/audience/claims reais). Core `/me` mockado por `load_user_rbac` controlado.

## 7. Testes — 49 passing

`~/venvs/engapi/bin/python -m pytest` (Python 3.12, pins de `requirements.txt` + `shared[fastapi]` editable):

| Área | Cobertura |
|---|---|
| `test_auth_middleware.py` (22) | permissão efetiva→200; sem permissão→403; permissão sibling→403; claims JWT não autorizam→403; superadmin Core→200; ausente/malformado/expirado/assinatura/iss/aud/claims→401; Core down/erro→503; rotas públicas; variantes root_path; não-público→401; probe fora do OpenAPI; service token não bypassa sem env; service token configurado→principal `service` (comportamento canônico documentado); contexto não vaza entre requests |
| `test_rbac_resolution.py` (7) | sucesso+cache hit; non-200→raise; timeout sem cache→raise; stale serve cache; `force_refresh` fail-closed; stale expirado→raise; service token sem env→falso |
| `test_startup.py` (3) | lifespan fail-fast sem envs; startup OK com envs; credencial fraca em produção→`RuntimeError` |
| `test_health.py` (6) | regressão F1.S1 — contratos intactos |
| `test_config.py` (6) | defaults, override, log level, sem atributos secret-like, `missing_auth_envs`, precedência `DELPI_AUTH_CORE_API_URL` |
| `test_architecture.py` (3) | sem imports cross-context, sem deps proibidas, sem camadas prematuras (`middleware/` removido da lista — camada real agora) |

Smoke real: `uvicorn engineering_app.main:app` com envs → `/health` 200, `/ready` 200 (`auth_configured:true`), `/v1/anything` 401, `/openapi.json` 200.

## 8. Achados e residuais

1. **Service token → superadmin.** `request_has_valid_internal_service_token` minta `principal_type="service"`, `is_superadmin=True` — comportamento canônico para server-to-server, **não** bypass da Engenharia. Rotas futuras de dados de usuário devem exigir `principal_type == "user"` conforme docstring da própria lib. Registrado; nenhuma alteração local criada.
2. **Stale cache pode autorizar com dados antigos** (até 900s) — política oficial de degradação da plataforma; `force_refresh=True` existe para escritas sensíveis. Nenhuma divergência do contrato.
3. **Core-down sem cache → 503** (`rbac_unavailable` → `Service Unavailable`) — fail-closed confirmado; resolve o `TO_INVENTORY` pendente da F1.S1.
4. **`/openapi.json` permanece público** — decisão canônica da lib (`is_public_path` inclui a spec técnica); o schema só contém `/health`+`/ready`, sem segredos.
5. `pytest.ini` ganhou `asyncio_mode = auto` (precedente api-delpi) para os testes async do RBAC resolution.

## 9. Limitações declaradas

- Nenhuma rota de negócio existe — autorização provada apenas via harness; a aplicação em rotas reais vem com o primeiro use case.
- Docker build: `TEST_NOT_RUN` (sem daemon no ambiente); Dockerfile verificado estruturalmente contra o padrão commercial.
- `engineering.access` não registrado na Core — deliberado (doc 06 §2.3); o harness usa a string apenas como contrato.
- `check_credentials` strict depende de `APP_ENV`; em `development` apenas warnings.
- Nenhum deploy: gateway/Compose/FASE_API são F1.S5.

## 10. Próximo bounded step

F1.S3 — observabilidade de request estruturada (correlation id, logs, métricas) — somente mediante autorização da Coordenação.

---

## 11. F1.S2R1 — Security Rework / Strict Public Path Matching

> **SHA da correção:** registrado neste documento após push (ver §11.8).
> **Veredicto que originou o rework:** REWORK — bypass potencial na allowlist pública.

### 11.1. Problema original e causa-raiz

A classificação de caminho público usava matching por sufixo:

```python
return normalized.endswith(_PUBLIC_SUFFIXES)
# _PUBLIC_SUFFIXES = ("/engineering-api/health", "/engineering-api/ready")
```

`endswith` aceita qualquer prefixo arbitrário — `/qualquer-prefixo/engineering-api/health` era classificado como público e dispensava JWT. O mesmo risco se aplicaria a qualquer rota futura que terminasse com os sufixos. Causa-raiz: matching aproximado onde o contrato exige comparação exata.

### 11.2. Risco de bypass

- Caminhos fora do contrato classificados como públicos → ausência de autenticação.
- Rotas futuras criadas sob prefixos arbitrários com sufixo coincidente herdariam o bypass silenciosamente.

### 11.3. Contrato de caminhos públicos

```text
/health
/ready
/apps/engineering-api/health
/apps/engineering-api/ready
/docs, /redoc, /openapi.json   (política canônica de docs, paths exatos)
```

Somente comparação exata após `normalize_path` (strip de query + trailing slash).

### 11.4. Correção aplicada

`engineering_app/middleware/auth_middleware.py`:

- `_PUBLIC_SUFFIXES`/`endswith` removidos → `_PUBLIC_PATHS` (frozenset) + `normalize_path(path) in _PUBLIC_PATHS`.
- **`is_public_path` compartilhada é mais ampla que o contrato** — aceita `*/docs`, `*/redoc`, `*/openapi.json` de qualquer prefixo, `/apps/<qualquer-svc>/health` e `*/api-delpi/health`. Como o middleware base re-executa essa checagem internamente, delegar diretamente reintroduziria o bypass para esses caminhos. Solução: paths que a lib considera públicos mas que não estão na allowlist da Engenharia passam pelo fluxo completo de autenticação do base — o `scope["path"]` é mascarado apenas durante a avaliação do middleware compartilhado e restaurado antes de `call_next` (roteamento vê o path real). Nenhuma linha de JWT foi reimplementada; `shared/delpi_auth` não foi modificada (a política ampla é a decisão canônica para as demais APIs — engenharia apenas a restringe para o próprio contexto, conforme diretriz do rework).

### 11.5. Testes negativos adicionados (32 novos → 81 total)

`test_auth_middleware.py`:

- Prefixos arbitrários → 401: `/qualquer-prefixo/...`, `/fake/apps/...`, `/v1/home`, `/v1/health`, `/engineering-api/health` (sem `/apps`), `/health/extra` e variantes, `/xapps/...`, `/appsx/...`, `/apps/engineering-apix/health`.
- Caminhos que a lib compartilhada aceitaria → 401: `/foo/docs`, `/x/redoc`, `/x/openapi.json`, `/apps/commercial-api/health`, `/x/api-delpi/health`.
- Dupla barra `//health`, `/apps//engineering-api/health` → 401.
- Trailing slash `/health/`, `/ready/`, `/apps/engineering-api/health/` → público e 404 (redirect_slashes=False).
- Encoding `/he%61lth` → resolve para `/health` (200) — é a rota canônica.
- Segmentos `/./health`, `/x/../health` → normalizados pelo transporte para `/health` (200) — não é bypass.
- Query string `/health?foo=bar` → 200; `/v1/anything?x=/health` → 401.
- Rota desconhecida `/nonexistent-route` → 401.
- Unit: `_is_engineering_public_path` — conjunto exato positivo/negativo.

Para cada caso negativo a prova é `401` (middleware exigiu Bearer antes do roteamento), não `404`.

### 11.6. Regressão

Suíte completa: **49 anteriores + 32 novos = 81 passed** (SHA da correção, Python 3.12, pins + `shared[fastapi]`). Autorização Core, JWT, stale/force_refresh, startup fail-fast, health/readiness e OpenAPI intactos.

### 11.7. Residuais

- ~~O mascaramento de `scope["path"]` existe apenas para forçar o fluxo de auth da lib sobre paths que a política compartilhada ampla aceitaria~~ — **RESOLVIDO na F1.S4** (`11-f1-foundation-completion.md` §2.1): `shared/delpi_auth` passou a aceitar `public_path_checker` opcional por chamada (backward-compatible, default intacto) e o wrapper da Engenharia delega o predicado estrito sem tocar o request. Nenhuma mutação de `scope["path"]` permanece.
- A política ampla da lib permanece inalterada (owner: `shared/delpi_auth` + demais consumidores) — a restrição segue sendo uma decisão do consumidor, agora via contrato explícito.

### 11.8. Resultado

Correção publicada em `main` — commit e SHA finais no EVA EXECUTION REPORT da F1.S2R1.
