# SC/PC Detail Enrichment — Roadmap de Implementação (proposta, não autorizada)

> Status: `DISCOVERY_COMPLETE` · `IMPLEMENTATION_NOT_AUTHORIZED` · `NO_CODE_CHANGE`
> Baseline: `f89e73376c` · Sequência proposta — nenhuma etapa inicia sem
> autorização explícita. Companheiros: `SC-PC-DETAIL-ENRICHMENT-P0.md`,
> `SC-PC-DETAIL-DATA-CONTRACT-MATRIX.md`, `SC-PC-DETAIL-UX-WIREFRAMES.md`.

Prefixo de fases: `EN.*` (série própria do enriquecimento SC/PC).

## Fase A — Quick wins visuais (zero contrato novo)

Somente campos `PROVEN_IN_BFF`; nenhum backend alterado.

| Etapa | Escopo | Owner | RQ/AC |
|---|---|---|---|
| EN.A1 | SC: estender `types.ts` (`header.purchase_orders/suppliers/totais/datas/has_overdue_order/max_days_overdue`; linha `unit/request_required_date/ordered_quantity/request_open_quantity/approval.approver_name/suggested_supplier/residual/purchase_orders`) | `plugins/supplies` | RQ: todos os campos mapeados batem no payload real. AC: typecheck + structural tests atualizados |
| EN.A2 | SC: hero enriquecido — KPIs solicitado/em pedidos/recebido, badge aprovação, CCs c/ descrição | `plugins/supplies` | AC: wireframe SC §desktop; campos ausentes → «—» |
| EN.A3 | SC: tabela de itens + colunas UM, necessidade, qtd. pedida, saldo; expansão por item com pedidos/recebimentos | `plugins/supplies` | AC: empty/partial por item; receipts ≠ delivered rotulados |
| EN.A4 | SC: seção «Pedidos vinculados» + `SuppliesEventsSection` para `timeline` | `plugins/supplies` | AC: empty «Nenhum pedido vinculado…»; timeline ordenada |
| EN.A5 | Links `SuppliesEntityLink`: linha SC→PC (`/purchase-orders/{branch}/{number}`), PC item→SC (`/purchase-requests/{branch}/{number}`) | `plugins/supplies` | AC: deep link + `?from=` retorno; F5/back-forward |
| EN.A6 | PC: hierarquia de seções, alerta «Em atraso — pior item» derivado de itens existentes, copy 404 «não localizado ou já totalmente entregue» (gate **D1**) | `plugins/supplies` | AC: copy aprovada pelo PO |
| EN.A7 | Help: `SP_HELP` novas seções, `purchaseRequestsColumnHelp`/`purchaseOrdersColumnHelp`, Manual, FAQ | `plugins/supplies` | `feature-help-sync` obrigatório |

- **Dependências:** D1, D2 (approver/fornecedor sugerido na UI).
- **Arquivos candidatos:** `PurchaseRequestDetailPage.tsx`,
  `PurchaseOrderDetailPage.tsx`, `types.ts`, `content.ts`,
  `*ColumnHelp.ts`, `helpTooltips.ts`, `userManualContent.ts`,
  `PurchaseRequests.structural.test.ts`, `PurchaseOrders.structural.test.ts`.
- **Critério de parada:** qualquer campo que não existir de fato no payload em
  produção → retira da etapa, nunca simular no MFE.
- **Testes:** render por seção, empty/partial/erro, links, keyboard, mobile,
  regressão das fichas + suíte MFE completa.

## Fase B — Enriquecimento com dados existentes nos produtores

| Etapa | Escopo | Owner | Gate |
|---|---|---|---|
| EN.B1 | Header agregado PC (`order_totals{ordered,received,open}`, `overall_delivery_status`, `supplier` dedup) — **contrato novo** em `api-delpi` + pass-through BFF | `api-delpi` → `supplies-api` → MFE | **D3** — evolução aditiva (`contract-evolution-backward-compatibility`) |
| EN.B2 | Nome do comprador — `C7_COMPRA` → resolução (campo `buyer_name` no produtor **ou** reuse do identity service) | `api-delpi` ou Core identity | **D4** |
| EN.B3 | `C7_UM` e demais campos simples provados em consulta real | `api-delpi` | prova em PROTHEUS antes de contrato |

- **Dependências:** Fase A publicada; decisões D3/D4.
- **Critério de parada:** campos TOTVS sem prova de vigência ficam fora.
- **Relação C1/C2/C3:** nenhuma mudança de ownership do produtor SC; apenas
  leituras aditivas na `api-delpi`.

## Fase C — Rastreabilidade completa

| Etapa | Escopo | Owner | Gate |
|---|---|---|---|
| EN.C1 | Campos fiscais aprovados (CNPJ/endereço fornecedor, `D1_NFORI/TES/TIPO`) — só se **D5** aprovado | `api-delpi` | **D5** sensibilidade |
| EN.C2 | Rótulos canônicos «baixa do pedido» vs «notas registradas»; reconciliação documentada | `plugins/supplies` + PO | copy aprovada |
| EN.C3 | Link PC→documento de recebimento — **somente** se rota MFE/contrato da NF existir (hoje não existe → sem link) | `plugins/supplies` | prova de rota |

## Fase D — Acompanhamento gerencial

| Etapa | Escopo | Owner | Gate |
|---|---|---|---|
| EN.D1 | «Próximo passo»/«dono da ação» — requer owner de orquestração (campo explícito, nunca inferência de stage) | a definir (**D6**) | **D6** |
| EN.D2 | Histórico auditável de alterações (prazo, cancelamento) | owner do evento | fonte provada |
| EN.D3 | Alertas gerenciais (dias de atraso já provados → destaque/notificação) | `plugins/supplies` | regra de negócio definida |

## Gates transversais (todas as fases)

- `feature-help-sync`: toda etapa user-facing sincroniza Help + Manual + FAQ.
- AuthZ: backend-first; filial permanece filtro — jamais permission por filial.
- Sem writes ERP, sem jobs novos, sem migrations, sem manifest novo.
- Deploy: `local-first-deploy` (pull + `up-prod-sequential.sh`) somente após
  autorização por fase — esta P0 **não** realizou deploy.
- Evidência: toda etapa fecha com testes + build + smoke autenticado quando
  exigido (E11 demonstrou que smoke autenticado pode permanecer INCONCLUSIVE —
  registrar como residual, não bloquear código).

## Cobertura RQ → AC → fase

| Pergunta do usuário | Resposta hoje | Fase que resolve |
|---|---|---|
| Quem/quando/filial/CC/o quê/qtd/situação | provado/renderizado | — |
| Aprovada? | parcial (status; nome do aprovador não renderizado) | A2 |
| Pedido vinculado? quanto comprado/recebido/pendente? | provado, **invisível** | A2–A4 |
| Próximo passo/dono | **sem fonte** | D1/D6 |
| PC: fornecedor/comprador/SC/qtds/preço/aberto/datas/atraso/NFs/parciais | provado | A6 (hierarquia) |
| PC: comprador nome, condição pgto, moeda, obs | `TO_INVENTORY` | B2–B3, C1 |
| PC: valor total do pedido / header agregado | `PLANNED` | B1 (D3) |
