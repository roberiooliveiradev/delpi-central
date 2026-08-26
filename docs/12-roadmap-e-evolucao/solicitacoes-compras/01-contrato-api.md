# Painel de Solicitações de Compras — Contrato técnico da API (Fase 0.2)

> **Status:** contrato congelado para implementação (ago/2026)  
> **Produto:** Minha DELPI — plugin `purchase-requests` (Painel de Solicitações de Compras)  
> **Evidência TOTVS:** [Fase 0.1 — probe](../solicitacoes-compras/) · scripts `api-delpi/scripts/sql/purchase_requests_totvs_probe*.py`  
> **Naming:** paths, `operationId`, enums e permissões em **English**; labels ao usuário em **pt-BR**  
> **Escopo desta fase:** contrato apenas — **sem** código produtivo, migrations, MFE ou manifesto

---

## 1. Objetivo

Transformar as evidências comprovadas da Fase 0.1 em um **contrato técnico formal** suficiente para implementar, depois, a API do painel sem rediscutir grão, joins, autorização ou shape dos DTOs.

Este documento define:

- domínio e grão canônico;
- DTOs, enums e status derivados;
- endpoints públicos e administrativos (conceituais);
- regras de visibilidade por centro de custo (CC) e filial;
- estratégia de vínculo usuário Minha DELPI ↔ Protheus;
- envelope HTTP, erros e paginação alinhados à API DELPI (Playbook 10);
- lacunas explicitamente **não resolvidas** nesta fase.

---

## 2. Evidências confirmadas no TOTVS

### 2.1 SC1010 — Solicitação de compra

| Fato | Evidência |
|------|-----------|
| Grão = `C1_FILIAL` + `C1_NUM` + `C1_ITEM` | SX3010 + probe |
| Solicitante estável = `C1_USER` → `SYS_USR.USR_ID` | 100% fill; join comprovado |
| `C1_SOLICIT` = rótulo legível | Não usar como chave |
| CC = `C1_CC` por **item** | Probe + `CTT010` |
| `C1_CONTA` = conta contábil | Distinto de CC |
| Saldo SC = `C1_QUANT - C1_QUJE` | Probe cenários A–C |
| `C1_APROV`: `L` / `R` / `B` / vazio | Distribuição comprovada |
| `C1_RESIDUO = 'S'` ≠ cancelamento | Probe resíduo vs delete |
| `D_E_L_E_T_ = '*'` = exclusão lógica | Probe cenário K |

### 2.2 SC7010 — Pedido de compra

| Fato | Evidência |
|------|-----------|
| Join canônico SC→PC | `C7_FILIAL` + `C7_NUMSC` + `C7_ITEMSC` |
| `C1_PEDIDO = C7_NUM` auxiliar | Insuficiente sozinho |
| `C1_ITEM ≠ C7_ITEM` | Probe cardinalidade |
| 1 SC → N PCs; 1 PC → N SCs; 1 item SC → N linhas PC | Probe cenários I + âncora 164708 |
| `C7_QUJE` = qtd recebida no pedido | Match 97,3% com SD1 + `D1_ITEMPC` |
| `C7_COMPRA` = comprador formal (sparse) | Fill rate fil 01 baixo |
| `C7_USER` = usuário Protheus do pedido | 100% fill; **≠ comprador formal** |
| `C7_APROV` = grupo de alçada | Não é status operacional |

### 2.3 SD1010 — Documento de entrada

| Fato | Evidência |
|------|-----------|
| Join PC→SD1 | `D1_PEDIDO`, `D1_FORNECE`, `D1_LOJA`, `D1_COD`, **`D1_ITEMPC`** |
| `D1_DTDIGIT` = lançamento/entrada | Probe datas âncora |
| Mesmo PC → até 26 NFs | Probe cenário G |
| Número de PC reutilizado entre filiais | Âncora 041446 (fil 01 legado + fil 02 atual) |

### 2.4 Catálogo CC

~99,98% dos `C1_CC` (fil 01) existem em `vw_fin_despesas_centro_custo.centro_custo_codigo`. Descrição via `CTT010` (`CTT_CUSTO`, `CTT_DESC01`).

---

## 3. Limites e lacunas conhecidas

| Lacuna | Impacto no contrato |
|--------|---------------------|
| Workflow de aprovação (quem/quando/histórico) | Enum `approval_status` parcial; sem eventos de timeline |
| Semântica de `C1_APROV` vazio no legado | Mapeado para `unknown`, **nunca** `waiting_approval` |
| Comprador formal (`C7_COMPRA`) esparso | `buyer` nullable |
| Setor organizacional formal na SC | Sem campo; reservado para extensão futura |
| Cancelamento de negócio vs resíduo | `residual` explícito; sem status `cancelled` |
| Mapping automático Minha DELPI ↔ Protheus | Estratégia documentada; estados `unmapped` / `ambiguous` |
| Threshold `due_soon` | Apenas `days_until_due` / `days_overdue` por enquanto |
| Divergências `C7_QUJE` vs `SUM(D1_QUANT)` (~2,7%) | Campo derivado `receipt_quantity_mismatch` opcional no detalhe |

---

## 4. Princípios do domínio

1. **Grão canônico = item da SC** (`purchase_request_line`). Toda autorização e agregação parte daí.
2. **Autorização antes da agregação** — nunca agregar cabeçalho da SC e depois filtrar itens.
3. **Fail closed** — usuário com `.access` sem escopo CC e sem `.view-all` vê **zero** registros.
4. **Filial obrigatória** em todo join e toda rota que identifique documento TOTVS.
5. **Duas camadas de autorização independentes:**
   - **RBAC Minha DELPI** (Core API / JWT): pode acessar o módulo?
   - **Escopo de dados do domínio** (postgres-plugins): quais CCs dentro das filiais permitidas?
6. **Não inventar campos TOTVS** — somente os comprovados na Fase 0.1.
7. **Comprador ≠ usuário do pedido** — nunca preencher `buyer` com `C7_USER` silenciosamente.
8. **Resíduo ≠ cancelamento** — não rotular como cancelado.
9. **Exclusão lógica** (`D_E_L_E_T_ = '*'`) fora da listagem operacional padrão.
10. **Performance:** implementação futura em batch/CTE — proibido N+1 SC→PC→SD1 na listagem.

### Arquitetura de serviços (decisão de fronteira)

Alinhado a `mfe-own-api-no-direct-api-delpi.mdc` e `maintenance/PLAYBOOK-01-fronteiras-api-delpi.md`:

```text
MFE purchase-requests
        │
        ▼ HTTP + JWT
purchase-requests-api          ← contrato PÚBLICO deste documento
  │ escopo CC, mapping user, agregações, timeline
  │ postgres-plugins (escopos, mappings)
  │
  └── gateway HTTP ──▶ api-delpi
                          └── SQL TOTVS puro (SC1/SC7/SD1)
                              sem regra de CC do módulo
```

- **Envelope público:** `{ success, message, data, meta }` — mesmo Playbook 10 que `api_delpi_success` / `ResponseMetaBuilder`.
- **Persistência de domínio:** schema `purchase_requests` no `postgres-plugins` (futuro).
- **TOTVS:** somente via `api-delpi`; rotas internas documentadas na §19.2.

---

## 5. Grão canônico

### 5.1 Entidade primária — `purchase_request_line`

Chave natural:

```text
branch          (C1_FILIAL)
request_number  (C1_NUM)
request_item    (C1_ITEM)
```

Representa uma linha ativa de SC1010 (`D_E_L_E_T_ = ' '` na listagem padrão).

### 5.2 Entidades relacionadas

| Entidade | Grão | Chave |
|----------|------|-------|
| `purchase_order_line` | item PC | `branch` + `order_number` + `order_item` |
| `receipt_line` | item NF | `branch` + `invoice_number` + `invoice_series` + `invoice_item` (+ fornecedor) |
| `purchase_request` (agregado) | cabeçalho visível | `branch` + `request_number` — **derivado após** filtro de linhas autorizadas |

### 5.3 Cardinalidade suportada

```text
purchase_request_line  1 ──▶ N  purchase_order_line   (via C7_NUMSC/C7_ITEMSC)
purchase_order_line    1 ──▶ N  receipt_line          (via join SD1 + D1_ITEMPC)
purchase_request       1 ──▶ N  purchase_request_line (visíveis)
```

---

## 6. Modelo de autorização

### 6.1 Camada 1 — RBAC (Core API)

Permissões propostas (ajustadas para convenção EN dos manifestos — cf. `travel-expenses.*`):

| Código | Significado |
|--------|-------------|
| `purchase-requests.access` | Entrar no módulo. **Não** bypassa escopo CC. |
| `purchase-requests.admin` | CRUD de escopos de visibilidade e mappings de usuário. |
| `purchase-requests.view-all` | Bypass do filtro CC **dentro** das filiais que o usuário já pode ver. |
| `purchase-requests.export` | Exportações futuras (mesmo universo autorizado). |

Filial continua governada pelo padrão existente (`BranchAccessGate` + permissões `purchase-requests.unit.filial-01` / `filial-02` ou equivalente global — **mesmo mecanismo** de `travel-expenses.unit.*`, a definir no manifesto).

**Não** criar segundo sistema de acesso a filial.

### 6.2 Camada 2 — Escopo por CC (domínio)

Aplicada **por linha** (`purchase_request_line`), usando `C1_CC`.

Pipeline obrigatório (listagem, detalhe, facets, indicadores, export):

```text
1. Resolver filiais permitidas (RBAC filial)
2. Resolver allowed_cost_centers (união escopos ativos OU all-CC se view-all)
3. Consultar TOTVS no grão linha
4. Filtrar linhas: C1_CC ∈ allowed_cost_centers (por filial)
5. Aplicar filtros do usuário (interseção)
6. Agregar cabeçalhos / KPIs somente sobre linhas restantes
```

### 6.3 Fail closed

| Condição | Resultado |
|----------|-----------|
| Tem `.access`, sem `.view-all`, sem CC em escopo | **0 registros** (200 + lista vazia) |
| Filtro explícito `cost_center` ∉ allowed | **403 Forbidden** |
| Filial não autorizada (RBAC) | **403 Forbidden** (padrão `BranchAccessGate`) |
| SC existe, todos itens fora do escopo | **404 Not Found** (anti-enumeração) |

### 6.4 Proteção contra vazamento por agregação

Quando o usuário vê **parte** de uma SC:

- Totais, contagens, fornecedores, pedidos e datas refletem **somente itens autorizados**.
- **Proibido:** `hidden_items_count`, listar CCs não autorizados, inferir existência de itens ocultos.
- Nome preferido: `visible_items_count` (ou `items_count` documentado como “já filtrado por autorização”).

---

## 7. Escopos por centro de custo

### 7.1 Modelo conceitual (postgres-plugins)

Schema proposto: **`purchase_requests`** (convenção `migrations/plugins/{slug}/`).

| Tabela | Colunas principais |
|--------|---------------------|
| `purchase_requests.visibility_scopes` | `id` (UUID), `name`, `description`, `active`, `created_at`, `updated_at` |
| `purchase_requests.visibility_scope_users` | `scope_id`, `user_id` (Core API UUID) |
| `purchase_requests.visibility_scope_cost_centers` | `scope_id`, `branch`, `cost_center_code` |

Índices futuros: `(user_id)`, `(branch, cost_center_code)`, `(scope_id)`.

### 7.2 União de escopos

```text
allowed_cost_centers(branch) =
  ⋃ { cost_center_code
      | scope.active
      | user ∈ scope.users
      | (branch, cost_center_code) ∈ scope.cost_centers
    }
```

Duplicatas eliminadas. Usuário em múltiplos escopos recebe **união**.

### 7.3 `.view-all`

Usuário com `purchase-requests.view-all`:

```text
allowed_cost_centers(branch) = { todos C1_CC distintos observados na filial }
```

Ainda respeita RBAC de filial. **Não** ignora filial.

### 7.4 Filtro solicitado vs autorizado

```text
effective_cost_centers =
  requested_cost_centers ∩ allowed_cost_centers   (se filtro explícito)
  allowed_cost_centers                          (se sem filtro)
```

---

## 8. Vínculo Minha DELPI ↔ Protheus

### 8.1 Tabela conceitual

| Tabela | Colunas |
|--------|---------|
| `purchase_requests.user_protheus_mappings` | `user_id` (PK, Core API), `protheus_user_id` (`USR_ID`), `protheus_user_code` (`USR_CODIGO`), `mapping_status` (`mapped` \| `unmapped` \| `ambiguous`), `mapping_source` (`manual` \| `email_match` \| `login_match`), `verified` (bool), `created_at`, `updated_at` |

**Chave principal plataforma:** `user_id` (Core API). **Nunca** nome como chave.

### 8.2 Estratégia de associação automática (futura)

| Tentativa | Regra | Resultado |
|-----------|-------|-----------|
| 1 | Email exato (Minha DELPI ↔ `SYS_USR.USR_EMAIL`), ambos não vazios | Candidato `mapped` se único |
| 2 | Login/username normalizado (Minha DELPI ↔ `USR_CODIGO`) | Candidato se único |
| 0 matches | — | `unmapped` |
| >1 match | — | `ambiguous` — exige confirmação admin |

**Proibido:** match por `USR_NOME`, fuzzy name, ou “aproximação”.

### 8.3 Filtro `mine=true`

```text
JWT user_id → user_protheus_mappings → protheus_user_id → filtro C1_USER
```

| Situação | Comportamento |
|----------|---------------|
| `mapping_status = mapped` e `verified = true` | Filtra `C1_USER = protheus_user_id` |
| `unmapped` | **422** `PROTHEUS_USER_MAPPING_REQUIRED` (domínio) — não adivinhar |
| `ambiguous` | **422** `PROTHEUS_USER_MAPPING_AMBIGUOUS` |

Facets de solicitante listam **somente** solicitantes presentes no universo já autorizado por CC.

---

## 9. DTO PurchaseRequestLine

Grão canônico exposto no detalhe (e base da listagem quando expandida).

| Campo | Tipo | Nullable | Origem TOTVS / regra |
|-------|------|----------|----------------------|
| `branch` | `string` | não | `C1_FILIAL` |
| `request_number` | `string` | não | `C1_NUM` |
| `request_item` | `string` | não | `C1_ITEM` |
| `product_code` | `string` | não | `C1_PRODUTO` |
| `product_description` | `string` | sim | `C1_DESCRI` ou join `SB1.B1_DESC` |
| `unit` | `string` | sim | `C1_UM` |
| `requested_quantity` | `number` | não | `C1_QUANT` |
| `ordered_quantity` | `number` | não | `C1_QUJE` (fonte canônica SC) |
| `request_open_quantity` | `number` | não | `max(C1_QUANT - C1_QUJE, 0)` |
| `request_issue_date` | `string` (ISO date) | não | `C1_EMISSAO` |
| `request_required_date` | `string` (ISO date) | sim | `C1_DATPRF` |
| `requester.protheus_user_id` | `string` | não | `C1_USER` |
| `requester.code` | `string` | sim | `SYS_USR.USR_CODIGO` |
| `requester.name` | `string` | sim | `C1_SOLICIT` ou `USR_NOME` |
| `cost_center.code` | `string` | sim | `C1_CC` |
| `cost_center.description` | `string` | sim | `CTT010.CTT_DESC01` |
| `account_code` | `string` | sim | `C1_CONTA` (contábil) |
| `approval.status` | `ApprovalStatus` | não | ver §13 |
| `approval.approver_name` | `string` | sim | `C1_NOMAPRO` (parcial) |
| `residual` | `boolean` | não | `C1_RESIDUO = 'S'` |
| `suggested_supplier.code` | `string` | sim | `C1_FORNECE` |
| `suggested_supplier.store` | `string` | sim | `C1_LOJA` |
| `suggested_supplier.name` | `string` | sim | join SA2 |
| `purchase_orders` | `PurchaseOrderLine[]` | não | join SC7 via §4 |
| `derived.order_status` | `OrderStatus` | não | §14 |
| `derived.receipt_status` | `ReceiptStatus` | não | §15 |
| `derived.overall_stage` | `OverallStage` | não | §14 |

`department` / `area`: **reservados** (`null`, não preenchidos) — extensão futura.

---

## 10. DTO PurchaseRequest

Visão agregada **pós-autorização** (somente linhas visíveis).

| Campo | Tipo | Regra |
|-------|------|-------|
| `branch` | `string` | |
| `request_number` | `string` | |
| `issue_date` | ISO date | `min(C1_EMISSAO)` das linhas visíveis |
| `requester` | `RequesterSummary` | do primeiro item ou consenso se único solicitante |
| `visible_items_count` | `integer` | count linhas visíveis |
| `cost_centers` | `{ code, description }[]` | distinct das linhas visíveis |
| `approval_summary` | `{ status, counts? }` | pior caso ou dominante — documentar na impl. |
| `overall_stage` | `OverallStage` | derivado das linhas visíveis (regra conservadora: estágio “menos avançado” ou pior — definir na impl.) |
| `purchase_orders` | `PurchaseOrderSummary[]` | PCs alcançados por linhas visíveis |
| `suppliers` | `SupplierSummary[]` | distinct fornecedores das linhas visíveis |
| `first_order_date` | ISO date \| null | min `C7_EMISSAO` |
| `last_order_date` | ISO date \| null | max `C7_EMISSAO` |
| `first_receipt_date` | ISO date \| null | min `D1_DTDIGIT` |
| `last_receipt_date` | ISO date \| null | max `D1_DTDIGIT` |
| `requested_quantity` | `number` | sum linhas visíveis |
| `ordered_quantity` | `number` | sum `C1_QUJE` visíveis |
| `received_quantity` | `number` | sum recebimentos das linhas visíveis |
| `has_overdue_order` | `boolean` | algum PC visível overdue |
| `max_days_overdue` | `integer` \| null | max entre PCs visíveis |

**Listagem:** retorna array de `PurchaseRequest` (resumo), não todas as linhas/NFs.

---

## 11. DTO PurchaseOrderLine

| Campo | Tipo | Nullable | Origem |
|-------|------|----------|--------|
| `branch` | `string` | não | `C7_FILIAL` |
| `order_number` | `string` | não | `C7_NUM` |
| `order_item` | `string` | não | `C7_ITEM` |
| `source_request_number` | `string` | sim | `C7_NUMSC` |
| `source_request_item` | `string` | sim | `C7_ITEMSC` |
| `product_code` | `string` | não | `C7_PRODUTO` |
| `product_description` | `string` | sim | `C7_DESCR` / SB1 |
| `ordered_quantity` | `number` | não | `C7_QUANT` |
| `received_quantity` | `number` | não | `C7_QUJE` |
| `open_quantity` | `number` | não | `max(C7_QUANT - C7_QUJE, 0)` |
| `issue_date` | ISO date | sim | `C7_EMISSAO` |
| `expected_delivery_date` | ISO date | sim | `C7_DATPRF` |
| `supplier.code` / `store` / `name` | | | `C7_FORNECE`, `C7_LOJA`, SA2 |
| `buyer.code` | `string` | **sim** | `C7_COMPRA` — **null se vazio** |
| `buyer.name` | `string` | sim | cadastro comprador (futuro) ou null |
| `order_user.protheus_user_id` | `string` | sim | `C7_USER` |
| `order_user.code` | `string` | sim | `USR_CODIGO` |
| `order_user.name` | `string` | sim | `USR_NOME` |
| `residual` | `boolean` | não | `C7_RESIDUO = 'S'` |
| `receipts` | `ReceiptLine[]` | não | SD1 join §5 |
| `derived.delivery_status` | `DeliveryStatus` | não | §35 |
| `derived.days_until_due` | `integer` \| null | sim | calc |
| `derived.days_overdue` | `integer` \| null | sim | calc |
| `derived.receipt_status` | `ReceiptStatus` | não | §15 |

**Regra explícita:** `buyer` **nunca** recebe valor de `order_user`.

---

## 12. DTO ReceiptLine

| Campo | Tipo | Origem |
|-------|------|--------|
| `branch` | `string` | `D1_FILIAL` |
| `invoice_number` | `string` | `D1_DOC` |
| `invoice_series` | `string` | `D1_SERIE` |
| `invoice_item` | `string` | `D1_ITEM` |
| `purchase_order_number` | `string` | `D1_PEDIDO` |
| `purchase_order_item` | `string` | **`D1_ITEMPC`** |
| `product_code` | `string` | `D1_COD` |
| `supplier_code` | `string` | `D1_FORNECE` |
| `supplier_store` | `string` | `D1_LOJA` |
| `quantity` | `number` | `D1_QUANT` |
| `unit_price` | `number` | `D1_VUNIT` |
| `total_value` | `number` | `D1_TOTAL` |
| `invoice_issue_date` | ISO date | `D1_EMISSAO` |
| `entry_date` | ISO date | `D1_DTDIGIT` |

---

## 13. Aprovação

### 13.1 Enum `ApprovalStatus` (dimensão independente)

```text
approved   ← C1_APROV = 'L'
rejected   ← C1_APROV = 'R'
blocked    ← C1_APROV = 'B'
unknown    ← vazio, qualquer outro, ou legado não classificado
```

**Proibido:** `waiting_approval` até comprovação de semântica.

### 13.2 Extensibilidade futura (sem breaking change)

Reservar em `approval` (nullable hoje):

```text
submitted_at
approved_at
rejected_at
approver_protheus_user_id
approval_group_code    ← futuro C1_XGRPAPR
workflow_instance_id
```

### 13.3 Impacto no `overall_stage`

Aprovação **desconhecida não bloqueia** automaticamente avanço material (§29).

---

## 14. Etapas operacionais

### 14.1 Enum `OverallStage`

| Valor | Regra determinística (prioridade top-down na derivação por linha) |
|-------|---------------------------------------------------------------------|
| `deleted` | `D_E_L_E_T_ = '*'` — excluído da listagem padrão |
| `residual_closed` | `C1_RESIDUO = 'S'` (SC) ou linha PC residual encerrando fluxo |
| `completed` | `C1_QUJE >= C1_QUANT` e recebimento PC associado integral (`C7_QUJE >= C7_QUANT` quando existir PC) |
| `partially_received` | existe PC com `0 < C7_QUJE < C7_QUANT` para a linha |
| `awaiting_receipt` | `C1_QUJE >= C1_QUANT` (ou PC emitido) e `C7_QUJE = 0` |
| `ordered` | `C1_QUJE >= C1_QUANT` e ainda sem recebimento — alias operacional de awaiting_receipt no nível SC; usar `awaiting_receipt` como canônico |
| `partially_ordered` | `0 < C1_QUJE < C1_QUANT` |
| `awaiting_order` | SC ativa, não residual, `C1_QUANT > 0`, `C1_QUJE = 0`, sem linha SC7 vinculada (`C7_NUMSC`+`C7_ITEMSC`) |

**Fonte quantitativa SC:** `C1_QUJE`. SC7 detalha e valida.

**Agregação cabeçalho:** estágio = função conservadora sobre linhas visíveis (ex.: se qualquer linha `awaiting_order` → cabeçalho `awaiting_order`; se misto → `partially_ordered` / pior estágio — fechar na implementação com tabela de precedência).

### 14.2 Enum `OrderStatus` (linha SC)

```text
not_ordered      ← C1_QUJE = 0 e sem SC7
partially_ordered ← 0 < C1_QUJE < C1_QUANT
fully_ordered    ← C1_QUJE >= C1_QUANT
```

---

## 15. Recebimento

### 15.1 Enum `ReceiptStatus`

| Valor | Condição (nível PC; propagar para SC) |
|-------|----------------------------------------|
| `not_ordered` | sem PC |
| `awaiting_receipt` | PC existe, `C7_QUJE = 0` |
| `partially_received` | `0 < C7_QUJE < C7_QUANT` |
| `received` | `C7_QUJE >= C7_QUANT` |

### 15.2 Quantidades

- **Canônica recebida (pedido):** `C7_QUJE`
- **Detalhamento:** `SUM(D1_QUANT)` com join §5 incluindo `D1_ITEMPC`
- **Divergência:** se `abs(C7_QUJE - sum_d1) > ε`, expor `receipt_quantity_mismatch: true` no detalhe (opcional)

### 15.3 Parcialidades

Uma linha SC pode gerar **várias** linhas PC (âncora 164708). Recebimentos somam por **cada** `purchase_order_line`.

---

## 16. Resíduo e exclusão

| Sinal | Campo | Apresentação |
|-------|-------|--------------|
| Resíduo SC | `C1_RESIDUO = 'S'` | `residual: true`; stage pode ser `residual_closed` |
| Resíduo PC | `C7_RESIDUO = 'S'` | idem no PC |
| Exclusão lógica | `D_E_L_E_T_ = '*'` | **omitir** da listagem operacional |
| Cancelamento formal | — | **não modelado** |

---

## 17. Datas e lead times

### 17.1 Semântica (confirmada)

| Campo TOTVS | Papel |
|-------------|-------|
| `C1_EMISSAO` | Abertura SC |
| `C1_DATPRF` | Necessidade original SC |
| `C7_EMISSAO` | Emissão PC |
| `C7_DATPRF` | Previsão PC |
| `D1_EMISSAO` | Emissão fiscal NF |
| `D1_DTDIGIT` | Entrada/lançamento TOTVS |

### 17.2 Derivados (calculados, não persistidos)

| Campo | Cálculo |
|-------|---------|
| `first_receipt_date` | `MIN(D1_DTDIGIT)` por linha/PC visível |
| `last_receipt_date` | `MAX(D1_DTDIGIT)` |
| `completed_receipt_date` | data do evento em que acumulado recebido ≥ `C7_QUANT` (simulação cronológica por `D1_DTDIGIT`) |

### 17.3 Lead times (campos derivados futuros)

| Métrica | Início | Fim |
|---------|--------|-----|
| `request_to_order_days` | `C1_EMISSAO` | `MIN(C7_EMISSAO)` dos PCs da linha |
| `order_to_first_receipt_days` | `C7_EMISSAO` | `first_receipt_date` |
| `order_to_complete_receipt_days` | `C7_EMISSAO` | `completed_receipt_date` |
| `request_to_complete_days` | `C1_EMISSAO` | `completed_receipt_date` ou último marco |
| `days_open` | `C1_EMISSAO` | hoje ou data conclusão |

---

## 18. Timeline

Eventos **derivados** (não persistidos). Tipos:

```text
request_created          ← C1_EMISSAO
purchase_order_created   ← C7_EMISSAO (+ ref PC)
expected_delivery        ← C7_DATPRF
partial_receipt          ← D1_DTDIGIT quando parcial
receipt                  ← D1_DTDIGIT
completed                ← completed_receipt_date
```

Shape:

```json
{
  "type": "receipt",
  "date": "2026-04-30",
  "label": "Entrada NF",
  "reference": { "invoice_number": "…", "order_number": "…" },
  "metadata": {}
}
```

**Não incluir** `approval_date` até mapeamento confiável. Aprovação = status atual em `approval.status`.

---

## 19. Endpoints públicos do domínio

### 19.1 API pública — `purchase-requests-api`

Gateway: `/apps/purchase-requests-api`  
Prefixo interno: `/purchase-requests`

| Método | Path | operationId | Shape |
|--------|------|-------------|-------|
| GET | `/purchase-requests` | `list_purchase_requests` | `paged_list` |
| GET | `/purchase-requests/{branch}/{request_number}` | `get_purchase_request` | `composite_analysis` |
| GET | `/purchase-requests/filters` | `get_purchase_request_filters` | `scalar` |
| GET | `/purchase-requests/indicators` | `get_purchase_request_indicators` | `composite_analysis` |

**Admin** (prefixo `/purchase-requests/admin`):

| Método | Path | operationId |
|--------|------|-------------|
| GET/POST | `/visibility-scopes` | `list/create_purchase_request_visibility_scopes` |
| GET/PUT/DELETE | `/visibility-scopes/{id}` | CRUD scope |
| PUT | `/visibility-scopes/{id}/users` | replace users |
| PUT | `/visibility-scopes/{id}/cost-centers` | replace CCs |
| GET/PUT | `/user-mappings` | list/update mappings |

Permissões admin: `purchase-requests.admin`.

### 19.2 API interna TOTVS — `api-delpi` (gateway do BFF)

Prefixo existente: `/supplies/purchase-requests`

Rotas **internas** (consumo HTTP pelo BFF, não pelo MFE):

| Método | Path | operationId | Notas |
|--------|------|-------------|-------|
| GET | `/supplies/purchase-requests/lines` | `list_supplies_purchase_request_lines` | batch SC1+SC7+SD1; **sem** filtro CC |
| GET | `/supplies/purchase-requests/lines/{branch}/{request_number}` | `get_supplies_purchase_request_lines` | detalhe TOTVS puro |

A rota legada `GET .../open-coverage` permanece para estoque de segurança (MP); **não** é o painel.

---

## 20. Endpoint de listagem

`GET /purchase-requests`

**Resposta:** `{ items: PurchaseRequest[], page, page_size, total, total_pages }` dentro de `data`.

**Universo:** solicitações com ≥1 linha autorizada após pipeline §6.

**Não incluir:** timeline completa, todas NFs, linhas de PC no nível item (somente resumo).

**Query obrigatória:** `branch` (ou política multi-filial explícita futura — MVP: uma filial por request, padrão DELPI).

---

## 21. Endpoint de detalhe

`GET /purchase-requests/{branch}/{request_number}`

Path escolhido por alinhamento a rotas com filial explícita (cf. módulos multi-filial DELPI).

**Resposta `data`:**

```text
header: PurchaseRequest
lines: PurchaseRequestLine[]   (somente autorizadas)
timeline: TimelineEvent[]
```

Se nenhuma linha autorizada → **404** (mesmo que SC exista no TOTVS).

---

## 22. Endpoint de filtros/facets

`GET /purchase-requests/filters`

Retorna opções **dentro do universo autorizado** (mesma pipeline, período padrão aplicado):

```json
{
  "requesters": [{ "protheus_user_id", "code", "name" }],
  "cost_centers": [{ "code", "description" }],
  "suppliers": [{ "code", "store", "name" }],
  "approval_statuses": ["approved", "…"],
  "overall_stages": ["…"],
  "receipt_statuses": ["…"],
  "delivery_statuses": ["…"]
}
```

Decisão: **endpoint dedicado** (padrão similar a módulos com facets; evita payloads pesados na listagem).

---

## 23. Endpoint de indicadores

`GET /purchase-requests/indicators`

Mesmos filtros da listagem + pipeline de autorização idêntico.

Campos propostos em `data.summary`:

```text
total_open, opened_in_period, completed_in_period,
awaiting_order, awaiting_receipt, partially_received, overdue,
on_time_percentage,
average_request_to_order, average_order_to_receipt, average_total_lead_time
```

Shape: `composite_analysis`. KPI **nunca** inclui linhas que a listagem omitiria.

---

## 24. Endpoints administrativos

Escopos e mappings (§19.1 admin).

- **PUT replace** para listas de users/CCs (padrão commercial-api `replace_seller_customers`).
- Soft-delete de scope: `active = false`.
- Audit trail: fase futura; reservar `updated_at`.

---

## 25. Filtros

| Parâmetro | Tipo | Notas |
|-----------|------|-------|
| `branch` | string | obrigatório MVP; gate filial |
| `date_from` / `date_to` | ISO date | aplicados a **`C1_EMISSAO`** |
| `request_number` | string | |
| `requester_user_id` | UUID | Core API — via mapping |
| `requester_code` | string | `USR_CODIGO` |
| `cost_center` | string | interseção §7.4; explícito fora escopo → 403 |
| `product_code` | string | |
| `supplier_code` | string | |
| `order_number` | string | |
| `approval_status` | enum | |
| `overall_stage` | enum | |
| `receipt_status` | enum | |
| `delivery_status` | enum | |
| `has_overdue_order` | boolean | |
| `buyer` | string | **documentar:** limitado por `C7_COMPRA` sparse |
| `mine` | boolean | §8.3 |

**Não misturar** período SC com `C7_EMISSAO` / `D1_DTDIGIT` neste contrato inicial.

---

## 26. Paginação e ordenação

Padrão DELPI (`ResponseMetaBuilder.pagination_from_data`):

```json
"data": {
  "items": [],
  "page": 1,
  "page_size": 50,
  "total": 1234,
  "total_pages": 25
}
```

| Parâmetro | Default | Max |
|-----------|---------|-----|
| `page` | 1 | — |
| `page_size` | 50 | 200 |

**Ordenação default:** `request_issue_date DESC`, `request_number DESC` (mapeia `C1_EMISSAO`, `C1_NUM`).

**Sort permitido:** `request_issue_date`, `request_number`, `request_required_date`, `overall_stage`, `has_overdue_order` — whitelist na implementação.

### Política de período

Precedente: `pedidos-venda-abertos` usa **90 dias** quando período omitido.

**Decisão:** sem `date_from`/`date_to` → últimos **90 dias** em `C1_EMISSAO`.

Justificativa: volume ~142k SC/filial; painel operacional de fila recente; alinhado a módulos transacionais DELPI.

---

## 27. Regras de autorização por endpoint

| Endpoint | RBAC | Escopo CC | Filial | Observação |
|----------|------|-----------|--------|------------|
| `list_purchase_requests` | `.access` | sim | sim | fail closed |
| `get_purchase_request` | `.access` | sim | sim | 404 se zero linhas visíveis |
| `get_purchase_request_filters` | `.access` | sim | sim | facets autorizados |
| `get_purchase_request_indicators` | `.access` | sim | sim | idem listagem |
| Admin scopes/mappings | `.admin` | — | — | sem bypass filial TOTVS |
| Export futuro | `.export` | sim | sim | mesmo universo |

`.view-all`: bypass CC apenas. `.admin` **não** implica `.view-all` automaticamente.

---

## 28. Respostas e envelopes

### 28.1 Sucesso

```json
{
  "success": true,
  "message": "…",
  "data": { },
  "meta": {
    "dataVersion": "…",
    "operationId": "list_purchase_requests",
    "entity": "purchase_request",
    "shape": "paged_list",
    "pagination": { "page": 1, "page_size": 50, "total": 100, "total_pages": 2 }
  }
}
```

Implementação BFF: espelhar `api_delpi_success` + `route_contract_registry` entries.

### 28.2 Registro contrato

| operationId | entity | shape |
|-------------|--------|-------|
| `list_purchase_requests` | `purchase_request` | `paged_list` |
| `get_purchase_request` | `purchase_request` | `composite_analysis` |
| `get_purchase_request_filters` | `purchase_request_filters` | `scalar` |
| `get_purchase_request_indicators` | `purchase_request_indicators` | `composite_analysis` |

---

## 29. Erros

Padrão existente: `error_response(message, status_code=…)` / `{ success: false, message, … }`.

| Situação | HTTP | Código domínio (proposta) |
|----------|------|---------------------------|
| Sem `.access` | 403 | `FORBIDDEN` |
| Filial não autorizada | 403 | `BRANCH_FORBIDDEN` |
| CC explícito fora escopo | 403 | `COST_CENTER_FORBIDDEN` |
| `mine=true` sem mapping | 422 | `PROTHEUS_USER_MAPPING_REQUIRED` |
| Mapping ambíguo | 422 | `PROTHEUS_USER_MAPPING_AMBIGUOUS` |
| SC inexistente ou sem linhas visíveis | **404** | `PURCHASE_REQUEST_NOT_FOUND` |
| Período inválido | 400 | `INVALID_PERIOD` |
| Filtro enum inválido | 400 | `INVALID_FILTER` |
| TOTVS indisponível | 503 | `TOTVS_UNAVAILABLE` |

### 29.1 Anti-enumeração

SC existente com todos itens fora do escopo → **404**, não 403 com mensagem reveladora.

---

## 30. Performance

Requisitos para implementação futura:

1. **Uma ou poucas queries** batch por página (CTE: SC1 filtrada → SC7 → SD1 agregado).
2. Filtro pushdown: filial + período + CC autorizados **antes** de join pesado.
3. Paginação no backend — nunca materializar SC completa em memória.
4. Índices TOTVS: responsabilidade DBA; contrato **não** exige DDL no TOTVS.
5. Cache opcional por chave `(branch, period, allowed_cc_hash)` — TTL a definir na impl.
6. Detalhe: carregar timeline/receipts só no GET detalhe, não na listagem.

---

## 31. Exemplos JSON

### 31.1 Listagem

```json
{
  "success": true,
  "message": "Purchase requests loaded successfully.",
  "data": {
    "items": [
      {
        "branch": "02",
        "request_number": "164708",
        "issue_date": "2026-04-30",
        "requester": {
          "protheus_user_id": "000234",
          "code": "YAGO.ROCHA",
          "name": "YAGO.ROCHA"
        },
        "visible_items_count": 1,
        "cost_centers": [{ "code": "0413", "description": "INSUMOS DE PRODUÇÃO" }],
        "approval_summary": { "status": "approved" },
        "overall_stage": "completed",
        "requested_quantity": 300000,
        "ordered_quantity": 300000,
        "received_quantity": 476000,
        "has_overdue_order": false,
        "first_receipt_date": "2026-04-30",
        "last_receipt_date": "2026-04-30"
      }
    ],
    "page": 1,
    "page_size": 50,
    "total": 1,
    "total_pages": 1
  },
  "meta": {
    "operationId": "list_purchase_requests",
    "entity": "purchase_request",
    "shape": "paged_list",
    "pagination": { "page": 1, "page_size": 50, "total": 1, "total_pages": 1 }
  }
}
```

### 31.2 Linha no detalhe (trecho)

```json
{
  "branch": "02",
  "request_number": "164708",
  "request_item": "0001",
  "product_code": "10080001",
  "requested_quantity": 300000,
  "ordered_quantity": 300000,
  "request_open_quantity": 0,
  "approval": { "status": "approved", "approver_name": null },
  "residual": false,
  "purchase_orders": [
    {
      "order_number": "041446",
      "order_item": "0001",
      "ordered_quantity": 294000,
      "received_quantity": 294000,
      "buyer": null,
      "order_user": { "protheus_user_id": "000234", "code": "YAGO.ROCHA", "name": "…" },
      "derived": { "receipt_status": "received", "delivery_status": "received" }
    }
  ],
  "derived": {
    "overall_stage": "completed",
    "receipt_status": "received",
    "order_status": "fully_ordered"
  }
}
```

---

## 32. Decisões fechadas

- ✓ Grão = **item da SC** (`branch` + `request_number` + `request_item`)
- ✓ **`C1_USER`** identifica solicitante; **`C1_SOLICIT`** é rótulo
- ✓ **`C1_CC`** identifica centro de custo **por item**
- ✓ SC→PC usa **`C7_NUMSC` + `C7_ITEMSC` + filial**
- ✓ PC→SD1 usa **`D1_ITEMPC`**
- ✓ Autorização de dados **antes** da agregação
- ✓ Usuário sem escopo CC → **zero registros** (fail closed)
- ✓ **`C1_RESIDUO`** não significa cancelamento
- ✓ **`C7_USER`** não significa comprador formal
- ✓ **`D1_DTDIGIT`** representa entrada no TOTVS
- ✓ **Filial** participa obrigatoriamente de todos os joins
- ✓ Permissões em **English:** `purchase-requests.*`
- ✓ Arquitetura **purchase-requests-api** (BFF) + **api-delpi** (TOTVS puro)
- ✓ Período default listagem: **90 dias** em `C1_EMISSAO`
- ✓ CC explícito não autorizado → **403**; SC sem linhas visíveis → **404**
- ✓ **`ApprovalStatus.unknown`** para vazio/legado — sem `waiting_approval`

---

## 33. Decisões ainda pendentes

- ? Workflow detalhado de aprovação (datas, aprovadores, pendências)
- ? Significado operacional de **`C1_APROV` vazio** no legado
- ? Resolução de **`C7_COMPRA`** quando vazio (cadastro comprador vs null permanente)
- ? Setor organizacional formal além de CC/`USR_DEPTO`
- ? Regra definitiva de **cancelamento** de negócio
- ? Fluxo operacional de confirmação do **mapping** Minha DELPI ↔ Protheus
- ? Threshold de **“próximo do vencimento”** (`due_soon`)
- ? Precedência exata ao agregar **`overall_stage`** no cabeçalho com linhas heterogêneas
- ? Permissões granulares de filial (`purchase-requests.unit.filial-*`) — espelhar travel-expenses

---

## 34. Critérios de aceite da futura API

1. Nenhum campo TOTVS fora do probe.
2. Joins idênticos aos §4–§5.
3. CC filtrado **por item** antes de agregar.
4. Zero vazamento de itens/CC ocultos em totais ou facets.
5. Cardinalidade 1:N SC↔PC↔SD1 suportada nos DTOs.
6. `buyer` nullable; `order_user` separado.
7. `ApprovalStatus` sem `waiting_approval` automático.
8. `mine=true` exige mapping — sem guess por nome.
9. Listagem, detalhe, filters e indicators compartilham pipeline de autorização.
10. Envelope Playbook 10 + `operationId` registrado.
11. Período default 90d; paginação backend.
12. Implementação sem N+1 na listagem.
13. Exclusões lógicas omitidas da listagem padrão.
14. MFE consome **somente** `purchase-requests-api`.

---

## 35. Próxima fase recomendada

**Fase 1 — Fundação backend (sem MFE):**

1. Migration `purchase_requests` no postgres-plugins (escopos + mappings).
2. Pacote `purchase-requests-api` com auth, pipeline de escopo CC, gateway api-delpi.
3. Rotas TOTVS batch em api-delpi (`list_supplies_purchase_request_lines`).
4. Testes de contrato + regressão de autorização (fail closed, 404, 403 CC).
5. OpenAPI gerado a partir deste documento.

**Não iniciar MFE** antes dos testes de autorização por CC estarem verdes.

---

## Apêndice A — Enum `DeliveryStatus`

| Valor | Regra |
|-------|-------|
| `not_applicable` | sem PC ou já recebido integral |
| `on_time` | `open_quantity > 0` e `expected_delivery_date >= today` |
| `due_soon` | reservado — **não calcular** até config SLA |
| `overdue` | `expected_delivery_date < today` e `open_quantity > 0` |
| `received` | `open_quantity = 0` e `received_quantity > 0` |

Campos numéricos sempre expostos: `days_until_due`, `days_overdue`.

---

## Apêndice B — Referências internas

| Artefato | Caminho |
|----------|---------|
| Probe Fase 0.1 | `api-delpi/scripts/sql/purchase_requests_totvs_probe.py` |
| Rota legada SC abertas | `api-delpi/.../purchase_requests_router.py` |
| Envelope HTTP | `api-delpi/app/interface/http/route_response_helpers.py` |
| postgres-plugins | `docs/07-api-delpi/banco-postgres-plugins.md` |
| Fronteiras BFF | `docs/12-roadmap-e-evolucao/maintenance/PLAYBOOK-01-fronteiras-api-delpi.md` |
| Padrão permissões | `plugins/travel-expenses/travel-expenses.manifest.json` |
