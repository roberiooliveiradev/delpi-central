# Playbook DELPI — Análise inteligente de preço de matéria-prima

## 1. Objetivo

Este playbook define como implementar rotas na **api-delpi** para análise de preço de **matéria-prima (MP)**, consolidando:

- **Último fornecedor** e última compra válida (NF de entrada);
- **ICMS** (alíquota e valor na NF, alíquota cadastral);
- **Histórico de orçamento** (solicitações de compra + pedidos de compra);
- **Variação de preço** entre compras consecutivas;
- Visão **composta** (rota única, no mesmo espírito de `factory-status`).

Escopo: produto identificado por `{code}` no path. A análise assume `SB1010.B1_TIPO = 'MP'`; se o código não for MP, a rota deve responder com aviso explícito, mas ainda pode devolver dados de compra quando existirem.

---

## 2. Regra-mãe

```text
Análise inteligente de preço de MP =
cadastro SB1010 (tipo, último preço cadastral, alíquota ICMS)
+ última NF válida SD1010 (fornecedor real, preço unitário, ICMS)
+ histórico de orçamento SC1010 (solicitação) + SC7010 (pedido)
+ série temporal de preços SD1010 com variação percentual
+ enriquecimento SA2010 (fornecedor) + SA5010 (partnumber).
```

**Fonte de preço preferencial (compra efetiva):** `SD1010.D1_VUNIT` (NF autorizada).  
**Fonte de orçamento/cotação formal:** `SC7010.C7_PRECO` (pedido de compra).  
**Fonte de requisição interna:** `SC1010.C1_*` (solicitação — preço pode estar zerado até gerar PC).

---

## 3. Tabelas e colunas (mapeamento validado)

Todas as tabelas abaixo constam em `api-delpi/app/config/allowed_tables.json`.

### 3.1 SB1010 — Cadastro do produto

| Coluna Protheus | Alias API sugerido | Uso |
|---|---|---|
| `B1_COD` | `product_code` | Código |
| `B1_DESC` | `description` | Descrição |
| `B1_TIPO` | `product_type` | Deve ser `MP` |
| `B1_UM` | `unit` | Unidade |
| `B1_GRUPO` | `group_code` | Grupo |
| `B1_UPRC` | `registered_last_purchase_price` | Último preço no cadastro |
| `B1_UCOM` | `registered_last_purchase_date` | Data última compra cadastro |
| `B1_PICM` | `registered_icms_rate` | Alíquota ICMS cadastral (%) |
| `B1_CUSTD` | `standard_cost` | Custo padrão (referência) |

---

### 3.2 SD1010 — Itens de NF de entrada (compra efetiva)

Tabela **principal** para última compra, ICMS e histórico de preço real.

| Coluna Protheus | Alias API sugerido | Uso |
|---|---|---|
| `D1_FILIAL` | `branch` | Filial |
| `D1_COD` | `product_code` | Produto |
| `D1_DOC` | `invoice_number` | Número NF |
| `D1_SERIE` | `invoice_series` | Série |
| `D1_ITEM` | `item` | Item NF |
| `D1_EMISSAO` | `issue_date` | Data emissão (AAAAMMDD) |
| `D1_DTDIGIT` | `entry_date` | Data digitação |
| `D1_FORNECE` | `supplier_code` | Fornecedor |
| `D1_LOJA` | `supplier_store` | Loja fornecedor |
| `D1_QUANT` | `quantity` | Quantidade |
| `D1_VUNIT` | `unit_price` | Preço unitário NF |
| `D1_TOTAL` | `total_value` | Valor total item |
| `D1_VALICM` | `icms_value` | Valor ICMS |
| `D1_PICM` | `icms_rate` | Alíquota ICMS na NF (%) |
| `D1_PEDIDO` | `purchase_order` | PC vinculado (`SC7010.C7_NUM`) |

> **Validado** via `POST /data/sql` em jun/2026. Coluna `D1_PRECO` **não existe** no ambiente DELPI.

Preço unitário alternativo (fallback):

```sql
CASE WHEN D1_QUANT <> 0 THEN D1_TOTAL / D1_QUANT ELSE 0 END
```

---

### 3.3 SA2010 — Cadastro de fornecedores

| Coluna | Alias | Uso |
|---|---|---|
| `A2_COD` | `supplier_code` | Código |
| `A2_LOJA` | `supplier_store` | Loja |
| `A2_NOME` | `supplier_name` | Razão social |
| `A2_CGC` | `supplier_tax_id` | CNPJ |
| `A2_EST` | `supplier_state` | UF |

**Filtros de compra válida (homologados):**

```sql
AND SD1.D1_FORNECE NOT IN ('000019', '001149')   -- fornecedores internos DELPI
AND UPPER(SA2.A2_NOME) NOT LIKE '%TRANSP%'       -- excluir transportadoras
```

---

### 3.4 SA5010 — Produto × Fornecedor

| Coluna | Alias | Uso |
|---|---|---|
| `A5_PRODUTO` | `product_code` | Produto DELPI |
| `A5_FORNECE` | `supplier_code` | Fornecedor |
| `A5_LOJA` | `supplier_store` | Loja |
| `A5_CODPRF` | `supplier_part_number` | Partnumber fornecedor |
| `A5_NOMEFOR` | `supplier_name` | Nome (cadastro vínculo) |

Relação com NF:

```sql
SA5010.A5_PRODUTO = SD1010.D1_COD
AND SA5010.A5_FORNECE = SD1010.D1_FORNECE
AND SA5010.A5_LOJA = SD1010.D1_LOJA
```

---

### 3.5 SC1010 — Solicitações de compra (requisição / orçamento interno)

| Coluna | Alias | Uso |
|---|---|---|
| `C1_NUM` | `requisition_number` | Número SC |
| `C1_ITEM` | `item` | Item |
| `C1_FILIAL` | `branch` | Filial |
| `C1_PRODUTO` | `product_code` | Produto |
| `C1_EMISSAO` | `issue_date` | Data emissão |
| `C1_DATPRF` | `required_date` | Data necessidade |
| `C1_FORNECE` | `supplier_code` | Fornecedor sugerido |
| `C1_LOJA` | `supplier_store` | Loja |
| `C1_QUANT` | `quantity` | Quantidade solicitada |
| `C1_PRECO` | `unit_price` | Preço na SC (pode ser 0) |
| `C1_TOTAL` | `total_value` | Total |
| `C1_PEDIDO` | `purchase_order` | PC gerado (`SC7010.C7_NUM`) |

> **Validado** jun/2026. `C1_VLDESC` **não existe** no ambiente.

---

### 3.6 SC7010 — Pedidos de compra (orçamento formal / cotação fechada)

| Coluna | Alias | Uso |
|---|---|---|
| `C7_NUM` | `purchase_order` | Número PC |
| `C7_ITEM` | `item` | Item |
| `C7_FILIAL` | `branch` | Filial |
| `C7_PRODUTO` | `product_code` | Produto |
| `C7_EMISSAO` | `issue_date` | Data emissão PC |
| `C7_DATPRF` | `required_date` | Data prevista |
| `C7_FORNECE` | `supplier_code` | Fornecedor |
| `C7_LOJA` | `supplier_store` | Loja |
| `C7_QUANT` | `quantity` | Quantidade |
| `C7_PRECO` | `unit_price` | Preço unitário PC |
| `C7_TOTAL` | `total_value` | Total item |

Vínculo SC → PC → NF:

```text
SC1010.C1_PEDIDO = SC7010.C7_NUM
SC7010.C7_NUM = SD1010.D1_PEDIDO  (mesmo fornecedor/produto)
```

---

## 4. Relações entre tabelas

```text
SB1010 (cadastro MP)
  │
  ├─ SA5010 (fornecedores cadastrados do produto)
  │     └─ SA2010 (dados do fornecedor)
  │
  ├─ SC1010 (solicitação de compra)
  │     └─ SC7010 via C1_PEDIDO = C7_NUM
  │
  ├─ SC7010 (pedido de compra)
  │     └─ SD1010 via D1_PEDIDO = C7_NUM (+ D1_FORNECE/D1_LOJA/D1_COD)
  │
  └─ SD1010 (NF entrada — compra efetiva)
        └─ SA2010 + SA5010
```

**Regra prática:**

| Pergunta | Tabela base |
|---|---|
| Última compra / último fornecedor / ICMS na NF | `SD1010` |
| Preço cotado no pedido | `SC7010` |
| Requisição / demanda interna | `SC1010` |
| Partnumber fornecedor | `SA5010` |
| Alíquota ICMS cadastral | `SB1010.B1_PICM` |
| Descrição / validação MP | `SB1010` |

Nunca usar `SA2010` ou `SA5010` como tabela principal de compra — apenas enriquecimento.

---

## 5. Rotas propostas (api-delpi)

Seguir o padrão dos playbooks fabril (`production-status`, `shipping-status`, `factory-status`).

### 5.1 Rotas granulares

| Método | Path | operationId | shape | Descrição |
|---|---|---|---|---|
| GET | `/products/{code}/last-purchase` | `get_product_last_purchase` | `playbook_report` | Última NF válida + fornecedor + ICMS |
| GET | `/products/{code}/purchase-price-history` | `get_product_purchase_price_history` | `paged_list` | Série de NFs com preço e variação |
| GET | `/products/{code}/purchase-budget-history` | `get_product_purchase_budget_history` | `paged_list` | SC1010 + SC7010 unificados |
| GET | `/products/{code}/suppliers` | `get_product_suppliers` | `paged_list` | **Já existe** — reutilizar |
| GET | `/products/{code}/purchases` | `get_product_purchases` | `paged_list` | **Já existe** — PCs paginados |
| GET | `/products/{code}/inbound-invoice-items` | `get_product_inbound_invoice_items` | `paged_list` | **Já existe** — NFs paginadas |

### 5.2 Rota composta (preferida pelo chat)

| Método | Path | operationId | shape |
|---|---|---|---|
| GET | `/products/{code}/raw-material-price-intelligence` | `get_product_raw_material_price_intelligence` | `composite_analysis` |

**Query params sugeridos:**

| Param | Obrigatório | Default | Descrição |
|---|---|---|---|
| `code` | sim (path) | — | Código da MP |
| `branch` | não | todas | Filial (`D1_FILIAL` / `C7_FILIAL`) |
| `date_start` | não | últimos 12 meses | Início histórico (DD-MM-YYYY na API) |
| `date_end` | não | hoje | Fim histórico |
| `history_limit` | não | 24 | Máx. registros no histórico de preço |
| `legacy` | não | `false` | Compatibilidade SIM/NAO se necessário |

**Seções do payload composto** (via `build_composite_sections`):

```text
product              → cabeçalho SB1010
last_purchase        → última NF válida
budget_history       → SC1010 + SC7010
price_history        → SD1010 com variação
price_variation      → resumo (min/max/média/última variação %)
suppliers            → top fornecedores (SA5010 + último preço)
indicators           → KPIs consolidados
price_status         → classificação (estável / alta / queda / sem histórico)
```

---

## 6. Contrato de resposta (composite)

Modelo alinhado a `GET /products/{code}/factory-status`:

```json
{
  "success": true,
  "message": "Análise de preço da matéria-prima carregada com sucesso.",
  "meta": {
    "operationId": "get_product_raw_material_price_intelligence",
    "entity": "product_raw_material_price_intelligence",
    "shape": "composite_analysis",
    "relatedRoutes": ["/products/10080001/last-purchase", "..."]
  },
  "data": {
    "product": {
      "product_code": "10080001",
      "description": "...",
      "product_type": "MP",
      "unit": "UN",
      "registered_last_purchase_price": 0.0892799,
      "registered_last_purchase_date": "20260407",
      "registered_icms_rate": 7.0,
      "standard_cost": 0.08
    },
    "last_purchase": {
      "branch": "02",
      "invoice_number": "000984488",
      "issue_date": "20260407",
      "supplier_code": "000002",
      "supplier_name": "TE CONNECTIVITY...",
      "supplier_part_number": "...",
      "quantity": 182000.0,
      "unit_price": 0.0892799,
      "total_value": 16248.94,
      "icms_value": 1137.43,
      "icms_rate": 7.0,
      "purchase_order": "041446"
    },
    "budget_history": {
      "items": [
        {
          "source": "SC1010",
          "document_number": "164708",
          "issue_date": "20260430",
          "supplier_code": "000002",
          "quantity": 300000.0,
          "unit_price": 0.0,
          "purchase_order": "041446"
        },
        {
          "source": "SC7010",
          "document_number": "041446",
          "issue_date": "20260430",
          "supplier_code": "000002",
          "quantity": 294000.0,
          "unit_price": 0.0892799,
          "total_value": 26248.29
        }
      ],
      "summary": {
        "total_requisitions": 1,
        "total_purchase_orders": 1
      }
    },
    "price_history": {
      "items": [
        {
          "issue_date": "20260407",
          "invoice_number": "000984488",
          "supplier_name": "...",
          "unit_price": 0.0892799,
          "icms_rate": 7.0,
          "variation_percent": 0.0
        }
      ],
      "summary": {
        "min_unit_price": 0.089,
        "max_unit_price": 0.092,
        "avg_unit_price": 0.090,
        "last_variation_percent": 0.0,
        "total_purchases": 12
      }
    },
    "price_status": "ESTAVEL",
    "indicators": {
      "registered_vs_last_nf_diff_percent": 0.0,
      "dominant_supplier_code": "000002",
      "dominant_supplier_share_percent": 95.0
    }
  }
}
```

---

## 7. Queries SQL (validadas)

Validar sempre via `POST /apps/api-delpi/data/sql` com body `{"sql": "..."}` antes de fixar no repositório.

### 7.1 Query 1 — Cabeçalho da matéria-prima

```sql
SELECT TOP 1
    B1_COD  AS product_code,
    B1_DESC AS description,
    B1_TIPO AS product_type,
    B1_UM   AS unit,
    B1_GRUPO AS group_code,
    B1_UPRC AS registered_last_purchase_price,
    B1_UCOM AS registered_last_purchase_date,
    B1_PICM AS registered_icms_rate,
    B1_CUSTD AS standard_cost
FROM SB1010 WITH (NOLOCK)
WHERE D_E_L_E_T_ = ''
  AND B1_COD = @PRODUTO;
```

---

### 7.2 Query 2 — Última NF válida (último fornecedor + última compra + ICMS)

```sql
DECLARE @PRODUTO VARCHAR(30) = '10080001';

WITH ULTIMA_NF AS (
    SELECT
        SD1.D1_FILIAL AS branch,
        SD1.D1_COD AS product_code,
        SD1.D1_DOC AS invoice_number,
        SD1.D1_SERIE AS invoice_series,
        SD1.D1_EMISSAO AS issue_date,
        SD1.D1_DTDIGIT AS entry_date,
        SD1.D1_FORNECE AS supplier_code,
        SD1.D1_LOJA AS supplier_store,
        SD1.D1_QUANT AS quantity,
        SD1.D1_VUNIT AS unit_price,
        SD1.D1_TOTAL AS total_value,
        SD1.D1_VALICM AS icms_value,
        SD1.D1_PICM AS icms_rate,
        SD1.D1_PEDIDO AS purchase_order,
        SA2.A2_NOME AS supplier_name,
        SA2.A2_CGC AS supplier_tax_id,
        SA2.A2_EST AS supplier_state,
        A5.A5_CODPRF AS supplier_part_number,
        ROW_NUMBER() OVER (
            PARTITION BY SD1.D1_COD
            ORDER BY
                SD1.D1_EMISSAO DESC,
                SD1.D1_DTDIGIT DESC,
                SD1.D1_DOC DESC
        ) AS rn
    FROM SD1010 SD1 WITH (NOLOCK)
    INNER JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = SD1.D1_FORNECE
       AND SA2.A2_LOJA = SD1.D1_LOJA
       AND SA2.D_E_L_E_T_ = ''
    LEFT JOIN SA5010 A5 WITH (NOLOCK)
        ON A5.A5_PRODUTO = SD1.D1_COD
       AND A5.A5_FORNECE = SD1.D1_FORNECE
       AND A5.A5_LOJA = SD1.D1_LOJA
       AND A5.D_E_L_E_T_ = ''
    WHERE SD1.D_E_L_E_T_ = ''
      AND SD1.D1_COD = @PRODUTO
      AND SD1.D1_FORNECE NOT IN ('000019', '001149')
      AND UPPER(SA2.A2_NOME) NOT LIKE '%TRANSP%'
)
SELECT *
FROM ULTIMA_NF
WHERE rn = 1;
```

**Critério de desempate (homologado):** `D1_EMISSAO DESC`, `D1_DTDIGIT DESC`, `D1_DOC DESC`.

---

### 7.3 Query 3 — Histórico de preço com variação percentual

```sql
DECLARE @PRODUTO VARCHAR(30) = '10080001';
DECLARE @LIMITE INT = 24;

WITH COMPRAS AS (
    SELECT
        SD1.D1_FILIAL AS branch,
        SD1.D1_EMISSAO AS issue_date,
        SD1.D1_DOC AS invoice_number,
        SD1.D1_FORNECE AS supplier_code,
        SA2.A2_NOME AS supplier_name,
        SD1.D1_VUNIT AS unit_price,
        SD1.D1_VALICM AS icms_value,
        SD1.D1_PICM AS icms_rate,
        SD1.D1_QUANT AS quantity,
        ROW_NUMBER() OVER (
            ORDER BY SD1.D1_EMISSAO DESC, SD1.D1_DTDIGIT DESC, SD1.D1_DOC DESC
        ) AS seq
    FROM SD1010 SD1 WITH (NOLOCK)
    INNER JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = SD1.D1_FORNECE
       AND SA2.A2_LOJA = SD1.D1_LOJA
       AND SA2.D_E_L_E_T_ = ''
    WHERE SD1.D_E_L_E_T_ = ''
      AND SD1.D1_COD = @PRODUTO
      AND SD1.D1_FORNECE NOT IN ('000019', '001149')
      AND UPPER(SA2.A2_NOME) NOT LIKE '%TRANSP%'
)
SELECT TOP (@LIMITE)
    C.branch,
    C.issue_date,
    C.invoice_number,
    C.supplier_code,
    C.supplier_name,
    C.unit_price,
    C.icms_value,
    C.icms_rate,
    C.quantity,
    P.unit_price AS previous_unit_price,
    CASE
        WHEN ISNULL(P.unit_price, 0) = 0 THEN NULL
        ELSE ((C.unit_price - P.unit_price) / P.unit_price) * 100
    END AS variation_percent
FROM COMPRAS C
LEFT JOIN COMPRAS P
    ON P.seq = C.seq + 1
ORDER BY C.seq;
```

---

### 7.4 Query 4 — Histórico de orçamento (SC1010 + SC7010)

```sql
DECLARE @PRODUTO VARCHAR(30) = '10080001';
DECLARE @DATA_INI VARCHAR(8) = '20250101';
DECLARE @DATA_FIM VARCHAR(8) = '20270101';  -- exclusivo

WITH REQUISICOES AS (
    SELECT
        'SC1010' AS source,
        C1.C1_FILIAL AS branch,
        C1.C1_NUM AS document_number,
        C1.C1_ITEM AS item,
        C1.C1_EMISSAO AS issue_date,
        C1.C1_DATPRF AS required_date,
        C1.C1_FORNECE AS supplier_code,
        C1.C1_LOJA AS supplier_store,
        C1.C1_QUANT AS quantity,
        C1.C1_PRECO AS unit_price,
        C1.C1_TOTAL AS total_value,
        C1.C1_PEDIDO AS purchase_order
    FROM SC1010 C1 WITH (NOLOCK)
    WHERE C1.D_E_L_E_T_ = ''
      AND C1.C1_PRODUTO = @PRODUTO
      AND C1.C1_EMISSAO >= @DATA_INI
      AND C1.C1_EMISSAO < @DATA_FIM
),
PEDIDOS AS (
    SELECT
        'SC7010' AS source,
        C7.C7_FILIAL AS branch,
        C7.C7_NUM AS document_number,
        C7.C7_ITEM AS item,
        C7.C7_EMISSAO AS issue_date,
        C7.C7_DATPRF AS required_date,
        C7.C7_FORNECE AS supplier_code,
        C7.C7_LOJA AS supplier_store,
        C7.C7_QUANT AS quantity,
        C7.C7_PRECO AS unit_price,
        C7.C7_TOTAL AS total_value,
        CAST(NULL AS VARCHAR(20)) AS purchase_order
    FROM SC7010 C7 WITH (NOLOCK)
    WHERE C7.D_E_L_E_T_ = ''
      AND C7.C7_PRODUTO = @PRODUTO
      AND C7.C7_EMISSAO >= @DATA_INI
      AND C7.C7_EMISSAO < @DATA_FIM
)
SELECT *
FROM (
    SELECT * FROM REQUISICOES
    UNION ALL
    SELECT * FROM PEDIDOS
) H
ORDER BY issue_date DESC, source DESC, document_number DESC;
```

**Interpretação:**

- `SC1010` = demanda/requisição (orçamento interno; `C1_PRECO` pode ser 0);
- `SC7010` = preço formalizado no pedido;
- Cruzar `C1_PEDIDO` com `C7_NUM` para narrativa «SC gerou PC X com preço Y».

---

### 7.5 Query 5 — Resumo de variação (KPIs)

```sql
-- Usar CTE COMPRAS da Query 3 e agregar:
SELECT
    COUNT(*) AS total_purchases,
    MIN(unit_price) AS min_unit_price,
    MAX(unit_price) AS max_unit_price,
    AVG(unit_price) AS avg_unit_price,
    MAX(CASE WHEN seq = 1 THEN variation_percent END) AS last_variation_percent
FROM (
    -- subquery COMPRAS + LEFT JOIN anterior (Query 3)
) X;
```

---

## 8. Classificação `price_status`

| Condição | Status |
|---|---|
| Sem NF válida | `SEM HISTORICO DE COMPRA` |
| Última variação entre -2% e +2% | `ESTAVEL` |
| Última variação > +2% | `ALTA DE PRECO` |
| Última variação < -2% | `QUEDA DE PRECO` |
| Cadastro `B1_UPRC` diverge > 5% da última NF | `DIVERGENCIA CADASTRO VS NF` |

Limiares configuráveis no serviço de domínio (`classify_price_status`), não no prompt do agente.

---

## 9. Implementação na api-delpi (checklist)

**Status: implementado (jun/2026)**

| Rota | Arquivo principal |
|---|---|
| `GET /products/{code}/last-purchase` | `get_product_raw_material_price_use_cases.py` |
| `GET /products/{code}/purchase-price-history` | idem |
| `GET /products/{code}/purchase-budget-history` | idem |
| `GET /products/{code}/raw-material-price-intelligence` | idem (composta) |

Repositório: `product_raw_material_price_repository.py`  
Serviço: `product_raw_material_price_service.py`  
Testes: `tests/test_product_raw_material_price_use_cases.py`

Integração chat (intent/vocabulário): pendente — ver backlog separado.

### 9.1 Camadas (referência)

| Camada | Arquivo sugerido |
|---|---|
| Port | `domain/ports/product/product_raw_material_price_repository_port.py` |
| Repository | `infrastructure/persistence/totvs/product_repositories/product_raw_material_price_repository.py` |
| Service | `application/services/product/product_raw_material_price_service.py` (summaries + classify) |
| DTO | Reutilizar `ProductPlaybookRequest` ou estender com `history_limit` |
| Use cases | `get_product_last_purchase_use_case.py`, `get_product_purchase_price_history_use_case.py`, `get_product_purchase_budget_history_use_case.py`, `get_product_raw_material_price_intelligence_use_case.py` |
| Composer | `composition/product_composer.py` |
| Routes | `interface/http/routes/product_routes.py` |
| OpenAPI | `openapi_agent_metadata.py` (`PRODUCT_RAW_MATERIAL_PRICE_INTELLIGENCE`, etc.) |
| Registry | `route_contract_registry.py` |
| Testes | `tests/test_product_raw_material_price_use_cases.py` + smoke |

### 9.2 Contrato HTTP

- Sucesso: `product_success(..., shape="composite_analysis")` ou `playbook_report`;
- `operationId` estável para chat;
- Erro 400 se produto inexistente;
- `?legacy=true` só se necessário (preferir bool/número nativo).

### 9.3 Rotas existentes — o que reaproveitar

| Rota existente | Limitação para esta análise |
|---|---|
| `/suppliers` | Preço por fornecedor via `SC7010`, sem ICMS NF |
| `/purchases` | Só PCs, sem variação nem ICMS |
| `/inbound-invoice-items` | NFs paginadas, sem variação agregada |
| `/pricing` | Tabela comercial `DA1010` — **não** é preço de compra MP |

A rota composta **unifica** o que hoje exige 3–4 chamadas + lógica no chat.

---

## 10. Integração chat (minha-delpi-ai-api)

| Item | Ação |
|---|---|
| Intent | Estender `ChatProductQueryIntentService` — termos: preço matéria-prima, última compra, ICMS compra, variação preço, orçamento compra |
| Seleção rota | `ExternalActionProductRouteSelectionService` → `get_product_raw_material_price_intelligence` |
| Presenter | `ExternalActionProductCompositeAnalysisPresenter` ou presenter dedicado |
| Vocabulário | `product_query_intent.json` → seção `rawMaterialPrice` |
| Textos UI | `presenter_content.json` / `column_labels.json` (sem strings em Python) |
| Regressão | `chat_intelligence_regression_cases.py` |
| Smoke | Estender `scripts/smoke_playbook_product_routes.py` |

**Frases recomendadas:**

- «Análise de preço da matéria-prima 10080001»
- «Última compra e ICMS do produto 10080001»
- «Histórico de orçamento de compra do 10080001 nos últimos 12 meses»

---

## 11. Validação técnica

### 11.1 SQL ad hoc

```bash
curl -s -X POST "http://localhost/apps/api-delpi/data/sql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sql":"SELECT TOP 1 D1_COD, D1_VUNIT, D1_VALICM, D1_PICM FROM SD1010 WHERE D_E_L_E_T_ = '\'''\''"}'
```

### 11.2 Produto de teste homologado

- `10080001` — MP com NF, PC, SC e fornecedor TE Connectivity (validado jun/2026).

### 11.3 Colunas confirmadas / rejeitadas

| Coluna | Status |
|---|---|
| `SD1010.D1_VUNIT`, `D1_VALICM`, `D1_PICM` | OK |
| `SD1010.D1_PRECO` | **Não existe** |
| `SC1010.C1_PRECO`, `C1_TOTAL`, `C1_PEDIDO` | OK |
| `SC1010.C1_VLDESC` | **Não existe** |
| `SC7010.C7_PRECO`, `C7_TOTAL` | OK |

---

## 12. Fontes de verdade por pergunta

| Pergunta do usuário | Fonte principal |
|---|---|
| Quem é o último fornecedor? | `SD1010` última NF válida |
| Quando foi a última compra? | `SD1010.D1_EMISSAO` |
| Qual o preço da última compra? | `SD1010.D1_VUNIT` |
| Quanto de ICMS na última NF? | `SD1010.D1_VALICM` / `D1_PICM` |
| Qual a alíquota cadastral? | `SB1010.B1_PICM` |
| Histórico de orçamento? | `SC1010` + `SC7010` |
| Como variou o preço? | Série `SD1010` + `variation_percent` |
| Partnumber do fornecedor? | `SA5010.A5_CODPRF` |

---

## 13. Resumo executivo

```text
Para análise inteligente de preço de matéria-prima, parta do cadastro SB1010,
identifique a última NF válida em SD1010 (excluindo transportadoras e fornecedores internos),
extraia fornecedor, preço unitário e ICMS, complemente com histórico SC1010/SC7010
e calcule variação percentual entre compras consecutivas.
Exponha rotas granulares e uma rota composta raw-material-price-intelligence,
no mesmo padrão dos playbooks fabril já implementados.
```
