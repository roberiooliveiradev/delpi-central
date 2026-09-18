# Keycloak runbook — Transformômetro MCP / TÉO resource audience binding

> **Specialist brand:** TÉO — Especialista em Transformação Digital
> **Technical client id:** `mcp-transformometro` (do not rename to `mcp-teo` / do not reuse `chatgpt-transformometro`)
> **Surface:** FULL CRUD (READ + PREPARE + ACT) — not DAVI READ-only.

> **KEYCLOAK_CONFIG = APPLIED_EVALUATE_PROVEN** (produção, 2026-09-17, host `srv-api`).
> ChatGPT Plugin OAuth + tool discovery + READ live = **PROVEN**.
> Shared onboarding: [`docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`](../../../docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md).

## Goal

Access tokens used at:

```text
https://minhadelpi.com.br/apps/transformometro-api/mcp
```

must contain **both** audiences:

```text
delpi-central
https://minhadelpi.com.br/apps/transformometro-api/mcp
```

and must **not** contain another MCP resource (ex.: `…/api-delpi/mcp`).

JWT `scope` claim (padrão ChatGPT comprovado):

```text
openid email profile mcp:tools
```

Opcional quando o Plugin solicita refresh prolongado:

```text
… offline_access
```

```text
Keycloak realm role offline_access
≠
OAuth scope claim "offline_access"
```

Keycloak client scope `audience-delpi` permanece **Default** e causa `aud` → `delpi-central`. Não precisa aparecer na string `scope` do JWT.

MCP resource URL: match exato, **sem trailing slash**.

## Client (PROVEN)

| Field | Value |
|---|---|
| Client ID | `mcp-transformometro` |
| Mode | `PREDEFINED` / **Cliente OAuth definido pelo usuário** no ChatGPT |
| Do not reuse | `delpi-central`, Portal, `chatgpt-transformometro`, `mcp-api-delpi` |
| Capability type | OpenID Connect |
| Access type | Confidential |
| Client authentication | ON |
| Token endpoint auth | `client_secret_post` |
| Standard Flow | ON |
| Direct Access Grants | **OFF** |
| Service Accounts | **OFF** |
| Implicit | OFF |
| PKCE | S256 |

Nunca registrar client secret em docs/git/chat.

## Shared scope `mcp:tools` ≠ resource binding

`mcp:tools` é **scope compartilhado e genérico** entre MCPs autorizados.

| Pertence a | Não pertence a |
|---|---|
| Mechanismo OAuth comum (scope string no token) | Audience de um MCP específico |
| Client assignment Default em cada `mcp-*` | Semântica “só DAVI” ou “só TÉO” |

**Proibido:** Audience mapper de resource URL específica dentro do client scope compartilhado `mcp:tools`.

Incidente comprovado: mapper `mcp-api-delpi-resource-audience` (`…/api-delpi/mcp`) estava no shared `mcp:tools` e fazia o TÉO receber audience do DAVI indevidamente.

Correção:

```text
remover resource-specific Audience mapper de mcp:tools
→ manter/adicionar Audience mapper no client dedicado (ou dedicated client scope)
```

Resultado PROVEN (2026-09-17):

| Client | `azp` | `aud` inclui | `aud` NÃO inclui |
|---|---|---|---|
| `mcp-transformometro` | `mcp-transformometro` | `delpi-central`, `…/transformometro-api/mcp`, `account` | `…/api-delpi/mcp` |
| `mcp-api-delpi` | `mcp-api-delpi` | `delpi-central`, `…/api-delpi/mcp`, `account` | `…/transformometro-api/mcp` |

```text
MCP RESOURCE ISOLATION = PROVEN / PASS
```

## Dedicated resource audience (TÉO)

No client `mcp-transformometro` (mapper de client ou dedicated scope **deste** client):

| Campo | Valor |
|---|---|
| Mapper type | Audience |
| Included Custom Audience | `https://minhadelpi.com.br/apps/transformometro-api/mcp` (**exact**) |
| Add to access token | ON |

Também Default no client:

```text
profile
email
audience-delpi
mcp:tools
```

Postconditions:

```text
JWT scope contains mcp:tools
JWT aud contains https://minhadelpi.com.br/apps/transformometro-api/mcp
JWT aud contains delpi-central
JWT aud does NOT contain https://minhadelpi.com.br/apps/api-delpi/mcp
```

`mcp:tools` **não** é autorização de negócio. Backend RBAC permanece autoridade.

## Redirect URI — regra crítica

**Não inventar** URI antecipadamente. **Não** copiar callback do DAVI nem GPT Actions (`/aip/g-...`).

1. ChatGPT → Plugins → Novo plugin → OAuth → advanced.
2. Selecionar **Cliente OAuth definido pelo usuário**.
3. Copiar a **URL de retorno** exatamente.
4. Keycloak → Clients → `mcp-transformometro` → Valid redirect URIs → colar.
5. Salvar → voltar ao ChatGPT.
6. Sem wildcard `*` em produção.

Cada Plugin pode gerar connector-id próprio.

## ChatGPT Plugin registration (fluxo que funcionou)

| Campo | Valor |
|---|---|
| Name | `TÉO — Transformômetro` |
| Server URL | `https://minhadelpi.com.br/apps/transformometro-api/mcp` |
| Authentication | OAuth |
| Registration method | Cliente OAuth definido pelo usuário |
| Client ID | `mcp-transformometro` |
| Token auth | `client_secret_post` |
| Default scopes | `openid` `profile` `email` `mcp:tools` |
| Always requested | `offline_access` |

Não usar DCR/CIMD como padrão quando o client governado já existe. Aviso de CIMD indisponível **não** bloqueia este fluxo.

Discovery automática pelo ChatGPT (PROVEN): authorization/token/registration endpoints, AS base, resource, OIDC config, userinfo, supported scopes.

Issuer esperado:

```text
https://minhadelpi.com.br/auth/realms/delpi
```

Protected Resource Metadata:

```text
https://minhadelpi.com.br/apps/transformometro-api/.well-known/oauth-protected-resource
```

## Tool model (não confundir com GPT Actions)

| Métrica | Valor |
|---|---|
| GPT Actions capabilities (legacy) | **21** importable operationIds (`gpt_get_methodology_guide` included). 20 was the 2026-09-17 inventory. |
| MCP tools | **33** (10 READ including `get_methodology_guide` + 1 ANALYSIS + 11 PREPARE + 11 ACT) |
| Capability coverage | **20/20** |

`32 ≠ 20` **não** é regression: 1 capability GPT pode virar READ + PREPARE + ACT.

## Bridge policy

| Client | Surface | Status |
|---|---|---|
| `chatgpt-transformometro` | Custom GPT Actions `/gpt-actions/v1` | **LEGACY_TRANSITIONAL_BRIDGE** — 21 importable operationIds; manter até parity + writes aceitos + período de transição |
| `mcp-transformometro` | Plugin MCP `/mcp` | **CURRENT** para agents (READ live PROVEN; PREPARE/ACT ChatGPT = TEST_NOT_RUN) |

## ENVIRONMENT PROVENANCE GATE

Antes de verdict de produção: provar host SSH (`srv-api`), compose, Keycloak prod, gateway, container, endpoint público.

```text
Local Keycloak/Docker ≠ production evidence
```

Findings locais de “client ABSENT / mcp:tools ABSENT” foram **INVALIDATED_BY_WRONG_ENVIRONMENT** e depois corrigidos via SSH.

## Env (API)

Optional override:

```text
MCP_RESOURCE_URL=https://minhadelpi.com.br/apps/transformometro-api/mcp
PUBLIC_BASE_URL=https://minhadelpi.com.br
KEYCLOAK_ISSUER=<realm issuer>
```

## Reference

- Shared runbook: `docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`
- Product MCP docs: `transformometro-api/docs/integrations/openai-plugin-mcp.md`
- DAVI sibling: `api-delpi/docs/integrations/keycloak-mcp-client-runbook.md`
- Smoke: `teo-mcp-plugin-agent-smoke.md`
