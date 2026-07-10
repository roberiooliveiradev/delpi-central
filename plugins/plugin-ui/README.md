# `@delpi/plugin-ui`

Biblioteca de **componentes React reutilizáveis** para plugins MFE do monorepo Minha DELPI.

Centraliza primitivos de UI que hoje estão duplicados em dezenas de plugins (ex.: `HelpTooltip` em 14+ pastas). Textos em português permanecem em `content/helpTooltips.ts` de cada plugin — este pacote é **só interação, layout e acessibilidade**.

---

## Documentação

| Recurso | Descrição |
|---------|-----------|
| [docs/README.md](./docs/README.md) | Índice da documentação |
| [docs/architecture.md](./docs/architecture.md) | Estrutura, tokens CSS, integração Vite / MF |
| [docs/module-federation.md](./docs/module-federation.md) | **Remote runtime** — Docker, remotes, rollout |
| [docs/component-catalog.md](./docs/component-catalog.md) | API de cada export + exemplos |
| [docs/contributing.md](./docs/contributing.md) | Como adicionar componentes |
| [docs/migration-catalog.md](./docs/migration-catalog.md) | Plugins a migrar das cópias locais |
| [docs/export-catalog.md](./docs/export-catalog.md) | Formatos de exportação (CSV/XLSX/PDF) e fases E1–E4 |

---

## Quick start

### Module Federation (obrigatório — todo MFE)

Guia completo: **[docs/module-federation.md](./docs/module-federation.md)** · Checklist novo plugin: **[../../docs/05-plugin-system/novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md)**.

```ts
// vite.config.ts — helper plugins/vite/federation.shared.ts
remotes: pluginUiRemote(),
shared: { ...FEDERATION_SHARED_REACT },
```

```ts
// bootstrap.tsx
import { preparePluginUiRemote } from "../../vite/federationShareScope";
await preparePluginUiRemote();
```

Docker: subir `delpi-plugin-ui` antes do consumidor (`<<: *plugin-ui-federated` no compose).

### Bundled legado (descontinuado para plugin-ui)

#### 1. Alias no consumidor (Vite)

```ts
// plugins/meu-plugin/vite.config.ts
import path from "node:path";

resolve: {
  alias: {
    "@delpi/plugin-ui": path.resolve(__dirname, "../plugin-ui/src/index.ts"),
  },
  dedupe: ["react", "react-dom"],
},
```

#### 2. Estilos (uma vez)

```ts
// src/main.tsx — ajuste o caminho relativo
import "../../plugin-ui/src/styles.css";
import "./index.css";
```

#### 3. Tokens no root do dashboard

```css
.dashboard-meu-plugin {
  --delpi-ui-accent: var(--meu-accent, var(--primary, #089bdb));
  --delpi-ui-surface: var(--meu-surface, var(--surface, #fff));
  --delpi-ui-text: var(--meu-text, var(--text, #111));
  --delpi-ui-border: var(--meu-border, var(--border, #e5e7eb));
  --delpi-ui-muted: var(--meu-muted);
}
```

#### 4. Uso

```tsx
import { FieldLabel, HelpTooltip, HintAction, SectionHintLabel, TabHintCell } from "@delpi/plugin-ui";
import { MEU_HELP } from "./content/helpTooltips";

<FieldLabel htmlFor="periodo" label="Período" hint={MEU_HELP.fields.period} className="meu-field__label" />

<SectionHintLabel label="Filtros" hint={MEU_HELP.sections.filters} className="meu-ribbon__label" />
```

---

## Exports atuais

| Export | Função |
|--------|--------|
| `HelpTooltip` | Balão ? ou `wrap` em qualquer elemento |
| `FieldLabel` | Label de formulário + ajuda |
| `SectionHintLabel` | Rótulo de seção (ribbon) + ajuda |
| `TabHintCell` | Aba + ? sem botão aninhado |
| `HintAction` | Botão/controle com balão ao hover |
| `ChartCard` | Cartão de gráfico (layout headless + `classNames` BEM) |
| `chartCardBemClasses` | Helper para mapa BEM `{prefix}-chart-card__*` |
| `KpiCard` | Cartão KPI departamental (meta, badges IDD, ícone) |
| `kpiCardBemClasses` / `createDashboardKpiCard` | Helpers BEM + factory de wrapper |
| `LoadingActivityCard` | Spinner + barra de progresso de carregamento |
| `loadingActivityBemClasses` / `createDashboardLoadingActivityCard` | Helpers BEM + factory |
| `Pagination` / `TablePageSizeSelect` | Rodapé de tabela + seletor de page size |
| `paginationBemClasses` / `createDashboardPaginationKit` | Helpers BEM + factory |
| `buildVisiblePageItems` / `parsePageJumpInput` | Utils de paginação |
| `TABLE_PAGE_SIZE_OPTIONS` | Opções default de itens por página |
| `MultiSelectField` | Dropdown multiseleção com busca opcional |
| `createDashboardCreatableMultiSelectField` | Multi-select com opção de criar valores (ex.: categorias kaizen) |
| `multiSelectBemClasses` / `createDashboardMultiSelectField` | Helpers BEM + factory |
| `DateField` / `createDashboardDateField` | Input `type="date"` com label + hint |
| `dateFieldBemClasses` | Helper BEM para DateField |
| `buildMultiSelectTriggerLabel` | Label do trigger conforme seleção |
| `FiltersRow` / `FilterInputField` / `FilterSelectField` | Linha de filtros + campos input/select |
| `filtersRowBemClasses` / `createDashboardFiltersKit` | Helpers BEM + factory |
| `SimpleKpiCard` / `createKaizenKpiCard` | KPI estilo kaizen (`{prefix}-kpi--{tone}`) |
| `createAnalyticsKpiCard` | KPI `{prefix}-analytics-kpi` (auditoria-5s) |
| `simpleKpiKaizenBemClasses` / `simpleKpiKaizenToneClass` | BEM kaizen para KPI |
| `SectionCard` / `createDashboardSectionCard` | Seção estática com título + hint |
| `sectionCardKaizenBemClasses` / `sectionCardPacBemClasses` | BEM por plugin |
| `FormGrid` / `createDashboardFormGrid` | Grade de formulário (`{prefix}-form-grid`) |
| `FormActions` / `createDashboardFormActions` | Rodapé de ações de formulário |
| `createDashboardNativeFormFields` | Factory TextField/SelectField/TextAreaField/FormFieldShell |
| `formFieldShellKaizenClasses` | BEM shell kaizen (`kz-field`) |
| `StateBanner` / `createDashboardStateBanner` | Banner de estado (erro/sucesso/info) |
| `PageHeader` / `createDashboardPageHeader` | Cabeçalho de página (variantes brand/compact) |
| `ChartToolbar` / `ChartGranularityToggle` | Barra de gráfico + agrupamento |
| `chartToolbarBemClasses` / `createDashboardChartToolbarKit` | Helpers BEM + factory |
| `DetailFieldGrid` | Grade `<dl>` para fichas de detalhe |
| `detailFieldGridBemClasses` / `createDashboardDetailFieldGrid` | Helpers BEM + factory |
| `EditableSectionCard` | Seção editável (read/edit + ações) |
| `editableSectionCardBemClasses` / `createDashboardEditableSectionCard` | Helpers BEM + factory |
| `ReadOnlyField` | Campo somente leitura (kaizen/PAC) |
| `readOnlyFieldKaizenBemClasses` / `createDashboardReadOnlyField` | Helpers BEM + factory |
| `SelectField` / `SelectControl` | Dropdown single-select |
| `selectControlBemClasses` / `createDashboardSelectField` | Helpers BEM + factory |
| `CHART_COLORS_*` / `CHART_HEIGHT_DEFAULT` | Paletas de gráfico compartilhadas |
| `goalDisplay` / `operationalUnitLabels` | Meta IDD e filiais TOTVS |
| `DataTable` / `DataTableSection` | Tabela + seção com busca/paginação |
| `dataTableBemClasses` / `createDashboardDataTableKit` | Helpers BEM + factory |

Detalhes: [component-catalog.md](./docs/component-catalog.md).

---

## Estrutura do pacote

```text
src/
├── index.ts              # barrel público
├── styles.css            # classes delpi-ui-*
└── components/
    ├── help/             # balões explicativos
    ├── layout/           # ChartCard, KpiCard, FiltersRow, DetailFieldGrid
    ├── feedback/         # LoadingActivityCard
    ├── data/             # Pagination, TablePageSizeSelect
    └── forms/            # MultiSelectField, ReadOnlyField, SelectField
└── utils/
    └── paginationPages.ts
```

---

## Consumidores

| Plugin | Status |
|--------|--------|
| `tv-dashboard` | ✅ Integrado (referência) |
| `dashboard-commercial` | ✅ Fase 1 |
| `dashboard-engineering` | ✅ Fase 1 |
| `dashboard-financial` | ✅ Fase 1 |
| `dashboard-hr` | ✅ Fase 1 |
| `dashboard-lmps` | ✅ Fase 1 |
| `dashboard-production` | ✅ Fase 1 |
| `dashboard-quality` | ✅ Fase 1 |
| `dashboard-supplies` | ✅ Fase 1 |
| `cadastro-kaizen` | ✅ F1 + F2/F3 | Migração UI completa — [UI-PLUGIN-UI.md](../cadastro-kaizen/docs/UI-PLUGIN-UI.md) |
| `transformometro` | ✅ Fase 1 |
| `quality-action-plans` | ✅ Fase 1 |
| `eficiencia-fabril` | ✅ Fase 1 |
| `maintenance` | ✅ Fase 1 |
| `portal` | ❌ Fora de escopo (shell) |

Demais plugins — ver [migration-catalog.md](./docs/migration-catalog.md).

---

## Desenvolvimento

```bash
cd plugins/plugin-ui
npm install
npm test
```

Build do consumidor (valida resolução do alias):

```bash
cd plugins/tv-dashboard
npm run build
```

---

## Relacionados

| Pacote / doc | Papel |
|--------------|-------|
| `@delpi/tv-dashboard-presentation` | Motor de apresentação TV (domínio) |
| [docs/08-plugins/README.md](../../docs/08-plugins/README.md) | Inventário de plugins |
| [plugins-visual-design-system.mdc](../../.cursor/rules/plugins-visual-design-system.mdc) | Tokens e escopo CSS dos MFEs |
| [plugins-reusable-components.mdc](../../.cursor/rules/plugins-reusable-components.mdc) | **Diretriz Cursor:** plugins devem usar este pacote |

---

## Changelog

Ver [CHANGELOG.md](./CHANGELOG.md).
