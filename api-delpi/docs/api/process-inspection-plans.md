# Process inspection plans — cadastro (QP6) vs OPs abertas

Consultas de **planos de inspeção de processo** (como inspecionar o produto — tabelas `QP6010`/`QP7010`/`QP8010`), correlacionados a **OPs abertas** (`SC2010`).

**Não confundir** com [`inspecoes-processo.md`](./inspecoes-processo.md) (`/inspecoes-processo`), que cobre **inspeções em linha** (execução QIP / QPR / QPK).

**Permissão:** `inspecoes-processo.view`, `inspecoes-processo.view.filial-01`, `inspecoes-processo.view.filial-02` ou `api-delpi.access`

**Validação por filial:** mesmo gate de inspeções de processo. `branch=all` (ou omitir) exige permissão consolidada e **não** aplica filtro SQL de filial nas rotas de lacunas.

**Formato:** envelope `{ success, message, data, meta }` (Playbook 10). Paths e `operationId` em **inglês**.

---

## Endpoints

| Método | Rota | `meta.shape` | Descrição |
|--------|------|--------------|-----------|
| GET | `/process-inspection-plans/summary` | `scalar` | KPIs + distribuição com/sem plano |
| GET | `/process-inspection-plans/orders-without-plan` | `paged_list` | OPs abertas sem QP6 |
| GET | `/process-inspection-plans/products-without-plan` | `paged_list` | Produtos distintos sem QP6 com OP aberta |
| GET | `/process-inspection-plans/products` | `paged_list` | Produtos **com** plano (revisão ativa) |
| GET | `/process-inspection-plans/products/{code}` | `composite_analysis` | Detalhe QP6+QP7+QP8 |

### Semântica SQL

- **Escopo de produto:** apenas **produto acabado** — `SB1010.B1_TIPO = 'PA'`.
- **OP aberta:** `SC2010` com `D_E_L_E_T_ = ''` e `C2_DATRF` vazio (join PA).
- **Tem plano:** existe linha em `QP6010` para o `C2_PRODUTO` (`QP6_PRODUT`).
- **OBS:** `C2_YOBSQUA`.
- Filial: `C2_FILIAL` quando `branch` ∈ {`01`,`02`}.
- Detalhe por produto reutiliza `ProductInspectionRepository` (`MAX(QP6_REVI)` só neste módulo de cadastro — não alterar auditoria QPK); só retorna se o código for PA com QP6.

---

## GET `/process-inspection-plans/summary`

**Query:** `branch` opcional (`all` \| `01` \| `02`)

**`meta.operationId`:** `get_process_inspection_plans_summary` · **`meta.entity`:** `process_inspection_plans_summary`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `branch` | string | Escopo |
| `products_without_plan` | int | Produtos distintos sem plano com OP aberta |
| `orders_without_plan` | int | OPs abertas sem plano |
| `total_open_orders` | int | Total de OPs abertas |
| `orders_with_plan` | int | OPs abertas com plano |
| `registered_pct` | float | % de OPs com plano |
| `distribution` | array | `{ status, label, count, pct }` — `with_plan` / `without_plan` |

---

## GET `/process-inspection-plans/orders-without-plan`

**Query:** `branch`, `page` (default 1), `page_size` (default 50, máx. 200)

**`meta.operationId`:** `get_process_inspection_plans_orders_without_plan`

Item: `branch`, `product_code`, `product_description`, `production_order`, `observation` + `pagination` (`is_complete`).

---

## GET `/process-inspection-plans/products-without-plan`

**Query:** `branch`, `page`, `page_size`

**`meta.operationId`:** `get_process_inspection_plans_products_without_plan`

Item: `product_code`, `product_description`, `open_orders_count`.

---

## GET `/process-inspection-plans/products`

**Query:** `page`, `page_size` (cadastro QP6 é global por produto — sem `branch`)

**`meta.operationId`:** `get_process_inspection_plans_products`

Item: `product_code`, `product_description`, `revision`, `description`, `inspection_type`, `created_at`, `start_date`.

---

## GET `/process-inspection-plans/products/{code}`

**Query:** `include_bom` (bool, default `false`)

**`meta.operationId`:** `get_process_inspection_plans_product`

Retorna nós de inspeção (header QP6 + ensaios QP7/QP8). Sem plano → **404**.
