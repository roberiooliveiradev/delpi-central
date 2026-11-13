# 121 — EVA MCP: execução E2E autenticada (runbook operacional)

**RUNBOOK_VERSION:** `1.0` — 2026-11-13
**OWNER:** Engenharia / EVA (docs canônicos `119`/`120`; Issue #131)
**CAPABILITY:** `product.drawing_understanding` (tool MCP `analyze`)
**ENVIRONMENTS:** DEV, PROD
**AUTH_FLOW:** impersonation admin → OAuth/OIDC oficial do client MCP
**AUTHZ_OWNER:** Core `/me` RBAC — `engineering.access` **ou**
`is_superadmin` (mesmo gate das rotas REST,
`_require_engineering_human`)
**REPEATABLE_WITHOUT_ADMIN_MUTATIONS:** **YES** — nenhum passo cria
usuário, concede permissão, altera client ou credencial; a sessão de
impersonation é efêmera e não persiste mudança.

## 1. Por que este caminho é o oficial

| Camada | Contrato real |
|---|---|
| Endpoint MCP | `https://minhadelpi.com.br/apps/engineering-api/mcp` (PROD) · gateway DEV em `:80` |
| Audience exigida | URL exata do recurso MCP (`MCP_RESOURCE_URL`) |
| Scope exigido | `mcp:tools` (+ `openid`) |
| Client OAuth | `mcp-engineering` (confidencial, PKCE obrigatório, redirect `chatgpt.com/connector_platform_oauth_redirect`) |
| Permissão | `engineering.access` ou `is_superadmin` via Core `/me` |
| Principal | humano (`principal_type=user`) |

Token exchange (`delia-api` → `mcp-engineering`) funciona em DEV e
está **negado por política** em PROD — em PROD usar o code-flow
direto no `mcp-engineering` (§78 do Doc 119 já usava esse caminho).

## 2. Principais legítimos

| Ambiente | Principal | Autorização |
|---|---|---|
| DEV | `rober` (`rober@dev.local`) | `engineering.access` + `api-delpi.access` (seed DEV) |
| PROD | `rober` (`inovacao@delpi.com.br`) | `is_superadmin=true` no Core — acesso legítimo preexistente |

Se a Coordination designar outro principal (ex.: restaurar o usuário
KC de `deploy01.smoke@delpi.local`, cuja linha Core já possui
`engineering.access` via role), o procedimento é idêntico — trocar
apenas `username` na etapa de impersonation.

## 3. Pré-requisitos (preflight curto)

1. `engineering-api` saudável (`/health` 200 interno + gateway).
2. Acesso admin ao realm `delpi` (credenciais do container KC:
   `$KEYCLOAK_ADMIN`/`$KEYCLOAK_ADMIN_PASSWORD` — nunca copiar
   valores para scripts, docs ou logs).
3. `client_secret` de `mcp-engineering` recuperado via
   `kcadm.sh get clients/{uuid}/client-secret` (PROD) ou client de
   exchange `delia-api` (DEV).
4. PDF oficial acessível pela fonte governada
   (`/drawing-pdfs` na api-delpi; CIFS prod).
5. Nenhum restart pendente — o `AnalysisJobStore` é processo-local;
   restart descarta jobs (`job_not_found`).

## 4. Procedimento — PROD (provado 2026-11-13)

Executado dentro do container `delpi-engineering-api` (rede interna):

1. Admin token: `POST keycloak:8080/auth/realms/master/protocol/
   openid-connect/token` — `grant_type=password`,
   `client_id=admin-cli`, credenciais admin.
2. `POST /admin/realms/delpi/users/{uid}/impersonation`
   (`username=rober`) → cookies de sessão.
3. `GET /realms/delpi/protocol/openid-connect/auth` —
   `client_id=mcp-engineering`,
   `redirect_uri=https://chatgpt.com/connector_platform_oauth_redirect`,
   `response_type=code`, `scope=openid mcp:tools`,
   `code_challenge`(S256) → `code` no `Location`.
4. `POST /realms/delpi/protocol/openid-connect/token` —
   `grant_type=authorization_code`, `client_id=mcp-engineering`,
   `client_secret`, `redirect_uri` idêntico, `code`, `code_verifier`
   → token com `aud` contendo a resource URL e `scope=mcp:tools`.
5. MCP streamable-HTTP em `http://127.0.0.1:8000/mcp` (ou gateway):
   `initialize` → `notifications/initialized` →
   `tools/call analyze` `{analysis_type, parameters:{product_code}}`
   → `job_id`.
6. Poll: mesmo `tools/call` com `parameters.job_id` até
   `status!=RUNNING` (~4–30 min; JOB cap 2700s).

## 5. Procedimento — DEV (provado 2026-11-13)

Igual ao PROD exceto:

- `mcp-engineering` DEV não tem `redirectUris` → usar
  `client_id=delpi-central` com `response_type=token` (implicit),
  `redirect_uri=http://localhost/cb` (registrado `http://localhost/*`).
- Trocar o subject-token por token MCP:
  `grant_type=urn:ietf:params:oauth:grant-type:token-exchange`,
  `client_id=delia-api` + `DELIA_EXCHANGE_CLIENT_SECRET` (env do
  container), `audience=mcp-engineering`, `scope=openid mcp:tools`.
- Header `Host: localhost` em todas as chamadas ao KC interno
  (`keycloak:8080`) — o `iss` esperado é
  `http://localhost/auth/realms/delpi` (sem porta).
- Endpoint MCP DEV: `http://127.0.0.1:8000/mcp` no container ou
  `http://localhost/apps/engineering-api/mcp` no gateway.

## 6. Validação das ocorrências (página 12, `90264135`)

No resultado do job (`understanding.structure_occurrences` /
`table_perception`):

| Controle | Esperado |
|---|---|
| `AE|1|10010028 → 50225702` | `IDENTIFIED` `rowspan_anchor` |
| `AE|1|10010028 → 50225704/740` | `IDENTIFIED` |
| `AH|1|10080897`, `AG|1|10110676 → 50225740` | `IDENTIFIED` |
| `AF|1|10010005 → 50225741` | `IDENTIFIED` |
| `AG|16|10110676` | `UNKNOWN` (fail-closed) |
| Duplicatas / falsas promoções | 0 |

## 7. Diagnóstico de erros comuns

| Sintoma | Causa | Ação |
|---|---|---|
| `401 Invalid token` | `iss` divergente (porta) ou token do realm errado | DEV: header `Host: localhost` |
| `401` no initialize | aud sem a resource URL | conferir `audience`/client |
| `403` no tools/call | principal sem `engineering.access`/superadmin | trocar principal — NÃO conceder grant ad hoc |
| exchange 403 | política prod nega `delia-api→mcp` | usar code-flow `mcp-engineering`+PKCE |
| `Missing code_challenge` | PKCE obrigatório | enviar S256 + verifier |
| `job_not_found` | restart do serviço (store processo-local) | resubmeter analyze |
| `source_unavailable` | fonte de PDFs não montada | conferir `/drawing-pdfs` na api-delpi |

## 8. Higiene

- Nenhum token, secret ou cookie em logs/docs/git.
- Secrets consumidos via env do próprio container/KC admin CLI.
- Impersonation não muta realm nem usuário — não há revogação
  pendente além da expiração natural da sessão.
- Não criar/alterar usuários, roles, permissions ou clients para
  executar este runbook — exceções exigem aprovação do owner IAM/Core.
