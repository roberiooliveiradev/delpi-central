# Mapeamento API — Inspeções de Entrada

Base URL (browser, via gateway):

```text
/apps/api-delpi/inspecoes-entrada
```

**Permissões:** `inspecoes-entrada.view`, `inspecoes-entrada.view.filial-01`, `inspecoes-entrada.view.filial-02` ou `api-delpi.access`

**Header recomendado:** `X-Delpi-Caller-App: inspecoes-entrada`

**Envelope de resposta:**

```json
{
  "success": true,
  "message": "...",
  "data": { },
  "meta": {
    "operationId": "...",
    "entity": "...",
    "shape": "..."
  }
}
```

Documentação oficial: [api-delpi/docs/api/inspecoes-entrada.md](../../../api-delpi/docs/api/inspecoes-entrada.md).

---

## Endpoints consumidos pelo MFE

| Função no plugin | Método | Rota | Query params principais |
|---|---|---|---|
| `fetchInspecoesEntradaResumo` | GET | `/resumo` | `branch` |
| `fetchInspecoesEntradaPendentes` | GET | `/pendentes` | `branch`, `page`, `page_size` |
| `fetchInspecoesEntradaPendentesFornecedor` | GET | `/pendentes-fornecedor` | `branch` |
| `fetchInspecoesEntradaRejeitadasProduto` | GET | `/rejeitadas-produto` | `branch`, `limit` |
| `fetchInspecoesEntradaHistorico` | GET | `/historico` | `branch`, filtros, `page`, `page_size` |
| `fetchInspecoesEntradaHistoricoDetalhe` | GET | `/historico/detalhe` | `branch`, `inspection_id` |

---

## Endpoint disponível (não consumido no MFE v0.1)

| Função (futura) | Método | Rota | Observação |
|---|---|---|---|
| Rejeitadas por ensaiador | GET | `/rejeitadas-ensaiador` | API + testes prontos; painel previsto no roadmap |

---

## Exemplos de URL completas

```text
GET /apps/api-delpi/inspecoes-entrada/resumo?branch=01
GET /apps/api-delpi/inspecoes-entrada/pendentes?branch=02&page=1&page_size=50
GET /apps/api-delpi/inspecoes-entrada/historico?branch=01&result=REJEITADA&date_from=2026-01-01&page=1&page_size=20
GET /apps/api-delpi/inspecoes-entrada/historico/detalhe?branch=01&inspection_id=01%7C...
```

---

## Mapeamento view TOTVS → campo API (histórico)

| Coluna view | Campo API (`items[]`) |
|---|---|
| `Id_Inspecao` | `inspection_id` |
| `Data_Recebimento` / `Hora_Recebimento` | `received_date` / `received_time` |
| `Data_Laudo` / `Hora_Laudo` | `report_date` / `report_time` |
| `Nota_Fiscal` | `invoice_number` |
| `Nome_Fornecedor` | `supplier_name` |
| `Codigo_Produto` | `product_code` |
| `Descricao_Produto` (join SB1) | `product_description` |
| `Resultado_Resumo` | `result` |
| `Nome_Ensaiador` | `inspector_name` |
| `Qtde_Ensaios` / `Qtde_Ensaios_Reprovados` | `tests_count` / `failed_tests_count` |

---

## Implementação de referência (api-delpi)

| Peça | Caminho |
|---|---|
| Router | `api-delpi/app/interface/http/routes/inspecoes_entrada/inspecoes_entrada_router.py` |
| Composer | `api-delpi/app/composition/inspecoes_entrada_composer.py` |
| Repository | `api-delpi/app/infrastructure/persistence/totvs/inspecoes_entrada/` |
| DTOs | `api-delpi/app/application/dto/inspecoes_entrada/` |
| Contratos meta | `api-delpi/app/interface/http/route_contract_registry.py` |

Ao tipar o frontend, inspecionar DTOs Python acima — os tipos TS em `src/types/` espelham `data` após unwrap do envelope.
