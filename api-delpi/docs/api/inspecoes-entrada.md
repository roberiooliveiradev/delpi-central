# Inspeções de Entrada — `/inspecoes-entrada`

Consultas operacionais de **inspeção de recebimento** (entrada de materiais), alimentadas pelo **TOTVS Protheus** (views dedicadas + tabelas QER).

**Permissão:** `inspecoes-entrada.view`, `inspecoes-entrada.view.filial-01`, `inspecoes-entrada.view.filial-02` ou `api-delpi.access`

**Validação por filial:** usuários com permissão apenas de uma filial recebem `403` ao consultar a outra (exceto superadmin ou `inspecoes-entrada.view`).

**Formato:** envelope `{ success, message, data, meta }` (Playbook 10).

Parâmetro comum:

| Parâmetro | Descrição |
|---|---|
| `branch` | Filial `01` ou `02` (obrigatório em todas as rotas) |

Plugin consumidor: `plugins/inspecoes-entrada` · Doc views: [ESPECIFICACAO-VIEW.md](../../../docs/12-roadmap-e-evolucao/inspecoes-entrada/ESPECIFICACAO-VIEW.md).

---

## Endpoints

| Método | Rota | `meta.shape` | Descrição |
|---|---|---|---|
| GET | `/inspecoes-entrada/resumo` | `scalar` | KPIs da filial |
| GET | `/inspecoes-entrada/pendentes` | `paged_list` | Inspeções aguardando laudo |
| GET | `/inspecoes-entrada/pendentes-fornecedor` | `list` | Ranking fornecedor × pendências |
| GET | `/inspecoes-entrada/rejeitadas-ensaiador` | `list` | Rejeições por ensaiador |
| GET | `/inspecoes-entrada/rejeitadas-produto` | `list` | Rejeições recentes por produto |
| GET | `/inspecoes-entrada/historico` | `paged_list` | Histórico laudado |
| GET | `/inspecoes-entrada/historico/detalhe` | `composite_analysis` | Cabeçalho + ensaios |

---

## GET `/inspecoes-entrada/resumo`

**Query:** `branch` (obrigatório)

**`meta.operationId`:** `get_inspecoes_entrada_resumo` · **`meta.entity`:** `inspecoes_entrada_resumo`

**Campos `data`:**

| Campo | Tipo | Descrição |
|---|---|---|
| `branch` | string | Filial |
| `pending_inspections` | int | Aguardando laudo |
| `inspected` | int | Total inspecionados |
| `approved_inspections` | int | Aprovados |
| `rejected_inspections` | int | Rejeitados |
| `approval_rate` | float | Taxa de aprovação (%) |
| `inspections_with_time` | int | Com tempo calculado |
| `average_time_hours` | float | Tempo médio (horas) |
| `average_time_days` | float | Tempo médio (dias) |

---

## GET `/inspecoes-entrada/pendentes`

**Query:**

| Parâmetro | Default | Descrição |
|---|---|---|
| `branch` | — | Obrigatório |
| `page` | 1 | Página |
| `page_size` | 50 | Máx. 200 |

**`meta.operationId`:** `get_inspecoes_entrada_pendentes`

**`data`:** `{ branch, items[], pagination }`

Item principal: `invoice_number`, `supplier_name`, `product_code`, `product_description`, `quantity`, `unit`, `inspection_status`, `received_date`, `received_time`.

---

## GET `/inspecoes-entrada/pendentes-fornecedor`

**Query:** `branch`

**`meta.operationId`:** `get_inspecoes_entrada_pendentes_fornecedor`

**`data`:** `{ branch, items[{ supplier_name, pending_count }], total_suppliers, total_pending }`

---

## GET `/inspecoes-entrada/rejeitadas-ensaiador`

**Query:** `branch`

**`meta.operationId`:** `get_inspecoes_entrada_rejeitadas_ensaiador`

**`data`:** `{ branch, items[{ inspector_registration, inspector_name, inspector_login, rejected_count }] }`

---

## GET `/inspecoes-entrada/rejeitadas-produto`

**Query:**

| Parâmetro | Default | Descrição |
|---|---|---|
| `branch` | — | Obrigatório |
| `limit` | 50 | Máx. 200 |

**`meta.operationId`:** `get_inspecoes_entrada_rejeitadas_produto`

**`data`:** `{ branch, items[], total }` — rejeições recentes (`result = REJEITADA`).

---

## GET `/inspecoes-entrada/historico`

**Query:**

| Parâmetro | Descrição |
|---|---|
| `branch` | Obrigatório |
| `page`, `page_size` | Paginação (máx. 200) |
| `result` | `APROVADA` ou `REJEITADA` |
| `date_from`, `date_to` | Filtro `Data_Laudo` (ISO date) |
| `supplier` | Parcial em nome fornecedor |
| `product_code` | Exato |
| `inspector` | Parcial em nome ensaiador |
| `invoice_number` | NF exata |
| `lot` | Lote exato |

**`meta.operationId`:** `get_inspecoes_entrada_historico`

**`data`:** `{ branch, items[], pagination, filters }`

Erros de validação: `422` (ex.: `result` inválido).

---

## GET `/inspecoes-entrada/historico/detalhe`

**Query:**

| Parâmetro | Descrição |
|---|---|
| `branch` | Obrigatório |
| `inspection_id` | Obrigatório (`Id_Inspecao` da view) |

**`meta.operationId`:** `get_inspecoes_entrada_historico_detalhe`

**`data`:**

```json
{
  "branch": "01",
  "inspection_id": "...",
  "summary": { },
  "tests": [ ],
  "totals": {
    "tests_count": 0,
    "approved_tests_count": 0,
    "failed_tests_count": 0
  }
}
```

**404:** `code: INSPECAO_NOT_FOUND` quando inspeção inexistente na filial.

Ensaios (`tests[]`): especificação, limites, `measured_value`, `measurement_source` (`QES`|`QEQ`), `result`, amostra, laboratório.

---

## Exemplos (gateway)

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: inspecoes-entrada" \
     "http://localhost/apps/api-delpi/inspecoes-entrada/resumo?branch=01" \
  | jq '.meta, .data'

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: inspecoes-entrada" \
     "http://localhost/apps/api-delpi/inspecoes-entrada/historico?branch=01&result=REJEITADA&page=1&page_size=10" \
  | jq '.data.pagination'
```

---

## Implementação

| Peça | Caminho |
|---|---|
| Router | `app/interface/http/routes/inspecoes_entrada/inspecoes_entrada_router.py` |
| Repository | `app/infrastructure/persistence/totvs/inspecoes_entrada/` |
| Use cases | `app/application/use_cases/inspecoes_entrada/` |
| Contratos | `app/interface/http/route_contract_registry.py` |
| Validação views | `scripts/validate_inspecoes_entrada_views.py` |

Testes: `tests/test_inspecoes_entrada_*`.
