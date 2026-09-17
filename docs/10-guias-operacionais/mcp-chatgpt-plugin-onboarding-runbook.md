# MCP / ChatGPT Plugin — onboarding runbook (novos especialistas)

> **Owner transversal:** plataforma Minha DELPI (OAuth/MCP)
> **Consumers:** TÉO (`transformometro-api`), DAVI (`api-delpi`), futuros `mcp-<domain>`
> **Status:** CURRENT (2026-09-17) — consolidado após acceptance prod do TÉO
> **Documentação ≠ runtime.** Cada go-live exige evidência fresca no ambiente correto.

Referências de produto:

| Especialista | Docs canônicos |
|---|---|
| TÉO | `transformometro-api/docs/integrations/openai-plugin-mcp.md` + Keycloak runbook |
| DAVI | `api-delpi/docs/integrations/openai-plugin-mcp.md` + Keycloak runbook |
| Regra Cursor | `.cursor/rules/openai-plugin-mcp-integration.mdc` |

---

## Princípios (não negociáveis)

```text
MCP = interface/protocol/adapter
MCP ≠ Domain API
MCP ≠ RBAC
MCP ≠ generic proxy

Specialist capability ≤ authenticated user capability
ChatGPT confirmation ≠ authorization
Backend AuthZ = autoridade final
```

```text
shared OAuth mechanics
+
isolated resource audience
```

```text
shared scope mcp:tools
≠
resource binding
```

Nunca colocar Audience mapper de um MCP específico dentro do client scope compartilhado `mcp:tools`.

---

## ENVIRONMENT PROVENANCE GATE (obrigatório antes de verdict de produção)

Antes de classificar PASS/FAIL/EXECUTION_DRIFT de **produção**, provar explicitamente:

| Prova | Exemplo |
|---|---|
| Host | SSH `operador@192.168.1.237` (`srv-api`) — não WSL/dev local |
| Compose/runtime | `docker-compose.yml` prod no host |
| Keycloak | container Keycloak **do mesmo host** / realm `delpi` prod |
| Gateway | nginx/gateway do mesmo host |
| Container | nome/imagem do serviço MCP |
| Endpoint | `https://minhadelpi.com.br/...` alinhado ao container |

```text
Local environment ≠ production evidence
```

Nunca emitir verdict de produção usando Keycloak/compose/Python local.

Findings gerados no ambiente errado devem ser marcados:

```text
INVALIDATED_BY_WRONG_ENVIRONMENT
```

---

## FASE A — Inventory

1. Owner do domínio / bounded context.
2. MCP endpoint público (HTTPS).
3. Resource URI **exata** (sem trailing slash).
4. Capabilities esperadas (READ / PREPARE / ACT).
5. Tool count esperado (pode ser N tools por capability GPT).
6. Garantir: MCP não cria autoridade paralela (reusa application/use cases + AuthZ canônica).

---

## FASE B — Keycloak

Criar client dedicado:

```text
mcp-<domain>
```

| Campo | Valor |
|---|---|
| Protocol | OpenID Connect |
| Access | Confidential |
| Client authentication | ON |
| Standard Flow | ON |
| Direct Access Grants | **OFF** |
| Service Accounts | **OFF** |
| PKCE | S256 |
| Token endpoint auth | `client_secret_post` (padrão comprovado ChatGPT) |

**Shared (genérico):**

```text
client scope: mcp:tools
```

- Reutilizar o mesmo scope entre MCPs.
- **Proibido** Audience mapper de resource URL específica neste scope.
- `mcp:tools` ≠ autorização de negócio.

**Transversal audience:**

```text
audience-delpi → aud contém delpi-central
```

**Dedicated (por MCP):**

```text
Audience mapper no client (ou dedicated client scope do client)
→ Included Custom Audience = https://…/<api>/mcp
→ Add to access token = ON
```

**Optional scopes:** `offline_access` (quando o Plugin solicitar refresh prolongado).

Nunca registrar client secret em docs/git/chat.

---

## FASE C — Token e isolamento

Antes do ChatGPT, Evaluate (Keycloak) ou token real de usuário:

Provar claims sanitizados:

| Claim | Esperado |
|---|---|
| `iss` | `https://minhadelpi.com.br/auth/realms/delpi` |
| `azp` | `mcp-<domain>` |
| `aud` | contém `delpi-central` **e** resource MCP deste domínio |
| `scope` | contém `openid profile email mcp:tools` (e `offline_access` se solicitado) |

Provar isolamento:

```text
aud NÃO contém resource de outro MCP
```

Exemplos:

| Client | aud deve incluir | aud NÃO deve incluir |
|---|---|---|
| `mcp-transformometro` | `…/transformometro-api/mcp` | `…/api-delpi/mcp` |
| `mcp-api-delpi` | `…/api-delpi/mcp` | `…/transformometro-api/mcp` |

Distinção crítica:

```text
Keycloak realm role offline_access
≠
OAuth scope claim "offline_access"
```

O que importa no access token é `scope` conter `offline_access` quando o Plugin pediu.

---

## FASE D — Deploy

1. Deploy da API dona do MCP **antes** de cadastrar Plugin.
2. Provar no **mesmo** interpreter do uvicorn: `import mcp`.
3. Health / readiness relevantes.
4. GET protected-resource metadata (resource + issuer + scopes).
5. OIDC discovery do realm.
6. POST `/mcp` sem token → 401 + `WWW-Authenticate`.
7. Token inválido → 401.
8. Registro de tools (in-process e, depois, provider).

Não cadastrar Plugin ChatGPT com MCP remoto quebrado.

---

## FASE E — ChatGPT Plugin

```text
Plugins → Novo plugin
```

| Campo | Valor |
|---|---|
| Name | nome do especialista (ex.: `TÉO — Transformômetro`) |
| Connection | URL do servidor |
| Server URL | resource MCP exact |
| Authentication | OAuth |
| Advanced OAuth | **Cliente OAuth definido pelo usuário** |

**Não** usar como padrão deste fluxo:

- DCR como dependência obrigatória quando já existe client governado;
- CIMD como bloqueador (aviso de CIMD indisponível **não** impede user-defined client).

Motivo: client governado já carrega audience, scopes, PKCE e lifecycle security-reviewed.

### Redirect URI — regra crítica

A redirect URI **não** se inventa antecipadamente.

1. Criar/configurar o Plugin no ChatGPT.
2. Selecionar **Cliente OAuth definido pelo usuário**.
3. ChatGPT exibe **URL de retorno**.
4. Copiar **exatamente**.
5. Keycloak → Clients → `mcp-<domain>` → Valid redirect URIs → colar.
6. Salvar → voltar ao ChatGPT → continuar OAuth.

Proibido:

- `*` / wildcards em produção;
- callback de outro Plugin (DAVI ≠ TÉO);
- callback GPT Actions (`/aip/g-.../oauth/callback`);
- URI “padrão” inventada.

### Scopes no ChatGPT

Default OAuth scopes:

```text
openid
profile
email
mcp:tools
```

Basic / always requested (padrão comprovado TÉO):

```text
offline_access
```

Client ID + Client Secret (colar direto Keycloak → ChatGPT; nunca no repositório).

Token authentication: `client_secret_post`.

---

## FASE F — Connect

1. Criar Plugin.
2. Login com **usuário real** DELPI.
3. Proibido: service account, impersonation, client credentials simulando usuário.
4. Verificar conexão OAuth.

---

## FASE G — Tool discovery

Comparar:

```text
expected tool count
vs
ChatGPT-visible tool count
```

Registrar missing / unexpected / unbound ACT.

In-process `list_tools` **não** substitui discovery do provider.

Nota TÉO: 20 GPT Actions capabilities → **32** MCP tools (READ/PREPARE/ACT). `32 ≠ 20` **não** é regression se coverage = 20/20.

---

## FASE H — READ acceptance

Executar:

1. contexto do usuário (ex. `get_my_context`);
2. catálogo equivalente;
3. uma READ real de domínio.

Provar: propagação do usuário autenticado + dado canônico.

---

## FASE I — PREPARE acceptance

PREPARE segura **sem** ACT.

Verificar: `proposal_handle`, actor binding, fingerprint, expiration, exact change, `act_allowed`.

---

## FASE J — ACT acceptance

Somente após autorização explícita de teste:

```text
READ CURRENT STATE
→ PREPARE
→ SHOW
→ CONFIRM
→ ACT(proposal_handle)
→ AUTHORITATIVE READ-BACK
→ VERIFY
```

HTTP 2xx ≠ outcome verificado. Falha de read-back → `OUTCOME_VERIFICATION_FAILED`.

---

## FASE K — Legacy

Se existir bridge anterior (GPT Actions):

- manter até parity MCP + período de transição;
- não remover nesta fase de onboarding.

Estado típico:

```text
GPT Actions = LEGACY_TRANSITIONAL_BRIDGE
MCP Plugin = TARGET
```

---

## Troubleshooting (erros já ocorridos)

### Audience de outro MCP no token

**Causa:** Audience mapper de resource específico dentro do shared `mcp:tools`.
**Correção:** mover mapper para client/dedicated scope do MCP dono.
**Prova:** TÉO e DAVI com aud isolados (2026-09-17) → `MCP RESOURCE ISOLATION = PROVEN`.

### Client “existe no browser” mas verificação diz ABSENT

**Causa:** consulta Keycloak **local** em vez de produção.
**Correção:** ENVIRONMENT PROVENANCE GATE via SSH no host prod.

### `import mcp` falhou

Provar container + Python + interpreter do uvicorn.
Não usar `.venv` do host como evidência do container.

### ChatGPT insiste em DCR

Selecionar **Cliente OAuth definido pelo usuário** e usar `mcp-<domain>` governado.

### Redirect URI desconhecida

Gerar Plugin primeiro; copiar URL de retorno do ChatGPT.

### `offline_access` só em realm roles

Insuficiente. Verificar claim `scope`.

### Tool count ≠ número de GPT Actions

Pode ser correto (PREPARE/ACT split). Medir **capability coverage**, não igualdade numérica cega.

---

## Classificação de evidência

Use sempre:

```text
PROVEN | TO_INVENTORY | PLANNED | TARGET
PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE
```

Documentação não prova runtime.
