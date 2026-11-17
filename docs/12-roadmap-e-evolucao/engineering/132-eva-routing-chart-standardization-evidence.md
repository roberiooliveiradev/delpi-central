# 132 — Padronização corporativa dos gráficos da aba Roteiro (EVA)

**TASK_ID:** `EVA-PORTAL-ENGINEERING-CHART-STANDARDIZATION-01`
**Commit:** `2362f5866e`
**Status:** `HML_APPROVED + PROD_DEPLOYED` — smoke produtivo autenticado
pendente de principal humano Keycloak (mesma pendência do gate V2).

## Escopo

Migração dos três gráficos da seção "Análise visual" da aba Roteiro de
`ConfigurableSeriesChart` para a composição corporativa do Plugin UI —
a mesma usada pelo gráfico Evolução do ROL do Portal Comercial:

- `ChartViewShell` (toolbar) + `MultiTypeSeriesChart` (renderer Recharts,
  de propriedade do Plugin UI).
- `ChartTypeSegmentToggle` (família `categorical`: Colunas / Barras).
- `ChartOverlayOptionsPopover` (rótulos de valor).
- `ChartSeriesColorsPopover` (visibilidade/cor por série).
- `TabularExportButtons` + `runTabularExport` — CSV, Excel e PDF com
  contexto completo (produto, filial, estágio, cenário, unidade,
  proveniência OBSERVED/CALCULATED/SIMULATION).
- `usePersistedChartPreferences` com namespace próprio
  `engineering:routing:{produto}:{gráfico}` — separado do Comercial e do
  rascunho técnico do estudo (sessionStorage V2 inalterado).
- Alternância de unidade Auto/s/min na toolbar — conversão só na camada
  de apresentação; valores oficiais permanecem em minutos.

## Alterações por owner

**Plugin UI (owner da infra gráfica):**
- `chartDataFamilies.ts`: `CATEGORICAL_TYPES` passa a incluir
  `horizontal_bar`.
- `usePersistedChartPreferences.ts`: campos opcionais `displayUnit` e
  `showValueLabels` (schema genérico, interpretado pelo host).
- `styles/multi-type-series-chart.css` (novo): chrome do renderer
  Recharts tematizado por tokens `--delpi-ui-*` — ticks, eixos, grid,
  tooltip e legenda consistentes em dark/light para todos os hosts.

**Engineering (owner da composição):**
- `RoutingSeriesChart.tsx` (novo): composição única dos três gráficos.
- `routingChartExport.ts` (novo): builders de payload de exportação.
- `ProductRoutingTab.tsx`: `VisualSection` migrada; removidos
  `ConfigurableSeriesChart` e `usePortalTheme` da aba.
- Sem `recharts` nem imports de `plugins/commercial` — zero renderer
  paralelo e zero dependência do MFE Comercial.

## Contratos preservados

- Motor de balanceamento determinístico e contratos BFF
  (`GET /routing`, `POST /line-balance`) inalterados.
- Routing Study Workspace V2 integral: página única, postos hipotéticos,
  cenários, sessionStorage, restore/clear, STALE.
- Simulação continua rotulada SIMULATION — alocação por capacidade de
  takt, sem precedência; não é distribuição física validada.

## Evidência

- `tsc --noEmit` engineering: limpo (falhas pré-existentes em arquivos de
  teste do plugin-ui não relacionados constam de HEAD).
- Vitest engineering: 511/511 (incl. `routingChartExport.test.ts` e
  asserts estruturais da composição corporativa).
- Vitest plugin-ui dos arquivos tocados: verde.
- Builds `vite` plugin-ui e engineering: OK
  (`App-DW--lCnZ.js`, `expose_Index-cqRzv7EO.js`).
- E2E HML autenticado (SSO real): 30/30 — desktop, mobile, tablet,
  mobile-390, mobile-320; inclui asserts do chrome corporativo
  (toggle de tipo, catálogo Colunas/Barras, popover de séries/cores,
  botões CSV/Excel/PDF) e capturas dark/light inspecionadas.
- Verify oficial: `INCONCLUSIVE` — `devin auth` indisponível no ambiente
  (mesmo bloqueio das rodadas anteriores); não convertido em PASS.

## Deploy

- **HML** (`projetos-teste` @ `2362f5866e`): `up-hml-sequential.sh
  --build plugin-ui engineering` — containers healthy; bundle
  `App-DW--lCnZ.js` e CSS `multi-type-series-chart` servidos.
- **PROD** (`projetos` @ `72263ca132`, contém `2362f5866e`):
  `up-prod-sequential.sh --build plugin-ui engineering` — remoteEntry
  `expose_App-BVgGg7lr` + `App-DW--lCnZ.js` (200 via
  minhadelpi.com.br, contém `engineering:routing`), Index expose e CSS
  do Plugin UI com `bar","horizontal_bar` e `multi-type-series-chart`.

## Residuais

- Verify oficial INCONCLUSIVE (bloqueio de infra — `devin auth login`).
- Smoke visual autenticado em produção: pendente de principal humano.
- Rollback: `git revert 2362f5866e` + rebuild `plugin-ui`/`engineering`.
