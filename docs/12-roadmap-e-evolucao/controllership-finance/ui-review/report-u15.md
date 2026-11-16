# Report U15 — polimento (P1–P4)

Data: 2026-11-16. Âncora: `bd5675c7`+. HEAD código U15: `7e2f650a90` (MFE) · `7639a2abab` (BFF).

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

Resumo do verificador: theme/bg transparente, daily sem `day`, hero 390 e KPIs 2 col confirmados por código+testes+artefatos HML; P4b residual kit confirmado; e2e HML não reproduzível pelo verificador (`TEST_NOT_RUN`).

## P1 — tema do gráfico (sem kit)

| Item | Valor |
|---|---|
| Adaptador | `CfBarSeriesChart` → `options.theme` via `usePortalColorScheme` (`data-theme` / `prefers-color-scheme`) + `backgroundColor: "transparent"` |
| Kit | zero diff em `plugins/plugin-ui` |
| Vitest | `cfBarSeriesChart.theme.test.tsx` PASS |
| HML | `chart-bg-dark.json` / `chart-bg-light.json`: fill/bg `rgba(0,0,0,0)` |

## P2 — daily sem filtrar a si mesmo (AC-SEL-3)

| Item | Valor |
|---|---|
| BFF | `service.daily` usa `_filters_without(filters, "day")` na série atual e `previous`; `day` permanece na rota/demais leitores |
| SHA | `7639a2abab` |
| Pytest | `test_daily_excludes_own_day_filter` · 4/4 PASS |
| HML | `daily-before-day` / `daily-with-day`: `positiveCount` **9=9**, `barCount` **15=15** |
| Tag | `rollback-ui-review-u15-controllership-finance-api` @ `7639a2abab` |

## P3 — hero 390

| Antes | Depois |
|---|---|
| título cortado; «Nova análise» fora; glow inflava `scrollWidth` | título com wrap; ações empilhadas/wrap; glow oculto ≤480; path `__current` com reticências |

Artefato `hero-kpi-390.json`: `heroScrollWidth` **346≤346**; `actionsOutsideHero` **0**; `pathCurrentOverflow` **true**.

## P4 — KPIs + lasca zero

| Item | Status |
|---|---|
| P4a KPIs 2 col ≤480 | PASS — `kpiColumns: 2` |
| P4b dia 0 sem lasca | **RESIDUAL kit** — `ChartSeriesBar.tsx` força `height≥4` quando `pointSelectable`; U15 proíbe mexer no plugin-ui |

## Medições HML (`/tmp/ui-review-u15/`)

| Artefato | Valor |
|---|---|
| chart-bg-dark | bg/fill `rgba(0,0,0,0)` |
| chart-bg-light | bg/fill `rgba(0,0,0,0)` |
| daily-before-day | positiveCount **9** |
| daily-with-day | positiveCount **9** |
| hero-kpi-390 | 346≤346 · actionsOutside **0** · kpiColumns **2** |

Playwright `u15-hml-measures` · 2/2 PASS @ HML `7e2f650a90` (executor). Verificador: e2e `TEST_NOT_RUN` (rede/credenciais).

## PROD

| Item | Valor |
|---|---|
| Ordem | BFF → MFE |
| BFF | início `2026-11-16T03:33:51Z` · fim `2026-11-16T03:33:54Z` · healthy |
| MFE | início `2026-11-16T03:33:54Z` · fim `2026-11-16T03:34:03Z` |
| Tags | `rollback-ui-review-u15-controllership-finance-api` · `rollback-ui-review-u15-controllership-finance` |
| Smoke | remoteEntry CF + plugin-ui → **200** |
| PROD_HEAD (pull) | `4bccc31a12` (inclui U15) |

## Commits

| SHA | Mensagem |
|---|---|
| `7639a2abab` | fix(controllership-finance-api): U15 P2 — daily ignora filtro day (AC-SEL-3) |
| `ca1e0eabab` | feat(controllership-finance): U15 P1/P3/P4a — tema do gráfico, hero 390 e KPIs 2 col |
| `f6f3f0be4f` | fix(controllership-finance): U15 — hero 390 wrap/path e clique day na medição |
| `7e2f650a90` | fix(controllership-finance): U15 — esconde glow do hero em 390 (scrollWidth) |

## Residual

| ID | Descrição | Destino |
|---|---|---|
| P4b | lasca de barra em dia 0 (min-height 4 com `onPointSelect`) | próxima etapa com mudança aditiva no `plugin-ui` / `ChartSeriesBar` |

## Pedido ao owner

Conferir visualmente em PROD: gráfico diário no tema escuro sem fundo branco; com um dia selecionado, os outros dias permanecem visíveis (não zerados); hero em 390 sem corte/botão fora; KPIs em 2 colunas.
