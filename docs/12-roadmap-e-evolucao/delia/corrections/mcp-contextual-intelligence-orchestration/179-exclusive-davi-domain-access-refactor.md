# 179 — DÉLIA · Exclusive DAVI Domain Access Refactor

**TASK_ID:** `DELIA-C3-DAVI-EXCLUSIVE-DELPI-DOMAIN-ACCESS-REFACTOR-01`
**Executor:** Cursor / Devin
**Base HEAD:** `cd3eb369c72aae5deead18cbe2d0545581eea124`
**Decisão de produto:** explícita do usuário — eliminar o caminho direto DÉLIA → API DELPI; DAVI (`mcp-api-delpi`) é a superfície de integração empresarial para esses dados. Direção **não** reaberta.
**Status:** implementado localmente; deploy NÃO autorizado/não executado.

---

## 1. Reancoragem

HEAD/origin `cd3eb369c7`; worktree limpa antes do diff. Autoridades 16→50→17→49→51→52→21→20→25; docs 170–178; ledger; arquitetura provider-neutral (§6.130), MCP capability authority (§6.118/§6.126). Fase C3 — CP/RQ não avançado.

## 2. Inventário — caminho direto

O acesso direto DÉLIA → API DELPI existe como **família de provider OpenAPI** com um único source:

- `root_composer._wire_openapi_provider` → `build_openapi_source(source_id="delpi")` → `OpenApiCapabilityProvider`.
- Config: `DELIA_OPENAPI_DELPI_ENABLED` + `DELIA_OPENAPI_DELPI_BASE_URL` + `DELIA_OPENAPI_DELPI_DECLARATIONS_PATH` (settings.py; compose prod/dev; env.example).
- Contrato semântico governado: `delia-api/config/openapi_declarations.delpi.json` — 4 capabilities declaradas.

O caminho DAVI já existe: `McpCapabilityProvider` → `SpecialistInterop` → specialist `davi` (resource `mcp-api-delpi`), tools live `tools/list` → grupos de capability. A orquestração já implementa o fluxo do owner `candidate_token` (discover→execute) via `_is_candidate_bound`/`_discover_candidate`/`_candidate_arguments` — nenhum mecanismo novo criado.

## 3. Inventário — superfície DAVI (owner real)

`api-delpi/app/interface/mcp/server.py`: 2 tools — `discover_delpi_information` (classe DISCOVERY) e `execute_delpi_information` (classe READ). Ações executáveis = action index construído do OpenAPI do owner filtrado por `app/content/davi_external_read_allowlist.json` (**97 operações**). Erros: `CallToolResult{isError:true, structuredContent:{code:"VALIDATION_ERROR", message}}` para rejeição de parâmetros/token (`validation_error_tool_result`); `PermissionError` → isError + meta WWW-Authenticate/“Forbidden”; transport 401/403 → autenticação/autorização.

## 4. Matriz de migração

| Capability direta | Operação owner | DAVI (allowlist) | Ação |
|---|---|---|---|
| `delpi.search_products` | `search_products` | ✓ presente | **Migrada** — declaração removida |
| `delpi.get_product_stock` | `get_product_stock` | ✓ presente | **Migrada** — declaração removida |
| `delpi.get_product_summary` | `get_product_summary` | ✗ ausente (`get_product_detail` ≠ superset: sem stock/prices) | **`CAPABILITY_MIGRATION_BLOCKED` — preservada sob bloqueio** |
| `delpi.search_customers` | `search_customers` | ✗ ausente | **`CAPABILITY_MIGRATION_BLOCKED` — preservada sob bloqueio** |

**`OWNER_DECISION_REQUIRED` (api-delpi/DAVI):** exposição de `get_product_summary` e `search_customers` na allowlist de READ externo (ou substituto semântico aprovado). Alteração de superfície do owner não autorizada nesta task → as duas declarações permanecem como único remanescente do binding direto — não duplicatas: são as únicas formas de chegar a essas operações.

Delta funcional registrado (não bloqueante, mas real): a projeção externa de `search_products` via DAVI aprova somente `code, description, group_code, page, page_size` (`PRODUCT_SEARCH_INPUT_FIELDS`) — `product_type`, `sort`, `direction` e `customer_reference` não entram pelo caminho DAVI. `customer_reference` já era deny-by-default; `product_type` inválido agora falha na **validação de argumentos do DAVI** (VALIDATION_ERROR) antes de chegar à rota — recuperável pelo contrato tipado, resolvendo a lacuna de declaração do doc 177 para este fluxo.

## 5. Mudanças implementadas

| Arquivo | Mudança |
|---|---|
| `delia-api/config/openapi_declarations.delpi.json` | 4→2 declarações: removidas `search_products`/`get_product_stock` (cobertas por DAVI); mantidas as 2 bloqueadas |
| `delia-api/app/application/specialist_interop/errors.py` | `OWNER_ARGUMENT_REJECTED` — valor canônico do código de provider no vocabulário leaf de erros do boundary |
| `delia-api/app/application/capability_provision/contracts.py` | constante passa a re-exportar do leaf (fonte única; OpenAPI e MCP projetam o mesmo código) |
| `delia-api/app/application/specialist_interop/specialist_interop.py` | `_normalize_outcome`: `isError` com `structuredContent.code` ∈ `{VALIDATION_ERROR}` e sem `recoverable:false` → `SpecialistInteropError(OWNER_ARGUMENT_REJECTED)` + hint sanitizado de `structured.message`; demais resultados de erro → `mcp_protocol_error` (inalterado) |
| `delia-api/tests/test_specialist_interop_usecase.py` | +4 testes da matriz de erro MCP |
| `delia-api/tests/test_openapi_capability_provider.py` | +1 teste do arquivo governado de declarações |
| `delia-api/scripts/governed_davi_migration_eval.py` | eval pareado B0 direto × B1 DAVI |

**Preservados (componentes compartilhados, não removidos):** `HttpOpenApiInvoker`, `OpenApiCapabilityProvider`, `source_loader`, `capability_catalog_adapter`, settings/envs `DELIA_OPENAPI_DELPI_*` (necessários às 2 capabilities preservadas), `_wire_openapi_provider`. Nenhum adaptador, planner, engine ou catálogo novo. Nenhum regex/roteamento por provider — a seleção permanece semântica sobre o catálogo live (DAVI `tools/list` → grupo `davi`).

## 6. RED → GREEN

- **RED:** `test_remote_error_typed_validation_code_is_argument_rejected` falhava (`mcp_protocol_error`); `test_governed_delpi_declarations_exclude_davi_covered_capabilities` falhava (`delpi.search_products` ainda declarada).
- **GREEN:** +5 testes passam; arquivos tocados 148 testes verdes (interop usecase, openapi provider, goal/evidence relevance, mcp adapter, interop security).

## 7. Avaliação pareada B0 × B1 (`governed_davi_migration_eval.py`)

Mesmas propostas stage-conditioned por família, mesma rejeição inicial, mesma proposta de reparo. B1 usa a porta MCP real (`SpecialistInterop` + `McpCapabilityProvider`) com wire MCP roteado por fake port (discover→execute do owner preservado — o passo discover re-executa por invocação candidate-bound, conforme contrato do owner).

| Cenário | B0 direto | B1 DAVI |
|---|---|---|
| declared_recoverable_rejection | SUCCESS (2 wire: invoke+repair) | **SUCCESS** (4 wire: discover+execute, repair, discover+execute) → relevance → synthesis |
| undeclared_rejection | SOURCE_UNAVAILABLE (1) | SOURCE_UNAVAILABLE (2: discover+execute) — fail closed |
| explicit_non_recoverable | terminal (1) | terminal (2) |
| forbidden | AUTHZ_DENIED (1) | AUTHZ_DENIED (2) |
| transient_unavailable | terminal (1) | terminal (2) |
| repeated_declared_rejection | bounded stop (2) | bounded stop (4) — teto mantido |

`FALSE_POSITIVES=0`, `FABRICATED_RECORDS=0`, `UNAUTHORIZED_ACTS=0`, `UNAUTHORIZED_PREPARES=0`, `UNBOUNDED_LOOPS=0`. A diferença de wire_calls (2×) é o passo discover do próprio contrato owner, não retry.

## 8. Regressão e segurança

- Suíte completa `delia-api/tests/`: **1 falha pré-existente** — `PRE_EXISTING_CRI_CONTRACT_DRIFT` (doc 177 residual do owner da instrução; inalterada).
- Architecture Phase 3 gate `--base HEAD --check`: OK.
- AuthZ: transporte MCP 401/403 → `mcp_authentication_failed`/`mcp_authorization_denied` (inalterado); erro de ferramenta "Forbidden" permanece `mcp_protocol_error` + hint (comportamento anterior preservado — residual §10).
- `structuredContent`/`_meta` de ferramenta seguem untrusted-data; o hint é sanitizado (printable, ≤160, sem URL).
- Zero secrets em diff/testes/scripts; eval sem rede.

## 9. Caminho removido / remanescente

- **Removido do catálogo:** `delpi.search_products`, `delpi.get_product_stock` — agora servidas exclusivamente por DAVI (discover→execute→`search_products`/`get_product_stock` no action index allowlisted).
- **Remanescente sob bloqueio:** `delpi.get_product_summary`, `delpi.search_customers` — `CAPABILITY_MIGRATION_BLOCKED`, dependentes de decisão do owner DAVI (allowlist). Sem fallback silencioso: são as únicas declarações restantes, não aliases das capacidades DAVI.
- Variáveis `DELIA_OPENAPI_DELPI_*` permanecem — requeridas pelo binding remanescente; removê-las eliminaria as 2 capabilities preservadas.

## 10. Residuais

1. `OWNER_DECISION_REQUIRED`: `get_product_summary` + `search_customers` na allowlist DAVI (owner api-delpi). Após exposição, remover as 2 declarações e, então, avaliar retirada completa do binding/settings.
2. `VALIDATION_ERROR` do DAVI cobre também erros GovernedExecutionError não-argumentais ("Action is not DAVI-eligible", "Catalog action execution failed") — semanticamente amplos para "argument rejected"; o recovery é bounded (≤1 reparo) então o pior caso é uma reformulação desperdiçada. Owner pode especializar códigos (doc 178).
3. Erro "Forbidden" como tool-result → `mcp_protocol_error` (não `mcp_authorization_denied`) — comportamento anterior, preservado; owner pode declarar código AuthZ tipado no structured content.
4. `PRE_EXISTING_CRI_CONTRACT_DRIFT` — inalterado, owner da instrução.
5. Security gate doc 174 — inalterado (deploy não autorizado de qualquer forma).

## 11. Veredito

**LOCAL_PASS_WITH_RESIDUAL / PARTIAL_MIGRATION** — o caminho DAVI substitui funcionalmente o direto para 2 de 4 capabilities com paridade contratual comprovada (incluindo recuperação READ governada, AuthZ fail-closed e descoberta live); as 2 restantes permanecem sob bloqueio legítimo de owner, documentadas — capacidade produtiva não foi removida sem substituto. `INDEPENDENT_REVIEW=PENDING`. Deploy não executado por escopo de autorização.
