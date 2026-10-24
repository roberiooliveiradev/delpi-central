# SC/PC Detail Enrichment — Matriz de Contratos e Dados (P0 Discovery)

> Status: `DISCOVERY_COMPLETE` · `IMPLEMENTATION_NOT_AUTHORIZED` · `NO_CODE_CHANGE`
> Baseline: `f89e73376c` · Data: 2026-06-06 · Autor: Devin (investigação read-only)

Matriz mestra de campos das fichas **Detalhe da SC** e **Detalhe do PC** do Portal Suprimentos.
Cada campo é classificado por prova real de código — nunca por roadmap ou inferência.

## Legenda de classificação

| Classe | Significado |
|---|---|
| `PROVEN_IN_FRONTEND` | Campo já declarado no `types.ts` do MFE (e geralmente renderizado). |
| `PROVEN_IN_BFF` | Campo efetivamente exposto pelo `supplies-api` (passthrough ou enriquecimento). |
| `PROVEN_IN_PRODUCER` | Campo emitido pelo owner canônico (purchase-requests-api / api-delpi). |
| `TO_INVENTORY` | Fonte candidata existe (TOTVS/doc), sem confirmação de contrato em produção. |
| `PLANNED` | Informação desejada sem contrato aprovado — exige decisão arquitetural. |

## Cadeia de custódia comprovada

```
SC1 (TOTVS) ──api-delpi──▶ /supplies/purchase-requests/lines/{branch}/{number}
                ──purchase-requests-api──▶ /purchase-requests/{branch}/{number}
                ──supplies-api──▶ GET /purchase-requests/{branch}/{number}  → MFE

SC7 (TOTVS) ──api-delpi──▶ /supplies/purchase-orders/{branch}/{number}
                ──supplies-api──▶ GET /purchase-orders/{branch}/{number}   → MFE
SD1 (recebimentos) ──aninhados por item em ambos os produtores──▶ MFE
```

- `purchase-requests-api` **não** é um agregador leve: o `GetPurchaseRequestUseCase` chama
  `DelpiPurchaseRequestsGateway.get_request_lines()` que lê `api-delpi`
  (`/supplies/purchase-requests/lines/{branch}/{request_number}`) e aplica
  `PurchaseRequestAggregationService` (escopo por CC, stage derivado, timeline).
- O BFF repassa o payload **completo** do produtor SC (`_unwrap_data` →
  `enrich_payload` só injeta `display_name`/`photo_url`/`user_id` nos `requester` refs).
  → **Todo campo do produtor SC já chega ao MFE**; os não declarados em `types.ts`
  são `PROVEN_IN_BFF`, não `PLANNED`.
- PC detail no BFF é passthrough de `api-delpi` (`unwrap_delpi_envelope`), sem enriquecimento.

## Matriz mestra — SC (Detalhe da Solicitação de Compra)

### Cabeçalho

| Campo funcional | Campo técnico | Fonte | Página renderiza? | Classe | Evidência |
|---|---|---|---|---|---|
| Filial | `header.branch` | `C1_FILIAL` | Sim (hero) | `PROVEN_IN_FRONTEND` | `PurchaseRequestDetailPage.tsx` |
| Número da SC | `header.request_number` | `C1_NUM` | Sim (hero) | `PROVEN_IN_FRONTEND` | idem |
| Data de abertura | `header.issue_date` | `MIN(C1_EMISSAO)` | Sim | `PROVEN_IN_FRONTEND` | `lines_sql.py:292`, `_aggregate_header` |
| Solicitante | `header.requester{name,code,protheus_user_id,display_name,photo_url,user_id}` | `C1_SOLICIT`/`C1_USER`/`USR_*` + Core | Sim (nome+foto) | `PROVEN_IN_FRONTEND` | `requester_identity_service.py` |
| Situação geral | `header.overall_stage` | derivado (7 estágios) | Sim | `PROVEN_IN_FRONTEND` | `_conservative_stage` |
| Itens visíveis | `header.visible_items_count` | contagem pós-escopo | Sim | `PROVEN_IN_FRONTEND` | agregação |
| Aprovação (resumo) | `header.approval_summary.status` | `C1_APROV` → `map_approval_status` | Sim (badge) | `PROVEN_IN_FRONTEND` | `lines_sql.py:327` |
| Centros de custo | `header.cost_centers[{code,description}]` | `C1_CC` + `CTT_DESC01` | **Não** | `PROVEN_IN_BFF` | agregação — MFE declara mas não renderiza a descrição |
| Pedidos vinculados | `header.purchase_orders[{branch,order_number,order_item,supplier_*}]` | `C7_*` via linhas | **Não** | `PROVEN_IN_BFF` | `_aggregate_header` orders dict |
| Fornecedores | `header.suppliers[{code,store,name}]` | `C7_FORNECE/C7_LOJA`+`A2_*` | **Não** | `PROVEN_IN_BFF` | idem |
| Primeira/última emissão de pedido | `header.first_order_date`, `last_order_date` | `C7_EMISSAO` | **Não** | `PROVEN_IN_BFF` | idem |
| Primeiro/último recebimento | `header.first_receipt_date`, `last_receipt_date` | `D1_DTDIGIT` | **Não** | `PROVEN_IN_BFF` | idem |
| Totais solicitado/pedido/recebido | `header.requested_quantity`, `ordered_quantity`, `received_quantity` | `C1_QUANT`,`C1_QUJE`,`D1_QUANT` | **Não** | `PROVEN_IN_BFF` | idem |
| Alerta de atraso | `header.has_overdue_order`, `max_days_overdue` | `C7_DATPRF` derivado | **Não** | `PROVEN_IN_BFF` | idem |

### Itens (`lines[]`)

| Campo funcional | Campo técnico | Fonte | Renderizado? | Classe | Evidência |
|---|---|---|---|---|---|
| Item | `request_item` | `C1_ITEM` | Sim | `PROVEN_IN_FRONTEND` | `lines_sql.py:307` |
| Produto / descrição | `product_code`, `product_description` | `C1_PRODUTO` + `B1_DESC`/`C1_DESCRI` | Sim | `PROVEN_IN_FRONTEND` | `lines_sql.py:308-309` |
| Quantidade solicitada | `requested_quantity` | `C1_QUANT` | Sim | `PROVEN_IN_FRONTEND` | `lines_sql.py:311` |
| Centro de custo | `cost_center_code` / `cost_center{code,description}` | `C1_CC` + `CTT` | Parcial (só código) | `PROVEN_IN_BFF` | `lines_sql.py:324-325` |
| Situação do item | `derived.overall_stage` | derivado | Sim | `PROVEN_IN_FRONTEND` | `_enrich_line` |
| Unidade de medida | `unit` | `C1_UM` | **Não** | `PROVEN_IN_BFF` | `lines_sql.py:310` |
| Data de necessidade | `request_required_date` | `C1_DATPRF` | **Não** | `PROVEN_IN_BFF` | `lines_sql.py:320` |
| Quantidade pedida | `ordered_quantity` | `C1_QUJE` | **Não** | `PROVEN_IN_BFF` | `lines_sql.py:312` |
| Saldo da SC | `request_open_quantity` | `C1_QUANT−C1_QUJE` | **Não** | `PROVEN_IN_BFF` | `lines_sql.py:318` |
| Aprovação do item | `approval{status,approver_name}` | `C1_APROV` + `C1_NOMAPRO` | **Não** | `PROVEN_IN_BFF` | `lines_sql.py:327-328`, `_enrich_line` |
| Fornecedor sugerido | `suggested_supplier{code,store,name}` | `C1_FORNECE`/`C1_LOJA` + `A2` | **Não** | `PROVEN_IN_BFF` | `lines_sql.py:330-332` |
| Conta contábil | `account_code` | `C1_CONTA` | **Não** | `PROVEN_IN_BFF` | `lines_sql.py:326` |
| Resíduo | `residual` | `C1_RESIDUO='S'` | **Não** (via stage) | `PROVEN_IN_BFF` | `lines_sql.py:329` |
| Pedidos por item | `purchase_orders[]` com `order_number`,`order_item`,`ordered_quantity`,`received_quantity`,`open_quantity`,`issue_date`,`expected_delivery_date`,`supplier_*`,`buyer`,`order_user_*`,`derived{delivery_status,days_overdue,days_until_due,receipt_status}`,`receipts[]` | SC7 + SD1 | **Não** | `PROVEN_IN_BFF` | `lines_sql.py:505-545`, `_enrich_order` |

### Timeline

| Campo | Tipo | Eventos provados | Renderizado? | Classe |
|---|---|---|---|---|
| `timeline[]` | `{type,date,label,reference,metadata}` | `request_created`, `purchase_order_created`, `expected_delivery`, `receipt` (ordenado por data) | **Não** | `PROVEN_IN_BFF` (`_build_timeline:499`) |

### Desejado mas NÃO comprovado — SC

| Campo funcional | Classe | Observação |
|---|---|---|
| Aprovador com identidade portal (foto/link) | `TO_INVENTORY` | `C1_NOMAPRO` retorna nome de texto; resolução de identidade exige contrato novo |
| "Próximo passo" / responsável pela ação | `PLANNED` | Nenhum owner define ação recomendada; não inferir do stage |
| Comprador responsável pela SC | `PLANNED` | `buyer` existe só nos pedidos vinculados (`C7_COMPRA`), não na SC sem pedido |
| Histórico de eventos auditável (alteração de previsão, cancelamentos) | `TO_INVENTORY` | timeline atual é derivada de datas de SC7/SD1 — não é auditoria |
| Quantidade recebida por item da SC | `PROVEN_IN_BFF` | derivável de `line.purchase_orders[].received_quantity` (com nota: ver P15) |

## Matriz mestra — PC (Detalhe do Pedido de Compra)

> **Restrição estrutural provada:** `get_open_order`/`build_purchase_orders_list_filters`
> só cobre linhas abertas (`C7_QUANT > C7_QUJE`, `C7_RESIDUO <> 'S'`).
> Pedido totalmente entregue/residual retorna **404** — a ficha PC é uma ficha de
> pedidos *em aberto*, não um histórico completo. Ver `CONTRACT_GAPS`.

### Cabeçalho

| Campo funcional | Campo técnico | Fonte | Renderizado? | Classe | Evidência |
|---|---|---|---|---|---|
| Filial | `branch` | `C7_FILIAL` | Sim | `PROVEN_IN_FRONTEND` | `purchase_orders_list_sql.py:249` |
| Número | `order_number` | `C7_NUM` | Sim | `PROVEN_IN_FRONTEND` | `lines:250` |
| Data de emissão | `items[].issue_date` (por item, não header) | `C7_EMISSAO` | Sim (por item) | `PROVEN_IN_FRONTEND` | `lines:263` |
| Fornecedor | `items[].supplier_{code,store,name}` | `C7_FORNECE`/`C7_LOJA` + `A2_NREDUZ/A2_NOME` | Sim (por item) | `PROVEN_IN_FRONTEND` | `lines:265-267` |
| Comprador | `items[].buyer_code` | `C7_COMPRA` | Sim (badge por item) | `PROVEN_IN_FRONTEND` | `lines:245` |
| SC de origem | `items[].source_request_number`, `source_request_item` | `C7_NUMSC`/`C7_ITEMSC` | Sim (texto) | `PROVEN_IN_FRONTEND` | `lines:246-247` |
| **Header agregado** (total do pedido, fornecedor único, status geral, valor recebido) | — | — | — | `PLANNED` | `compose_open_purchase_order` retorna só `{branch,order_number,items}` |

### Itens (`items[]`)

| Campo funcional | Fonte | Renderizado? | Classe |
|---|---|---|---|
| `order_item`, `product_code`, `product_description` | `C7_ITEM`,`C7_PRODUTO`,`B1_DESC`/`C7_DESCRI` | Sim | `PROVEN_IN_FRONTEND` |
| `ordered_quantity`, `delivered_quantity`, `open_quantity` | `C7_QUANT`,`C7_QUJE`, diferença | Sim | `PROVEN_IN_FRONTEND` |
| `unit_price` | `C7_PRECO` | Sim | `PROVEN_IN_FRONTEND` |
| `open_value` | `C7_TOTAL+IPI+FRETE−DESCONTO × balance_factor` | Sim | `PROVEN_IN_FRONTEND` (`_OPEN_VALUE_EXPRESSION:32-38`) |
| `issue_date`, `expected_delivery_date` | `C7_EMISSAO`,`C7_DATPRF` | Sim | `PROVEN_IN_FRONTEND` |
| `delivery_status` (`late`/`on_time`/`no_date`) | derivado | Sim | `PROVEN_IN_FRONTEND` |
| `receipts[]` `{invoice_number,invoice_series,invoice_item,quantity,unit_price,total_value,invoice_issue_date,entry_date}` | `SD1` | Sim (tabela por item) | `PROVEN_IN_FRONTEND` |

### Desejado mas NÃO comprovado — PC

| Campo funcional | Candidato TOTVS | Classe | Observação |
|---|---|---|---|
| Nome do comprador | `SAK?`/`SYS_USR`/`C7_COMPRA`→cadastro | `TO_INVENTORY` | só `buyer_code`; nome exige join/lookup novo |
| Unidade de medida do item | `C7_UM` | `TO_INVENTORY` | não selecionado no SQL atual |
| Condição de pagamento | `C7_COND` | `TO_INVENTORY` | fonte: `COMXPROC.prw`, `IXMLSEF.prw` |
| Moeda | `C7_MOEDA` | `TO_INVENTORY` | idem |
| Observação/mensagem do pedido | `C7_OBS`/`C7_MSG`/`C7_MENSPAD` | `TO_INVENTORY` | fonte: `COMXPROC.prw`, `DLPMATR110.prw` |
| CNPJ/identificação fiscal do fornecedor | `A2_CGC`/`A2_END`/`A2_TEL` | `TO_INVENTORY` | join SA2 já existe — campos não selecionados; decisão de sensibilidade necessária |
| Breakdown de IPI/frete/desconto | `C7_VALIPI`,`C7_VALFRE`,`C7_VLDESC` | `TO_INVENTORY` | já entram no `open_value` mas não expostos |
| Frete/impostos totais do pedido | agregação nova | `PLANNED` | exige contrato de header |
| Solicitante da SC de origem | SC1 via `C7_NUMSC` | `PLANNED` | cross-read já provado no produtor SC — reutilização depende de owner |
| Ocorrências/histórico de prazo | sem fonte provada | `PLANNED` | fontes `MT120*` (recebimento) investigáveis |
| NF de origem/devolução | `D1_NFORI`/`D1_SERIORI`/`D1_TES`/`D1_TIPO` | `TO_INVENTORY` | fontes: `DLP005.prw`, `IXMLSEF.prw`, `M116ACOL.prw` |

## Rastreabilidade SC → PC → Recebimento (comprovada)

| Ligação | Chave | Fonte | Cardinalidade |
|---|---|---|---|
| SC → Pedidos | `C7_NUMSC` = `C1_NUM`, `C7_ITEMSC` = `C1_ITEM` (por linha) | SC7 | 1 linha SC : N linhas pedido |
| PC → SC | `source_request_number`/`source_request_item` por item | SC7 | N itens : 1 SC cada |
| Pedido → NF | `D1_PEDIDO`+`D1_ITEMPC`+`D1_COD`+`D1_FORNECE`+`D1_LOJA`+`D1_FILIAL` (composta, inclui filial) | SD1 | 1 item pedido : N recebimentos |
| Rotas MFE | `/apps/supplies/purchase-requests/{branch}/{number}` e `/apps/supplies/purchase-orders/{branch}/{number}` **ambas existem** → links bidirecionais implementáveis | `pluginRoutes.ts` | — |

- Recebimentos parciais: provados (múltiplas linhas `receipts[]` por item).
- SC atendida por N pedidos: provada (`purchase_orders` agrupa por `(order_number,order_item)`).
- Pedido com N SCs: estrutural (vínculo é por item).
- ⚠️ `received_quantity` do pedido usa `C7_QUJE` (baixa na SC7) enquanto `receipts` somam `D1_QUANT` — divergências por reconciliação são possíveis; documentar em UX como "entregue (baixa)" vs "notas registradas".

## Endpoints BFF atuais

| Endpoint | Owner upstream | AuthZ | Parâmetros | Estados |
|---|---|---|---|---|
| `GET /purchase-requests/{branch}/{number}` | purchase-requests-api → api-delpi | `can_use_purchase_requests` + `@require_unit` | query forward (`date_from`,`date_to`,`cost_center[]`) | 200/401/403/404/5xx |
| `GET /purchase-orders/{branch}/{number}` | api-delpi | `can_use_operations` + `@require_unit` | nenhum | 200/401/403/404/422/5xx |

Rotas produtores relacionadas já existentes (não necessariamente expostas no BFF):
`/supplies/purchase-requests/open-coverage`, `/lines`, `/lines/export`, `/requesters`,
`/cost-centers`, `/approval-states`, `/recent-linked-orders`, `/recent-linked-receipts`.

## Fontes TOTVS consultadas (`docs/13-fontes-totvs-protheus/`)

- `02.Compras/` — 97 fontes; hits relevantes:
  `COMXPROC.prw`, `DLPMATR110.prw`, `IXMLSEF.prw`, `matr110_dlp.prx` (C7_OBS/COND/MOEDA),
  `DLP005.prw`, `M116ACOL.prw` (D1_NFORI/TES/TIPO),
  `MA110BUT.prw`, `MT110ROT.prw`, `NG400FI1.prw` (SC1/aprovação),
  `MT097GRV.prw`, `MT120BRW.prw`, `MT120FIM.prw`, `MT120LOK.prw` (recebimento SC7/SD1).
- `04. Estoque/` — não material para estas fichas (recebimentos são SD1/Compras).
- Achados de fonte **não provam** implantação/vigência — todos classificados `TO_INVENTORY`.
