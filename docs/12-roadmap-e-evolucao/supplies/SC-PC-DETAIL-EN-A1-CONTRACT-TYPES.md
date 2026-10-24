# EN.A1 — SC Detail: Tipagem e Validação de Contrato

> Status: `DONE` · `NO_BACKEND_CHANGE` · `NO_VISUAL_CHANGE` · `NO_DEPLOY`
> Baseline: `dc9d701112` (com D1/D2 aprovadas pelo PO) · Data: 2026-10-24
> Owner: `plugins/supplies` · Fatia: Fase A / EN.A1 do roadmap
> `SC-PC-DETAIL-IMPLEMENTATION-ROADMAP.md`

## 1. Escopo executado

Declaração tipada completa do payload `GET /purchase-requests/{branch}/{number}`
já entregue pelo BFF — sem alteração de contrato de rede, regras de domínio,
backend, layout ou navegação. EN.A2–A7 **não** iniciadas.

## 2. DTOs comprovados (prova em código)

| Camada | Evidência |
|---|---|
| api-delpi (SQL SC1/SC7/SD1) | `purchase_request_lines_sql.py:305-332` (linhas SC1), `:505-545` (pedidos SC7), `:572-585` (recebimentos SD1) |
| purchase-requests-api (agregação) | `purchase_request_aggregation_service.py` `_aggregate_header`/`_enrich_line`/`_enrich_order`/`_build_timeline` |
| supplies-api (BFF) | `purchase_requests_routes.py` — passthrough + `enrich_payload` (só injeta identidade do solicitante) |
| MFE | `plugins/supplies/src/features/purchase-requests/types.ts` |

## 3. Campos adicionados ao `types.ts`

**Header (`PurchaseRequestDetailHeader`):** `purchase_orders[]`, `suppliers[]`,
`first_order_date`, `last_order_date`, `first_receipt_date`,
`last_receipt_date`, `requested_quantity`, `ordered_quantity`,
`received_quantity`, `has_overdue_order`, `max_days_overdue`.

**Linha (`PurchaseRequestDetailLine`):** `unit`, `request_required_date`,
`ordered_quantity`, `request_open_quantity`, `request_issue_date`, `requester`,
`cost_center`, `account_code`, `approval{status,approver_name}`,
`suggested_supplier`, `residual`, `purchase_orders[]`, `derived` ampliado
(`order_status`, `receipt_status`).

**Novos subtipos nomeados:** `SupplierRef`, `ApprovalRef`,
`PurchaseRequestReceipt`, `PurchaseRequestLinkedOrder`,
`PurchaseRequestTimelineEvent`, `PurchaseRequestDetailHeader`,
`PurchaseRequestDetailLine`.

## 4. Semântica e disciplina de dados

- **Quantidades:** `header.requested/ordered/received_quantity` declarados
  **com caveat técnico explícito** — soma sem agrupar por UM e sobre linhas
  autorizadas; proibido exibir como KPI único (P0.R1). Nenhuma conversão criada.
- **Conta contábil (D2 aprovada):** `lines[].account_code` string por item —
  preserva zeros à esquerda, sem agregação, sem default de outro item, sem
  confundir com centro de custo, ausência ≠ `0`.
- **Timeline:** tipada como eventos derivados (`request_created`,
  `purchase_order_created`, `expected_delivery` — marco planejado, `receipt`);
  não é trilha de auditoria.
- **`delivery_status` dos pedidos vinculados:** vocabulário do produtor
  (`received`/`not_applicable`/`overdue`/`on_time`) — distinto do contrato PC
  (`late`/`on_time`/`no_date`); documentado no tipo.
- **Opcionais:** todos os novos campos opcionais (`?`/`| null`) — fichas
  existentes e payloads parciais seguem válidos; nenhuma validação nova
  endurecida, nenhuma biblioteca adicionada (padrão da feature: `httpGet<T>`).

## 5. Segurança e escopo

Nenhuma permissão nova; `supplies.access` e escopo CC do produtor inalterados;
filial permanece filtro; nenhum campo obtido por consulta adicional — os dados
declarados já estavam no recurso que o usuário autorizado acessa.

## 6. Testes

Novo `PurchaseRequestDetail.contract.test.ts` (9 testes): fixture fiel ao
payload real (2 linhas, UMs heterogêneas MT/UN, 2 pedidos implícitos,
recebimento parcial, timeline completa), conta com zeros à esquerda, aprovador
por item, fornecedor sugerido presente/ausente, marco planejado vs. evento,
payload mínimo legítimo.

**Resultados:** 447/447 testes MFE · typecheck `tsc --noEmit` PASS ·
`vite build` PASS (chunk-size warning pré-existente) · lint dos arquivos
alterados limpo · `git diff --check` limpo.

## 7. Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `plugins/supplies/src/features/purchase-requests/types.ts` | tipos ampliados + subtipos + comentários semânticos |
| `plugins/supplies/src/features/purchase-requests/PurchaseRequestDetail.contract.test.ts` | **novo** — fixture e contrato |
| `docs/12-roadmap-e-evolucao/supplies/SC-PC-DETAIL-EN-A1-CONTRACT-TYPES.md` | **novo** — este registro |

## 8. Limitações conhecidas

- Tipos são contrato em tempo de compilação; não há validação runtime
  (consistente com o padrão atual do MFE — introduzi-la exigiria decisão
  arquitetural separada).
- `header.*_quantity` existe no contrato mas permanece **não renderizável**
  como total único até existir agregação por UM no produtor.
- `buyer` nos pedidos vinculados é código (`buyer_code`); `order_user_*`
  existe no payload mas sem uso definido nesta fase.

## 9. Readiness EN.A2

**READY** — hero da SC tem todos os dados tipados que precisa (contadores,
aprovação+aprovador, CCs com descrição, alerta de atraso). Bloqueio restante:
nenhum técnico; apenas decisões de apresentação (EN.A2 usa contadores, nunca
soma de quantidades).

**COMMIT_SHA:** `ver abaixo no relatório de execução`
