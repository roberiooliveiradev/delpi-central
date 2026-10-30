# SURI-MCP-FULL-PARITY-V4 — G1 SUPPLIERS COMPLETO — Evidência

Data: 2026-10-30 · Lote: `P1-R5` (suppliers reads + creation preview + postal lookup)

```text
TASK:            SURI-MCP-FULL-PARITY-V4-G1
DOMAIN:          SUPPLIERS (+ postal_codes lookup)
BASE HEAD:       5dd65182a9 (worktree delpi-central-g1-wt, detached)
ORIGIN MAIN:     37041b686d no momento da escrita (commits concorrentes docs-only)
GIT STATUS:      worktree isolado; apenas supplies-api tocado
```

## CURRENT STATE

```text
SURI_CATALOG_VERSION:        4 (rev.3 → rev.4, aditivo/non-breaking)
SURI_TOOLS:                  get_context, read, analyze, knowledge, execute (inalteradas)
read.entities:               purchase_orders, suppliers, postal_codes
read.actions (suppliers):    search, get, catalogs, search_by_tax_id,
                             existing, operations, integration_status
read.actions (postal_codes): lookup
analyze.analyses:            purchase_orders_summary, supplier_creation_preview
execute (preservado):        suppliers create|update — sem regressão
```

## RQ/AC

```text
RQ-01 suppliers.search            → read(suppliers,search)   PASS
RQ-02 suppliers.get (ficha 360)   → read(suppliers,get)      PASS
RQ-03 suppliers.search_by_tax_id  → read(suppliers,search_by_tax_id) PASS
RQ-04 suppliers.catalogs          → read(suppliers,catalogs) PASS
RQ-05 suppliers.existing          → read(suppliers,existing) PASS
RQ-06 suppliers.operations        → read(suppliers,operations) PASS
RQ-07 suppliers.integration_status→ read(suppliers,integration_status) PASS (manage-only)
RQ-08 postal_codes.lookup         → read(postal_codes,lookup) PASS
RQ-09 CNPJ externo (pré-cadastro) → analyze(supplier_creation_preview) PASS
RQ-10 Jornada composta CNPJ+CEP   → capacidades publicadas no catálogo v4
                                   (composição é do cliente LLM; cada
                                   chamada re-deriva autorização)
```

## OWNERS / CONTRACTS

```text
VOCABULÁRIO/PROJEÇÕES:  supplies_dto (owner canônico) — SUPPLIER_CATALOG_KINDS,
                        SUPPLIER_CATALOG_QUERY_KEYS, SUPPLIER_LIST_QUERY_KEYS,
                        SUPPLIER_CATALOG_LIMIT_MAX, SUPPLIER_EXISTING_PAGE_SIZE_MAX,
                        normalize_postal_code, project_postal_lookup,
                        project_existing_supplier_item, normalize_supplier_id,
                        normalize_operation_id, project_integration_status,
                        project_list_envelope, project_detail, project_operation
ERROS REGISTRY:         supplier_enrichment/contracts.classify_registry_error
                        (consumido pela rota HTTP e pelo bridge MCP — mapping único)
PREVIEW:                SupplierCreationPreviewService + DelpiSupplierDuplicateSearch
                        + registry_rate_limiter + company_registry_provider
                        (mesmos objetos da rota de creation — zero regra reescrita)
TRANSPORTE:             DelpiS2SApiGateway (mesma credencial S2S do BFF suppliers —
                        X-Delpi-Service-Authorization), access_token do usuário
                        propagado para actor binding upstream
MCP INPUT VOCAB:        mcp/constants — READ_ACTIONS_BY_ENTITY, ANALYSIS_KINDS,
                        *_FILTER_KEYS / *_IDENTITY_KEYS fechados por operação
UPSTREAM (inalterado):  /supplies/suppliers, /supplies/supplier-catalogs/{kind},
                        /addresses/postal-codes/{cep}, /integrations/protheus/
                        suppliers/{id}, /integrations/protheus/status,
                        /integrations/operations/{id} — 1:1 com as rotas BFF
```

## FILES INSPECTED / CHANGED

```text
INSPECTED:  suppliers_routes, supplier_creation_routes, suppliers_dto,
            preview_service, supplier_enrichment/contracts, preview domain,
            DelpiSupplierDuplicateSearch, brasilapi_registry_provider,
            supplier_enrichment_adapters, server/schemas/constants/branding,
            test_execute, suri_fixtures, matriz/inventory/plan/briefs/freeze
CHANGED:    tool_bridge (+ handlers suppliers/postal/preview, dispatch por
            entidade), constants (READ_ACTIONS_BY_ENTITY, ANALYSIS_KINDS,
            vocabulários, CATALOG_VERSION=4, SEMANTIC_CAPABILITIES derivado),
            schemas (+7 modelos fechados rev.4), server (Literals/unions +
            descrições PT-BR), branding (instruções novas capacidades),
            suppliers_dto (+SUPPLIER_CATALOG_*, project_postal_lookup,
            project_existing_supplier_item, normalize_postal_code já canônico),
            suppliers_routes + supplier_creation_routes + preview_service
            (consomem owner canônico — projeções/clamps/classifier
            deduplicados), contracts (+classify_registry_error),
            test_tool_bridge (catálogo 3→4), test_suppliers_read (novo, 34)
DOCS:       MATRIX (R-15..R-22 → PROVEN, 14/45 = 31.1%), PLAN (P1-R5 executado),
            BRIEFS (P1-R5 executado), FREEZE-V3 (adendo rev.4 aditivo)
```

## AUTHZ

```text
POSITIVE:   supplies.access → todas as leituras/análise; supplies.manage →
            integration_status; access_token do usuário propagado ao upstream
NEGATIVE:   anônimo → 401; sem supplies.access → 403; integration_status sem
            manage → 403 (testado); (401/403) upstream propagado, não engolido
FAIL-CLOSED: _operations_user/_admin_user re-derivam permissão por chamada —
            metadata de tool nunca autoriza
```

## TESTS

```text
NOVOS:      tests/interface/suri_mcp/test_suppliers_read.py — 34 testes
            (positive/sibling/negative por operação; CNPJ com dígitos
            verificadores reais; envelope/projeção verificados)
SUÍTE SURI: 131/131 PASS
REGRESSÃO:  796 passed, 24 skipped (supplies-api inteira, exit 0)
```

## BUILD / RUNTIME

```text
RUNTIME:    create_mcp_server() lista 5 tools; read.entity enum =
            [purchase_orders, suppliers, postal_codes]; read.action enum =
            [search, get, catalogs, search_by_tax_id, existing, operations,
            integration_status, lookup]; analyze.analysis enum =
            [purchase_orders_summary, supplier_creation_preview];
            SEMANTIC_CAPABILITIES derivado de READ_ACTIONS_BY_ENTITY
BUILD:      não aplicável neste gate (sem deploy — G1 é implementação +
            evidência; deploy produtivo exige gate operacional específico)
```

## POSITIVE / SIBLING / NEGATIVE

```text
POSITIVE:   filtros repassados 1:1 (query/state/blocked/page/sort); identidade
            código+loja → /integrations/protheus/suppliers/{code6}{store2};
            catalogs kind válido → allowlist upstream; CNPJ válido → dup-check
            com projeção mínima; operation_id UUID → project_operation;
            CEP 8 dígitos → project_postal_lookup; preview → suggestions com
            proveniência + duplicate_check + unavailable_fields + write_enabled=false
SIBLING:    existing vs search_by_tax_id (mesma lookup, envelopes distintos);
            catalogs ×14 kinds fechados; preview rate-limit por ator compartilhado
NEGATIVE:   kind fora da allowlist → 422 sem chamada upstream; CNPJ inválido →
            422; identity em search / filters em get → 422; operation_id não-UUID
            → 422; CEP inválido → 422; entidade/ação desconhecidos → 422;
            análise inexistente → 422; provider CEP unreachable → 504
            provider_unreachable; provider error → 502 provider_error;
            registry provider indisponível → 503 ENRICHMENT_SOURCE_UNAVAILABLE;
            rate limiter → 429 ENRICHMENT_RATE_LIMITED (+retry_after)
```

## RESIDUAL SEARCH

```text
DUPLICAÇÃO:   eliminada — _existing_suppliers_minimal (rota→dto),
              projeção postal (rota+bridge→dto), _EXISTING_PAGE_SIZE_MAX e
              clamp 500 (rota+MCP→dto), classifier registry (rota→contracts)
              agora compartilhado por HTTP e MCP
STALE REFS:   READ_ACTIONS removido; nenhuma referência residual a
              catálogo v3 em código/testes; freeze V3 recebeu adendo, não
              reescrita (histórico preservado)
SECRETS:    nenhum valor impresso; diagnósticos não republicam URL/host/token
```

## FACTS PROVEN

```text
- Catálogo v4 publicado em código com enums Literals fechados (runtime-verified)
- 7 capacidades suppliers + 1 postal lookup + 1 análise preview homologadas
  por teste (34 novos, todos verdes)
- READ e ANALYZE não causam escrita: preview devolve write_enabled=false e
  nenhum handler de leitura chama POST/PUT upstream
- AuthZ parity com o BFF: access para reads, manage para integration_status
- provider indisponível/bloqueado → estado honesto, nunca dado inventado
- Matriz atualizada: 14/45 capacidades PROVEN (31.1%)
```

## TO_INVENTORY / UNRESOLVED

```text
- Jornada composta CNPJ+CEP→create depende de orquestração do cliente LLM;
  cada passo é uma tool call independente — homologação end-to-end autenticada
  no ChatGPT permanece pendente (fluxo OAuth user-delegated)
- G2+ (purchase_requests, deliveries, estoque, indicadores, mercado, writes
  adicionais) não iniciados — aguardam aceite de G1 e autorização de lote
```

## EXECUTION_DRIFT: nenhum

## POSTCONDITION

```text
publicação do catálogo v4 em código ≠ homologação autenticada via ChatGPT;
nenhuma escrita nova foi exercida além das já PROVEN (create/update)
```

## COMMITS / NEXT STEP

```text
COMMIT:    pendente no momento da escrita — ver mensagem do commit G1
NEXT STEP: revisão arquitetural do GPT Arquiteto → aceite G1 → autorização
           do próximo lote (G2 solicitações/pedidos); deploy produtivo somente
           com gate operacional específico
```
