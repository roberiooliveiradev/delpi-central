# SURI — S0 Baseline & Decisão de Arquitetura (ARCH-MCP-01)

> **Plano:** SURI-MCP-MASTER-001 · **Etapa:** S0 · **Data:** 2026-10-29  
> **BASE HEAD:** `ac1899b194` (proc-0076 worktree, inclui docs SURI mergeados de `docs/suri-mcp-product-definition-20261027`)

## 1. Inventário executado (evidência real no HEAD)

### 1.1 Referências MCP existentes — mesmo padrão provado 4×

| App | Runtime | MCP mount | AuthN transporte | AuthZ negócio |
|---|---|---|---|---|
| CLARA (`controllership-finance-api`) | FastAPI/uvicorn | `app.mount("/mcp", mcp_http_app)` | `mcp_transport_auth` dentro de `jwt_middleware` | `authorized_user`/`has_permission` por tool (BFF interna) |
| TÉO / VISTA / DAVI | FastAPI/uvicorn | idem | idem | idem |

`shared/delpi_mcp` (instalado via `pip install -e "/shared[...]"`) já provê:
- `transport.py`: `mcp_mount_path_middleware`, `combine_lifespans`, `mcp_transport_security_settings` (DNS-rebinding sempre on);
- `auth.py`: `McpTransportAuthPolicy` + `mcp_transport_auth` — service-token ban, Bearer, `delpi_auth.validate_token`, `aud` exato, scopes, delega ao `jwt_middleware` canônico (que carrega RBAC via Core `/me`, com cache + fail-closed);
- `identity.py`: `require_mcp_context()` → `{user, authorization}`; `build_mcp_request`;
- `resource_contract.py`: RFC 9728 metadata + `mcp_metadata_router` (FastAPI), `build_www_authenticate_challenge`, `MCP_TRANSPORT_SCOPES`, `mcp_allowed_hosts_and_origins`;
- `errors.py`: `mcp_tool_result`, `kind_for_http_status`, `redact_error_details`;
- `tool_metadata.py`: taxonomia `DISCOVERY|READ|ANALYSIS|PREPARE|ACT`, annotations, `delpi/*` meta keys.

### 1.2 supplies-api hoje

- **Runtime:** Flask 3.1 + gunicorn (`Dockerfile` CMD), `SUPPLIES_API_ROOT_PATH=/apps/supplies-api`.
- **AuthZ:** `AuthorizationService.resolve_effective_user(access_token)` → `CoreApiHttpGateway.get_me` (Core `/me`) → `EffectiveUser(permissions, is_superadmin, access_token)`. Políticas em `supplies_permissions.py` (`supplies.access`, `supplies.manage`, `OPERATIONAL_UNITS=("01","02")`).
- **READ alvo (S1 ratifica):** `GET /purchase-orders` — `require_policy(can_use_operations)` + `require_units("branch")` (fail-closed: lista não vazia e cada branch ∈ unidades permitidas) → `DelpiApiGateway.get("/supplies/purchase-orders", access_token, params)` → envelope `api-delpi`. Erros mapeados 401/403/404/4xx/502.
- **requirements.txt:** sem `fastapi`, `starlette`, `uvicorn`, `httpx`, `mcp` — o adapter ASGI exige adicioná-los (não substitui o Flask).
- **Compose:** `delpi-supplies-api` (port 8000), envs `CORE_API_BASE_URL`, `KEYCLOAK_*`, `JWT_*`, `DELPI_API_URL`, `PUBLIC_BASE_URL`.
- **Gateway:** `location ^~ /apps/supplies-api/ → supplies-api:8000` com rewrite `^/apps/supplies-api/?(.*)$ /$1`.

### 1.3 Identidade/conteúdo

- `shared/delpi_character_profiles` instalado; contrato `CharacterProfile`/`CharacterPublicProfile` + `validate_profile` + projeções. Padrão DAVI: JSON de conteúdo (`app/content/davi_agent_intelligence.json`) → `build_davi_profile()` → ficha imutável.
- `supplies-api/docs/SURI-CHARACTER-PROFILE-PREVIEW.md`: identidade aprovada (mulher negra, 25 anos, black natural/tranças nagô, dinâmica/perspicaz/negociadora/comunicativa/resolutiva). Relações com DAVI/VISTA/TÉO/CLARA/EVA = **propostas, não registradas**.
- **Avatar:** `Suri no Escritório de Suprimentos.png` localizado em Downloads do usuário; SHA-256 `C624D36E…B3B0` confere **byte-a-byte** com o hash registrado na prévia (`c624d36e6c670d7b63455c81529141449e3f95113c37145c3ae5bd736566b3b0`). Integridade PROVEN → incorporável como asset versionado do owner.
- **Knowledge (S5):** corpus autorizado = manual oficial do Portal (`plugins/supplies/src/content/userManualContent.ts` + `glossaryContent` + column help), citável por arquivo+seção.

## 2. Decisão — ADR ARCH-MCP-01

**Opções avaliadas:**

| | A — Adapter ASGI irmão no mesmo image (ESCOLHIDA) | B — MCP co-localizado no processo Flask |
|---|---|---|
| Runtime | Novo serviço `supplies-mcp` (uvicorn, FastAPI app `app.interface.mcp`) no **mesmo Dockerfile/imagem** do supplies-api; importa gateways/serviços/supplies_permissions in-process | WSGI/ASGI bridging ou dispatcher híbrido dentro do Flask |
| Boundary Flask | **Preservado 100%** — nenhum mixin, nenhum middleware duplo | Exige ponte WSGI↔ASGI não-padrão no monorepo |
| Reuso `delpi_mcp` | **Integral** (transport/auth/identity/resource/errors/metadata) — é Starlette/FastAPI-native | Requer adapters artificiais sobre Starlette middleware |
| AuthZ parity | `require_mcp_context()` → `EffectiveUser` mapeado do `request.state.user` já resolvido por `jwt_middleware` (mesmo Core `/me`), depois `can_use_operations`/`require_units`/`DelpiApiGateway` **idênticos** às rotas | mesma lógica, porém sob ContextVars de um runtime híbrido |
| Deploy | serviço irmão (precedente: `external-data-scheduler` no R10); gateway ganha location específica `/apps/supplies-api/mcp` + `/.well-known/oauth-protected-resource` | in-place no gunicorn (sem processo separado) |
| Risco | +1 container, deps novas no image | runtime não-testado, mistura de frameworks, observabilidade dupla |

**Decisão:** **A**. `supplies-api` permanece Flask para HTTP de negócio; a SURI é um adapter ASGI owner-local no mesmo bounded context e imagem, reutilizando `delpi_mcp` e chamando as **mesmas** portas/gateways/políticas que as rotas Flask — nenhuma regra de negócio duplicada.

**Consequências:**
- Novos módulos: `app/interface/mcp/*`, `app/persona/suri_profile.py`, `app/content/suri_*.json`, `app/assets/characters/suri/`.
- `requirements.txt` ganha `fastapi`, `uvicorn[standard]`, `httpx`, `mcp>=2,<3`.
- Novo serviço compose `supplies-mcp` (mesmo build, `command` uvicorn).
- Gateway: `location ^~ /apps/supplies-api/mcp` → `supplies-mcp:8000` e `location = /apps/supplies-api/.well-known/oauth-protected-resource` → `supplies-mcp:8000` (rewrite strip prefix).
- Envs novas documentadas: `DELPI_AUTH_CORE_API_URL`, `MCP_RESOURCE_URL`, `PUBLIC_BASE_URL` (já existe), `SUPPLIES_MCP_PORT`.
- Canonical resource URL (TARGET): `https://minhadelpi.com.br/apps/supplies-api/mcp` — confirmada contra o gateway contract existente.

**Não-decisões (out of scope):** nenhum registro Keycloak, nenhum secret, nenhuma write/CRUD, nenhuma tool por endpoint, nenhum deploy produtivo.
