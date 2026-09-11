---
name: WF-05 Pedidos lista
overview: "E7 — lista operacional de Pedidos de Compra (SC7 aberto) no Portal Suprimentos: contrato api-delpi + BFF supplies-api + MFE kit-first. Sem detalhe (E8) nem Entregas (E9)."
todos:
  - id: e7-s1-api-delpi-contract
    content: E7.S1 GET /supplies/purchase-orders (SC7 aberto paginado) + testes
    status: completed
  - id: e7-s2-bff
    content: E7.S2 BFF supplies-api GET /purchase-orders + AuthZ operations+unit
    status: completed
  - id: e7-s3-mfe
    content: E7.S3 MFE lista kit-first + URL/F5 + estados (sem detalhe)
    status: completed
  - id: e7-s4-help-gate
    content: E7.S4 Help + GATE-FEATURE docs/testes; smoke INCONCLUSIVE se preciso
    status: completed
isProject: false
---

# E7 — WF-05 Pedidos de Compra (lista)

**Autorização PO:** explícita nesta conversa (2026-09-11).  
**Pré-condição:** E6.S5 / WF-04 PASS.

## Ledger

| RQ | Requisito | Estado |
|----|-----------|--------|
| RQ-01 | Lista operacional de PCs abertos (filial) | ATENDIDO_NO_PLANO |
| RQ-02 | MFE → supplies-api → api-delpi (sem MFE→api-delpi) | ATENDIDO_NO_PLANO |
| RQ-03 | AuthZ `supplies.operations.access` + unit | ATENDIDO_NO_PLANO |
| RQ-04 | Kit-first + estados + URL/F5 | ATENDIDO_NO_PLANO |
| RQ-05 | Help sincronizado | ATENDIDO_NO_PLANO |
| RQ-06 | Positive + sibling + negative | ATENDIDO_NO_PLANO |
| RQ-07 | Detalhe do pedido | FORA_DO_ESCOPO — E8 |
| RQ-08 | Entregas / OTD panel worklist | FORA_DO_ESCOPO — E9 / analytics |
| RQ-09 | Export CSV | FORA_DO_ESCOPO nesta onda |
| RQ-10 | Follow-up write | FORA_DO_ESCOPO até contrato |

## Decisão travada — universo da lista

**CONFIRMADO:** OTD `/purchase-order-otd/panel` = linhas de **recebimento** MP (pontualidade histórica).  
**CONFIRMADO:** `open_purchase_orders_sql` (SC7) = PCs **abertos** (saldo `C7_QUANT > C7_QUJE`, residual ≠ S) — já usado em ESTSEG/LNF.

**Decisão:** WF-05 lista = **SC7 aberto**, linha a linha, paginado.  
Não usar OTD panel como worklist. CTA “abrir detalhe” navega para rota E8 (placeholder até E8).

## Arquitetura

```text
plugins/supplies /purchase-orders
  → supplies-api GET /purchase-orders  (operations + unit)
    → api-delpi GET /supplies/purchase-orders  (KPI_SUPPLIES_ACCESS)
      → SC7010 open_purchase_orders (+ filtros/paginação)
```

## Delta

| Caso | Antes | Depois |
|------|-------|--------|
| P0 | PlaceholderPage | Lista kit-first com linhas abertas |
| Sibling filial 02 | — | unit scope no BFF |
| Negativo sem operations | Forbidden shell | Intact |
| Invariante | OTD analytics / SC / Overview | Intactos |

## Etapas

### E7.S1 — Contrato api-delpi
- `GET /supplies/purchase-orders` `operationId=list_supplies_purchase_orders`
- Params: `branch` (obrigatório), `page`, `page_size`, `order_number`, `product_code`, `supplier_code`, `expected_delivery_from/to`, `late_only`
- SQL: generalizar open SC7 com count + OFFSET/FETCH; reutilizar regra residual/saldo
- Registry + OpenAPI locale mínimo + smoke A
- **Não** import Action Catalog nesta etapa (Portal-first; chat = follow-up checklist)

### E7.S2 — BFF
- Gateway + rota Flask espelhando SC
- Testes positive / unit forbidden / access forbidden

### E7.S3 — MFE
- Feature `purchase-orders` espelhando DoD de SC (PageHero/FilterBar/SectionCard)
- Deep link detalhe → placeholder E8 sem implementar detalhe
- Sem export nesta onda

### E7.S4 — Help + GATE
- Tooltips/Manual/Quero→onde
- Atualizar README/WIREFRAMES/API-ROUTES/IMPLEMENTATION-PLAN
- Smoke federado `INCONCLUSIVE` se ambiente não permitir

## Fora
E8 detalhe, E9 entregas, KPI-PO-LATE no Overview, C2, cutover.
