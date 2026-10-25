# Ficha pública — cadastro ChatGPT da CLARA (MCP)

`EXECUTION_ID: CF-PROC0072-CLARA-CHATGPT-EARLY-VALIDATION-001`
(Doc 107) · SHA de referência: `e8d9361dee` · Ambiente:
`https://minhadelpi.com.br` (srv-api — produção, piloto somente
após gates; ver §Estado).

> **Nunca** publicar client secret, tokens, senhas ou valores de
> `.env`. O secret do client `mcp-clara` fica no cofre/canal
> seguro do Operador — referenciar, nunca copiar para cá.

## Valores de cadastro (verificados)

| Campo | Valor | Evidência |
|---|---|---|
| Nome sugerido | `CLARA — Central de Fechamento` | produto Doc 94 |
| MCP URL (connector endpoint) | `https://minhadelpi.com.br/apps/controllership-finance-api/mcp` | `GET`/`POST` ⇒ HTTP 401 JSON no edge (montado; SHA pré-rework em prod) |
| Protected-resource metadata (RFC 9728) | `https://minhadelpi.com.br/apps/controllership-finance-api/.well-known/oauth-protected-resource` | contrato no código; resposta JSON esperada pós-deploy do SHA `e8d9361dee` (a 401 atual é do header `WWW-Authenticate` → ver nota) |
| Issuer | `https://minhadelpi.com.br/auth/realms/delpi` | `/.well-known/openid-configuration` — verificado 2026-10-25 |
| Authorization URL | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/auth` | idem |
| Token URL | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/token` | idem |
| JWKS | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/certs` | idem |
| Client ID | `mcp-clara` | desired-state `infra/scripts/delia_mcp_keycloak_state.py` (SINGLE source) — provisionamento pendente (`--apply` pós-gate) |
| Client authentication | `client_secret_post` | padrão comprovado ChatGPT (runbook FASE B) |
| PKCE | `S256` | contrato do engine |
| Grant | `authorization_code` (+ `refresh_token`/`offline_access` opcional) | discovery do realm |
| Scopes | `openid profile email mcp:tools` (+ `offline_access` se refresh prolongado) | contrato `mcp:tools` compartilhado |
| Audience (resource) | `https://minhadelpi.com.br/apps/controllership-finance-api/mcp` (+ `delpi-central`) | audience mapper dedicado do client — nunca no scope `mcp:tools` |
| Redirect/callback URI | **fornecida pelo ChatGPT no fluxo real de cadastro** — registrar o valor exato aqui após o cadastro | ação do usuário no workspace |
| Secret | no cofre do Operador | NÃO publicar |

## Passos de cadastro (usuário, no ChatGPT)

1. Criar o conector/app com a MCP URL acima e OAuth "custom".
2. Informar Client ID `mcp-clara`, authorization/token URLs,
   scopes e `client_secret` (do cofre).
3. Copiar a **callback URI exata** exibida pelo ChatGPT e entregá-la
   ao Operador → registrá-la no `Valid redirect URIs` do client
   `mcp-clara` no Keycloak (`--apply` com a URI real).
4. Completar o login Keycloak no fluxo OAuth do ChatGPT.
5. Roteiro de aceite (Doc 107 §3): discovery `tools/list` → READ
   por usuário autorizado → consulta com fonte/citação → plano
   multiação → consentimento consolidado no Portal → ACT só sobre
   dados de teste → read-back + auditoria.

## Estado

| Item | Status |
|---|---|
| MCP endpoint no edge | montado (401 com challenge pós-deploy; imagem atual em prod = `8ca4e2512`, pré-V011) |
| Client `mcp-clara` | **PENDENTE** — `--check` bloqueado: credenciais admin do Keycloak rotacionadas (bootstrap env não autentica); owner deve fornecer `KC_ADMIN_TOKEN`/admin válido |
| Deploy do SHA `e8d9361dee` | **PENDENTE** — G2/G3 obrigatórios (Doc 107: produção não é piloto sem gates; não há ambiente de homologação autorizado separado) |
| Migrations V006–V014 | pendentes no runtime prod (imagem atual contém até V005) |
| Corpus governado | pendente de ingestão pós-deploy (`corpus_ingestion --docs-root`) |
| Redirect URI real | pendente — obtida no cadastro |
