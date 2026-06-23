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
| PDF | HTML certificado DELPI + `window.print()` (gráficos: imagem embutida quando `chartRoot` informado) |
| PNG | Rasterização SVG Recharts (somente em exportação de gráfico) |

## Variantes de UI

| `variant` | Escopo |
|-----------|--------|
| `table` | Uma tabela (`TableExportPayload`); suporta `resolvePayload` assíncrono |
| `dashboard` | Indicadores + ROL + funil + propostas; suporta `resolveContext` assíncrono |
| `detail` | Resumo OV + produtos + BOM + histórico |

## Builders

- `buildDashboardKpisPayload` — indicadores do dashboard
- `buildRolSeriesPayload` — série do gráfico ROL
- `buildFunnelPayload` — funil de conversão
- `buildProposalsPayload` — tabela de propostas (exportação busca até 200 linhas com filtros ativos via `getCommercialProposalsForExport`)
- `buildProductsPayload` — produtos da OV
- `buildProductStructuresPayload` — BOM achatado
- `buildHistoryPayload` — histórico AIJ010 (inclui fluxo e marcação da timeline)
- `buildDetailSummaryPayload` — cabeçalho da proposta

## Testes

```bash
npm run test
```
