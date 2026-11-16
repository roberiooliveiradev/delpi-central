# Report U15R — Evolução por dia (padrão Comercial) + KPI

Data: 2026-11-16. Âncora: `5610c687`+. HEAD código U15R: `4bc8a2c29e` (MFE).

## Verificador

| Rodada | Veredito |
|---|---|
| r1 | ACCEPT_WITH_RESIDUAL |

### Veredito r1 (sem edição)

```text
veredito: ACCEPT_WITH_RESIDUAL
rodada: 1
escalar: NAO
```

Resumo: chart no padrão Comercial, KPI mil/mi sem reticências, ícone×título sem overlap; vitest 533 PASS; e2e HML `TEST_NOT_RUN` no verificador (artefatos consistentes); `tsc -b` pré-existente fora do escopo.

## R1 — «Evolução por dia» no padrão do Comercial

| Item | Valor |
|---|---|
| Componente | `EntryAuditDailyEvolutionChart` — `ChartViewShell` + `ChartTypeSegmentToggle` (`period_compare`) + `MultiTypeSeriesChart` |
| Preferência | `controllership-finance:entry-audit:daily` (padrão `column`) |
| Clique | `onCategoryClick` → `day=` / limpa; `categoryFillKey` com destaque |
| Export / cores | `CfTabularExportButtons` + `ChartSeriesColorsPopover` |
| Removido | `CfBarSeriesChart` / `usePortalColorScheme` do MFE |
| Kit | zero diff em `plugins/plugin-ui`; `onPointSelect` do BarSeriesChart permanece (aditivo U14R2) |
| Tema escuro | `chart-white-dark.json`: **whiteCount 0** |

### Outros gráficos do MFE (listar, não migrar)

| Superfície | Status |
|---|---|
| `CfComparativeAreaChart` | adapter órfão **removido** com o BarSeries |
| Closing / Panorama / Breakdowns | donut, gauge, `HorizontalValueBars` — fora do escopo U15R |
| Uso de `BarSeriesChart` em features | **nenhum** |

## R2 — KPI sem reticências

| Antes | Depois |
|---|---|
| `formatMoneyBRLForKpi` só compactava ≥1 mi; CSS com `text-overflow: ellipsis` | ≥1 mil → `R$ 136,1 mil`; ≥1 mi → `R$ 1,06 mi`; CSS `clip` / sem ellipsis |

Artefatos: `kpi-ellipsis-1440.json` / `kpi-ellipsis-390.json` — `hasEllipsisChar: false` em todos os cartões.

## R3 — ícone × título em 390

| Item | Valor |
|---|---|
| CSS | label `min-width:0` / sem `max-content`; `--delpi-ui-kpi-icon-size: 28px` ≤480 |
| Medição | `kpi-icon-title-overlap-390.json`: **overlaps []** |

## Medições HML (`/tmp/ui-review-u15r/`)

| Artefato | Valor |
|---|---|
| chart-white-dark | whiteCount **0** |
| chart-type-after-toggle / after-f5 | `chartType: line` persistido (`Linhas`) |
| daily-categories-before / with-day | tickCount **13=13**; `?day=2026-11-04` |
| kpi-ellipsis-1440 / 390 | sem reticências |
| kpi-icon-title-overlap-390 | overlaps **[]** |

Playwright `u15r-hml-measures` · 2/2 PASS @ HML `4bc8a2c29e` (executor). Verificador: e2e `TEST_NOT_RUN`.

## PROD

| Item | Valor |
|---|---|
| Ordem | só MFE |
| MFE | início `2026-11-16T10:00:17Z` · fim `2026-11-16T10:00:27Z` |
| Tag | `rollback-ui-review-u15r-controllership-finance` @ `4bc8a2c29e` |
| Smoke | remoteEntry CF → **200** |
| PROD_HEAD (pull) | `0b96c59bd2` (inclui U15R) |

## Commits

| SHA | Mensagem |
|---|---|
| `75250f2beb` | feat(controllership-finance): U15R — Evolução por dia no padrão Comercial + KPI |
| `4bc8a2c29e` | fix(controllership-finance): U15R — fundo transparente no diário escuro e medição H6 |

## Residual / nota ao dono do plugin-ui

| ID | Descrição |
|---|---|
| kit-onPointSelect | prop `onPointSelect` / `selectedPointKey` do `BarSeriesChart` (U14R2) ficou no kit sem consumidor no CF — decidir se mantém ou remove |
| tsc pré-existente | `tsc -b` do MFE falha em arquivos fora do escopo U15R (`entryAuditTableColumns`, `HomePage`, `UserProfilePage`) |

## Pedido ao owner

Conferir visualmente em PROD: «Evolução por dia» com Colunas/Linhas/Área + export; clique no dia filtra e limpa; tema escuro sem fundo branco; KPIs monetários compactos sem reticências; em 390 ícone não cobre o título.
