# Catálogo de migração — cópias locais → `@delpi/plugin-ui`

Objetivo: **uma implementação** de balões explicativos e primitivos de label/aba nos **plugins MFE**. O **portal** (shell) permanece fora de escopo — não consome `@delpi/plugin-ui`.

**Frente ativa (jul/2026):** [Fase 7 — zero CSS de componente do kit no MFE](#fase-7--zero-css-de-componente-do-kit-no-mfe-jul2026) · plano [refactoring-roadmap.md § 8](./refactoring-roadmap.md).

## Status — Fase 1 (help)

| Plugin | Arquivo local | Status | Notas |
|--------|---------------|--------|-------|
| `tv-dashboard` | — | ✅ Migrado | Referência de integração |
| `dashboard-production` | — | ✅ Migrado | Piloto Fase 1 |
| `dashboard-commercial` | — | ✅ Migrado | |
| `dashboard-engineering` | — | ✅ Migrado | |
| `dashboard-financial` | — | ✅ Migrado | |
| `dashboard-hr` | — | ✅ Migrado | |
| `dashboard-lmps` | — | ✅ Migrado | |
| `dashboard-quality` | — | ✅ Migrado | |
| `dashboard-supplies` | — | ✅ Migrado | |
| `cadastro-kaizen` | — | ✅ Migrado | F2/F3 completo — ver [UI-PLUGIN-UI.md](../../cadastro-kaizen/docs/UI-PLUGIN-UI.md) |
| `eficiencia-fabril` | — | ✅ Migrado | |
| `transformometro` | — | ✅ Migrado | — |
| `quality-action-plans` | — | ✅ Migrado | — |
| `maintenance` | — | ✅ Migrado | re-export em `components/data/index.ts` |
| `portal` | `src/components/HelpTooltip.tsx` | ❌ Fora de escopo | Shell do host; API controlada (`open`, placement) diferente |

## Mapeamento de classes CSS legadas

| Prefixo antigo | Ação na migração |
|----------------|------------------|
| `*-help-tooltip*` | Remover do plugin; estilos em `plugin-ui/src/styles.css` (`delpi-ui-*`) |
| `*-kpi-card` / `*-section-card` / chrome de card/filtro/tabela/loading | Remover do plugin se dual-class + `.delpi-ui-*` cobrem; mapear só tokens `--delpi-ui-*` |
| `*-field__label` | Manter no plugin como `className` em `FieldLabel` |
| Layout de página (`*-page-stack`, `*-detail-grid`) | **Manter** no MFE — não é chrome de componente |

**Regra:** nunca recolocar no MFE o CSS estrutural que foi podado ao migrar para o kit. Bug visual → `plugins/plugin-ui/src/styles/` + rebuild remote. Ver [architecture.md](./architecture.md) § CSS · Cursor `plugins-reusable-components.mdc`.

## Ordem sugerida de migração (concluída Fase 1)

1. Dashboards departamentais — ✅
2. `cadastro-kaizen`, `transformometro`, `quality-action-plans`, `eficiencia-fabril`, `maintenance` — ✅

## Após cada migração

- [x] Remover arquivo `HelpTooltip.tsx` local
- [x] Remover bloco CSS `*-help-tooltip` do `index.css` do plugin
- [x] Atualizar esta tabela para ✅
- [x] `npm run build` do plugin
- [x] Compose: `context: ../plugins`, `dockerfile: {plugin}/Dockerfile`

## Roadmap completo

Fases 0–6: **[refactoring-roadmap.md](./refactoring-roadmap.md)** (§ 1–7).  
**Frente ativa — Fase 7** (zero CSS kit no MFE): roadmap **§ 8** + [seção abaixo](#fase-7--zero-css-de-componente-do-kit-no-mfe-jul2026). Regra Cursor: `plugins-reusable-components.mdc`.

## Componentes futuros no pacote

Ver inventário detalhado em [refactoring-roadmap.md § 1.3](./refactoring-roadmap.md#13-componentes-duplicados--candidatos-a-extrair-2-consumidores).

Resumo (2+ consumidores):

| Componente | Ocorrências | Fase sugerida |
|------------|-------------|---------------|
| `KpiCard` | 15 | F2 ✅ |
| `ChartCard` | 14 | F2 ✅ |
| `LoadingActivityCard` | 12 | F2 ✅ |
| `Pagination` (+ jump, page size) | 7 dashboards | F2 ✅ (7 dept.) |
| `MultiSelectField` | 13 | F2 ✅ (8 dept. + lmps + ef + tm) |
| `FilterBar` | 12 | F2 ✅ (FiltersRow + FilterInputField) |
| `FilterBarShell` | 2 | F2 ✅ (maintenance form/card; ef grid) |
| `FiltersRow` trailing/compact | 1 | F2 ✅ (quality-action-plans) |

## Gate CI

```bash
python3 scripts/ci/check_plugin_docker_shared_libraries.py --check
python3 scripts/ci/audit_plugin_ui_duplication.py --check          # bloqueia HelpTooltip local + integração
python3 scripts/ci/audit_plugin_ui_duplication.py --check --strict # falha em toda duplicata catalogada
python3 scripts/ci/audit_plugin_ui_native_form_controls.py --check # bloqueia <select>/<textarea> novos fora do pacote
python3 scripts/ci/audit_mfe_plugin_ui_css.py --check              # bloqueia seletores .delpi-ui-* em CSS de MFE (Fase 7)
```

Relatório: [native-form-controls-audit.md](./native-form-controls-audit.md)

| `DataTable` / `DataTableSection` | ~25 | F2 ✅ (7 dept. + lmps DataTable) |
| `DetailFieldGrid` | 5 | F3 ✅ (5 consumidores) |
| `EditableSectionCard` | 3 | F3 ✅ |
| `ReadOnlyField` | 2 | F3 ✅ |
| `SelectField` | 2 | F3 ✅ |
| `TextField` / `TextAreaField` | 1 (PAC) | F3 ✅ |
| `TitleWithHelp` | 1 (PAC) | F3 ✅ |
| `FilterCheckboxField` | 1 (PAC) | F3 ✅ |
| `FormGrid` / `FormActions` | PAC + kaizen | F3 ✅ |
| `FormFieldShell` / campos nativos | kaizen | F3 ✅ |
| `StateBanner` | kaizen | F3 ✅ |
| `PageHeader` (brand) | kaizen + transformometro + maintenance | F3 ✅ |
| `CreatableMultiSelectField` | PAC + kaizen categorias | F3 ✅ |
| `TableHeaderCell` | PAC + transformometro | F3 ✅ |
| `PageHeader` | 7 | F3 ✅ |
| `DetailCard` | 3 | F3 ✅ |
| `SectionCard` | PAC + kaizen | F3 ✅ |
| `EmptyState` / `LoadingState` | 2 | F3 ✅ |

## Status — Fase 4 (utilitários)

| Utilitário | Consumidores | Notas |
|------------|--------------|-------|
| `paginationPages` | plugin-ui Pagination | ✅ desde F2.4 |
| `chartColors` | 8 dashboards + transformometro + PAC | Paletas `DEPARTMENTAL`, `LMPS`, `CSS_VARS` |
| `operationalUnitLabels` | 8 dashboards | Filiais 01/02 TOTVS |
| `goalDisplay` | 8 dashboards | Badges IDD / meta KPI |

Reexport local (barrel do plugin): `export { goalDisplayFormat } from "@delpi/plugin-ui/index"` — preferir subpath MF, não paths relativos `plugin-ui/src/…`.

## Status — Fase 5 (evidências / confirm / SI)

| Plugin | FileDropzone | Confirm | Notas |
|--------|--------------|---------|-------|
| `cadastro-kaizen` | ✅ | — | `fileDropzoneKaizenClasses` |
| `quality-action-plans` | ✅ | ✅ | `useConfirmDialogController` + `ConfirmModalPanel` |
| `transformometro` | ✅ | ✅ | Provider + `ConfirmModalPanel` |
| `strategic-indicators` | — | — | `operationalUnitLabels` reexport |

| Componente | Pacote | Notas |
|------------|--------|-------|
| `ConfirmModalPanel` | ✅ F5 | Headless; `ModalShell` local (PAC, transformometro) |
| `ModalShell` | ✅ F5.5 | Portal + escape; `createHostContainedModalShell` preenche a área do MFE sem cobrir o chrome do host (`portalTarget` / `data-delpi-modal-host`) |

**Não** mover sem consolidar — ver [contributing.md](./contributing.md).

## Status — Fase 6 (diagrama / flowchart)

| Plugin | Arquivos locais removidos | Status | Notas |
|--------|---------------------------|--------|-------|
| `transformometro` | `components/diagram/FlowchartEditor*`, utils `diagram*`, `flowchartMermaid`, `exportFlowchartImage`, `types/bpmnNodeCatalog` | ✅ Migrado | Wrapper `TransformometroFlowchartEditor` + `content/flowchartEditorLabels.ts` |

Pacote: `plugin-ui/src/components/diagram/` + `styles/diagram.css`.

Após migração:
- [x] Wrapper fino com `labels`, `confirm`, `colorMode`, `shellClassName`
- [x] Reexport de tipos de API em `transformometro/src/types/diagram.ts`
- [x] `npm run build` transformometro + testes plugin-ui diagram
- [ ] Remover bloco CSS duplicado `tm-diagram-*` de `transformometro/src/index.css` (opcional — alias mantém compatibilidade)

## Infraestrutura de popover (`menu`) — `FixedPanelPortal` (jul/2026)

Primitivo de infraestrutura para popover posicionado por ponto (portal + tema + dismiss por clique fora/Escape + escopo MFE opcional). Consolida a lógica antes duplicada em cada popover de posição fixa.

| Consumidor | Papel | Notas |
|------------|-------|-------|
| `ContextMenu` (kit) | Reimplementado sobre `FixedPanelPortal` | Removeu portal/tema/dismiss inline; API pública inalterada |
| `DataPrepareColumnMenu` (`tv-dashboard`) | Popover de coluna (Preparar dados) | Usa `portalScopeClassName="dashboard-tv-dashboard"` para tokens/CSS de domínio nas sub-views; sem lógica de portal local |

Pacote: `plugin-ui/src/components/menu/FixedPanelPortal.tsx` (+ teste). Sem CSS próprio (infra; consumidores passam `className`, ex.: `delpi-ui-context-menu`). Para ancoragem a elemento use `AnchoredPanelPortal` (`components/shape`).

Após extração:
- [x] `FixedPanelPortal` + `FixedPanelPortal.test.tsx`
- [x] `ContextMenu` migrado (dois consumidores reais)
- [x] Catálogo (`visualComponents.ts` + demo `menu`) + `component-catalog.md` + `contributing.md`
- [x] `npm test` plugin-ui + `npm run build` tv-dashboard

## Status — Fase 2 (shell de dashboard)

| Plugin | Pagination | MultiSelect | FiltersRow | ChartCard | KpiCard | LoadingActivity | Notas |
|--------|------------|-------------|------------|-----------|---------|-----------------|-------|
| `dashboard-production` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Piloto F2 |
| `dashboard-commercial` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-engineering` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-financial` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-hr` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-quality` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-supplies` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | |
| `dashboard-lmps` | — | ✅ | ✅ | ✅ | ✅ | ✅ | Pagination via CompactPagination |
| `transformometro` | ✅ | ✅ | — | ✅ | ✅ | | CompactPagination + ChartCard + MultiSelect + KpiCard + DataTable + TableHeader F2/F3 |
| `eficiencia-fabril` | — | ✅ | — | ✅ | ✅ | ✅ | ChartCard + MetricKpiCard + FilterBarShell + MultiSelect F2 |
| `maintenance` | ✅ | ✅ | — | — | — | — | TablePaginationNav + FilterBarShell + MultiSelect + DataTable F2 |
| `controle-retrabalhos` | ✅ | — | ✅ | ✅ | ✅ | ✅ | Empty/Loading F3 + Kpi/Chart/LoadingActivity + FilterBarShell + PageHeader + CompactPagination |
| `financeiro-centro-custo` | ✅ | — | ✅ | ✅ | ✅ | — | ChartCard/KpiCard + FilterBarShell + CompactPagination + PageHeader F2/F3 |
| `auditoria-5s` | — | — | ✅ | ✅ | ✅ | — | ChartCard + AnalyticsKpi + FilterBarShell F2 |
| `pedidos-venda-abertos` | — | ✅ | ✅ | — | ✅ | — | PageHeader F3 + Pagination/KpiCard/MultiSelect/FilterBarShell F2 |
| `inspecoes-entrada` | ✅ | — | ✅ | — | ✅ | — | PageHeader + Pagination + KpiCard + FilterBarShell F2/F3 |
| `quality-action-plans` | — | ✅ | ✅ | ✅ | ✅ | — | FiltersRow + forms F3 (TextField, TableHeaderCell, FilterCheckbox) |
| `cadastro-kaizen` | — | ✅ | FiltersRow + FilterSelectField + createKaizenKpiCard + SectionCard + forms F2/F3 |

Após migração Pagination: remover `PaginationPageJump.tsx` e `utils/paginationPages.ts` locais; reexportar `TABLE_PAGE_SIZE_OPTIONS` em `./Pagination`.

Após migração MultiSelect: wrapper fino com `createDashboardMultiSelectField` (~20 linhas); **Onda 2 ✅** — shell em `multi-select.css` (`.delpi-ui-multi-select*`); MFE sem cópia estrutural.

### Onda 2 — MultiSelect + SelectControl (jul/2026)

| Item | Status |
|------|--------|
| `multiSelectBemClasses` / `selectControlBemClasses` | ✅ emitem prefix + `.delpi-ui-*` |
| Shell CSS | ✅ `multi-select.css` completo; `select-control.css` já canônico |
| Poda MFEs | ✅ chrome `{prefix}-multi-select*` / `{prefix}-select__*` removido |
| Domínio mantido | ribbon TV (`.delpi-ui-select` + densidade), `pac-table-select--status`, `filter-bar > field--multi-select` |

### Onda 3 — Chart / KPI / Loading / Filters / Export (jul/2026)

| Item | Status |
|------|--------|
| CSS canônico | ✅ `chart-card.css`, `departmental-kpi.css`, `loading-activity.css`, `dashboard-filters.css`, `export-actions.css` |
| Kits `*BemClasses` | ✅ emitem prefix + `.delpi-ui-*` |
| `LoadingActivityInline` (LMPS/SI) | ✅ kit `createDashboardLoadingActivityCard`; CSS local removido |
| Poda MFEs | ✅ chrome estrutural removido; `kpi-grid` / layout de página permanece |

### Hotfix — PAC wiring sem dual-class (jul/2026)

| Problema | Correção |
|----------|----------|
| KPI `MetricKpiCard` sem `delpi-ui-*` + override PAC | Dual-class + `body` no kit; PAC usa `createMetricKpiCard("pac")` |
| Tabelas raw `pac-table` | `PAC_TABLE = dataTableBemClasses("pac")` |
| SectionCard / MultiSelect / TextField sem filter-box dual | Dual no kit + `section-card.css` |
| FiltersRow fields apertados | Bridge em `dashboard-filters.css` |

### Hotfix — shell card / FilterBar / SimpleKpi (jul/2026)

Regressão pós-Onda 3 (PA, scrap, CR…): filtros em 1 coluna, KPI/chart/tabela sem padding.

| Correção | Onde |
|----------|------|
| `.delpi-ui-card` shell (padding/borda) | `card-shell.css` |
| FilterBar column + grid `width:100%` + bridge `*-filter-bar__grid` | `dashboard-filters.css` |
| `simpleKpiCardBemClasses` dual-class + layout ícone | `SimpleKpiCard.tsx` + `departmental-kpi.css` |
| Fields PA/SM/CR/FCC → `filtersRowBemClasses` | filtersUi dos MFEs |

### Resíduos finais (pós-Onda 3 → canônico)

| Item | Ação |
|------|------|
| CX `cx-export-actions*` | ✅ `TabularExportButtons` + `export-actions.css` (`--trailing` / `__label`) |
| PAC `filter-box__spacer` | ✅ `.delpi-ui-filter-box__spacer` + `filtersRowBemClasses.filterBoxSpacer` |
| Detail×table composição | ✅ `data-table.css`; blocos `.{prefix}-detail-card .{prefix}-table*` podados nos dept. |
| Print pagination/toolbar overflow | ✅ `pagination.css` + `data-table.css` (`@media print`); MFEs mantêm chrome de página |
| `inspecoes-processo` KpiCard | ✅ `createDashboardKpiCard({ prefix: "ip" })` + shell `.delpi-ui-kpi-card` |
| SI `LoadingActivityBadge` | ✅ kit plugin-ui + `loading-activity-badge.css`; `index_dep.css` legado removido |

### Onda 1 — CSS estrutural DataTable / Detail / Pagination (jul/2026)

Poda nos MFEs dos blocos BEM espelho cobertos por `data-table.css`, `detail-card.css` e `pagination.css` (classes estáveis `.delpi-ui-*`). Kits emitem `prefix` + `delpi-ui` via `delpiUiClass`.

| Item | Status |
|------|--------|
| Dashboards dept. + EF/TM/scrap/CR/financeiros/inspeções/auditoria/kaizen | ✅ chrome de tabela/detalhe/paginação podado; print/composição/domínio permanece |
| `maintenance` DataTable | ✅ `dataTableBemClasses("dm")` + CSS de domínio só (`DataTable.css`) |
| `tv-dashboard` Preparar dados | ✅ grade local migrada para `DataTable` `grid-preview`; grade completa, wrap, resize, seleção rica, sort/reorder M |

Resíduos justificados: `@media print`, `.detail-card .table*`, colunas de domínio (`a5s-table--dashboard`, `ef-table--routing`, actions), paginação custom (`a5s-pagination`, `ip-pagination`).

Após migração DetailFieldGrid: wrapper fino com `createDashboardDetailFieldGrid` (~12 linhas); **chrome de grid no pacote** (`detail-card.css`); MFE só tema/composição.

| Plugin | EditableSectionCard | Notas |
|--------|---------------------|-------|
| `cadastro-kaizen` | ✅ | `editableSectionCardBemClasses("kz")` |
| `transformometro` | ✅ | `editableSectionCardTransformometroClasses("ds")` |
| `quality-action-plans` | ✅ | `SectionCard` + `createDashboardEditableSectionCardPac` |

| Plugin | DetailCard | PageHeader | Empty/Loading |
|--------|------------|------------|---------------|
| `dashboard-production` | ✅ | — | — |
| `dashboard-commercial` | ✅ | — | — |
| `dashboard-lmps` | ✅ | — | — |
| `quality-action-plans` | — | ✅ | — |
| `transformometro` | — | ✅ | — |
| `maintenance` | — | ✅ | — |
| `pedidos-venda-abertos` | — | ✅ | — |
| `inspecoes-entrada` | — | ✅ | — |
| `propostas-comerciais` | — | ✅ | — |
| `strategic-indicators` | — | ✅ | — |
| `controle-retrabalhos` | — | ✅ | ✅ |
| `financeiro-centro-custo` | — | ✅ | ✅ |

## Integração `@delpi/plugin-ui` (Module Federation)

**Rollout concluído (jul/2026):** todos os MFEs abaixo usam `pluginUiRemote()` + `preparePluginUiRemote()` — **sem** `COPY plugin-ui` no Docker.

Checklist: [novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md).

| Plugin | F1 help | F2/F3 componentes | MF |
|--------|---------|-------------------|-----|
| `pedidos-venda-abertos` | — | PageHeader, Pagination, KpiCard, MultiSelect, FilterBarShell, **TableColumnVisibilityMenu** / **useTableColumnVisibility** | ✅ |
| `inspecoes-entrada` | — | PageHeader, Pagination, KpiCard, FilterBarShell | ✅ |
| `propostas-comerciais` | — | PageHeader, StateBox, PanelCard, InfoGrid | ✅ |
| `strategic-indicators` | — | PageHeader, InfoState, LoadingActivityInline, ContentCard, **StatusBadge**, **SectionBlock**, **FilterSelectField** / **SiSelectControl** | ✅ |
| `controle-retrabalhos` | — | KpiCard, ChartCard, LoadingActivity, FilterBarShell, PageHeader, CompactPagination | ✅ (referência) |
| `financeiro-centro-custo` | — | ChartCard, KpiCard, EmptyState, LoadingState, FilterBarShell, PageHeader, CompactPagination | ✅ |
| `auditoria-5s` | — | ChartCard, createAnalyticsKpiCard, FilterBarShell | ✅ |
| `quality-labels` | — | CertificateFormFields, Admin form | ✅ |
| `minha-delpi-chat` | — | ChatNative*, admin forms | ✅ |
| `public-hub` | — | shell público | ✅ |

## Referência — `cadastro-kaizen` (migração UI concluída)

Documento canônico do plugin: [cadastro-kaizen/docs/UI-PLUGIN-UI.md](../../cadastro-kaizen/docs/UI-PLUGIN-UI.md).

| Camada | Exports plugin-ui | Wrapper local |
|--------|-------------------|---------------|
| Help | `HelpTooltip`, `FieldLabel` (via factories) | — |
| Formulário | `createDashboardNativeFormFields`, `DateField`, `FormGrid`, `FormActions` | `components/ui/kzFormFields`, `DateField`, `FormGrid` |
| Filtros | `createDashboardFiltersKit` (+ `FilterSelectField`) | `FiltersKit.ts` |
| KPI dashboard | `createKaizenKpiCard` | `KpiCard.tsx` |
| Seções | `SectionCard`, `EditableSectionCard` | `SectionCard`, `EditableSectionCard` |
| Lista/tabela | `createDashboardDataTableKit`, Pagination | `components/data/dataTableUi.ts` |
| Multiselect | `createDashboardMultiSelectField`, creatable | `MultiSelectField`, `CategoryMultiSelectField` |
| Feedback | `createDashboardStateBanner`, `PageHeader` | `StateAlert`, `KaizenPageHeader` |
| Evidências | `createDashboardFileDropzone` | `KaizenEvidenceDropzone` |
| Modal | `createModalShell` | `Modal.tsx` |

## RangeField (jul/2026)

| Plugin | Antes | Depois |
|--------|-------|--------|
| `tv-dashboard` | `components/deck/DeckRangeField.tsx` (implementação local) | `RangeField` de `@delpi/plugin-ui`; `DeckRangeField` permanece como alias deprecated |

---

## Fase 7 — Zero CSS de componente do kit no MFE (jul/2026)

> **Plano canônico:** [refactoring-roadmap.md § 8](./refactoring-roadmap.md).  
> **Regra:** Cursor `plugins-reusable-components.mdc` — **zero** CSS de export/dual-class do kit no MFE.  
> **Implementação:** só após marcar onda ⏳ → ✅ aqui e no roadmap.

### Tracking de ondas

| Onda | Escopo | Status |
|------|--------|--------|
| **7.0** | Regra Cursor + docs (roadmap § 8, este catálogo, architecture/contributing) | ✅ |
| **7.1** | `tv-dashboard` + `tv-dashboard-presentation` — overrides `.delpi-ui-*` | ✅ |
| **7.2** | `quality-action-plans` + `controle-retrabalhos` — chrome espelho / residual kit | ✅ |
| **7.3** | `minha-delpi-chat` admin — **B** domínio isolado (`mdc-admin-*` / `mdc-audit-*`); overrides kit zerados | ✅ |
| **7.4** | `cadastro-kaizen`, `auditoria-5s`, `maintenance`, `transformometro`, `financeiro-inadimplencia` | ✅ |
| **7.5** | `inspecoes-processo` (Pagination/EmptyState), `strategic-indicators` (DataTable) | ✅ |
| **7.6** | Família `dashboard-*` + P2 (filters/state-box/table mobile) | ✅ |
| **7.7** | Gate CI anti-reintrodução | ✅ `scripts/ci/audit_mfe_plugin_ui_css.py --check` |
| **7.8** | `cipa` — botões de ação e voltar compartilhados | ✅ |
| **7.9** | `cipa` — UI base completa (header, cards, tabela, estados, navegação e formulários) | ✅ |

### Checklist por plugin (preencher ao fechar onda)

| Plugin | Onda | CSS kit zerado | TSX cópia/inline resolvido | Dual-class ok | Notas |
|--------|------|----------------|----------------------------|---------------|-------|
| `tv-dashboard` | 7.1 | ✅ | — | ✅ | density `data-delpi-ui-density` + format-pane--compact |
| `tv-dashboard-presentation` | 7.1 | ✅ | — | ✅ | fill modifiers no kit (`--fill`) |
| `quality-action-plans` | 7.2 | ✅ | headers dual `PAC_SECTION` | ✅ | ghost/state/section/table → kit; domain leftovers OK |
| `controle-retrabalhos` | 7.2 | ✅ | — | ✅ | stack-safe margin no kit; sem `.cr-card:not` / state-box mirror |
| `minha-delpi-chat` | 7.3 | ✅ | ✅ Admin* domínio (`mdc-admin-*` KPI/table; `mdc-audit-*` paginação) — **path B** (não kit shell) | ✅ checkboxes/switch/toolbar via kit + tokens; `delpi-ui-native-switch--compact` no kit |
| `cadastro-kaizen` | 7.4 | ✅ | ghost dual `KZ_GHOST_BTN` | ✅ `dataTableBemClasses` | section-card só gap; chrome no kit |
| `auditoria-5s` | 7.4 | ✅ | hero/list → `createAnalyticsKpiCard`; paginação domínio `a5s-list-pagination` | ✅ filtersUi dual filter-box | analytics-kpi CSS no kit; list table/filters-card domínio |
| `maintenance` | 7.9 | ✅ | StateBox dual kit; KPI factory + atalhos via `NavigationCard` horizontal | ✅ | CSS `dm-shortcut-card*` removido; DataTable.css domínio; filter-kpi toggle dual |
| `transformometro` | 7.4 | ✅ | ghost dual `DS_GHOST_BTN` | ✅ `dataTableBemClasses` | print help-tooltip + table ghost compact no kit; tree tokens no host |
| `financeiro-inadimplencia` | 7.4 | ✅ | secondary `createSimpleKpiCard`; hero/ranking domínio `fi-kpi-hero*` | ✅ | sem dual-class parcial no hero |
| `inspecoes-processo` | 7.5 | ✅ | Empty dual `state-box--empty`; Pagination → CompactPagination (`hasNext` sintético) | ✅ | chrome ip-pagination/ip-empty removido |
| `strategic-indicators` | 7.5 | — | ✅ DataTable kit `si` | ✅ `dataTableBemClasses` | `DataTable.css` removido |
| `dashboard-*` (8) | 7.6 | ✅ | state/ghost chrome helpers; print sem `.delpi-ui-*` | ✅ | state-box/ghost dual; token `--delpi-ui-state-box-min-height`; print hide help-tooltip só no kit |
| `scrap-monitoring` | 7.6 | ✅ | Empty → `emptyStateCardBemClasses` | ✅ | Error via `createStateBoxPanel` dual no kit; CSS state-box removido |
| `production-appointments` | 7.6 | ✅ | ErrorState dual card+error | ✅ | Empty/Loading já dual; chrome state-box podado |
| `inspecoes-entrada` | 7.6 | ✅ | state Chrome + `filtersRowBemClasses` | ✅ | compact/positive no kit; table-wrap dual; alert domínio |
| `pedidos-venda-abertos` | 7.6 | ✅ | state + filtersUi dual | ✅ | ghost espelho `.pva-ghost-btn` removido; `pva-btn--ghost` domínio OK |
| `eficiencia-fabril` | 7.6 | ✅ | `EF_GHOST_BTN` + table-wrap dual | ✅ | `.ef-btn--ghost` chrome removido; paginação inline domínio |
| `propostas-comerciais` | 7.6 | ✅ | StateBoxPanel dual via kit | ✅ | CSS `.pc-state-box*` removido; table-wrap dual |
| `financeiro-centro-custo` | 7.6 | ✅ | Empty/Loading card dual; Error dual | ✅ | `.fcc-state*` removido; filtersUi já dual |
| `cipa` | 7.9 | ✅ | ✅ `PageHeader`, `SectionCard`, `ContentCard`, `DataTable`, estados, `NavigationCard`, `IconButton`, actions/forms | ✅ | CSS local reduzido a tokens, layout de página e domínio de ata/assinatura; zero seletor `.delpi-ui-*` |

### DoD de um plugin na Fase 7

- [ ] `index.css` (e CSS satélites) sem seletores `.delpi-ui-*` e sem BEM espelho de exports do kit
- [ ] Tokens `--delpi-ui-*` mapeados (+ dark)
- [ ] Layout de página apenas (`*-page-stack`, gap, grids de seção)
- [ ] Sem Pagination/DataTable/EmptyState/KPI markup local quando o kit cobre
- [ ] Smoke claro/escuro no portal; rebuild remote antes se o kit mudou

### Onda 7.4 — o que foi para o kit vs. leftovers de domínio

| Para o kit (`plugin-ui/src/styles/`) | Leftovers de domínio (OK no MFE) |
|-------------------------------------|----------------------------------|
| `@media print` hide help-tooltip | `a5s-list-pagination*` (badge de página) |
| `analytics-kpi.css` + dual `simpleKpiAnalyticsBemClasses` | `a5s-filters-card` / `a5s-table*` (listagem) |
| state-box `--inline` / `--success` / dismiss | `dm-shortcut-card*`, `dm-filter-kpi.is-active` |
| ghost `--active`; table ghost compact | `fi-kpi-hero*` (hero + ranking clicável) |
| section-card title/header densidades | `kz-section-card` só `margin-bottom` (gap) |
| | `tm-rich-tree*` + tokens de guia no host |

### Onda 7.5 — wrappers Pagination/Empty/DataTable

| Plugin | Kit | Leftover |
|--------|-----|----------|
| `inspecoes-processo` | CompactPagination + EmptyState dual; `disabled` no kit; `:has(> h3)` no empty | `ip-button` ghost local; layout de página |
| `strategic-indicators` | `DataTable` + `dataTableBemClasses("si")` | células admin (`si-admin-table-cell`) |

### Onda 7.6 — dashboard-* + P2

| Para o kit (`plugin-ui/src/styles/` + factories) | Leftovers de domínio (OK no MFE) |
|-------------------------------------------------|----------------------------------|
| `stateBoxBemClasses` dual (card + icon + `--error/--empty`) | Print layout dept. (`dc-print-*`, hide pagination/nav) |
| `stateBoxPlaceholderBemClasses` / `--compact` / `--positive` | `*-ghost-btn--sm` / `ef-btn--sm` (só tamanho) |
| Icon layout `state-box__icon` + h2 no painel | `ie-alert` / `pva-alert`; grids de página/KPI |
| (print help-tooltip já na 7.4) | `pva-btn--ghost` (shell de botão local, não espelho kit) |
| | Paginação inline EF; table th/td domínio onde não é DataTable kit |
| | Filter `--wide` / label layout; appointments table domínio |

---

Commits de referência (jul/2026): série `refactor(cadastro-kaizen): … via plugin-ui` até barrels `ui`/`data`/`form`/`detail`/`evidence` e limpeza de shims; docs Fase 7 (`docs(plugin-ui): proíbe CSS…`).
