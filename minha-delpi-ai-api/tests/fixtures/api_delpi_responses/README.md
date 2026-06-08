# Fixtures — respostas api-delpi (baseline Fase 0)

Envelope HTTP **atual** (sem `meta` no root):

```json
{ "success": true, "message": "...", "data": { } }
```

**Códigos de produto:** fictícios, mas com **prefixos reais do ERP** (não usar códigos de itens reais da empresa).

| Prefixo | Tipo | Exemplo na fixture |
|---------|------|-------------------|
| `9026xxxx` | PA (produto acabado) | `90269001`, `90269002` |
| `502xxxxx` | PI (intermediário) | `50219001` |
| `1001xxxx`–`1021xxxx` | MP (matéria-prima) | `10019001` |

## Uso nos testes

```python
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture

envelope = load_api_delpi_fixture("product_stock_90269001.json")
data = envelope["data"]
```

## Arquivos

| Arquivo | Rota | `meta.shape` (futuro) |
|---------|------|------------------------|
| `product_search.json` | `/products/search` | `paged_list` |
| `product_detail_90269001.json` | `/products/{code}` | `product_snapshot` |
| `product_summary_90269001.json` | `/products/{code}/summary` | `product_snapshot` |
| `product_stock_90269001.json` | `/products/{code}/stock` | `paged_list` |
| `product_structure_90269001.json` | `/products/{code}/structure` | `hierarchy` |
| `product_analyser_90269001.json` | `/products/{code}/analyser` | `composite_analysis` |
| `product_factory_status_90269002.json` | `/products/{code}/factory-status` | `composite_analysis` |
| `supplies_cpv.json` | `/supplies/cpv` | `scalar` |

Relacionado: [`api-delpi/docs/roadmaps/fase-0-inventario-contrato-respostas.md`](../../../../api-delpi/docs/roadmaps/fase-0-inventario-contrato-respostas.md).
