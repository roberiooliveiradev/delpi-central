# EVA MCP V1 — Implementação e validação

Implementação end-to-end da superfície MCP da **EVA — Engenharia Virtual
Assistida**, montada na `engineering-api` (mesmo padrão TÉO/VISTA/CLARA/DAVI:
a API dona do domínio hospeda o próprio adapter MCP).

## 1. Arquitetura

```text
ChatGPT / DÉLIA
   │  Bearer JWT humano (Keycloak, aud = resource EVA + delpi-central)
   ▼
gateway  /apps/engineering-api/mcp ──► engineering-api:8000/mcp
   ▼
jwt_middleware (transport gate MCP)
   ├─ is_mcp_data_path → mcp_transport_auth (delpi_mcp)
   │    ├─ Bearer humano obrigatório — service token proibido (F2a.R1)
   │    ├─ aud exata do recurso + scope mcp:tools
   │    └─ WWW-Authenticate challenge (RFC 9728)
   ▼
delpi_auth base middleware → Core /me → principal + permissions
   ▼
MCPServer (mcp SDK, streamable HTTP, stateless, json_response)
   ▼
tool_bridge (adapter fino)
   ├─ _require_engineering_human(): principal_type=="user"
   │    + engineering.access (+ is_superadmin)  — mesma gate das rotas /v1
   └─ use cases canônicos (composition root) — sem recálculo
   ▼
GetEngineeringHome / GetEngineeringOverview
   ▼
owners downstream com Bearer humano propagado
```

Não foi criado serviço `mcp-engineering` separado: o padrão comprovado da
plataforma é o adapter in-process no serviço owner — mesma cadeia de
AuthN/AuthZ, mesmo lifecycle, mesmo deploy.

## 2. Arquivos

Novos (`engineering-api/engineering_app/interface/mcp/`):

| Arquivo | Papel |
|---|---|
| `constants.py` | tool names, classes (DISCOVERY/READ), client id `mcp-engineering`, canonical resource URL |
| `oauth_contract.py` | scopes OAuth, audience exata, challenge RFC 9728 (via `delpi_mcp.resource_contract`) |
| `resource_metadata.py` | `McpResourceConfig` + metadata document + hosts/origins do transport security |
| `routes.py` | router público `/.well-known/oauth-protected-resource(/mcp)` |
| `server.py` | `EngineeringMCPServer` — 3 tools, `securitySchemes` wire, annotations, instructions EVA |
| `tool_bridge.py` | adapter fino: contexto → use cases → `CallToolResult` tipado |
| `branding.py` | nome/missão/instructions EVA (grounding honesto) |
| `asgi.py` | `streamable_http_app` + mount path middleware + lifespan combinado |

Modificados:

- `engineering_app/middleware/auth_middleware.py` — gate de transporte MCP
  (`mcp_transport_auth` + `McpTransportAuthPolicy` + `service_token_gate`),
  metadata RFC 9728 como path público.
- `engineering_app/main.py` — `app.mount("/mcp")`, metadata router, lifespan
  combinado, mount-path middleware.
- `engineering-api/requirements.txt` — `mcp==2.2.0`; `pydantic>=2.12,<3`
  (exigência do SDK MCP 2.2.0 — conflito comprovado com pin 2.11.9).
- `engineering-api/tests/test_architecture.py` — `mcp`/`delpi_mcp` permitidos
  somente em `interface/mcp` (e `delpi_mcp.auth` no middleware); novo guard
  `test_inner_layers_never_import_mcp_adapter`.
- `engineering-api/tests/test_eva_mcp.py` — 23 testes (contrato, transporte,
  AuthZ negócio, bridge, conformidade).
- `infra/docker-compose.yml` — `MCP_RESOURCE_URL` + `PUBLIC_BASE_URL` no
  serviço `engineering-api`.
- `gateway/nginx.conf` + `gateway/nginx.dev.conf` — bloco engineering-api com
  `proxy_buffering off`, `Upgrade`/`Connection`, `proxy_read_timeout 86400`
  (streamable HTTP, mesmo padrão transformometro-api).

## 3. Ferramentas (G4–G6)

| Tool | Implementação |
|---|---|
| `get_catalog` | tools implementadas (schema in/out, classe, permissão requerida, owner, source) + `planned_capabilities` marcadas `not_implemented` + notas de disponibilidade e elegibilidade de metas |
| `get_engineering_home` | delega `GetEngineeringHome` com `HomeSourceContext` do principal humano; sem parâmetros |
| `get_engineering_overview` | validação idêntica à rota REST (`_validate_overview_filters`) → `OverviewQuery` → `GetEngineeringOverview` |

Ambas propagam `access_token` humano e `request_id` — rastreio
`MCP → engineering-api → owner` preservado.

## 4. Segurança (G3/G8)

- Transporte: Bearer JWT validado por `delpi_auth.validate_token` + audience
  exata do recurso + `mcp:tools`; challenge com `resource_metadata`.
- Negócio: `principal_type=="user"` + `engineering.access` (ou superadmin) —
  o MCP não concede nem infere permissão; a autorização efetiva continua
  Core + owners.
- Delegação: o Bearer humano é propagado aos downstreams; service token é
  rejeitado na superfície MCP (`service_token_gate`) — F2a.R1 preservado.
- Grounding: `EVA_MCP_INSTRUCTIONS` proíbe recalcular indicadores/metas/IDD,
  exige provenance e trata conteúdo downstream como não confiável.
- Isolamento: sem cache compartilhado, sem identidade por argumento, sem
  tokens em respostas/logs.

## 5. Testes e evidências

- `tests/test_eva_mcp.py` — **23 testes**: freeze de contrato, scopes,
  audience, metadata, challenge, wire `list_tools`, conformance
  (`delpi_mcp.conformance`, protocol mínimo), transporte (sem Bearer, aud
  ausente, scope ausente, service token, válido, metadata pública), AuthZ
  negócio (catalogo/home sem permissão, principal de serviço, sem contexto),
  delegação com token humano, validação de filtros, erro upstream honesto.
- Suíte completa engineering-api: **219 passed**.
- `test_architecture.py`: imports `mcp`/`delpi_mcp` confinados ao adapter +
  middleware; camadas internas não importam `interface.mcp`.
- Audits CI locais: `audit_backend_boundaries`, `audit_fastapi_authz`,
  `audit_platform_guardrails`, `audit_architecture_phase3` — **0 findings**.
- Docker build `delpi-engineering-api:eva-test` — OK; import de
  `engineering_app.main` + `interface.mcp` dentro da imagem — OK
  (pydantic 2.14.1 resolvido por `>=2.12,<3`).
- `docker compose config` — válido.

Não executado nesta etapa (depende de credenciais/ambiente): smoke
autenticado com JWT real Keycloak e conexão ChatGPT — gates registrados nos
docs 28/29 e no relatório de execução como `TEST_NOT_RUN`/`PENDING`.

## 6. Deploy e rollback

- Deploy: rebuild somente de `engineering-api` (+ gateway reload para o bloco
  nginx) via `infra/scripts/up-prod-sequential.sh`.
- Rollback: `git revert` do commit + redeploy de `engineering-api` e gateway;
  o adapter MCP é autônomo e não altera rotas `/v1` existentes.
- Endpoint fica **fail-closed** até a configuração Keycloak (client
  `mcp-engineering` + audience mapper dedicado): sem JWT com aud/scope
  corretos toda chamada `/mcp` retorna 401.
