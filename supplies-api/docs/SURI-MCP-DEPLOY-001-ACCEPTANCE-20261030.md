# SURI-MCP-DEPLOY-001 — Integração main + deploy produtivo + OAuth gate

Data: 2026-10-30 · Executor: Devin · Task: SURI-MCP-DEPLOY-001

## Resultado

| Item | Estado |
|---|---|
| Merge `feat/proc-0076-r4-implementation` → main | `bb7d7a88b9` (17 commits, escopo SURI puro) |
| `delpi-supplies-mcp` em prod | **Up / healthy** — image `infra-supplies-mcp` (`7ec1ad6ea9d7`) |
| Gateway com rotas SURI | rebuild `infra-gateway` (`14db752ff3b6`) — healthy |
| OAuth protected-resource metadata público | **HTTP 200** RFC 9728 |
| `POST /mcp` sem Bearer | **HTTP 401 + `WWW-Authenticate`** com `resource_metadata` |
| Tools MCP | `get_context`, `read`, `analyze`, `knowledge` (4) |

## Evidências públicas (sem credenciais)

```text
GET  /apps/supplies-api/.well-known/oauth-protected-resource
     → 200 application/json
       resource            https://minhadelpi.com.br/apps/supplies-api/mcp
       authorization_servers [https://minhadelpi.com.br/auth/realms/delpi]
       scopes_supported    openid profile email mcp:tools
       bearer_methods_supported header

POST /apps/supplies-api/mcp (sem Bearer)
     → 401 + WWW-Authenticate: Bearer realm="suri-mcp"
       resource_metadata="https://minhadelpi.com.br/apps/supplies-api/.well-known/oauth-protected-resource"
       scope="openid profile email mcp:tools" error="invalid_token"

GET  /auth/realms/delpi/.well-known/openid-configuration
     → 200, issuer correto, PKCE S256 presente

Negative: token KC válido (delpi-core-admin, aud=delpi-central) → 401 (audience isolation)
Sibling: /apps/supplies-api/health → 200 (BFF Flask inalterada)
TLS/redirects: HTTP/2, 0 redirects, sem fallback ao Flask
```

## Deploy

```text
srv-api git pull → bb7d7a88b9
up-prod-sequential.sh --build supplies-mcp   (imagem + up --no-deps)
up-prod-sequential.sh --build gateway        (nginx.conf embutida → rebuild+restart)
Container: 686e5f651b16 · healthcheck /healthz 200
```

## Conflito de merge resolvido

`infra/docker-compose.yml` (conflito whole-file): preservada estrutura vigente de
main + adicionado serviço `supplies-mcp` do branch (envs verificadas contra o
código ASGI: PUBLIC_BASE_URL, MCP_RESOURCE_URL com fallback, JWT/Keycloak,
DELPI_API_* + API_DELPI_INTERNAL_SERVICE_TOKEN, CORE_API_*, DELPI_AUTH_CORE_API_URL).

## Rollback

```text
srv-api: git reset --hard bf8f2a0d58
up-prod-sequential.sh --build gateway   (restaura nginx.conf anterior)
docker rm -f delpi-supplies-mcp
```

## Pendências

- `SURI_CHATGPT_CONNECTED = NO` (esperado): onboarding no ChatGPT pelo usuário;
  cadastrar redirect URI do ChatGPT no client `mcp-supplies` quando a URL do
  assistente de conector estiver disponível (`redirectUris` atualmente vazio).
- Autenticado E2E (tools/list com Bearer SURI): INCONCLUSIVE — requer fluxo
  OAuth user-delegated (direct grants/service accounts desabilitados por design).
- `SURI_MCP_RESOURCE_URL` não definida no `.env` prod — fallback canônico
  (`PUBLIC_BASE_URL + /apps/supplies-api/mcp`) resolvido e comprovado em runtime;
  defini-la é opcional (explícito), não bloqueio.
- Recomendação de higiene: rotacionar `KEYCLOAK_ADMIN_PASSWORD` (exposição
  transitória em saída de ferramenta durante investigação anterior; sem
  persistência encontrada em history/arquivos/eventos docker).
