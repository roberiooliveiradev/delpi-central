# EVA MCP V1 — Inventário factual e contratos

Missão: `EVA.MCP.V1` — primeira superfície MCP da especialista **EVA — Engenharia
Virtual Assistida**, somente leitura, sobre os contratos oficiais da
`engineering-api`.

Baseline: `origin/main` no início da missão (pós `0695a1e68c`); BASE_HEAD de
trabalho registrado no relatório de execução.

---

## 1. Inventário dos MCPs existentes

As especialistas MCP da plataforma **não são serviços separados** — cada uma é
um adapter montado dentro da API dona do domínio (`interface/mcp`), sobre o
transporte compartilhado `shared/delpi_mcp`:

| Especialista | Serviço hospedeiro | Pacote | Endpoint público |
|---|---|---|---|
| TÉO | `transformometro-api` | `tm_app/interface/mcp` | `/apps/transformometro-api/mcp` |
| VISTA | `tv-dashboard-api` | `tv_app/interface/mcp` | `/apps/tv-dashboard-api/mcp` |
| CLARA | `controllership-finance-api` | `controllership_finance_app/interface/mcp` | `/apps/controllership-finance-api/mcp` |
| DAVI | `api-delpi` | `app/interface/mcp` | `/apps/api-delpi/mcp` |
| **EVA** | **`engineering-api`** | **`engineering_app/interface/mcp`** | **`/apps/engineering-api/mcp`** |

DÉLIA atua como **consumidor/orquestrador** (`delia-api/app/infrastructure/
interoperability/mcp`), nunca como autoridade.

## 2. Matriz de referência

| Critério | TÉO / VISTA / CLARA / DAVI | EVA |
|---|---|---|
| Framework | Python MCP SDK (`mcp>=2,<3`) + `shared/delpi_mcp` | idem (`mcp==2.2.0`) |
| Transporte | Streamable HTTP, `stateless`, `json_response`, mount `/mcp` | idem |
| Metadata | RFC 9728 `/.well-known/oauth-protected-resource` pública | idem |
| Autenticação | Bearer JWT Keycloak + audience exata do recurso + scope `mcp:tools` | idem |
| Autorização negócio | Core `/me` via `delpi_auth` + owner downstream | idem — `engineering.access` + `principal_type=="user"` |
| Service token | Proibido na superfície MCP (`service_token_gate`) | idem (F2a.R1) |
| Client Keycloak | `mcp-<domain>` confidential, PKCE S256 | `mcp-engineering` (proposto) |
| Resource audience | URL exata `/apps/<api>/mcp`, env `MCP_RESOURCE_URL_<SVC>` | `MCP_RESOURCE_URL_ENGINEERING` |
| Deploy | rebuild do serviço dono via `up-prod-sequential.sh` | idem — `engineering-api` |
| Observabilidade | request id + tool + status + duração, sem tokens | idem |

## 3. Engineering API — capacidades atuais (G1)

- `GET /v1/home` (gateway `/apps/engineering-api/v1/home`): `schema_version`,
  `generated_at`, `status`, `sections`, `attention`, `tasks`, `lmps`,
  `requests`, `activity`, `collaboration` — com estados honestos por fonte
  (`available|empty|unavailable|forbidden|not_implemented`).
- `GET /v1/overview` (`/apps/engineering-api/v1/overview`): seis indicadores
  (`lmp_on_time`, `lmp_lead_time`, `lmp_total_proposals`,
  `transforma_gross_savings`, `transforma_solutions`, `transforma_roi`),
  filtros `start_date`/`end_date` (YYYY-MM-DD), `competence` (YYYY-MM),
  `branch`. Metas/IDD somente em `lmp_on_time` e `transforma_gross_savings`.
- `/health`, `/ready` — operacionais, não expostos como tools.

Capacidades sem contrato oficial (produtos, BOM, roteiros, desenhos,
especificações, inspeções, geração/aprovação/publicação) **não** têm tools —
aparecem no catálogo apenas como `planned_capabilities` marcadas
`not_implemented`.

## 4. Contrato MCP EVA V1

| Tool | Classe | Entrada | Fonte |
|---|---|---|---|
| `get_catalog` | DISCOVERY | — | declarativo (`_TOOL_CONTRACT`) |
| `get_engineering_home` | READ | — (sem parâmetros de identidade) | use case `GetEngineeringHome` |
| `get_engineering_overview` | READ | `start_date?`, `end_date?`, `competence?`, `branch?` | use case `GetEngineeringOverview` |

Invariantes:

- Zero tools de escrita; `DESTRUCTIVE_ACT_TOOLS = ∅`.
- Scopes OAuth declarados: `openid profile email mcp:tools` — nenhum código
  RBAC vaza em `securitySchemes`.
- `engineering.access` é **requisito** declarado no catálogo, não concessão.
- Erros tipados: `unauthenticated` 401, `forbidden` 403, `validation` 400,
  `timeout` 504, `upstream_error` 502 — nunca sucesso silencioso.
- Respostas preservam `generated_at`, status por fonte e provenance do
  payload oficial (sem recálculo).
- Identidade jamais entra por argumento da tool (sem `user_id`/`email`/token).

## 5. Contrato OAuth (RFC 9728)

- Resource metadata (pública): `GET /apps/engineering-api/.well-known/
  oauth-protected-resource` e `…/mcp`.
- Resource = audience exigida no `aud` do JWT: `https://minhadelpi.com.br/
  apps/engineering-api/mcp` (env `MCP_RESOURCE_URL_ENGINEERING`).
- Authorization server divulgado: `KEYCLOAK_ISSUER` (realm `delpi`).
- `WWW-Authenticate` em 401 transporta `resource_metadata=…` + scopes.
- `aud` deve conter `delpi-central` **e** a audience do recurso EVA — e não a
  de outro MCP (isolamento comprovado no runbook transversal).

## 6. Owners preservados

Keycloak (identidade/SSO) · Core API (RBAC efetivo) · engineering-api
(contratos + composição) · APIs de domínio (dados/autorização por recurso) ·
EVA/MCP (adapter de interoperabilidade, não autoridade) · ChatGPT/DÉLIA
(consumidores). Nenhuma autoridade foi alterada nesta missão.

## 7. Referências

- `docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`
  (padrão oficial de onboarding MCP/ChatGPT).
- `transformometro-api/tm_app/interface/mcp/*` (implementação de referência).
- `docs/12-roadmap-e-evolucao/engineering/05-f1-g0-architecture-decisions.md`,
  `06-f1-g0-core-authz-contract.md`, `12-f2a-home-contract-and-implementation.md`.
