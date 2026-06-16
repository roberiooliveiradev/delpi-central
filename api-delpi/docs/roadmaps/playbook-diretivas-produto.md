# Playbook DELPI — Diretivas do produto (referência cliente × código DELPI)

**Status:** implementado (jun/2026)  
**Rota:** `GET /products/directives/{identifier}` · `operationId`: `get_product_directives`  
**Contrato:** `composite_analysis` · entidade `product_directives`

---

## 1. Objetivo

Expor uma visão **integrada** para perguntas do tipo «diretivas 90260882» ou «diretivas 10018137», consolidando:

- Resolução do **PA** por código DELPI (`9026xxxx`) ou **referência do cliente** (`SB1010.B1_REFEREN`);
- **Estrutura multinível** (BOM vigente, todos os níveis);
- **Matérias-primas** da estrutura com **fornecedores** e **part number** (`SA5010`);
- **Última NF de compra válida** de cada MP com dados do fornecedor (`SD1010` + `SA2010`).

Evita que o chat dispare três rotas separadas (`/structure`, `/suppliers`, `/last-purchase`) para a mesma intenção.

---

## 2. Resolução do identificador

| Entrada | Prioridade | Exemplo |
|---------|------------|---------|
| Código com prefixo `9026` | Busca exata em `SB1010.B1_COD` | `90260882` |
| Demais códigos numéricos | Busca em `SB1010.B1_REFEREN` (preferir PA `9026%`) | `10018137` |
| Fallback | Busca exata em `B1_COD` | — |

Implementação: `ProductIdentifierResolutionService` + `ProductRepository.fetch_product_by_code` / `fetch_product_by_customer_reference`.

---

## 3. Fontes de dados (reutilização)

| Dado | Módulo canônico | Tabela(s) |
|------|-----------------|-----------|
| BOM multinível | `ProductPlaybookRepository.fetch_structure_with_exclusivity` | `SG1010`, `SB1010` |
| Fornecedores + part number | `ProductSuppliersRepository.list_suppliers_for_codes` | `SA5010`, `SA2010`, `SC7010` |
| Última compra válida | `ProductRawMaterialPriceRepository.fetch_last_purchases_for_codes` | `SD1010`, `SA2010`, `SA5010` |

Filtros de compra válida: `PurchaseValidityFilterService` (exclui transportadoras e fornecedores internos `000019`, `001149`).

---

## 4. Contrato de resposta (`data`)

```json
{
  "resolution": {
    "identifier": "10018137",
    "identifier_type": "customer_reference",
    "delpi_code": "90260882",
    "customer_reference": "10018137"
  },
  "product": { "product_code", "description", "product_type", "customer_reference", ... },
  "structure": { "items": [...], "summary": {...} },
  "raw_materials": [
    {
      "raw_material_code": "10080001",
      "description", "level", "accumulated_quantity", "path",
      "suppliers": [{ "supplier_code", "supplier_part_number", ... }],
      "last_purchase": { "invoice_number", "supplier_name", "unit_price", ... }
    }
  ],
  "summary": {
    "total_raw_material_entries",
    "total_supplier_links",
    "raw_materials_with_last_purchase",
    "raw_materials_without_last_purchase"
  }
}
```

`meta.sections`: `product`, `structure`, `raw_materials`, `summary`.

---

## 5. Parâmetros HTTP

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `identifier` | path | Código DELPI ou referência do cliente |
| `max_depth` | query, opcional | Profundidade BOM (default 50, máx. 100) |
| `branch` | query, opcional | Filial (2 chars) — filtra última compra por filial |

---

## 6. Chat — vocabulário e roteamento

| Artefato | Chave / domínio |
|----------|-----------------|
| Intenção | `product_query_intent.json` → `directives.terms` |
| Detecção | `ChatProductQueryIntentService._looks_like_directives_question` |
| Seleção de rota | `ExternalActionProductRouteSelectionService` (score +165 em `/directives/`) |
| Domínio operacional | `api_route_domains.json` → `product_directives` |
| Motivo da action | `external_action_responses.json` → `selectionReasons.productDirectives` |

**Exemplos de frases:** «Diretivas 90260882», «Diretivas 10018137», «referência do cliente com fornecedores e última compra».

**Não confundir:**

- `/directives/{identifier}` — visão composta por PA/referência;
- `/products/{code}/structure` — só BOM;
- `/products/{code}/suppliers` — fornecedores de **um** código;
- `/products/{code}/last-purchase` — última compra de **uma** MP.

---

## 7. Implementação (referência de código)

| Camada | Arquivo |
|--------|---------|
| Resolução | `app/domain/services/product/product_identifier_resolution_service.py` |
| Serviço | `app/application/services/product/product_directives_service.py` |
| Use case | `app/application/use_cases/product/get_product_directives_use_case.py` |
| Rota HTTP | `app/interface/http/routes/product_routes.py` |
| OpenAPI | `app/interface/http/openapi_agent_metadata.py` → `PRODUCT_DIRECTIVES` |
| Testes | `api-delpi/tests/test_product_directives.py` |

---

## 8. Pós-deploy

1. Reimportar OpenAPI no chat: `scripts/homologacao/sync-api-delpi-openapi.sh`
2. Reindexar RAG: [`minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md`](../../../minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md)

---

## 9. Validação homologada (jun/2026)

| Identificador | PA | Referência | MPs | Vínculos fornecedor | MPs c/ última compra |
|---------------|-----|------------|-----|---------------------|----------------------|
| `90260882` | 90260882 | 10018137 | 3 | 17 | 3 |
| `10018137` | 90260882 | 10018137 | 3 | 17 | 3 |

Ambos resolvem para o mesmo PA — amarração via `B1_REFEREN`.
