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

## 9. Aceite do fluxo — `DAVI-SIMILARITY-FLOW-ACCEPTANCE-002`

### 9.1 Root cause do gap de discovery

Reproduzido no HEAD `74fb1ba10b`:

| Query | Resultado |
|---|---|
| `Pesquise matérias-primas já cadastradas que possam ser similares ao terminal...` | `search_products` (OK — variante da revisão não reproduziu zero) |
| `Cadastro completo e comparação de materiais semelhantes ao código 10080001` | `search_products` (top-1; `get_product_detail` em top-5) |
| `Quero cadastrar uma MP, antes verifique se já existe algo igual ou similar` | **0 candidatos** — guard READ-only: token `cadastrar` = verbo de escrita explícito |
| `verifique se já existe produto similar cadastrado` | **0 candidatos** — vocabulário de similaridade sem aliases |
| `quais produtos são similares ao 10080001` | **0 candidatos** — idem |

Causas distintas: (a) **retrieval** — nenhum alias cobria `similar/semelhante/duplicidade/equivalente/já existe cadastrado`; (b) **guard deliberado** — `cadastrar` é verbo de mutação e zera candidatos por design. O guard **não** foi enfraquecido: a reformulação da intenção composta é responsabilidade da camada de inteligência do agente (`flows.similarity_dedup_check`), não do guard nem de novo endpoint.

### 9.2 Correção (menor diff, owner correto)

- `search_products`: +25 aliases de similaridade/dedup (`produtos similares`, `verificar duplicidade`, `equivalente cadastrado`, `já existe cadastrado`, …).
- `get_product_detail`: +13 aliases (`produto similar ao código`, `comparar produto`, `comparar especificações`, …).
- `davi_agent_intelligence.json` v2026.10.24.1: novo flow `similarity_dedup_check` — pipeline de 8 etapas, enum de classificação, limites de fan-out (top_k≤5, detail≤5), regras de não-equivalência e proveniência. Projetado via `capability_surface.agent_directives` (≤20KiB, testado).
- Allowlist v26 + coverageDecision link (cadeia = 10 decisões).
- Benchmark de discovery: +4 casos (238 total), `top-1` e `leaks=0` mantidos.

**Pós-fix:** `verifique se já existe produto similar`, `quais produtos são similares`, `verificar duplicidade`, `existe equivalente cadastrado` → `search_products`/`get_product_detail`. `quero cadastrar ... antes verifique`, `cadastre`, `crie`, `altere` → **0 candidatos preservado** (guard intacto; o agente reformula para READ puro).

### 9.3 Ratificação da matriz de 32 campos

| # | FIELD | SOURCE | MEANING | CLASS. | SIMILARITY VALUE | DECISION |
|---|---|---|---|---|---|---|
| 1 | code | SB1 B1_COD | chave do produto | público interno | chave de junção | APPROVED |
| 2 | description | SB1 B1_DESC | descrição técnica padronizada | interno | atributo primário | APPROVED |
| 3 | type | SB1 B1_TIPO | MP/PI/PA | interno | filtro de família | APPROVED |
| 4 | group_code | SB1 B1_GRUPO | grupo de materiais | interno | filtro de família | APPROVED |
| 5 | subgroup | SB1 B1_SG | subgrupo | interno | família fina | APPROVED |
| 6 | previous_code | SB1 B1_CODITE | código anterior/legado | interno | reconciliação | APPROVED |
| 7 | active | SB1 | ativo cadastral | interno | vigência | APPROVED |
| 8 | blocked | SB1 B1_MSBLQL | bloqueio de uso | interno | descarte de candidato | APPROVED |
| 9 | delpi_category | derivado | categoria DELPI | interno | família | APPROVED |
| 10 | delpi_segment | derivado | segmento DELPI | interno | família | APPROVED |
| 11 | unit | SB1 B1_UM | UM principal | interno | unidade p/ comparação | APPROVED |
| 12 | secondary_unit | SB1 B1_SEGUM | UM secundária | interno | conversão | APPROVED |
| 13 | conversion_factor | SB1 B1_CONV | fator de conversão | interno | normalização | APPROVED |
| 14 | conversion_type | SB1 B1_TIPCONV | tipo de conversão | interno | normalização | APPROVED |
| 15 | operation_decimal_type | SB1 | decimais por operação | interno | precisão | APPROVED |
| 16 | material_type | SB1 B1_TIPO_? | tipo de material | interno | característica | APPROVED |
| 17 | production_line | SB1 | linha de produção | interno | contexto fab | APPROVED |
| 18 | drawing_code | SB1 B1_DESENHO | desenho técnico | interno | evidência técnica | APPROVED |
| 19 | current_revision | SB1 | revisão vigente | interno | controle engenharia | APPROVED |
| 20 | last_revision_date | SB1 | data da revisão | interno | vigência técnica | APPROVED |
| 21 | net_weight | SB1 B1_PESO | peso líquido | interno | atributo físico | APPROVED |
| 22 | package_quantity | SB1 B1_QB | qtd por embalagem | interno | embalagem | APPROVED |
| 23 | barcode | SB1 B1_CODBAR | código de barras | interno | reconciliação | APPROVED |
| 24 | customer_packaging | SB1 | embalagem p/ cliente | interno | embalagem | APPROVED |
| 25 | default_warehouse | SB1 B1_LOCPAD | armazém padrão | interno | logística | APPROVED |
| 26 | qtd_pi | estrutura | qtd produto intermediário | interno | composição | APPROVED |
| 27 | rohs_indicator | SB1 | conformidade RoHS | interno | certificação | APPROVED |
| 28 | traceability | SB1 | rastreabilidade | interno | requisito qualidade | APPROVED |
| 29 | warranty_product | SB1 | produto garantia | interno | classificação | APPROVED |
| 30 | mrp_considered | SB1 | considerado no MRP | interno | planejamento | APPROVED |
| 31 | power_control | SB1 | controle de potência | interno | característica | APPROVED |
| 32 | make_or_buy | SB1 | comprado/fabricado | interno | origem | APPROVED |

**Classificação:** todos os 32 campos = dados cadastrais internos não-financeiros;
nenhum é PII, comercial restrito ou contábil. OWNER=api-delpi/SB1;
AUTHORITATIVE SOURCE=TOTVS SB1 (+derivados DELPI); CONSUMER=DAVI READ;
AUTHZ=`api-delpi.access` backend — inalterada. Campos sensíveis (preço, custo,
fiscal, contábil, comercial, `created_by`/`updated_by`, controles internos)
permanecem **não aprovados** — nunca projetados.

> Ratificação documental da matriz = este documento + decisão encadeada na
> allowlist v25/v26. Ratificação formal de negócio por campo (PO/Engenharia) =
> `PENDING_OWNER_REVIEW` para publicação ampla; a projeção já é a fatia mais
> restritiva coerente com o objetivo técnico.

### 9.4 Gates externos

```text
NEGATIVE_BUSINESS_AUTHZ (2ª identidade) = PENDING — não há usuário de teste
    sancionado sem permissão; 401 anônimo e forbidden-do-executor provados,
    mas não substituem negativa de negócio real. Publicação ampla permanece
    bloqueada conforme §10 do briefing.
PROVIDER_DISCOVERY (refresh pós-94 ops)   = PENDING/STALE_EVIDENCE.
LIVE_SIMILARITY_SCENARIO (MS3108E-18-1S, conectores 10090850/10090680) =
    PENDING — depende da superfície provider autenticada.
DATASHEET_PDF_TRANSPORT                   = TO_INVENTORY — sem boundary
    governada de arquivo; extração ocorre na superfície do consumidor.
SIM-20 FLUXO REAL CONSUMIDOR              = PENDING — requer sessão ChatGPT/
    Agent Studio autenticada; contrato e diretivas provados in-process.
```


## 10. Limites reconhecidos

- `get_product_detail` serve **somente** por `code`. Busca por descrição usa
  `search_products` (projeção de 3 campos → depois detail por código).
- Similaridade não tem score numérico ratificado; classificação é por
  evidência declarativa no agente.
- Validação live (produto 10080001, PN MS3108E-18-1S, conectores 10090850 vs
  10090680) depende de deploy + identidade autorizada — evidência separada no
  relatório de execução.


---

## 11. Live consumer case: TE Connectivity 626377-1 (2026-10-26)

**Execution context:** ChatGPT conversation with connected, end-user-authenticated DAVI
remote MCP plus an independently retrieved public manufacturer webpage. This is an
assisted consumer-session validation of the *existing governed READ capabilities*;
it is **not** an Agent Studio automation/eval, PDF transport validation, complete
inventory scan, second-user business AuthZ test, or evidence of a new deployed SHA.

| Dimension | State | Observation |
|---|---|---|
| External reference | PROVEN | TE Connectivity official product \`626377-1\`: https://www.te.com/pt/product-626377-1.html |
| MCP availability | PASS | \`discover_delpi_information\` + \`execute_delpi_information\`; 97 actions visible in the connected catalog |
| Exact part-number lookup | PASS | \`search_products_by_supplier_part_number(supplier_part_number="626377-1")\` returned \`total=1\`, \`is_complete=true\`: DELPI \`10080010\`, TE supplier \`000002/01\` |
| Governed detail | PASS | \`get_product_detail(code="10080010")\` returned 32 approved \`product.*\` fields, \`is_complete=true\`, product \`type=MP\`, \`group_code=1008\`, \`active=S\`, \`rohs_indicator=S\` |
| Supplier links | PASS | \`get_product_suppliers(code="10080010",page=1,page_size=15)\` returned 6 links, complete; TE \`626377-1\` and Heilind \`0-0626377-1\` among them |
| Descriptive candidate discovery | PASS with coverage limitation | \`search_products\` found same-family lingueta terminals; result set is paginated/partial, no automatic technical-equivalence determination |
| Identification outcome | PASS | A pre-existing DELPI record was located before hypothetical creation; **no actual duplicate creation or prevention event was executed** |
| Full Agent Studio orchestration | PENDING | This chat executed the sequence using the connected MCP; independent Agent Studio SIM-20 is not proven |
| Negative business AuthZ (2nd user) | PENDING | 401 anonymous and simulated forbidden are not the required distinct authenticated negative user |
| Owner ratification / broad rollout | PENDING | Formal PO/Engineering ratification of the 32-field projection remains open |
| PDF transport / comparison | TO_INVENTORY | This case read public HTML, not an uploaded drawing/datasheet through DAVI MCP |

### 11.1 Sources and technical evidence

**Manufacturer (public; not DELPI SoT):** TE \`626377-1\` is a FASTON 250
straight, uninsulated tab, 22-18 AWG / 0.32-0.82 mm2, mating width 6.35 mm,
mating thickness 0.81 mm, brass/unplated, F-crimp, 8,000/reel; TE also lists
UL/CSA-related approvals and recommends using the product drawing for design.
Official product source: https://www.te.com/pt/product-626377-1.html .

**DELPI (authoritative cadastral read through MCP):**

- Product \`10080010\`: \`TERM. LINGUETA 6,30X0,80 0,30-0,80MM2 NU S/ISOLACAO FITADO CURTO UL ROHS\`.
- Supplier-link match: \`supplier_code=000002\`, \`supplier_store=01\`,
  \`supplier_name=TE CONNECTIVITY BRASIL IND DE ELET LTDA\`,
  \`supplier_part_number=626377-1\`, \`unit=PC\`.
- Six supplier links in the bounded complete result, including TE and Heilind.
- Descriptive nearby candidates: \`10080060\` (estanhado), \`10081671\`
  (trava), \`10080225\` (trava/longo), \`10081405\` (smaller wire range).
  These are *candidates*, not approved replacements.
- The apparent nominal differences (6.35 x 0.81 versus cadastral
  6.30 x 0.80; 0.32-0.82 versus 0.30-0.80 mm2) must be reviewed against
  manufacturer tolerances/controlled drawings before interchangeability.
  \`FITADO\` versus \`reel\` requires packaging/grain validation, not an
  automatic contradiction. TE UL/CSA mentions do not prove every DELPI
  certification attribute. An exact SA5 supplier-PN match establishes the
  *registered supplier reference*, **not engineering substitution authority**.

### 11.2 Retrieval limitations discovered in this case

- Prefix-like descriptions can have very different search results. Broad
  \`TERM. LINGUETA 6,30X0,80\` and the more specific
  \`TERM. LINGUETA 6,30X0,80 0,30-0,80MM2\` returned relevant candidates,
  but the response \`total\` remained \`1501\` (group-scoped), while only the
  visible page contained the narrower matches. **Count semantics are
  INCONCLUSIVE** until the canonical owner repository/query is inspected.
- The 5-detail fan-out cap in \`similarity_dedup_check\` is a safety/latency
  limit, *not* evidence that the first five results are the top five
  technically relevant materials. Candidate selection/ranking needs positive,
  sibling and hard-negative evals.
- Use a **strict precedence**: (1) exact registered supplier PN;
  (2) canonical detailed product and supplier associations;
  (3) controlled, bounded descriptive candidate search;
  (4) technical comparison with attribute-level provenance. Distinguish
  \`REGISTERED_PART_NUMBER_MATCH\` as an evidence statement from the
  existing four classification outcomes; do not authorize equivalence on
  that basis.
- In the original user message, visible link text mentioned \`160404-2\`
  while the actual target URL pointed to \`626377-1\`. Prefer verified
  canonical URL/part number and disclose conflicts; do not silently merge
  different references.

**Verdict for this case:** \`LIVE_PN_IDENTIFICATION = PASS\`,
\`LIVE_GOVERNED_DETAIL = PASS\`, \`LIVE_SUPPLIER_LOOKUP = PASS\`,
\`ASSISTED_SIMILARITY_COMPARISON = PASS_WITH_LIMITATIONS\`;
\`FULL_AGENT_STUDIO_SIM20 = PENDING\`; \`ENGINEERING_EQUIVALENCE = NOT_AUTHORIZED\`.

This section updates the earlier time-specific \`LIVE_VALIDATION=PENDING\` for
the **626377-1** case only; the separate \`MS3108E-18-1S\` Agent Studio
scenario, authenticated USER_B negative test, and PDF transport remain open.
