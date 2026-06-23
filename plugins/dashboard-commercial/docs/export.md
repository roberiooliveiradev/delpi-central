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
| PNG | Rasterização do alvo `.dc-chart-export-root` (ver abaixo) |

## PNG — gráficos do dashboard

Botão **PNG** em `CommercialExportButtons` (`variant="table"`) quando `getChartRoot` / `chartRoot` está configurado.

| Gráfico | Técnica | Arquivo |
|---------|---------|---------|
| Evolução do ROL (Recharts) | Clone do SVG `.recharts-wrapper`, dimensões pelo `viewBox`, remoção de `clip-path`, canvas 2× | `src/export/chartPngExport.ts` |
| Funil de conversão (HTML/CSS) | `html2canvas` (import dinâmico) sobre `.dc-chart-export-root` | `src/export/chartPngExport.ts` |

### Contrato no MFE

1. O componente do gráfico expõe um wrapper com classe `dc-chart-export-root`.
2. A página mantém `ref` no container pai e passa `getChartRoot={() => ref.current}` aos botões de exportação.
3. PDF da mesma seção reutiliza `rasterizeChartElement` quando `chartRoot` é informado no dispatch.

### Dependência

- `html2canvas` — apenas para gráficos sem SVG Recharts (funil); carregada sob demanda (chunk separado no build).

## Impressão

- **Ctrl+P** do navegador e exportação **PDF** permanecem disponíveis.
- O botão **Imprimir** do header foi removido (redundante com PDF). `PrintReportSummary` e `@media print` em `index.css` seguem ativos.

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
- `buildProductStructuresPayload` — BOM achatado (árvore via `buildProductStructureTree`, alinhado à UI)
- `buildHistoryPayload` — histórico AIJ010 (inclui fluxo e marcação da timeline)
- `buildDetailSummaryPayload` — cabeçalho da proposta

## Testes

```bash
npm run test
```

Cobertura relevante:

- `src/export/export.test.ts` — builders e BOM
- `src/export/chartPngExport.test.ts` — `parseViewBoxSize`
- `src/utils/paginationPages.test.ts` — páginas visíveis no rodapé
