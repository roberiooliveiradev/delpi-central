# Estoque Suprimentos — modo híbrido (`stock_method`)

**Data:** jun/2026  
**Relacionado:** [estoque-supplies-matr460-resumo-jun2026.md](./estoque-supplies-matr460-resumo-jun2026.md)

## Problema

Com período histórico **sem** fechamento SB9 na `end_date`:

- **Kardex** (`estimated`) subestima vs. MATR460 (ex.: ~R$ 281k vs. ~R$ 3,6M filial 01).
- **SB2 atual** aproxima **EM ESTOQUE** do MATR460 (~99%), mas não é histórico contábil real.

## Solução híbrida

Parâmetro `stock_method` (default **`auto`**):

| Prioridade | Condição | Modo resolvido | Fonte |
|------------|----------|----------------|-------|
| 1 | SB9 em `end_date` | `official_closure` | `SUM(B9_VINI1)` |
| 2 | Sem SB9 na data (`auto` / `hybrid`) | `register_snapshot` | **SB2 atual** + proxy EM PROCESSO |
| — | `estimated` explícito | `estimated` | SB9 base + SD3 (Kardex) |

### `register_snapshot`

- **EM ESTOQUE (KPI):** `SUM(B2_VATU1)` — mesmo SQL do modo sem datas.
- **EM PROCESSO (proxy):** soma SB2 nos armazéns `99`, `50`, `98` (config: `app/content/supplies_stock_hybrid.json`).
- **Aviso:** `data_quality_warning` quando `closing_base_date < end_date` — valor é snapshot na consulta, **não** posição em `end_date`.

### Contrato API (`estimation`)

```json
{
  "method": "sb2_register_snapshot",
  "stock_method_resolved": "register_snapshot",
  "data_quality_warning": "...",
  "inventory_register": {
    "em_estoque_value": 3565738.09,
    "em_processo_proxy_value": 262318.99,
    "total_geral_proxy_value": 3828057.08,
    "snapshot_at_query_time": true,
    "period_end_requested": "20260531"
  },
  "wip_proxy": { "enabled": true, "total_wip_value": 262318.99 }
}
```

## Confiabilidade histórica

| Modo | Passado confiável? |
|------|-------------------|
| `official_closure` | Sim, se SB9 existir na data |
| `register_snapshot` | **Não** — só snapshot “agora”; útil para alinhar ao MATR460 emitido sem fechamento |
| `estimated` | Analítico; exige fechamentos SB9 intermediários |

## Scripts de validação

```bash
# Modelos MATR460 vs referência
export API_DELPI_INTERNAL_SERVICE_TOKEN=...
python3 scripts/run_matr460_approximation.py

# API com período maio/2026 (auto → register_snapshot)
curl -s "http://localhost/apps/api-delpi/supplies/stock-value?branch=01&start_date=2026-05-01&end_date=2026-05-31&summary_only=true" \
  -H "Authorization: Bearer $TOKEN"
```

## Arquivos

| Artefato | Caminho |
|----------|---------|
| Config locais processo + notas | `app/content/supplies_stock_hybrid.json` |
| Resolução de método | `stock_value_method_service.py` |
| Meta register + WIP | `stock_value_register_snapshot_service.py` |
| SQL SB2 + WIP | `stock_value_query_repository.py` |
| Payload estimation | `stock_value_estimation_payload_service.py` |
| MFE breakdown | `StockEstimationBreakdown.tsx` |
