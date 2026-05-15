# 03 — Vendas (ordens de venda)

Prefixo: `/sales`

**Permissão:** `api-delpi.access`

## GET /sales/

Lista ordens de venda com filtros opcionais.

| Query | Tipo | Descrição |
|---|---|---|
| `date_start` | string | Data inicial do período. |
| `date_end` | string | Data final. |
| `page` | int | Número da página. |
| `page_size` | int | Registros por página. |

**Exemplo:**

```http
GET /apps/api-delpi/sales/?date_start=20260101&date_end=20260131&page=1&page_size=50
```

**Resposta `200`:**

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": {
    "items": [],
    "page": 1,
    "page_size": 50,
    "total": 0,
    "total_pages": 0
  }
}
```

A estrutura exata de cada item em `data` segue o DTO `ListSaleOrderResponse` retornado pelo use case de listagem.
