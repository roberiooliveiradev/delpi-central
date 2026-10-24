# SC/PC Detail Enrichment — Roadmap de Implementação (proposta, não autorizada)

> Status: `DISCOVERY_COMPLETE` · `IMPLEMENTATION_NOT_AUTHORIZED` · `NO_CODE_CHANGE`
> Baseline: `f89e73376c` · Data editorial: 2026-10-24 · v2 reconciliada P0.R1
> Companheiros: `SC-PC-DETAIL-ENRICHMENT-P0.md`,
> `SC-PC-DETAIL-DATA-CONTRACT-MATRIX.md`, `SC-PC-DETAIL-UX-WIREFRAMES.md`.

Prefixo de fases: `EN.*`. **Readiness da Fase A: READY_FOR_PO** — todas as
etapas usam somente dados já entregues ao MFE; pendentes apenas decisões D1/D2.

## Matriz de decisões

| Decisão | Tema | Resultado esperado | Status |
|---|---|---|---|
| D1 | 404 do PC | **A:** copy neutra «não localizado entre os pedidos em aberto» (recomendada, zero contrato); **B:** endpoint de concluídos (futura) | **pronta para PO** — bloqueia EN.A6 |
| D2 | `approver_name`, `suggested_supplier`, `account_code` | aprovador: exibir junto ao badge; sugerido: exibir rotulado «Sugerido»; conta: fora da área principal | **pronta para PO** — bloqueia EN.A1–A3 |
| D3 | Header agregado do PC | contrato novo api-delpi | fora da Fase A (`PLANNED`) |
| D4 | Nome do comprador | lookup de identidade ou campo produtor | fora da Fase A (`TO_INVENTORY`) |
| D5 | Dados fiscais do fornecedor | sensibilidade + owner | fora da Fase A (`TO_INVENTORY`) |
| D6 | Próximo passo/dono da ação | owner canônico indefinido | fora da Fase A (`PLANNED`) |

## Fase A — Quick wins visuais (zero contrato novo)

### EN.A1 — Tipos da SC

| | |
|---|---|
| Owner | `plugins/supplies` |
| Dados comprovados | `header.purchase_orders[]`, `suppliers[]`, `first/last_order_date`, `first/last_receipt_date`, `has_overdue_order`, `max_days_overdue`, `cost_centers[].description`; linha `unit`, `request_required_date`, `ordered_quantity`, `request_open_quantity`, `approval{status,approver_name}`, `suggested_supplier`, `residual`, `purchase_orders[]` (com `receipts`, `buyer`, `derived{delivery_status,days_overdue,receipt_status}`); `timeline[]` |
| Dados excluídos | `header.requested/ordered/received_quantity` como KPI único (soma sem UM — P0.R1); `account_code` (depende de D2); `order_user_*` dos pedidos vinculados (uso não definido nesta fase) |
| Dependências | D2 (aprover/fornecedor sugerido) |
| RQ/AC | Todo campo declarado em `types.ts` corresponde 1:1 ao payload; typecheck + structural tests passam |
| Testes | positive: fixture com payload completo; sibling: linhas sem `purchase_orders`/`suggested_supplier`/`approver_name`; negative: campos nulos/ausentes → «—» |
| Stop | campo não presente no payload real → fora do tipo |

### EN.A2 — Hero da SC

| | |
|---|---|
| Owner | `plugins/supplies` |
| Dados comprovados | identidade atual + `cost_centers[].description`, `approval_summary.status` + `approval.approver_name` (por linha → agregar único do header/linhas), `has_overdue_order`/`max_days_overdue`, contagens derivadas de `purchase_orders[]`/`receipts` |
| Dados excluídos | totais de quantidade (P0.R1); primeiro/último recebimento como destaque (seção própria) |
| RQ/AC | hero exibe: filial, nº, solicitante+foto, abertura, badge aprovação (+nome), CCs c/ descrição, contadores Itens/Pedidos/Entradas, alerta de atraso; ausência → «—» |
| Testes | positive: aprovador presente; sibling: SC não aprovada (`unknown`); negative: SC sem pedidos → «sem atraso» |
| Stop | nenhum KPI de quantidade somada |

### EN.A3 — Itens da SC

| | |
|---|---|
| Owner | `plugins/supplies` |
| Dados comprovados | `unit`, `request_required_date`, `ordered_quantity`, `request_open_quantity`, `cost_center.description`, `suggested_supplier`, `residual`, expansão c/ `purchase_orders[]`+`receipts[]` do item |
| Dados excluídos | `account_code` (D2) |
| RQ/AC | colunas novas; cada quantidade exibida **com sua UM**; expansão mostra pedidos/recebimentos do item ou empty |
| Testes | positive: item com 2 pedidos parciais; sibling: item sem pedido → «Nenhum pedido vinculado»; negative: `unit`/`approver` ausentes |
| Stop | quantidade sem UM ao lado → não renderizar |

### EN.A4 — Pedidos vinculados + «Acompanhamento»

| | |
|---|---|
| Owner | `plugins/supplies` |
| Dados comprovados | `header.purchase_orders[]` (nº, item, fornecedor, datas issue/expected), linha `.purchase_orders[].receipts[]`, `timeline[]` (4 tipos derivados) |
| Dados excluídos | rótulo «Histórico»/auditoria; eventos de aprovação/prazo/cancelamento (não existem no contrato) |
| Dependências | — |
| RQ/AC | seção Pedidos vinculados por ordem cronológica; «Acompanhamento» via `SuppliesEventsSection`; `expected_delivery` como marco de previsão (visual distinto); hint documenta lacunas |
| Testes | positive: SC com pedidos+recebimentos; sibling: SC sem pedidos → empty + timeline só com criação; negative: datas ausentes |
| Stop | qualquer evento fora dos 4 tipos provados → não exibir |

### EN.A5 — Links SC ↔ PC

| | |
|---|---|
| Owner | `plugins/supplies` |
| Dados comprovados | rotas `/purchase-requests/{branch}/{number}` e `/purchase-orders/{branch}/{number}` existem; chaves `C7_NUMSC/C7_ITEMSC`, `source_request_*` |
| RQ/AC | links com chave composta `(filial, número)`; destino 403 → «Conteúdo não disponível para o seu perfil»; 404 → «registro não localizado»; `?from=` preserva retorno |
| Testes | positive: navegação ida e volta; sibling: PC com itens de SCs diferentes, SC com N PCs; negative: vínculo→403, vínculo→404, `source_request_*` vazio → «—» sem link, filial divergente |
| Stop | link que exija permissão nova ou rota inexistente → não criar |

### EN.A6 — Organização do PC

| | |
|---|---|
| Owner | `plugins/supplies` |
| Dados comprovados | campos já renderizados + link SC origem + badge «Em atraso» derivado de `delivery_status` + hierarquia de seções |
| Dados excluídos | header agregado (D3 — `PLANNED`), «dias de atraso» (campo não existe no contrato PC), nome do comprador (D4) |
| Dependências | **D1** (copy do 404) |
| RQ/AC | 404 → «Pedido não localizado entre os pedidos em aberto disponíveis para consulta.»; itens em cartões mobile; link SC origem com chave composta |
| Testes | positive: item com recebimentos parciais; sibling: PC sem SC origem; negative: 404 neutro (nunca «concluído»), destino SC→403 |
| Stop | qualquer indicador de header → bloqueia até contrato novo |

### EN.A7 — Help e conteúdo

| | |
|---|---|
| Owner | `plugins/supplies` |
| Escopo | `SP_HELP` por seção (itens, pedidos vinculados, recebimentos, acompanhamento — com disclaimer de eventos derivados), `purchaseRequestsColumnHelp`/`purchaseOrdersColumnHelp` novas colunas, Manual, FAQ |
| RQ/AC | `feature-help-sync` em cada etapa anterior; textos não afirmam dados ausentes |

## Fases B–D (fora desta autorização — propostas)

| Fase | Escopo | Gates |
|---|---|---|
| B — dados existentes nos produtores | header agregado PC (EN.B1), nome do comprador (EN.B2), `C7_UM` e simples provados (EN.B3) | D3, D4 + prova TOTVS em consulta real |
| C — rastreabilidade | campos fiscais aprovados, rótulos baixa-vs-NF, link PC→NF só se rota existir | D5 |
| D — gerencial | «próximo passo/dono» (owner indefinido), histórico auditável, alertas | D6 + fonte provada |

## Gates transversais (todas as fases)

- `feature-help-sync` obrigatório; AuthZ backend-first; filial = filtro.
- Sem writes ERP, jobs, migrations, manifest ou permission por filial.
- Deploy somente após autorização por fase (`local-first-deploy`) — esta P0
  não realiza deploy.
- Sem KPI de quantidade somada enquanto não existir agregação por UM no
  contrato (sem conversão no MFE — proibido).
- C2/C3 de Purchase Requests preservados: proposta render-only.

## Cobertura RQ → AC → fase

| Pergunta do usuário | Resposta hoje | Fase que resolve |
|---|---|---|
| Quem/quando/filial/CC/o quê/qtd/situação | provado/renderizado | — |
| Aprovada? | status provado; nome do aprovador provado não renderizado | A2 (D2) |
| Pedido vinculado? quanto comprado/recebido/pendente? | provado, **invisível** (por item c/ UM) | A3–A4 |
| Próximo passo/dono | **sem fonte** | D (D6) |
| PC: fornecedor/comprador/SC/qtds/preço/aberto/datas/atraso/NFs/parciais | provado | A6 |
| PC: comprador nome, condição pgto, moeda, obs | `TO_INVENTORY` | B2–B3, C1 |
| PC: valor total do pedido | `PLANNED` | B1 (D3) |


## Gate de decisão PO — D1/D2 aprovadas (2026-10-24)

**D1=APPROVED_OPTION_A:** mensagem neutra em 404 do PC, sem inferir conclusão nem construir endpoint histórico. **D2=APPROVED:** exibir na ficha SC (quando disponíveis/autorizados) `approval.approver_name`, `suggested_supplier` (rótulo «Fornecedor sugerido») e `account_code` (rótulo «Conta contábil», seção administrativa da ficha principal). A aprovação de D2 **substitui a recomendação anterior de deixar `account_code` fora da ficha principal**. A granularidade é por item quando assim estabelecida no produtor; evitar header fictício.

**EN.A1 escopo para autorização futura:** declarar e validar os DTOs SC atualmente entregues pelo BFF, inclusive campos D2, sem alterar UI, producer, BFF, segurança ou contratos de rede. Testar campos opcionais/nulos, identidades compostas e preservação de códigos. **EN.A1=READY_TO_AUTHORIZE, não autorizado automaticamente.** As etapas EN.A2–A7 seguem não autorizadas. D3–D6 permanecem fora da Fase A.

## EN.A1 executada (2026-10-24)

**EN.A1 = DONE.** `types.ts` da feature SC ampliado com todos os campos do
payload real (`PurchaseRequestDetailHeader/Line`, `SupplierRef`,
`ApprovalRef`, `PurchaseRequestLinkedOrder`, `PurchaseRequestReceipt`,
`PurchaseRequestTimelineEvent`); `account_code` declarado por item (string,
zeros à esquerda — conforme D2 aprovada); caveat semântico documentado nos
totais de quantidade. Novo `PurchaseRequestDetail.contract.test.ts` (9 testes)
+ 447/447 suíte MFE + typecheck + build. Registro completo:
`SC-PC-DETAIL-EN-A1-CONTRACT-TYPES.md`. **EN.A2 = READY_FOR_PO**
(pendente apenas autorização; dados tipados disponíveis).

## EN.A2 executada (2026-10-24)

**EN.A2 = DONE.** Hero da ficha SC reorganizado em 3 níveis: identificação
(unidade, nº, abertura, situação com badge), contexto (solicitante c/ foto,
CCs c/ descrição + `+N`, aprovação c/ aprovador granular — 1 nome ou
«N aprovadores», nunca promovido de linha) e indicadores seguros (itens
visíveis, `countLinkedOrders` por identidade `(filial, número)`, atraso por
`has_overdue_order`/`max_days_overdue`). Nenhum KPI de quantidade (guard no
structural test). `stageBadgeVariant`/`isKnownOverallStage` unificados em
`query.ts`. Help + Manual sincronizados; residual da fixture EN.A1 corrigido.
Registro: `SC-PC-DETAIL-EN-A2-SC-HERO.md`. **EN.A3 = READY_FOR_PO**.
