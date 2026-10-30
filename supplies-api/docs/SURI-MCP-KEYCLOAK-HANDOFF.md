# SURI MCP — Keycloak Handoff (pacote de cadastro)

Guia para o Operador IAM configurar o client OAuth da **SURI — Suprimentos
Unificados, Resultados e Inteligência** no Keycloak de produção. Sem
secrets neste documento — client secret é copiado diretamente Keycloak →
ChatGPT, nunca para o repositório/chat.

**Padrão de referência (obrigatório):**
`docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md` —
o runbook transversal já provou o fluxo para TÉO/DAVI/CLARA/EVA. Este
guia só fixa os valores específicos da SURI.

> **ENVIRONMENT PROVENANCE GATE:** toda verificação Keycloak deve ocorrer
> no realm **de produção**, nunca em Keycloak local/dev. Evidência de
> ambiente errado = `INVALIDATED_BY_WRONG_ENVIRONMENT`.
>
> **STATUS:** pacote preparado — client **não** registrado nesta release
> (`KEYCLOAK_REGISTERED=NO` por design). ChatGPT não conectado; deploy
> produtivo do `supplies-mcp` não realizado.

## 1. Valores SURI

| Parâmetro | Valor |
|---|---|
| Realm | `delpi` (produção) |
| Issuer esperado (`iss`) | `https://minhadelpi.com.br/auth/realms/delpi` |
| Client ID proposto | `mcp-supplies` |
| Resource MCP (audience exata) | `https://minhadelpi.com.br/apps/supplies-api/mcp` |
| Discovery OIDC | `https://minhadelpi.com.br/auth/realms/delpi/.well-known/openid-configuration` |
| Resource metadata (pública) | `https://minhadelpi.com.br/apps/supplies-api/.well-known/oauth-protected-resource` |
| Scopes OAuth | `openid profile email mcp:tools` (+ `offline_access` se o Plugin pedir) |
| Permissão de negócio requerida | `supplies.access` (Core `/me`) + escopo de filial — **não** são scopes OAuth |
| JWKS | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/certs` |
| Serviço | `supplies-mcp` (ASGI sibling, porta interna 8000, uvicorn) |
| Gateway | `location = /apps/supplies-api/mcp` → `supplies-mcp:8000` (exact-match antes do prefixo Flask) |

## 2. Criar o client

Clients → Create client:

| Campo | Valor |
|---|---|
| Protocol | OpenID Connect |
| Client ID | `mcp-supplies` |
| Access type | **Confidential** |
| Client authentication | ON |
| Standard Flow (Authorization Code) | ON |
| PKCE | S256 (Proof Key for Code Exchange = required) |
| Direct Access Grants | **OFF** |
| Service Accounts | **OFF** |
| Token endpoint auth method | `client_secret_post` (padrão comprovado ChatGPT) |
| Valid redirect URIs | **pendente** — gerar Plugin no ChatGPT primeiro e colar a URL de retorno exata (runbook FASE E) |
| Web origins | deixar vazio (server-to-server) |

**Proibido:** `*`/wildcards em redirect URIs, callback de outro Plugin
(TÉO/DAVI/CLARA/EVA ≠ SURI), GPT Actions callback (`/aip/g-*/oauth/callback`).

## 3. Client scopes e audience

### Shared scope (reutilizar, não criar)

- `mcp:tools` — client scope compartilhado já usado pelos demais MCPs.
  Vincular como *default* (ou *optional*) client scope de `mcp-supplies`.
- **Proibido** adicionar Audience mapper de resource específico dentro de
  `mcp:tools` — quebraria o isolamento entre MCPs.

### Audience transversal

- `audience-delpi` (já existente) → mint `aud` contendo `delpi-central`.
  Confirmar que o client herda esse mapper pelo realm/client scopes padrão.

### Audience dedicada SURI (obrigatória)

No client `mcp-supplies` → Client scopes → dedicated scope **ou** mapper
direto no client:

```text
Mapper: Audience
Included Custom Audience: https://minhadelpi.com.br/apps/supplies-api/mcp
Add to access token: ON
```

A URL deve ser **exata** (sem trailing slash) — idêntica a
`SURI_MCP_RESOURCE_URL`/`MCP_RESOURCE_URL` no compose do `supplies-mcp`.

## 4. Variáveis de ambiente (supplies-mcp)

| Variável | Valor | Origem |
|---|---|---|
| `PUBLIC_BASE_URL` | `https://minhadelpi.com.br` | `.env` existente (compartilhado) |
| `SURI_MCP_RESOURCE_URL` | `https://minhadelpi.com.br/apps/supplies-api/mcp` | novo — adicionar ao `.env` no deploy |
| `KEYCLOAK_ISSUER` / `KEYCLOAK_JWKS_URL` / `KEYCLOAK_REALM` / `KEYCLOAK_AUDIENCE` | padrão realm `delpi` | `.env` existente |
| `JWT_ALGORITHMS` | `RS256` | `.env` existente |
| `CORE_API_BASE_URL`, `DELPI_API_URL`, `DELPI_API_TIMEOUT`, `API_DELPI_INTERNAL_SERVICE_TOKEN` | internos | `.env` existente — o token de serviço vai **só** para `api-delpi` (egress), nunca aceito na superfície MCP |

## 5. Verificação do token (antes do ChatGPT)

Com Keycloak Evaluate ou token real de usuário de teste autorizado:

| Claim | Esperado |
|---|---|
| `iss` | `https://minhadelpi.com.br/auth/realms/delpi` |
| `azp` | `mcp-supplies` |
| `aud` | contém `delpi-central` **e** `…/supplies-api/mcp` |
| `aud` | **não** contém `…/transformometro-api/mcp`, `…/api-delpi/mcp`, `…/tv-dashboard-api/mcp`, `…/controllership-finance-api/mcp`, `…/engineering-api/mcp` |
| `scope` | contém `openid profile email mcp:tools` (e `offline_access` se solicitado) |
| `exp` | presente, futuro |

**Isolamento:** audience de outro MCP no token = mapper errado no shared
scope — corrigir conforme Troubleshooting do runbook.

## 6. Requisito de negócio (fora do Keycloak)

O usuário de teste precisa de `supplies.access` efetivo na Core (`/me`)
**e** escopo de filial (`branch` ∈ `{"01","02"}` resolvido pela
`AuthorizationService`). Keycloak autentica; **a autorização de negócio é
da Core e do BFF da `supplies-api`** — grants seguem o processo normal de
RBAC, nunca via scope/audience. Tokens de serviço internos são rejeitados
na superfície MCP (fail-closed).

## 7. Testes operacionais pós-cadastro

```text
1. GET …/apps/supplies-api/.well-known/oauth-protected-resource
   → 200 (resource + issuer + scopes)
2. POST /apps/supplies-api/mcp sem token → 401 + WWW-Authenticate
   com resource_metadata= e scope="openid profile email mcp:tools"
3. POST /mcp com token inválido → 401
4. POST /mcp com token sem aud SURI → 401
5. POST /mcp com token sem mcp:tools → 401
6. POST /mcp com token de serviço interno → 401 (principal_type=service
   banido na superfície)
7. POST /mcp com token válido + usuário sem supplies.access → tools
   respondem forbidden estruturado, nunca dados
8. initialize + tools/list com token válido → 4 tools semânticas
   (get_context, read, analyze, knowledge) — superfície semantic
   contract freeze rev.2; a V1 anterior (8 tools endpoint-oriented) foi
   substituída atomicamente antes do onboarding
9. read(action=search) com branch fora do escopo do usuário → 403
10. Reautenticação: revogar sessão → próximo initialize → 401 → fluxo
    OAuth reabre (refresh expirado)
```

## 8. Diagnóstico e rollback

| Sintoma | Causa provável | Ação |
|---|---|---|
| 401 `invalid_token` com bearer válido | `aud` sem `…/supplies-api/mcp` | conferir mapper dedicado do §3 |
| 401 `insufficient_scope` | `mcp:tools` não vinculado | vincular client scope §3 |
| 403 nas tools com token ok | usuário sem `supplies.access`/filial | grant RBAC na Core (§6) |
| 404/502 no gateway | `supplies-mcp` fora do ar | `docker compose ps supplies-mcp`; health `/healthz` |
| Redirect 307 em `/mcp` | location não exata no gateway | conferir `gateway/nginx.conf` exact-match `= /apps/supplies-api/mcp` |

Rollback do serviço: remover o `location` exact-match do gateway +
`docker stop delpi-supplies-mcp` — a `supplies-api` Flask não é
afetada (superfícies independentes). Rollback do client: desabilitar
`mcp-supplies` no Keycloak — tokens deixam de mintar `aud`/`scope` e a
superfície volta a 401 universal.
