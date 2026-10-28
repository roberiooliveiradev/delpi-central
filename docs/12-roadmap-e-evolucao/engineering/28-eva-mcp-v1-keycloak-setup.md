# EVA MCP V1 — Keycloak Setup (guia administrativo)

Guia para a Coordenação/Operador IAM configurar o client OAuth da **EVA —
Engenharia Virtual Assistida** no Keycloak de produção. Sem secrets neste
documento — client secret é copiado diretamente Keycloak → ChatGPT, nunca
para o repositório/chat.

**Padrão de referência (obrigatório):**
`docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md` —
o runbook transversal já provou o fluxo para TÉO/DAVI/CLARA. Este guia só
fixa os valores específicos da EVA.

> **ENVIRONMENT PROVENANCE GATE:** toda verificação Keycloak deve ocorrer no
> realm **de produção** (host `srv-api`), nunca em Keycloak local/dev.
> Evidência de ambiente errado = `INVALIDATED_BY_WRONG_ENVIRONMENT`.

## 1. Valores EVA

| Parâmetro | Valor |
|---|---|
| Realm | `delpi` (produção) |
| Issuer esperado (`iss`) | `https://minhadelpi.com.br/auth/realms/delpi` |
| Client ID proposto | `mcp-engineering` |
| Resource MCP (audience exata) | `https://minhadelpi.com.br/apps/engineering-api/mcp` |
| Discovery OIDC | `https://minhadelpi.com.br/auth/realms/delpi/.well-known/openid-configuration` |
| Resource metadata (pública) | `https://minhadelpi.com.br/apps/engineering-api/.well-known/oauth-protected-resource` |
| Scopes OAuth | `openid profile email mcp:tools` (+ `offline_access` se o Plugin pedir) |
| Permissão de negócio requerida | `engineering.access` (Core `/me`) — **não** é scope OAuth |
| JWKS | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/certs` |

## 2. Criar o client

Clients → Create client:

| Campo | Valor |
|---|---|
| Protocol | OpenID Connect |
| Client ID | `mcp-engineering` |
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
(TÉO/DAVI/CLARA ≠ EVA), GPT Actions callback (`/aip/g-*/oauth/callback`).

## 3. Client scopes e audience

### Shared scope (reutilizar, não criar)

- `mcp:tools` — client scope compartilhado já usado pelos demais MCPs.
  Vincular como *default* (ou *optional*) client scope de `mcp-engineering`.
- **Proibido** adicionar Audience mapper de resource específico dentro de
  `mcp:tools` — quebraria o isolamento entre MCPs.

### Audience transversal

- `audience-delpi` (já existente) → mint `aud` contendo `delpi-central`.
  Confirmar que o client herda esse mapper pelo realm/client scopes padrão.

### Audience dedicada EVA (obrigatória)

No client `mcp-engineering` → Client scopes → dedicated scope **ou** mapper
direto no client:

```text
Mapper: Audience
Included Custom Audience: https://minhadelpi.com.br/apps/engineering-api/mcp
Add to access token: ON
```

A URL deve ser **exata** (sem trailing slash) — idêntica a
`MCP_RESOURCE_URL_ENGINEERING` no compose.

## 4. Verificação do token (antes do ChatGPT)

Com Keycloak Evaluate ou token real de usuário de teste autorizado:

| Claim | Esperado |
|---|---|
| `iss` | `https://minhadelpi.com.br/auth/realms/delpi` |
| `azp` | `mcp-engineering` |
| `aud` | contém `delpi-central` **e** `…/engineering-api/mcp` |
| `aud` | **não** contém `…/transformometro-api/mcp`, `…/api-delpi/mcp`, `…/tv-dashboard-api/mcp`, `…/controllership-finance-api/mcp` |
| `scope` | contém `openid profile email mcp:tools` (e `offline_access` se solicitado) |

**Isolamento:** a audience de outro MCP no token = mapper errado no shared
scope — corrigir conforme Troubleshooting do runbook.

## 5. Requisito de negócio (fora do Keycloak)

O usuário de teste precisa de `engineering.access` efetivo na Core
(`/me`). Keycloak autentica; **a autorização de negócio é da Core e dos
owners downstream** — configurar grants segue o processo normal de RBAC,
nunca via scope/audience.

## 6. Testes operacionais

```text
1. GET …/.well-known/oauth-protected-resource → 200 (resource + issuer + scopes)
2. POST /apps/engineering-api/mcp sem token → 401 + WWW-Authenticate
   com resource_metadata=
3. POST /mcp com token inválido → 401
4. POST /mcp com token sem aud EVA → 401
5. POST /mcp com token sem mcp:tools → 401
6. POST /mcp com token válido + usuário sem engineering.access → tools
   respondem forbidden (403 estruturado), nunca dados
7. initialize + tools/list com token válido → 3 tools
   (get_catalog, get_engineering_home, get_engineering_overview)
```

## 7. Revogação e falhas

- Revogar sessão/consentimento no Keycloak invalida refresh; access tokens
  expiram pelo TTL do realm (sem lista de revogação — padrão JWT).
- `client_secret` comprometido → regenerar no client e atualizar somente o
  Plugin; não registrar o novo valor em docs.
- Rollback: desabilitar o client `mcp-engineering` → toda a superfície MCP
  EVA fica fail-closed (401) sem afetar `/v1` REST.

## 8. Parâmetros pendentes (não inventar)

| Item | Status |
|---|---|
| Client secret | `PENDING_ADMIN` — gerado pelo Keycloak, nunca no repo |
| Redirect URI definitiva | `PENDING_ADMIN` — exibida pelo ChatGPT ao criar o Plugin |
| `offline_access` como realm-scope opcional | verificar binding já existente (padrão TÉO) |
| Grant `engineering.access` de usuários piloto | `PENDING_ADMIN` — RBAC Core |
