# GLPI #1353 — Ajuste de layout/UX — evidência de deploy e aceite

**Data:** 2026-10-30 · **Escopo:** `plugins/supplies` (MFE only) · **Outcome:** DEPLOYED

## Contexto

Feedback visual do Product Owner sobre a área de filtros da Auditoria de Consumo
(`/apps/supplies/consumption-audit`) já em produção: arranjo ruim, excesso de
altura, pouco uso dos componentes do `plugin-ui` e ausência de atalhos de período.

## O que foi entregue

- Área de filtros reorganizada em três blocos canônicos sobre
  `SuppliesFilterBarShell`:
  - **Bloco A — busca principal:** filial + combobox de OP (autocomplete com
    debounce/abort preservado).
  - **Bloco B — período rápido:** `SuppliesSegmentToggle` com presets
    *Hoje, Ontem, Últimos 7/15/30 dias, Este mês, Mês passado, Personalizado*
    (`SUPPLIES_QUICK_PERIOD_OPTIONS` em `src/app/periodPreset.ts`, timezone
    `America/Sao_Paulo`) + botão dedicado «Limpar período».
  - **Bloco C — filtros avançados:** `<details>` colapsável que abre
    automaticamente quando a URL já traz filtro avançado; datas via
    `SuppliesDateField`, «Limpar filtros» via `SuppliesClearFiltersButton`,
    linhas em `spFiltersKit.FiltersRow`.
- `SuppliesPageHero` não carrega mais o formulário (cabeçalho compacto).
- Nenhum cálculo/regra de domínio no MFE; nenhum contrato backend alterado.

## Decisão de arquitetura — presets de período

O contrato canônico `plugins/plugin-ui/src/utils/periodPreset.ts` expõe apenas
`today, this_week, this_month, last_month, this_quarter, this_year,
last_12_months, custom`. Os presets `yesterday`, `last_7_days`, `last_15_days` e
`last_30_days` foram adicionados **no adapter de Suprimentos**
(`plugins/supplies/src/app/periodPreset.ts`), que continua reusando os helpers e
o tipo `PeriodPresetId`/`PeriodRange` do plugin-ui — sem duplicar a resolução dos
presets compartilhados. Se outros plugins precisarem desses atalhos, o owner
`plugin-ui` deve absorvê-los canonicamente (TO_INVENTORY).

## Commits / SHAs

| Owner | Commit | Conteúdo |
|---|---|---|
| `plugins/supplies` | `49d8f4dc63` | layout canônico + presets + content/help/manual + manifest 0.5.1 + testes |
| docs | (este arquivo) | evidência de deploy/aceite |

`origin/main` contém ambos.

## Deploy evidence

- Fluxo: `infra/scripts/up-prod-sequential.sh --pull --fase mfe --build supplies`
  em `srv-api` (apenas o MFE; nenhum backend tocado).
- srv-api HEAD pós-deploy: `49d8f4dc6`.
- Imagem: `infra-supplies` `e0ec6af18449` (build 2026-10-30 05:28 UTC) —
  container `delpi-supplies` up.
- Bundle em produção: `assets/App-BGkcutLI.js` contém `ca-period-preset`,
  `consumption-audit__advanced` e «Limpar período»; `remoteEntry.js` expõe
  `__federation_expose_App-KEluT_Au.js`.
- Smoke público: `remoteEntry.js` → 200; `App-BGkcutLI.js` → 200 via gateway
  `https://minhadelpi.com.br`.

## Testes

| Gate | Resultado |
|---|---|
| `consumptionAudit.structural.test.ts` | 27/27 PASS (+12 novos: presets e layout) |
| suíte `plugins/supplies` completa | 552/552 PASS |
| `tsc --noEmit` | 0 erros |
| `eslint` (arquivos tocados) | 0 warnings |
| `npm run build` | PASS |

## RQ/AC coverage

- RQ-01 arranjo corrigido — PASS (blocos A/B/C sobre FilterBarShell).
- RQ-02 plugin-ui — PASS (SegmentToggle, DateField, ClearFiltersButton,
  FilterBarShell, FiltersRow; sem design paralelo).
- RQ-03 ações rápidas de data — PASS (8 presets + limpar período; respeitam
  `date_type`; refletem na URL/fluxo existente).
- RQ-04 responsividade — PASS (FiltersRow + CSS escopado; sem teste de viewport
  manual — avaliação visual do PO pendente).
- RQ-05 acessibilidade — PASS (labels, `details/summary` nativo, combobox com
  `role`/`aria-activedescendant` preservados).
- RQ-06 não regressão — PASS (debounce, autocomplete, paginação, detalhe,
  comparação e query params intactos; 552 testes).
- RQ-07 help sync — PASS (helpTooltips + userManualContent atualizados com
  período rápido; manifest 0.5.1).

## Unresolved / next step

- Avaliação visual final do Product Owner em produção.
- TO_INVENTORY: absorver `yesterday`/`last_N_days` no `plugin-ui` se outros
  plugins adotarem.
