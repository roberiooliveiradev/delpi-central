# Keycloak runbook — CLARA MCP / Controllership-Finance resource audience binding

> **Specialist brand:** CLARA — Controladoria, Leitura, Análise, Resultados e Acompanhamento
> **Technical client id:** `mcp-controllership-finance` (decisão PO 2026-10-26; `mcp-clara` = id anterior, histórico; não reutilizar `delpi-central` nem outros clients MCP)
> **Surface:** READ + ANALYSIS + KNOWLEDGE + PREPARE + ACT + BATCH (PREPARE_BATCH → consent → EXECUTE)
> **Status:** `KEYCLOAK_CONFIG = NOT_CONFIGURED` — provisionamento somente após G2+G3 via Operador SSH.
> Shared onboarding: `docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`
> Sibling PROVEN: `transformometro-api/docs/integrations/keycloak-mcp-client-runbook.md` (mesmo contrato físico)

## Goal

Access tokens usados em:

```text
https://minhadelpi.com.br/apps/controllership-finance-api/mcp
```

devem conter **ambas** as audiences:

```text
delpi-central
https://minhadelpi.com.br/apps/controllership-finance-api/mcp
```

e **não** conter audience de outro MCP (ex.: `…/api-delpi/mcp`, `…/transformometro-api/mcp`).

JWT `scope` claim (padrão ChatGPT comprovado no TÉO):

```text
openid email profile mcp:tools
```

Opcional quando o Plugin solicita refresh prolongado: `… offline_access`.

MCP resource URL: match exato, **sem trailing slash**.

## Client (contrato — mesmo do TÉO, PROVEN em produção 2026-09-17)

| Field | Value |
|---|---|
| Client ID | `mcp-controllership-finance` |
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

## Provisionamento idempotente (engine compartilhada)

`mcp-controllership-finance` está registrado como specialist em
`infra/scripts/delia_mcp_keycloak_state.py` (`SPECIALISTS`), que
converge: client confidencial + PKCE S256 + client scope dedicado
`mcp-audience-clara` com o Audience mapper da resource URL exata +
permissão `token-exchange` na policy `delia-exchange-requester`.

Execução (somente Operador SSH autorizado, **após G2 e G3**):

```bash
# drift report read-only (seguro, default)
bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --check

# apply idempotente do contrato IAM (inclui mcp-controllership-finance)
bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --apply
```

Pós-condições a verificar no token (smoke autenticado):

```text
JWT scope contains mcp:tools
JWT aud contains https://minhadelpi.com.br/apps/controllership-finance-api/mcp
JWT aud contains delpi-central
JWT aud does NOT contain https://minhadelpi.com.br/apps/api-delpi/mcp
JWT aud does NOT contain https://minhadelpi.com.br/apps/transformometro-api/mcp
```

## Shared scope `mcp:tools` ≠ resource binding

Regra herdada do incidente TÉO (PROVEN): **proibido** Audience mapper
de resource URL específica dentro do client scope compartilhado
`mcp:tools`. O mapper da CLARA vive apenas no dedicated scope
`mcp-audience-clara` do client `mcp-controllership-finance`.

`mcp:tools` **não** é autorização de negócio: a BFF/Core continua
autoridade (`controllership-finance.access` / `.manage` + escopo).

## Redirect URI — regra crítica

**Não inventar** URI antecipadamente. **Não** copiar callback de outro
conector. O fluxo real:

1. ChatGPT → Plugins → Novo plugin → OAuth → advanced.
2. Selecionar **Cliente OAuth definido pelo usuário**.
3. Copiar a **URL de retorno** exatamente como exibida.
4. Keycloak → Clients → `mcp-controllership-finance` → Valid redirect URIs → colar.
5. Salvar → voltar ao ChatGPT.
6. Sem wildcard `*` em produção.

`OAUTH_REDIRECT_URIS = NOT_CONFIGURED` até o passo 3 acontecer de
verdade — cada Plugin pode gerar connector-id próprio.

## ChatGPT Plugin registration (fluxo esperado — mesmo do TÉO)

| Campo | Valor |
|---|---|
| Name | `CLARA — Controladoria & Finanças` |
| Server URL | `https://minhadelpi.com.br/apps/controllership-finance-api/mcp` |
| Authentication | OAuth |
| Registration method | Cliente OAuth definido pelo usuário |
| Client ID | `mcp-controllership-finance` |
| Token auth | `client_secret_post` |
| Default scopes | `openid` `profile` `email` `mcp:tools` |
| Always requested | `offline_access` |

Issuer esperado: `https://minhadelpi.com.br/auth/realms/delpi`

Protected Resource Metadata:

```text
https://minhadelpi.com.br/apps/controllership-finance-api/.well-known/oauth-protected-resource
```

## Confirmação nativa do ChatGPT

O host pode exigir confirmação nativa para tools de escrita
(`commit_proposal`, `execute_batch` — `destructiveHint=true`). Isso
não é contornável nem deve ser: é a confirmação do plano/ato no host.
O consentimento de negócio da CLARA (Modo B consolidado ou Modo A
HOST_ATTESTED) é registrado server-side via `confirm_batch` — a
confirmação nativa do host complementa, nunca substitui.

## Consentimento de lote — contrato físico

- **Modo B (CONSOLIDATED)** — implementado e testado: `confirm_batch`
  chamado pelo usuário autenticado com o `plan_hash` exato é a
  confirmação do plano inteiro (auditoria `CLARA_BATCH_CONFIRMED`).
- **Modo A (HOST_ATTESTED)** — contrato implementado, mecanismo
  **pendente de aprovação Segurança/Plataforma** (Doc 106 §4):
  `signature = HMAC-SHA256(CLARA_HOST_ATTESTATION_SECRET,
  "plan_hash|actor_sub|expires_at")`. Sem o segredo configurado o
  endpoint responde `host_attestation_unavailable` (fail-closed 503).
  `confirmed=true`, texto de modelo e posse de handle nunca bastam.

## ENV (API)

```text
MCP_RESOURCE_URL=https://minhadelpi.com.br/apps/controllership-finance-api/mcp
PUBLIC_BASE_URL=https://minhadelpi.com.br
KEYCLOAK_ISSUER=<realm issuer real>
CLARA_HOST_ATTESTATION_SECRET=<opcional; só após aprovação Segurança>
```

## ENVIRONMENT PROVENANCE GATE

Local Keycloak/Docker ≠ evidência de produção. Verdict de produção
exige host `srv-api`, compose, Keycloak prod, gateway e endpoint
público verificados pelo Operador — nunca inferir PASS por HTTP 200.

## Reference

- Shared runbook: `docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`
- TÉO sibling (PROVEN): `transformometro-api/docs/integrations/keycloak-mcp-client-runbook.md`
- Doc 106: `docs/12-roadmap-e-evolucao/controllership-finance/106-clara-batch-ssh-keycloak-chatgpt-go-e-gates.md`

## Gate 021 — verificação produtiva (31/10/2026)

Inspeção read-only confirmou `mcp-controllership-finance` provisionado conforme este runbook: enabled, public client, standard flow, PKCE S256, redirect `chatgpt.com/connector_platform_oauth_redirect`, default scopes `mcp:tools` + `audience-delpi`. Referência histórica `mcp-clara = BLOCKED_IAM` está superada (nomenclatura anterior). Próximo passo operacional: executar conexão real via conector ChatGPT (authorization code + PKCE) e validar `tools/list` + tools de leitura — pendente de sessão conectora autorizada; sem alteração de configuração necessária.
