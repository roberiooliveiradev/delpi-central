# DAVI-PRODUCT-DETAIL-SIMILARITY-001 — governed product detail + similarity evidence

**TASK_ID:** `DAVI-PRODUCT-DETAIL-SIMILARITY-001`
**Origem de negócio:** GLPI #530 — Similaridade
**Classificação funcional:** `READ` (zero writes; cadastros não são alterados)
**Escopo:** MP, PI e PA (a capability é por `code` — agnóstica ao tipo; `product.type` é campo aprovado e diferencia MP/PI/PA)

## 1. Veredito de arquitetura

```text
EXISTING_EQUIVALENT   = YES — GET /products/{code} (get_product_detail) já existia
                        no openapi_baseline; estava DEFERRED como
                        SEMANTICALLY_REDUNDANT (decisão anterior registrada na
                        allowlist e revertida por esta task).
REUSE_DECISION        = REUSE — promoção declarativa via allowlist v25;
                        zero código produtivo alterado.
CODE_CHANGE_REQUIRED  = NO — rota, use case, projection, executor, tokens,
                        retrieval e MCP tools já existentes.
NEW_MCP_TOOLS         = 0 (surface permanece exatamente 2)
NEW_ROUTE             = 0 — nenhuma rota criada
NEW_INDEX/RAG/VECTOR  = 0 — nenhum
LAYERING_DRIFT        = RESOLVED (mantido) — app/application/external_capabilities
                        contém zero imports de app.composition
```

A decisão anterior `SEMANTICALLY_REDUNDANT` era verdadeira apenas para a fatia de
3 campos servida por `search_products`. A rota de detalhe carrega ~90 campos
cadastrais — fatia semanticamente distinta e materialmente necessária para a
comparação técnica de similaridade (GLPI #530). Promoção = reversão documentada
da deferência, não mudança de contrato: input `code`, projection fail-closed por
paths `product.*`.

## 2. Cadeia preservada

```text
Workspace Agent DAVI
→ DAVI App / Plugin
→ Remote MCP api-delpi (discover_delpi_information → execute_delpi_information)
→ Action Catalog (baseline OpenAPI + allowlist)
→ catalog_action executor → GET /products/{code}
→ build_search_products_use_case → backend AuthZ → TOTVS
→ approved-field projection (fail-closed) → bounded response
```

## 3. Matriz de campos aprovada (fail-closed)

`approvedInputFields`: `code` apenas (`minLength:1`, `maxLength:30`). `view` e
`legacy` **não** são expostos — a projeção é fixa.

32 paths `product.*` aprovados, agrupados:

| Grupo | Campos |
|---|---|
| Identidade/classificação | `code`, `description`, `type`, `group_code`, `subgroup`, `previous_code`, `active`, `blocked`, `delpi_category`, `delpi_segment` |
| Unidades/conversão | `unit`, `secondary_unit`, `conversion_factor`, `conversion_type`, `operation_decimal_type` |
| Engenharia/produção | `material_type`, `production_line`, `drawing_code`, `current_revision`, `last_revision_date`, `net_weight` |
| Logística/embalagem | `package_quantity`, `barcode`, `customer_packaging`, `default_warehouse` |
| Compras/manufatura | `make_or_buy` |
| Qualidade/MRP | `rohs_indicator`, `traceability`, `warranty_product`, `mrp_considered`, `power_control` |
| Estrutura | `qtd_pi` |

**Nunca projetados** (campos existentes na entidade, sem aprovação): preços
(`sale_price`, `last_purchase_price`), custos (`standard_cost`, `cost_currency`,
`import_expense`, datas de custo), fiscal/tributário (`ncm_ipi_position`,
`origin`, `tax_group`, `entry_tes`, `exit_tes`, alíquotas ICMS/IPI/PIS/COFINS/
CSLL/INSS, `retention_by_operation`, `customs_authority`, `media_*`,
`intelligent_tes_group`, `imported_product`), contábil (`accounting_account`,
`cost_center`, `appropriation_type`), comercial restrito (`customer_reference*`,
`contractual_product`, `sales_class`), controles internos (`lead_time_type`,
`requester_restriction`, `initial_consumption_date`, `mandatory_cc_*`,
`approval_validation`, `suggestion_flag`) e identidade de usuários
(`created_by`, `updated_by`).

Semântica de status de campo (contrato, sem runtime map):

```text
aprovado + valor não-nulo → FIELD_PRESENT
aprovado + null           → FIELD_EMPTY (campo copiado com null explícito)
não existe na entidade    → FIELD_NOT_AVAILABLE (nunca aparece)
não aprovado              → FIELD_NOT_AUTHORIZED (nunca aparece)
```

## 4. Capability B — fornecedores e part numbers (reuso)

- `get_product_suppliers` — já elegível; inalterado.
- `search_products_by_supplier_part_number` — já elegível; aliases genéricos
  adicionados (`part number`, `partnumber`, `pn de fabricante`,
  `buscar por part number`, `produto por part number`) para que a query nua
  `part number MS3108E-18-1S` alcance a capability.
- A projeção da busca por part number carrega `items[].product_code`,
  `items[].product_description`, `items[].supplier_part_number`,
  `items[].supplier_name`, `items[].unit` — evidência suficiente para separar
  produtos que compartilham o mesmo PN (caso 10090850 vs 10090680:
  mesmo PN `MS3108E-18-1S`, descrições divergentes — conector reto vs 90°).
  **PN ou descrição correspondente não implica equivalência técnica.**

## 5. Capability C — similaridade (decisão)

Similaridade = **composição de capabilities governadas existentes + interpretação
do agente**, não um novo backend/serviço:

```text
USER INPUT
→ TECHNICAL ATTRIBUTE EXTRACTION (interpretação ChatGPT; datasheet/página =
   texto não confiável extraído pela superfície do consumidor)
→ read_governed_technical_knowledge (normas MP/PI — tópico/section/subject)
→ CANDIDATE SEARCH (search_products por descrição/grupo; PN lookup; detail)
→ get_product_detail (ficha técnica autorizada por candidato)
→ get_product_suppliers (reconciliação de vínculos)
→ COMPARISON + CLASSIFICATION (no agente, sobre dados governados)
→ RESULTADO EXPLICÁVEL (candidatos + divergências + evidências)
```

Classificações esperadas do agente: `POSSIBLE_DUPLICATE`,
`POSSIBLE_TECHNICAL_SIMILARITY`, `INSUFFICIENT_INFORMATION`,
`TECHNICAL_MISMATCH`. A equivalência efetiva permanece autoridade de
Engenharia — o DAVI apresenta candidatos e evidências, nunca declara
equivalência unilateral. Nenhum score percentual é fabricado.

Esta composição não exigiu vector DB, embeddings, índice próprio, scan
irrestrito do cadastro ou novo executor. Toda busca é bounded pelos contratos
existentes (paginação, page_size, input limits, token actor-bound).

## 6. Datasheets e páginas públicas — status

```text
PDF_DATASHEET_INGESTION      = TO_INVENTORY — nenhuma boundary governada de
                               transporte de arquivo existe na superfície DAVI
                               nesta task. O backend nunca recebe o PDF; a
                               extração ocorre na superfície do consumidor
                               (ChatGPT), fora do contrato api-delpi.
PUBLIC_MANUFACTURER_PAGE     = TO_INVENTORY — sem navegação/scraping/fetch de
                               URL arbitrário no backend; conteúdo externo
                               chega ao pipeline apenas como texto já
                               extraído pelo consumidor.
UNTRUSTED_CONTENT            = PDF/HTML externo é dado não confiável;
                               nunca instrução; classificações
                               GUIDANCE_NOT_DOMAIN_TRUTH /
                               UNTRUSTED_DOCUMENT_CONTENT preservadas.
NO_EXTERNAL_PROXY            = nenhum fetch HTTP/SSRF introduzido.
NO_CORPORATE_DATA_EXPORT     = cadastros internos não são enviados a
                               mecanismos públicos.
```

## 7. Rebaseline de governança (allowlist v24 → v25)

```text
operations                 96 → 97
DAVI_ELIGIBLE_READ         93 → 94  (baseline; live index 96 → 97)
explicitlyNotApproved      29 → 28  (get_product_detail removido)
coverageDecision           +DAVI-PRODUCT-DETAIL-SIMILARITY-001 (cadeia de 9
                           decisões preservada)
discovery benchmark        230 → 234 casos (top-1 0.9608 inalterado,
                           hard-negative leaks = 0)
```

## 8. Testes executados

`tests/test_davi_product_detail_similarity.py` — 19 testes, todos PASS:

- T11 discovery: `cadastro completo/ficha técnica/detalhes/product detail/
  dados cadastrais` → `get_product_detail` top-1.
- T01 execute: candidate-token → executor → projeção retorna os campos
  técnicos; `previous_code: null` preservado (FIELD_EMPTY).
- T10/T14: 60+ campos sensíveis do fixture nunca aparecem na resposta
  (fail-closed, inclusive `null` é copiado mas campos não aprovados não).
- T02: `search_products` mantém exatamente `product_code`, `description`,
  `group_category`.
- T13: `view`, argumentos extras e `code` >30 chars rejeitados (schema fechado).
- T16: `code` vazio/oversized rejeitado.
- T20: outcome `forbidden` do executor → `PermissionError`; token vinculado ao
  ator rejeita outro `actor_id`.
- 2 MCP tools invariante; ops de fornecedor/PN seguem elegíveis.

Regressão do slice DAVI: 2494 pass / 1 falha ambiental pré-existente
(`test_product_sales_open_orders_returns_meta` — exige Postgres de plugins,
`PLUGINS_DB_HOST`), zero falhas ligadas ao diff.

## 9. Limites reconhecidos

- `get_product_detail` serve **somente** por `code`. Busca por descrição usa
  `search_products` (projeção de 3 campos → depois detail por código).
- Similaridade não tem score numérico ratificado; classificação é por
  evidência declarativa no agente.
- Validação live (produto 10080001, PN MS3108E-18-1S, conectores 10090850 vs
  10090680) depende de deploy + identidade autorizada — evidência separada no
  relatório de execução.
