# SURI — Semantic Contract Freeze (rev.2)

> **Status:** FROZEN — executado em `SURI-MCP-TOOLS-SEMANTIC-001`.
> **Substitui:** rev.1 (`SURI-S1-CONTRACT-FREEZE.md`, superfície de 8
> tools endpoint-oriented), que permanece como registro histórico.
> Substituição atômica permitida pelo plano §2: sem consumidores vivos
> (Keycloak não registrado, ChatGPT não conectado).
> **Plano:** `SURI-MCP-SEMANTIC-TOOLS-REFACTOR-PLAN.md`.

## 1. Superfície pública — exatamente 4 tools

| Tool | Classe | Discriminador | Capacidades v1 |
|---|---|---|---|
| `get_context` | DISCOVERY | `action` | `context`, `catalog` |
| `read` | READ | `entity` + `action` | `purchase_orders`: `search`, `get` |
| `analyze` | ANALYSIS | `analysis` | `purchase_orders_summary` |
| `knowledge` | READ | `action` | `search`, `get`, `sources` |

Zero ACT/PREPARE. `execute` e `delete` são famílias TARGET documentadas
— nunca registradas até existir contrato + autorização reais.

## 2. Paridade 8→4 (comportamento legado preservado)

| Legado rev.1 | Envelope rev.2 |
|---|---|
| `get_my_context` | `get_context(action=context)` |
| `get_catalog` | `get_context(action=catalog)` |
| `list_purchase_orders` | `read(entity=purchase_orders, action=search, filters)` |
| `get_purchase_order` | `read(entity=purchase_orders, action=get, identity)` |
| `analyze_purchase_orders` | `analyze(analysis=purchase_orders_summary, filters, sample_size)` |
| `search_supplies_knowledge` | `knowledge(action=search, query/topic/limit)` |
| `get_knowledge_item` | `knowledge(action=get, knowledge_id)` |
| `list_knowledge_sources` | `knowledge(action=sources)` |

## 3. Schemas tipados (wire)

- Discriminadores são `const`/`enum` JSON Schema via `Literal` — valores
  fora do conjunto falham na validação de argumentos do SDK.
- `filters`/`identity` são modelos pydantic `extra="forbid"` →
  `additionalProperties: false` no wire; chaves desconhecidas → 422
  (`ValidationError` mapeado), nunca encaminhadas à BFF.
- `read(action=search)` → `PurchaseOrderSearchFilters` (branch
  obrigatória, vocabulário BFF completo + paginação).
- `read(action=get)` → `PurchaseOrderIdentity` `{branch, order_number}`.
- `analyze` → `PurchaseOrderAnalyzeFilters` (sem sort/page).
- Combinações inválidas (identity em search, filters em get,
  parâmetros errados por action de knowledge) → 422 `validation`.

## 4. Registry semântico

`constants.SEMANTIC_CAPABILITIES` + conjuntos fechados
(`READ_ENTITIES`, `READ_ACTIONS`, `ANALYSIS_KINDS`,
`KNOWLEDGE_ACTIONS`, `CONTEXT_ACTIONS`, `PO_*_FILTER_KEYS`) são a única
fonte do dispatch e do catálogo. Adicionar capability = contrato + owner
AuthZ + handler + testes — nunca tool nova por padrão nem campo livre.

FUTURE (não executável): `purchase_requests`, `deliveries`,
`inventory`, `suppliers`; análises de deliveries/inventory/suppliers.

## 5. AuthZ e erros — inalterados

`capability AND unit_scope AND resource_scope AND business_rule`:
transporte (JWT + aud exata + `mcp:tools`, service-token banido) →
`_effective_user`/`_operations_user`/`_knowledge_user` (Core `/me` +
`can_use_operations`/`has_canonical_access` + `require_units`).
401 → envelope + `mcp/www_authenticate` meta; 403 forbidden;
404 not_found; 422 validation; 502/503 upstream.

## 6. Composição

Ferramentas são stateless e independentes — o conector encadeia
`read → analyze → knowledge` para respostas compostas; cada chamada
re-verifica autorização; falha parcial de uma não fabrica as demais.

## 7. Versão

`CATALOG_VERSION = 2` (rev.1 = 1).
