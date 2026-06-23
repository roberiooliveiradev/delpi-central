# Exportação — Dashboard Comercial

Módulo centralizado em `src/export/`, alinhado ao padrão do `minha-delpi-chat`.

## Ponto de entrada

```typescript
import {
  runCommercialExport,
  CommercialExportButtons,
  buildProposalsPayload,
} from "../export";
```

## Formatos

| Formato | Implementação |
|---------|----------------|
| CSV | UTF-8 com BOM, separador `;` |
| Excel | `xlsx` (dynamic import) |
| PDF | HTML certificado DELPI + `window.print()` |

## Variantes de UI

| `variant` | Escopo |
|-----------|--------|
| `table` | Uma tabela (`TableExportPayload`) |
| `dashboard` | Indicadores + ROL + funil + propostas |
| `detail` | Resumo OV + produtos + BOM + histórico |

## Builders

- `buildDashboardKpisPayload` — indicadores do dashboard
- `buildRolSeriesPayload` — série do gráfico ROL
- `buildFunnelPayload` — funil de conversão
- `buildProposalsPayload` — tabela de propostas
- `buildProductsPayload` — produtos da OV
- `buildProductStructuresPayload` — BOM achatado
- `buildHistoryPayload` — histórico AIJ010 (inclui fluxo e marcação da timeline)
- `buildDetailSummaryPayload` — cabeçalho da proposta

## Testes

```bash
npm run test
```
