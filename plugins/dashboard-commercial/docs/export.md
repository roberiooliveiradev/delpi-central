# Exportação — Dashboard Comercial

Motor tabular/PDF: **`@delpi/plugin-ui`** ([export-catalog.md](../../plugin-ui/docs/export-catalog.md)).

Neste plugin ficam builders de domínio, `dispatch` e `CommercialExportButtons`.

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
| CSV | UTF-8 com BOM, separador `;` (`plugin-ui`) |
| Excel | `xlsx` dynamic import (`plugin-ui`) |
| PDF | HTML certificado DELPI + print (`plugin-ui`) |
| PNG | Ainda só no chat (`chartPngExport`) — backlog E2 |

## Variantes de UI

| `variant` | Escopo |
|-----------|--------|
| `table` | Uma tabela (`TableExportPayload`); suporta `resolvePayload` assíncrono |
| `dashboard` | Indicadores + ROL + funil + propostas |
| `detail` | Resumo OV + produtos + BOM + histórico |

## Builders

- `buildDashboardKpisPayload`, `buildRolSeriesPayload`, `buildFunnelPayload`
- `buildProposalsPayload`, `buildProductsPayload`, `buildProductStructuresPayload`
- `buildHistoryPayload`, `buildDetailSummaryPayload`

## Testes

```bash
npm run test
```

- `src/export/export.test.ts` — builders + primitives (via reexport)
