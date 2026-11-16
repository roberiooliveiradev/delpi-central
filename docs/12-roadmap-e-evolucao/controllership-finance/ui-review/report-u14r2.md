# Report U14R2 — H2–H6 + DR-1=(b)

Data: 2026-11-16. Âncora: `927af73a`+. HEAD entregue: `360d300cf3`.

## Verificador

| Rodada | Veredito |
|---|---|
| r1 | REWORK (OC-1 CSS `.delpi-ui-*` no MFE; OC-2 TS2345) |
| r2 | ACCEPT_WITH_RESIDUAL |

### Veredito r2 (sem edição)

```text
veredito: ACCEPT_WITH_RESIDUAL
rodada: 2
escalar: NAO
```

## K1 — plugin-ui (aditivo)

| Item | Valor |
|---|---|
| SHA | `9d3bce1dde` + axe `09e1e2c0fe` |
| Tag | `rollback-ui-review-u14r2-plugin-ui` @ `09e1e2c0fe` |
| API | `onPointSelect?`, `selectedPointKey?`, `pointKey?` em `BarSeriesChart` |
| A11y | `role=button`, Enter/Espaço, `aria-pressed`, rótulo «data: valor»; SVG `role=group` quando interativo |
| Caracterização | sem props → sem botões / `role=img`; 6/6 + 429 charts PASS |
| HML smoke | HTTP 200: CF, my-requests, engineering, plugin-ui/assets |
| PROD | `up-prod-sequential.sh --build plugin-ui` · início `2026-11-16T01:50:18Z` · fim `2026-11-16T01:50:51Z` |

## K2 — Evolução por dia em barras

| Antes | Depois |
|---|---|
| `CfComparativeAreaChart` (área) sem clique por dia | `CfBarSeriesChart` + `seriesList` anterior alinhado; clique → `day=`; reclique limpa |

## K3 — H2 / H4 / H5

- H2: `columns:v2`, `field:false`; chave abreviada + Copiar; tabela `table-layout:fixed` em `.cf-entry-audit-occurrences-table` (só `cf-*`).
- H4: label «Pendentes»; CSS `cf-kpi-card__label` / `cf-kpi-title`.
- H5: `DOCUMENT_TYPE_ORDER` / `formatDocumentTypes` canônico.

## K4 — medições HML (`/tmp/ui-review-u14r2/`)

| Artefato | Valor |
|---|---|
| panorama-1440 | cardHeight **305** (≤520); legendDot **9** (≤16); centerOutside **0** |
| panorama-390 | legendDot **10** |
| pending-title-1440 | «Pendentes» **78≤78** |
| table-width-clean | **1040≤1040** |
| table-width-v1-legacy | **1040≤1040** |
| daily-bars-1440 | barCount **15** |
| daily-bars-click | toggleDay **ok** |
| axe-1440 | `newSeriousCritical: []` (residuais: color-contrast, aria-required-children HorizontalValueBars, aria-valid-attr-value underline-nav) |

Playwright `u14r2-hml-measures` · 3/3 PASS @ HML `360d300cf3`.

## PROD MFE

| Item | Valor |
|---|---|
| SHA | `360d300cf3` |
| Tag | `rollback-ui-review-u14r2-controllership-finance` |
| Ordem | plugin-ui → controllership-finance |
| MFE | início `2026-11-16T01:51:58Z` · fim `2026-11-16T01:52:07Z` |
| Smoke | remoteEntry plugin-ui + CF + my-requests + engineering → **200** |

## Commits (principais)

| SHA | Mensagem |
|---|---|
| `9d3bce1dde` | feat(plugin-ui): U14R2 K1 — BarSeriesChart com onPointSelect aditivo |
| `6648586df4` | feat(controllership-finance): U14R2 K2–K3 — barras com day, tabela v2 e Pendentes |
| `09e1e2c0fe` | fix(plugin-ui): ChartFrame role=group com onPointSelect (axe) |
| `90bb5203fe` / `b88ab177ca` / `360d300cf3` | fixes tabela/Pendentes/OC CSS+tipo |

## Pedido ao owner

Conferir visualmente em PROD (1440): Panorama, KPI «Pendentes», tabela de ocorrências sem scroll horizontal, barras da Evolução por dia com clique/`day` e limpeza no segundo clique.
