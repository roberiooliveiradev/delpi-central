# TÉO / Transformômetro — OpenAI Plugin + MCP

> Documentation does not prove runtime. Evidence below is classified; revalidate after material deploy/auth changes.

Shared onboarding (novos MCPs):
[`docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`](../../../docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md)

## Specialist identity

| Field | Value |
|---|---|
| Short name | **TÉO** |
| Full name | TÉO — Especialista em Transformação Digital |
| Plugin display name | `TÉO — Transformômetro` |
| Mission | Transformação / eficiência / otimização de processos no Transformômetro |
| Role | Conversational specialist = **governed MCP consumer** |

```text
TÉO capability ≤ authenticated user capability
ChatGPT confirmation ≠ authorization
MCP ≠ Domain API
MCP ≠ RBAC
MCP ≠ generic proxy
AuthZ final = backend / domínio Transformômetro
```

Branding ≠ authorization.

## Technical identities

| Surface | Technical id |
|---|---|
| Plugin / MCP server name | `transformometro` |
| Keycloak client | `mcp-transformometro` |
| MCP endpoint / resource | `https://minhadelpi.com.br/apps/transformometro-api/mcp` |
| Protected Resource Metadata | `https://minhadelpi.com.br/apps/transformometro-api/.well-known/oauth-protected-resource` |
| OIDC issuer | `https://minhadelpi.com.br/auth/realms/delpi` |
| Manifest | `integrations/openai-plugin/mcp.json` |

## Architecture

```text
Workspace Agent / ChatGPT Plugin (TÉO)
  → OAuth Authorization Code + PKCE (user-defined client)
  → Keycloak end-user identity (mcp-transformometro)
  → MCP Streamable HTTP /apps/transformometro-api/mcp
  → interface/mcp adapter
  → application services + governed writes (FULL_CRUD_GOVERNED)
  → canonical AuthZ (capability ≤ user)
  → Postgres transformometro
```

## Surface policy

```text
TEO_MCP_SURFACE = FULL_CRUD_GOVERNED
READ + PREPARE + ACT = REQUIRED
DAVI_READ_ONLY_COPY = FORBIDDEN
```

### Capability vs tools

```text
21 GPT Actions capabilities
≠
33 MCP tools
```

No MCP atual, 1 capability GPT pode decompor-se em READ / PREPARE / ACT.

| Métrica | Valor | Classificação |
|---|---|---|
| GPT Actions importable | **21**, incluindo `gpt_get_methodology_guide` | CURRENT no código |
| GPT Actions em 2026-09-17 | 20 | HISTORICAL |
| MCP tools registered | **33** (10 READ + 1 ANALYSIS + 11 PREPARE + 11 ACT) | código; ChatGPT 33/33 = TEST_NOT_RUN |
| Unbound ACT | 0 | PROVEN |
| ACT input | somente `proposal_handle` | PROVEN (código) |

`33 ≠ 21` **não** é regression. A metodologia existe nas duas superfícies pela mesma fonte. Writes MCP continuam PREPARE/ACT. Ver `teo-mcp-capability-parity.md`.

## Methodology guide

```text
Agent Instructions = coordenação
query_methodology_guide = fonte única
MCP get_methodology_guide = adapter
GPT gpt_get_methodology_guide = adapter legado
Transformômetro domain = dados e regras finais
```

A capability é READ-only. Método não autoriza, não persiste e não transforma hipótese em fato. SIPOC, Ishikawa, SWOT e os demais playbooks **não** viram entidades. Diagramas continuam em `get_catalog.diagram_catalog` (`flowchart_v1` canônico; Mermaid derivado).

Fonte editorial: `docs/gpt-actions/teo-method-playbooks.md`. Runtime: `tm_app/application/methodology/guide.py`.

GPT Builder: reimportar o OpenAPI depois do deploy. O app MCP publicado não muda de schema nesta Action.

## Write governance (MCP)

```text
PREPARE → proposal_handle
ACT → proposal_handle only
```

Proposal (server-side) contém: actor binding, exact change, state fingerprint, expiration, expected postcondition.

ACT: revalida AuthZ + fingerprint → executa exact change → authoritative read-back → verifica outcome.

Se read-back falhar:

```text
OUTCOME_VERIFICATION_FAILED
```

| Item | Estado |
|---|---|
| Proposal store | in-process, TTL ≈ 15 min |
| Replicas (prod) | 1 |
| `CURRENT SINGLE-REPLICA OPERATION` | **ACCEPTED_WITH_RESIDUAL** |
| Shared proposal store (Redis etc.) | **TARGET** se escala horizontal |

Incomplete packages: `ready=false` / `act_allowed=false` → NO WRITE.
Honor `confirm_*`. MCP metadata / OAuth scopes ≠ RBAC.

## Shared OAuth vs isolated resource

Mesma regra transversal que DAVI:

| Camada | Valor |
|---|---|
| Shared scope | `mcp:tools` (genérico; **não** carrega audience de um MCP) |
| Transversal aud | `delpi-central` via `audience-delpi` |
| Dedicated aud TÉO | `https://minhadelpi.com.br/apps/transformometro-api/mcp` |
| Dedicated aud DAVI | `https://minhadelpi.com.br/apps/api-delpi/mcp` |

```text
shared scope ≠ resource binding
MCP RESOURCE ISOLATION = PROVEN / PASS (2026-09-17)
```

Detalhes Keycloak: [keycloak-mcp-client-runbook.md](./keycloak-mcp-client-runbook.md).

## Auth model

- Transport exige OAuth antes de tools/list
- JWT `azp` = `mcp-transformometro`
- JWT `aud` inclui `delpi-central` **e** resource TÉO; **não** resource DAVI
- JWT `scope` inclui `openid profile email mcp:tools` (+ `offline_access` quando solicitado pelo Plugin)
- Service tokens / client credentials simulando usuário = proibidos em `/mcp`

## Bridge

| Surface | Client | Lifecycle |
|---|---|---|
| GPT Actions | `chatgpt-transformometro` | **LEGACY_TRANSITIONAL_BRIDGE** (21 importable operationIds; `gpt_get_openapi_schema` continua meta) |
| MCP Plugin | `mcp-transformometro` | **CURRENT** para agents |

Não remover GPT Actions nesta fase. Critério futuro de depreciação:

```text
MCP runtime acceptance suficiente
+ capability parity comprovada
+ writes governados aceitos
+ período de transição definido
```

## Production evidence (2026-09-17) — ENVIRONMENT PROVENANCE = SSH `srv-api`

Primeira verificação usou stack **local** → falsos ABSENT (client, scope, import). **INVALIDATED_BY_WRONG_ENVIRONMENT.**

Verificação corrigida (produção):

| Check | Status |
|---|---|
| Código com governança `b4454fea…` no runtime | PASS |
| `mcp==1.30.0` no Python 3.11 do uvicorn | PASS |
| `import mcp` | PASS |
| FastMCP carregado | PASS |
| Endpoint MCP | PASS |
| Protected-resource metadata | PASS |
| Keycloak PROD (`mcp-transformometro`, scopes) | PASS |
| GPT Actions importable em 2026-09-17 | 20 (HISTORICAL) |
| GPT Actions importable no código | 21 |
| MCP tools em 2026-09-17 | 32 (HISTORICAL) |
| MCP tools no código | 33 |
| Replicas | 1 | PASS |

## ChatGPT Plugin acceptance (PROVEN)

| Check | Status |
|---|---|
| Plugin criado (`TÉO — Transformômetro`) | PASS |
| OAuth user connection | PASS |
| Tools discovery | 32/32 PASS em 2026-09-17; código atual = **33** (`get_methodology_guide`). Rediscovery no app publicado = **TEST_NOT_RUN** |
| `get_my_context` | PASS |
| `get_catalog` | PASS |
| `search_records` (entity=process, q=Transforma → PROC-0001 ativo; diagram_node_count=115; decomposition_node_count=64) | PASS |
| Authenticated tool execution | PASS |
| READ domain data | PASS |
| PREPARE via ChatGPT | **TEST_NOT_RUN** |
| ACT via ChatGPT | **TEST_NOT_RUN** |
| WRITE BUSINESS OUTCOME | **TEST_NOT_RUN** |

Não promover PREPARE/ACT/outcome por esta evidência.

## Residuals

| Gap | Status |
|---|---|
| PREPARE acceptance real via ChatGPT | TEST_NOT_RUN |
| ACT acceptance real via ChatGPT | TEST_NOT_RUN |
| WRITE BUSINESS OUTCOME | TEST_NOT_RUN |
| Refresh-token lifecycle prolongado | só promover a PROVEN com evidência runtime adequada |
| Horizontal scaling + in-process proposals | TARGET |

## Ops

1. Deploy `transformometro-api` com dependency `mcp` no mesmo Python do runtime.
2. Keycloak per [keycloak-mcp-client-runbook.md](./keycloak-mcp-client-runbook.md) (audience dedicada; shared `mcp:tools` limpo).
3. Registrar Plugin com client governado + redirect URI copiada do ChatGPT.
4. Smoke: READ live (feito) → PREPARE → ACT com autorização explícita.
5. Checklist: [teo-mcp-plugin-agent-smoke.md](./teo-mcp-plugin-agent-smoke.md).

## Code ownership

| Piece | Path |
|---|---|
| OAuth contract | `tm_app/interface/mcp/oauth_contract.py` |
| FastMCP server | `tm_app/interface/mcp/server.py` |
| Tool bridge | `tm_app/interface/mcp/tool_bridge.py` |
| Governed writes | `tm_app/application/governed_writes/` |
| Auth middleware | `tm_app/middleware/auth_middleware.py` |
| Mount | `tm_app/main.py` → `/mcp` |
