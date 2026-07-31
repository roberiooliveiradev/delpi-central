# Financeiro — Despesas por Centro de Custo

Consultas analíticas de **despesas por centro de custo** (lançamentos de entrada / SD1), alimentadas pelo **TOTVS Protheus**.

**Base:** `/apps/api-delpi/financeiro/despesas-centro-custo`

**Permissão:** `financeiro-centro-custo.access`, `financeiro-centro-custo.view` ou `api-delpi.access` (`FINANCEIRO_CENTRO_CUSTO_READ_PERMISSIONS`).

**Formato:** envelope `{ success, message, data, meta }` (Playbook 10).

**Qualidade de rotas:** [padrao-qualidade-rotas.md](./padrao-qualidade-rotas.md) — Wave 4 (estratégia A: `pagination` com `total_items`, alias `total`, `is_complete`).

Plugin consumidor: `plugins/financeiro-centro-custo`.

---

## Endpoints

| Método | Rota | `operationId` | `meta.shape` |
|---|---|---|---|
| GET | `/filtros` | `get_financeiro_despesas_centro_custo_filtros` | (filtros) |
| GET | `/resumo` | `get_financeiro_despesas_centro_custo_resumo` | scalar / KPI |
| GET | `/serie` | `get_financeiro_despesas_centro_custo_serie` | série |
| GET | `/ranking-centros` | `get_financeiro_despesas_centro_custo_ranking_centros` | list |
| GET | `/ranking-fornecedores` | `get_financeiro_despesas_centro_custo_ranking_fornecedores` | list |
| GET | `/lancamentos` | `get_financeiro_despesas_centro_custo_lancamentos` | `paged_list` |

---

## Parâmetros (query — inglês)

| Param | Onde | Notas |
|---|---|---|
| `start_date` / `end_date` | todas | Período obrigatório (ISO `YYYY-MM-DD`) |
| `branch` | opcional | Filial |
| `cost_center` | opcional | Código do centro de custo |
| `supplier_code` / `supplier_store` | resumo/série/lancamentos | Fornecedor |
| `search` | lançamentos | Busca textual |
| `page` / `page_size` | lançamentos | Default 1 / 50 |
| `sort_by` / `sort_dir` | lançamentos | Whitelist no DTO |
| `limit` | rankings | Top N |

---

## Body / `data` (nota)

Campos de resposta em **snake_case PT** (legado do módulo) — ex.: `centro_custo_codigo`, `valor_total`, `data_emissao`.  
Query params já estão em **EN**. Alinhamento full EN do body fica para estratégia B/C ([padrao-qualidade-rotas.md](./padrao-qualidade-rotas.md)).

### Paginação (`/lancamentos`)

```json
{
  "page": 1,
  "page_size": 50,
  "total_items": 120,
  "total": 120,
  "total_pages": 3,
  "has_next": true,
  "has_previous": false,
  "is_complete": false
}
```

`total` é alias canônico de `total_items`. `is_complete` = última página (ou lista vazia).

---

## Referências

- Índice: [06-modulos-departamentais.md](./06-modulos-departamentais.md)
- Padrão de qualidade: [padrao-qualidade-rotas.md](./padrao-qualidade-rotas.md)
- OpenAPI / TV: [openapi-bilingue-catalogo-canonico.md](./openapi-bilingue-catalogo-canonico.md)
