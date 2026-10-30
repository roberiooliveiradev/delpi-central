# CAIO MCP — Keycloak + ChatGPT handoff

> **Specialist:** CAIO — Consultor de Análise e Inteligência Operacional
> **Technical client id:** `mcp-commercial`
> **Owner:** `commercial-api` (`commercial_app.interface.mcp`)
> **Status:** `KEYCLOAK_CONFIG = NOT_CONFIGURED` — provisionamento somente
> pelo Operador SSH autorizado, após deploy validado (G2+G3).
> Shared onboarding: `docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`
> Sibling PROVEN contract: `controllership-finance-api/docs/integrations/keycloak-mcp-client-runbook.md` (mesmo contrato físico que TÉO/CLARA).

## Endpoints confirmados

| Item | Valor |
|---|---|
| MCP (Streamable HTTP) | `https://minhadelpi.com.br/apps/commercial-api/mcp` |
| Protected Resource Metadata | `https://minhadelpi.com.br/apps/commercial-api/.well-known/oauth-protected-resource` |
| Metadata alias | `https://minhadelpi.com.br/apps/commercial-api/.well-known/oauth-protected-resource/mcp` |
| OIDC issuer (`iss`) | `https://minhadelpi.com.br/auth/realms/delpi` |
| OIDC discovery | `https://minhadelpi.com.br/auth/realms/delpi/.well-known/openid-configuration` |
| JWKS | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/certs` |
| Authorization endpoint | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/auth` |
| Token endpoint | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/token` |
| Avatar público (quando aprovado) | `https://minhadelpi.com.br/apps/commercial-api/public/characters/caio/avatar/avatar-v1.png` |

## Audience / resource binding

Access tokens usados no endpoint MCP devem conter **ambas** as audiences:

```text
delpi-central
https://minhadelpi.com.br/apps/commercial-api/mcp
```

e **não** conter audience de outro MCP (`…/api-delpi/mcp`,
`…/transformometro-api/mcp`, `…/engineering-api/mcp`,
`…/controllership-finance-api/mcp`).

Resource URL: match exato, **sem trailing slash** — bind via
`MCP_RESOURCE_URL` (default
`https://minhadelpi.com.br/apps/commercial-api/mcp`).

## Scopes

JWT `scope` claim exigido pelo transporte (padrão comprovado TÉO/CLARA):

```text
openid email profile mcp:tools
```

Opcional quando o Plugin solicita refresh prolongado: `… offline_access`.

`securitySchemes` exposto no `tools/list`:

```json
[{"type": "oauth2", "scopes": ["openid", "profile", "email", "mcp:tools"]}]
```

## Client Keycloak (contrato — mesmo do TÉO/CLARA, PROVEN)

| Field | Value |
|---|---|
| Client ID | `mcp-commercial` |
| Mode | `PREDEFINED` / **Cliente OAuth definido pelo usuário** no ChatGPT |
| Capability type | OpenID Connect |
| Access type | Confidential |
| Client authentication | ON |
| Token endpoint auth | `client_secret_post` |
| Standard Flow | ON |
| Direct Access Grants | **OFF** |
| Service Accounts | **OFF** |
| Implicit | OFF |
| PKCE | S256 |

Nunca registrar client secret em docs/git/chat/relatório.

## Redirect URIs (preencher no cadastro)

O ChatGPT fornece a redirect URI no momento do registro do
Plugin/Connector — preencher então no client `mcp-commercial`:

| Field | Value |
|---|---|
| Valid redirect URIs | `<a preencher pelo responsável no cadastro>` |
| Web origins | `<a preencher pelo responsável no cadastro>` |

## Provisionamento idempotente (engine compartilhada)

`mcp-commercial` está declarado como specialist em
`infra/scripts/delia_mcp_keycloak_state.py` (`SPECIALISTS`), que
converge: client confidencial + PKCE S256 + client scope dedicado
`mcp-audience-caio` com o Audience mapper da resource URL exata +
permissão `token-exchange` na policy `delia-exchange-requester`.

Execução (somente Operador SSH autorizado):

```bash
# drift report read-only (seguro, default)
bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --check

# apply idempotente do contrato IAM (inclui mcp-commercial)
bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --apply
```

## Permissões do usuário de teste

O transporte MCP exige apenas o JWT OAuth válido; a autorização
comercial é resolvida pelo backend (`delpi_auth` → Core `/me`).

| Caso | Permissão RBAC |
|---|---|
| Leitura comercial (read/analyze/knowledge) | `commercial.access` **ou** `commercial.manage` |
| Escopo irrestrito / carteiras selecionadas | `commercial.manage` (ou team scope) |
| Escopo de membership | usuário vinculado a carteira ativa |
| Sem nenhuma permissão comercial | `403` em todas as tools |

## Registro no ChatGPT (após provisionamento)

1. ChatGPT → conector/plugin MCP → **Cliente OAuth definido pelo usuário**.
2. URL do MCP: `https://minhadelpi.com.br/apps/commercial-api/mcp`.
3. Client ID `mcp-commercial` + secret do cadastro Keycloak.
4. Authorization URL / Token URL conforme tabela acima; PKCE S256.
5. Scopes: `openid email profile mcp:tools`.
6. Concluir fluxo OAuth com usuário de teste com `commercial.access`.

## Checklist pós-cadastro

- [ ] `GET /.well-known/oauth-protected-resource` → `resource` =
      `https://minhadelpi.com.br/apps/commercial-api/mcp`,
      `authorization_servers` contém o issuer.
- [ ] `POST /mcp` sem Bearer → `401` + `WWW-Authenticate: Bearer …`
      com `resource_metadata` correto.
- [ ] Token sem `mcp:tools` → `401/403` (challenge OAuth).
- [ ] Token com audience de outro MCP → rejeitado.
- [ ] `tools/list` → exatamente 6 tools: `get_context`, `read`,
      `analyze`, `knowledge`, `execute`, `delete`.
- [ ] `get_context` → entidades/ações, capacidades e
      `agent_directives` do CAIO.
- [ ] `read` `customer.list` → clientes do escopo do usuário de teste.
- [ ] `analyze` `portfolio.open_summary` → KPI observado com
      proveniência.
- [ ] `execute`/`delete` → `not_implemented` honesto (v1 não ativa
      escritas).
- [ ] Usuário sem `commercial.access`/`manage` → `403`.
- [ ] Avatar: `GET /public/characters/caio/avatar/avatar-v1.png` →
      `200` + `image/png` + SHA-256 documentado abaixo
      (**PENDING_ASSET** enquanto o PNG aprovado não for incorporado —
      hoje responde `404` por contrato).

## Avatar

| Item | Valor |
|---|---|
| Versão | `avatar-v1.png` |
| URL pública | `https://minhadelpi.com.br/apps/commercial-api/public/characters/caio/avatar/avatar-v1.png` |
| SHA-256 | `PENDING_ASSET` — a preencher com o hash do PNG original aprovado |
| Status | `REFERENCE_NOT_OFFICIAL_AVATAR` até o arquivo ser incorporado em `commercial-api/commercial_app/assets/characters/caio/avatar-v1.png` |

## Fora de escopo deste handoff

- Registro efetivo do client no Keycloak (Operador SSH).
- Conexão efetiva no ChatGPT (responsável humano).
- Escritas governadas (`execute`/`delete`) — deny-by-default na v1.
