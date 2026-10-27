# F1-G0 — Contrato Core AuthZ — engineering-api

> **Documento:** `06-f1-g0-core-authz-contract.md`
> **Fase:** F1-G0 (somente documentação; nenhum seed/permissão/manifest executado)
> **BASE_HEAD:** `486831a025bfad52694a5aa0a0711dffc2340f95`
> **Escopo:** mecanismo canônico de registro, permission code, contrato AuthN/AuthZ do bootstrap, comportamento de falha, testes.

---

## 1. Mecanismo canônico de registro de app/permissões (PROVEN)

### 1.1. Endpoint e fluxo

```text
POST /core-api/admin/apps/register
Authorization: Bearer <JWT com apps.manage>
Body: manifest JSON (schemaVersion 1.0.0)
```

`core-api/app/interfaces/http/apps_controller.py:207-228` — `register_plugin()` → `RegisterPluginUseCase` (`core-api/app/application/use_cases/register_plugin_use_case.py`):

```text
ManifestValidator.validate_manifest_rules
→ plugins.create(build_app_create_payload)      [apps]
→ plugin_manifests.save(manifest, checksum)      [app_manifests]
→ plugin_versions.create                         [app_versions]
→ PluginPermissionSyncService.normalize_desired
→ plugin_permissions.sync_module(plugin_id, …)   [permissions, module=plugin_id]
→ plugin_routes.bulk_create(routes[])            [routes]
→ AdminChangedEvent (Portal recarrega apps)
```

Operações relacionadas (mesmo controller):

| Endpoint | Uso |
|---|---|
| `PUT /admin/apps/<id>/manifest` | mudanças não-estruturais (nome, descrição, ícone) |
| `POST /admin/apps/register` (nova versão) | mudanças estruturais — permissions, basePath, type, backend contract |
| `DELETE /admin/apps/<id>` | unregister (bloqueado por `dependencies` de outros plugins) |
| `POST /admin/apps/<id>/rollback` | rollback de versão (restaura manifesto + re-sincroniza permissions) |

Script canônico por plugin: `plugins/<id>/scripts/register-manifest.sh` (padrão verificado em `plugins/commercial`, `plugins/delia`, `plugins/auditoria-5s`, `plugins/cipa`, etc.) — `curl -X POST $BASE_URL/core-api/admin/apps/register -H "Authorization: Bearer $TOKEN"` com JWT `apps.manage`/superadmin.

### 1.2. Regras do manifesto (`core-api/app/domain/plugins/manifest_rules.py`)

| Regra | Detalhe | Linha |
|---|---|---|
| `PLUGIN_ID_RE` | `^[a-z0-9]+(?:-[a-z0-9]+)*$` — `engineering`, `engineering-api` válidos | :13 |
| `PERMISSION_CODE_RE` | `^[a-z][a-z0-9-]*\.[a-z0-9-]+(?:\.[a-z0-9-]+)*$` — `engineering.access` válido (≥2 partes) | :14-16 |
| `permission_module_mismatch` | `permissions[].module` **deve** ser igual ao `id` do plugin | :127-129 |
| `route_permission_not_declared` | `routes[].permission` deve existir em `permissions[].code` | :202-207 |
| `missing_access_permission` | recomendação forte: `<plugin_id>.access` para backend-only | :278-284 |
| `backend-only` | `type:"backend-only"` exige `backend.required=true`, `validateJwt` definido, `entry:null`, `routes:[]`, sem `ui`, ≥1 permission; `issuer`/`audience` obrigatórios se `validateJwt=true` | `docs/05-plugin-system/backend-only.md` |

### 1.3. Fato relevante

**Nenhum manifest `backend-only` existe hoje em `plugins/*`** — os 60 manifests verificados são `microfrontend` (58) ou `iframe` (2: `idd_production`, `kaizen-suggestion`). Na prática, **APIs de backend não são registradas como plugins**: `commercial-api`, `requests-api`, `delia-api` não possuem manifest em `plugins/`. Os permission codes que elas verificam (`commercial.access`, etc.) são **declarados pelo manifest do MFE correspondente** — o código é global no catálogo `permissions`, não pertence à API.

Consequência: `engineering-api` não *precisa* de registro Core próprio; o code `engineering.access` pertence ao futuro manifest `plugins/engineering` (id `engineering`, `module: engineering` — satisfaz `permission_module_mismatch`).

---

## 2. Permission code inicial

### 2.1. Verificação de existência

```bash
grep -rn "engineering" core-api/migrations/ core-api/app/domain/ core-api/app/content/ → 0 hits
```

`engineering.access` **não existe** em seeds/migrations/conteúdo Core no SHA inspecionado. Também não existe manifest `plugins/engineering`. O code é `PROPOSED`, não `PROVEN` — exigência da tarefa cumprida separando existente de candidato.

### 2.2. Decisão proposta

| Item | Proposta |
|---|---|
| Code | **`engineering.access`** |
| Owner declarante | manifest `plugins/engineering` (id `engineering`, `module: engineering`) — conforme `MANIFEST-DRAFT.md` §3 e `PERFIS-E-PERMISSOES.md` §2 |
| Descrição | "Acessar Portal de Engenharia" — acesso base à entrada do app e às rotas da API que exigem contexto de portal |
| Consumidores | `plugins/engineering` (rota base, showInMenu), `engineering-api` (AuthZ backend-first em rotas de negócio futuras) |
| Efeito | usuário com `engineering.access` → `/me/apps` inclui app `engineering`; `delpi_auth` resolve effective access → rotas da API autorizadas |
| Legado a mapear (coexistência) | `dashboard-engineering.view` → `engineering.access` + `engineering.analytics.access`; `dashboard-lmps.view` → `engineering.access` + `engineering.lmps.access`; `dashboard-lmps.nc.write` → `engineering.nonconformities.write` (`PERFIS-E-PERMISSOES.md` §3) |

### 2.3. Timing do registro — `ARCHITECTURE_DECISION_REQUIRED` leve

F1 entrega **somente** bootstrap (health/ready/auth plumbado). Rotas de negócio não existem → `engineering.access` não é exigida em F1. Opções:

| Opção | Descrição | Risco |
|---|---|---|
| **A (recomendada)** | Adiar registro ao manifesto real do MFE (F3a); F1 prova AuthZ via harness com Core mockado (padrão `delia-api` — "rota só de teste no harness") | nenhum code registrado antes da hora |
| B | Registrar `engineering` como `backend-only` v0.1.0 já em F1 (id `engineering`, `serviceName: engineering-api`, `routes:[]`, permission `engineering.access`); conversão para `microfrontend` em F3a via nova versão (mudança estrutural permitida — `backend-only.md` §13) | expõe app `engineering` no catálogo sem UI — aceitável (sem rotas → fora do launcher), mas cria registro antes do contrato do MFE estar pronto |
| C | Registrar `engineering-api` como `backend-only` com `engineering-api.access` | **rejeitada** — fragmenta identidade (dois codes para um produto) e contraria `MANIFEST-DRAFT.md` (um único app `engineering`) |

A/B preservam a regra `module == plugin_id`. A decisão final é da Coordenação — **nenhum registro é executado em F1-G0 nem em F1 por padrão**.

---

## 3. Contrato AuthN/AuthZ do bootstrap

### 3.1. Pipeline (padrão provado — `delpi_auth`)

```text
Authorization: Bearer <Keycloak JWT>
→ engineering_app/middleware/auth_middleware.py
   ├── path ∈ PUBLIC_PATHS ("/health","/ready",+ root_path variants) → skip auth
   └── else → delpi_auth.middleware.fastapi_auth.jwt_middleware
        ├── validate_token (delpi_auth.jwt_validator — Keycloak JWKS/issuer/audience)
        │     └── falha → 401
        ├── GET {CORE_API_URL}/me (cache TTL normal/stale; force_refresh em writes)
        │     └── falha de resolução → erro de autorização (fail-closed)
        └── contexto de usuário/permissions no request state
→ handler → require_any_permission("engineering.access", …) em rotas de negócio futuras
```

Fatos verificados (`shared/delpi_auth/`):
- `fastapi_auth.py` — JWT + `/me` + cache com TTL normal e stale; `force_refresh=True` desabilita stale fallback em writes sensíveis;
- `authorization.py` — `require_any_permission`, `has_any_permission`, `has_all_permissions`;
- `context_resolver.py` — resolve contexto pós-middleware;
- `service_token*.py` — service tokens existem mas **não são usados em F1**;
- `credential_guard.check_credentials()` — falha de boot se env obrigatória ausente (lifespan).

### 3.2. Saúde pública ≠ autorização

`/health` e `/ready` são **públicas por design** (padrão commercial/requests: `normalized in {"/ready","/health"}` no allowlist do wrapper). Isso prova liveness/readiness de infra — **não** prova autorização de rotas de negócio. A exigência da tarefa está coberta pelo contrato de testes (§5).

### 3.3. Comportamento de erro esperado

| Caso | Resposta | Base |
|---|---|---|
| Sem `Authorization` | `401` (`unauthenticated`) | `delpi_auth` jwt_middleware |
| Bearer malformado/expirado/assinatura inválida | `401` | `jwt_validator` |
| Autenticado sem `engineering.access` em rota protegida | `403` | `require_any_permission` |
| Core `/me` indisponível em rota que exige resolução | erro de autorização (fail-closed; padrão delia-api responde `503 authority_unavailable`) | `delpi_auth` middleware; `delia-api/app/interfaces/http/auth_middleware.py:46-55` |
| `RequestValidationError` | `422` com `fail(msg)` | padrão `commercial_app/main.py:116-123` |
| Exceção não tratada | `500` `fail("Erro interno do servidor.")` — sem stack/SQL/hostname | `commercial_app/main.py:125-127` |

Nota: o mapeamento exato Core-indisponível→status no `delpi_auth` FastAPI middleware deve ser confirmado na leitura linha-a-linha em F1 (a regra canônica é fail-closed; `delia-api` usa 503 explícito em `authority_unavailable`).

### 3.4. Relação acesso Portal × acesso API

- **Portal** (`/me/apps` + `ProtectedRoute`): presença do app `engineering` + rota `engineering.access` no effective access → entrada liberada.
- **API**: cada rota de negócio exige `require_any_permission` backend-side — nunca depender do frontend esconder UI.
- Um único code `engineering.access` cobre a entrada de ambos; segregações futuras (`engineering.lmps.access`, `engineering.nonconformities.write`, etc.) seguem `PERFIS-E-PERMISSOES.md` — **não inflar** permissions por tela/botão.

---

## 4. JWT

| Campo | Fonte |
|---|---|
| Issuer | `KEYCLOAK_ISSUER` (realm `delpi`) |
| Audience | `KEYCLOAK_AUDIENCE` (`delpi-central`) |
| JWKS | `KEYCLOAK_JWKS_URL` (ou discovery via `KEYCLOAK_URL`/`KEYCLOAK_REALM`) |
| Algoritmo | `JWT_ALGORITHMS` (default `RS256`) |
| Validação | `delpi_auth.jwt_validator.validate_token` — assinatura, exp, iss, aud |

Sem JWT local, sem RBAC local, sem permission embutida no token como autoridade (effective access vem do Core `/me`, não do claim — regra canônica).

---

## 5. Testes de autorização (contrato F1)

| Teste | Tipo | Verifica |
|---|---|---|
| `test_health.py` | smoke | `/health` 200 sem token; `/ready` 200/degraded explícito |
| `test_auth_middleware.py` | negative | sem header → 401; Bearer malformado → 401 |
| `test_auth_middleware.py` | negative | token inválido/expirado (mock validator) → 401 |
| `test_auth_middleware.py` | positive | token válido + Core `/me` mock → rota probe protegida 200 |
| `test_auth_middleware.py` | negative | token válido + `/me` sem `engineering.access` → 403 (quando rota probe com permission existir; pode ser rota TEST-only do harness, padrão delia-api) |
| `test_auth_middleware.py` | negative | Core indisponível → fail-closed (erro, não acesso) |
| `test_no_cross_context_imports.py` | arch | `engineering_app` não importa `app.` (api-delpi), `commercial_app`, `requests_app`, `delia`, `minha_delpi` |
| `test_config.py` | unit | env defaults + `check_credentials` falha fechada sem env |

Princípio (de `PERFIS-E-PERMISSOES.md` §10, aplicável às rotas de negócio quando existirem): positive + sibling + negative + IDOR + Core-down + permissão sensível. F1 cobre o subset possível sem rotas de negócio.

---

## 6. Gaps registrados

| Gap | Estado |
|---|---|
| `engineering.access` não existe no catálogo | `PROPOSED` — registro em F3a (opção A) ou backend-only F1 (opção B) — decisão da Coordenação |
| Status code exato Core-down no `delpi_auth` FastAPI (401 vs 503) | `TO_INVENTORY` em F1 — ler `fastapi_auth.py` linha a linha |
| `DELPI_AUTH_CORE_API_URL` vs `CORE_API_URL` — nome de env efetivamente lido pelo shared | `TO_INVENTORY` em F1 (compose usa ambos em serviços diferentes) |
| `dependencies` do MFE `engineering` → `engineering-api` no manifest futuro | `PLANNED` — declarar quando ambos existirem (protege unregister) |
| População/personas para grant de `engineering.access` | `NOT_READY` — provisionamento no cutover (`PERFIS-E-PERMISSOES.md` §11) |
