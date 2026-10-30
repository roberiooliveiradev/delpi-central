# SURI — S1 Contract Freeze

> **Plano:** SURI-MCP-MASTER-001 · **Etapa:** S1 · **BASE:** commit S0 `9cd69b9dda`  
> Congela nomes, schemas, contrato OAuth/resource e catálogo. Nenhuma permissão é criada por tool; `mcp:tools` é binding de transporte, nunca grant de negócio.

## 1. Identidade técnica (frozen)

| Item | Valor |
|---|---|
| MCP server name | `supplies` |
| Persona | SURI — Especialista em Suprimentos da Minha DELPI |
| Canonical resource URL (TARGET) | `https://minhadelpi.com.br/apps/supplies-api/mcp` |
| Gateway root | `/apps/supplies-api` |
| Internal mount | `/mcp` (ASGI `streamable_http_app`, `stateless_http=True`, `json_response=True`) |
| Keycloak client (candidato — **não registrar**) | `mcp-supplies` |
| Realm/flows | confidential; authorization code + PKCE S256; direct access grants OFF; service accounts OFF |
| Required scopes (claim `scope`) | `openid profile email mcp:tools` |
| Required audience (claim `aud`) | resource URL exata (`MCP_RESOURCE_URL` env > `PUBLIC_BASE_URL`+gateway root > canonical) |
| Protected-resource metadata | `{PUBLIC_BASE_URL}/apps/supplies-api/.well-known/oauth-protected-resource` |
| Catalog version | `1` |

## 2. Tools congeladas (RQ→tool→owner→AuthZ)

| Tool | Classe | Owner upstream | AuthZ exigida (server-side, por call) |
|---|---|---|---|
| `get_my_context` | READ | Core `/me` via delpi_auth | principal humano; retorna capabilities declarativas, **sem grant** |
| `get_catalog` | DISCOVERY | contrato local | autenticado; lista tools implementadas + limites |
| `list_purchase_orders` | READ | `GET /purchase-orders` → `DelpiApiGateway` → api-delpi `/supplies/purchase-orders` | `can_use_operations` (`supplies.access`) + `require_units(branch)` — fail-closed, ≥1 branch ⊆ ("01","02") |
| `get_purchase_order` | READ | `GET /purchase-orders/<branch>/<number>` | `can_use_operations` + `require_unit(branch)` |
| `search_supplies_knowledge` | READ | corpus `app/content/suri_knowledge.json` (manual oficial do Portal Suprimentos) | `supplies.access` |
| `get_knowledge_item` | READ | idem | `supplies.access` |
| `list_knowledge_sources` | DISCOVERY | idem | `supplies.access` |
| `analyze_purchase_orders` | ANALYSIS | mesmo contrato de `list_purchase_orders` | `can_use_operations` + `require_units(branch)` |

Decisão S1: `get_purchase_order` incluído (rota existe, custo marginal, paridade Portal). Nenhuma tool de escrita, export, suppliers, requests ou market-intelligence nesta release.

## 3. Input contracts (frozen)

`list_purchase_orders` / `analyze_purchase_orders` compartilham o filtro:

| Campo | Tipo | Obrig. | Regra |
|---|---|---|---|
| `branch` | `list[str]` | sim | 1..2 itens; cada um ∈ `("01","02")`; `require_units` fail-closed |
| `order_number`, `product_code`, `supplier_code` | `str` | não | pass-through ao contrato BFF |
| `expected_delivery_from`, `expected_delivery_to` | `str` | não | `YYYY-MM-DD` |
| `late_only` | `bool` | não | default `false` |
| `sort_by`, `sort_dir` | `str` | não | pass-through; `sort_dir` ∈ `asc|desc` quando presente |
| `page` | `int` | não | ≥1, default 1 (`list_purchase_orders` apenas) |
| `page_size` | `int` | não | 1..100, default 25 (`list_purchase_orders` apenas) |
| `sample_size` | `int` | não | 1..100, default 50 (`analyze_purchase_orders` apenas — janela determinística) |

`get_purchase_order`: `branch: str` (obrig.), `order_number: str` (obrig., não vazio).
`search_supplies_knowledge`: `query: str|None`, `topic: str|None`, `limit: int 1..20` (default 8).
`get_knowledge_item`: `knowledge_id: str` (obrig.).

## 4. Output/error contract (frozen)

- Sucesso: `{success: true, message: "ok", data: <payload>}` via `mcp_tool_result`; `structuredContent` espelha o envelope.
- Falha tipada: `{success: false, message, data: {error_code, error_kind, ...}, status_code}`; `error_kind ∈ unauthenticated|forbidden|not_found|conflict|validation|upstream|internal`.
- 401 em tool adiciona `_meta["mcp/www_authenticate"]` = `[challenge]` (forma lista — padrão CLARA/DAVI/TÉO).
- Nenhum stack trace, token, header ou secret em `data`; `redact_error_details` aplica-se.
- `list_purchase_orders` retorna o payload BFF desembrulhado + `_meta.source="bff:/purchase-orders"`; payload contém `items`, `total` e campos de paginação do contrato upstream — **sem reinterpretação**.
- `analyze_purchase_orders` retorna `{facts[], calculations[], recommendations[], input_hash, source, sample}` — achados rotulados `FACT` (dado owner) / `CALCULATION` (determinístico reproduzível) / `RECOMMENDATION` (orientação, nunca ACT).
- Knowledge: itens com `knowledge_id`, `title`, `summary`, `content`, `topic`, `source` (`{file, locator, authority}`), `evidence_class ∈ PROVEN|OWNER_REPORTED|TO_INVENTORY`, `corpus_version`, `corpus_sha256`.

## 5. Transport contract (frozen)

- `POST /mcp` JSON-RPC (Streamable HTTP, stateless, JSON responses); `GET /mcp` → 405 SDK; GET `/.well-known/oauth-protected-resource` público.
- 401 com `WWW-Authenticate: Bearer realm="suri-mcp" resource_metadata="<metadata_url>" scope="openid profile email mcp:tools" error=...` (separator espaço, scopes antes do par de erro — forma DAVI/TÉO/CLARA).
- DNS-rebinding protection on; allowlist = localhost + `{host do PUBLIC_BASE_URL}` + origins ChatGPT (`https://chatgpt.com`, `https://chat.openai.com`).
- Service tokens (`X-Delpi-Service-Token`) → 401 `User authentication required`.
- `principal_type != "user"` rejeitado na tool (defesa em profundidade).
- Nenhum endpoint de negócio Flask é exposto pelo processo MCP; o adapter só serve `/mcp` + metadata + `/healthz`.

## 6. Testes previstos (gate S4/S7)

Positive: initialize/list_tools/call_tool com user `supplies.access`+unidade válida. Sibling: branch "02", outro filtro. Negative: sem Bearer, aud errada, scope faltando, service token, `supplies.access` ausente (403), branch fora ("03") (403), sem branch (403 fail-closed), Core indisponível (503/upstream), tool desconhecida, JSON-RPC malformado, cross-request actor leak. Conformance: `list_tools` expõe `securitySchemes`/`delpi/toolClass`/schemas.
