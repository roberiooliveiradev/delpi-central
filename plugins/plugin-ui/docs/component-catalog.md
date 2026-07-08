# Catálogo de componentes

Exports públicos de `@delpi/plugin-ui`. Import único.

Exportação tabular (CSV / Excel / PDF DELPI) e botões (`TabularExportButtons`, `DocumentExportActions`, `ExcelExportButton`): ver [export-catalog.md](./export-catalog.md).

Imports:

```ts
import { HelpTooltip, FieldLabel, TabHintCell } from "@delpi/plugin-ui";
```

---

## Família `help` — balões explicativos

Textos em português vêm do **plugin consumidor** (`content/helpTooltips.ts`). Este pacote só fornece interação e acessibilidade.

### `HelpTooltip`

Balão ao passar o mouse ou focar. Ícone **?** por padrão; modo `wrap` envolve filho arbitrário.

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `content` | `string` | — | Texto do balão (obrigatório) |
| `ariaLabel` | `string` | `"Saiba mais"` | Rótulo acessível do gatilho |
| `wrap` | `boolean` | `false` | Se `true`, filhos são o gatilho (sem botão ?) |
| `placement` | `"top" \| "bottom"` | `"top"` | Preferência; inverte se não couber na viewport |
| `className` | `string` | — | Classe no root |

```tsx
<HelpTooltip content="Explicação curta." ariaLabel="Ajuda: campo X" />

<HelpTooltip content="Abre ao passar no botão." wrap placement="bottom" ariaLabel="Ajuda: salvar">
  <button type="button" className="meu-btn">Salvar</button>
</HelpTooltip>
```

**Não** aninhe `<button>` dentro de `<button>`. Para abas, use `TabHintCell`.

---

### `FieldLabel`

Rótulo de formulário com **?** opcional. Usa `<label htmlFor>` quando `htmlFor` é passado.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `label` | `string` | Texto visível |
| `hint` | `string?` | Conteúdo do balão |
| `htmlFor` | `string?` | Associa ao input |
| `className` | `string` | Default: `delpi-ui-field-label` |

```tsx
<FieldLabel htmlFor="periodo" label="Período (dias)" hint={H.fields.period} className="td-field__label" />
```

---

### `SectionHintLabel`

Rótulo de seção (ribbon, painel) com balão no hover. Equivalente a `HelpTooltip` + `wrap` em um `<span>`.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `label` | `string` | Texto da seção |
| `hint` | `string` | Explicação |
| `className` | `string?` | Classe do span (ex.: `td-deck-ribbon__label`) |

```tsx
<SectionHintLabel label="Inserir" hint={H.ribbon.insert} className="td-deck-ribbon__label" />
```

---

### `TabHintCell`

Aba acessível (`role="tab"`) + ícone **?** como **irmão** (evita HTML inválido).

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `label` | `string` | — | Texto da aba |
| `hint` | `string` | — | Balão da aba |
| `icon` | `LucideIcon?` | — | Ícone à esquerda do label |
| `active` | `boolean` | `false` | Estado selecionado |
| `disabled` | `boolean` | `false` | Desabilita a aba |
| `onSelect` | `() => void` | — | Clique na aba |
| `cellClassName` | `string` | `delpi-ui-tab-cell` | Wrapper |
| `tabClassName` | `string` | `delpi-ui-tab` | Botão da aba |
| `tabActiveClassName` | `string` | `delpi-ui-tab--active` | Classe quando ativa |
| `hintPlacement` | `"top" \| "bottom"` | `"bottom"` | Posição do balão |
| `children` | `ReactNode?` | — | Substitui ícone+label padrão |

```tsx
<TabHintCell
  label="Programação"
  hint={H.tabs.playlist}
  icon={Settings2}
  active={tab === "playlist"}
  onSelect={() => setTab("playlist")}
  tabClassName="td-deck-tabs__tab"
  tabActiveClassName="td-deck-tabs__tab--active"
  cellClassName="td-deck-tabs__tab-cell"
/>
```

---

### `HintAction`

Atalho para `HelpTooltip` com `wrap` em um único filho (botão, input color, etc.).

| Prop | Tipo | Default |
|------|------|---------|
| `hint` | `string` | — |
| `ariaLabel` | `string` | — |
| `placement` | `"top" \| "bottom"` | `"bottom"` |
| `children` | `ReactElement` | — |

```tsx
<HintAction hint={H.ribbon.duplicate} ariaLabel="Ajuda: Duplicar">
  <button type="button" className="td-btn td-btn--sm" onClick={onDuplicate}>
    <Copy size={15} /> Duplicar
  </button>
</HintAction>
```

---

## Família `layout` — cartões de painel

### `ChartCard`

Cartão de gráfico com título, hint opcional, ações no header e corpo para o chart. **Estilos visuais ficam no plugin** via `classNames` BEM; o pacote só monta a estrutura e a11y.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `title` | `string` | Título da região |
| `titleHint` | `string?` | Balão no título |
| `hint` | `string?` | Subtítulo abaixo do título |
| `children` | `ReactNode` | Conteúdo (chart) |
| `headerActions` | `ReactNode?` | Toolbar à direita (ex.: export) |
| `classNames` | `ChartCardClassNames` | Classes BEM do plugin |
| `className` | `string?` | Extra no `<section>` |
| `titleLevel` | `2 \| 3` | Nível do heading (default `2`) |

Helper `chartCardBemClasses(prefix, options?)` gera o mapa BEM padrão `{prefix}-chart-card__*`.

```tsx
import { ChartCard, chartCardBemClasses } from "@delpi/plugin-ui";

const classNames = chartCardBemClasses("dp", { withHeading: false, withActions: false });

<ChartCard title="OEE" titleHint={H.charts.oee} classNames={classNames}>
  <ResponsiveContainer>...</ResponsiveContainer>
</ChartCard>
```

**Padrão nos dashboards:** wrapper fino local reexporta `ChartCard` com `classNames` fixo do prefixo do plugin.

### `KpiCard`

Cartão KPI departamental com valor, meta, badges IDD e ícone. Textos fixos (`Meta`, `Nota IDD`, aria de badges) vêm do plugin via `labels`.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `title` / `titleHint` | `string` | Rótulo e balão |
| `value` | `string` | Valor principal |
| `valueVariant` | `"default" \| "per-unit"` | Modificador CSS do valor |
| `goalLabel` / badges | ver tipos `KpiScopeBadge`, `KpiPerformanceBadge` | Metas e IDD |
| `icon` | `ReactNode` | Ícone à direita |
| `footer` | `ReactNode?` | Slot inferior |
| `loading` | `boolean?` | Placeholder `…` |
| `classNames` | `KpiCardClassNames` | BEM do plugin |
| `labels` | `KpiCardLabels` | Textos PT do plugin |

Helpers: `kpiCardBemClasses(prefix)` e `createDashboardKpiCard({ prefix, labels })` para wrapper de uma linha nos dashboards.

### `LoadingActivityCard`

Feedback de carregamento com spinner, barra de progresso (determinada ou indeterminada) e variantes `compact` / `panel`.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `title` / `description` | `string` | Textos do plugin |
| `variant` | `"compact" \| "panel"` | Densidade |
| `tone` | `"neutral" \| "info"` | Estilo |
| `sticky` | `boolean?` | Default: `true` quando `compact` |
| `progressPercent` | `number?` | 0–100 para barra determinada |
| `classNames` | `LoadingActivityCardClassNames` | BEM do plugin |
| `labels` | `LoadingActivityCardLabels` | Textos PT (progresso restante, aria) |

Helpers: `loadingActivityBemClasses(prefix, { withCopyWrapper? })` e `createDashboardLoadingActivityCard`.

### `Pagination` + `TablePageSizeSelect`

Rodapé de tabela com navegação, páginas visíveis (reticências), «Ir para» e seletor de itens por página.

| Prop / export | Tipo | Descrição |
|---------------|------|-----------|
| `page` / `totalPages` / `total` | `number` | Estado da paginação |
| `onPageChange` | `(page: number) => void` | Callback de página |
| `classNames` | `PaginationClassNames` | BEM do plugin |
| `labels` | `PaginationLabels` | Textos PT (Anterior, Próxima, info, erros de jump) |
| `hints` | `PaginationHints?` | Conteúdo dos `HelpTooltip` |
| `TABLE_PAGE_SIZE_OPTIONS` | `readonly number[]` | Opções default `[10, 25, 50, 100]` |

Utils: `buildVisiblePageItems`, `parsePageJumpInput` em `src/utils/paginationPages.ts`.

Helpers: `paginationBemClasses(prefix)` e `createDashboardPaginationKit({ prefix, labels, hints, tablePageSizeLabels })` — wrapper fino nos dashboards (~50 linhas) com textos de `helpTooltips.pagination`.

### `MultiSelectField`

Dropdown multiseleção com busca opcional, ações «Marcar visíveis» / «Limpar» e label via `FieldLabel`.

| Prop / export | Tipo | Descrição |
|---------------|------|-----------|
| `options` / `selectedValues` | `MultiSelectOption[]` / `string[]` | Opções e seleção |
| `onChange` | `(values: string[]) => void` | Callback |
| `searchable` / `disabled` | `boolean?` | Comportamento |
| `classNames` | `MultiSelectFieldClassNames` | BEM do plugin |
| `labels` | `MultiSelectFieldLabels` | Textos PT (Todos, Buscar…, ações) |

Utils: `buildMultiSelectTriggerLabel` em `src/utils/multiSelectLabel.ts`.

Helpers: `multiSelectBemClasses(prefix)` e `createDashboardMultiSelectField({ prefix, labels })`.

### `FiltersRow` / `FilterInputField` / `FilterSelectField` (FilterBar)

Shell da linha de filtros (`{prefix}-filters-row`) e campos label+controle reutilizáveis.

| Export | Descrição |
|--------|-----------|
| `FiltersRow` | `<section>` com `aria-label`, variante `extended`, slot `trailing` |
| `FilterInputField` | Label + `FieldLabel` + input (`month`/`date`/`text`/`search`) |
| `FilterSelectField` | Label + `<select>` com `placeholderOption` opcional |
| `FilterBar` | Alias de `FiltersRow` (roadmap F2.6) |

Helpers: `filtersRowBemClasses(prefix)` e `createDashboardFiltersKit({ prefix, labels })` — retorna `FiltersRow`, `FilterInputField` e `FilterSelectField`.

### `SimpleKpiCard` / `createKaizenKpiCard` / `createAnalyticsKpiCard`

Cartão KPI compacto com ícone. Variante kaizen usa BEM `{prefix}-kpi`; analytics usa `{prefix}-analytics-kpi` (rótulo `__label`, hint `__hint`).

| Export | Descrição |
|--------|-----------|
| `SimpleKpiCard` | Layout iconStart/iconEnd headless |
| `createKaizenKpiCard(prefix)` | Wrapper kaizen: `tone`, `label`, `value`, `sub`, `icon` |
| `createAnalyticsKpiCard(prefix)` | Wrapper analytics: `title`, `value`, `subtitle`, `variant`, `icon` |
| `simpleKpiKaizenBemClasses` | Mapa BEM `{prefix}-kpi__*` |
| `simpleKpiKaizenToneClass` | Classe modificadora de tom |
| `simpleKpiAnalyticsBemClasses` | Mapa BEM `{prefix}-analytics-kpi__*` |

### `SectionCard`

Seção estática com header (título, hint, subtítulo) — sem modo edição.

Helpers: `sectionCardKaizenBemClasses`, `sectionCardPacBemClasses`, `createDashboardSectionCard({ classNames, labels })`.

### `FormGrid` / `FormActions`

Grade CSS grid para formulários e rodapé de botões.

Helpers: `createDashboardFormGrid({ classNames })`, `createDashboardFormActions({ classNames })`.

### `NativeFormFields` (`createDashboardNativeFormFields`)

Campos nativos label+controle para plugins que estilizam `<input>`/`<select>`/`<textarea>` diretamente (ex.: kaizen `kz-field`).

| Export | Descrição |
|--------|-----------|
| `TextField` / `SelectField` / `TextAreaField` | Campo com `FormFieldShell` (`type`: `text` \| `date` \| `datetime-local` \| `number`; `afterControl`; `onBlur` / `readOnly` / `max` / `autoFocus`) |
| `FormFieldShell` | Label + hint + slot children + `afterControl` opcional |
| `formFieldShellKaizenClasses` | BEM `{prefix}-field`, `{prefix}-span-2` |

### `StateBanner` / `PageHeader`

Feedback inline (`createDashboardStateBanner`) e cabeçalho de página com slots (`createDashboardPageHeader` — variantes brand/compact documentadas no código).

### `ChartToolbar` + `ChartGranularityToggle`

Barra de gráfico com toggle de agrupamento (segment), export CSV opcional e slots `extra` / `exportActions`.

| Export | Descrição |
|--------|-----------|
| `ChartGranularityToggle` | Botões Dia/Semana/Mês/Ano (`{prefix}-segment-toggle`) |
| `ChartToolbar` | Layout toolbar + ações; suporta hints e `granularityField` (lmps) |

Helpers: `chartToolbarBemClasses(prefix)` e `createDashboardChartToolbarKit({ prefix, labels })`.

### `DataTable` + `DataTableSection`

Tabela genérica com sort, empty/loading e seção completa (busca, page size, paginação, loading cards).

| Export | Descrição |
|--------|-----------|
| `DataTable` | `<table>` responsiva com colunas declarativas |
| `DataTableSection` | Card + toolbar + tabela + paginação |
| `useClientPagination` | Hook de paginação client-side |
| `buildDataTableSearchText` | Haystack para filtro local |

Helpers: `dataTableBemClasses`, `dataTableSectionBemClasses`, `createDashboardDataTableKit`.

### `DetailFieldGrid`

Grade de detalhe (`<dl>`) para fichas operacionais — rótulos, valores, hint opcional e coluna wide.

| Export | Descrição |
|--------|-----------|
| `DetailFieldGrid` | Lista de campos `{ label, value, hint?, wide? }` |
| `DetailField` | Tipo de item da grade |

Helpers: `detailFieldGridBemClasses(prefix)` e `createDashboardDetailFieldGrid({ prefix, labels, valueFallback?, wrapLabels? })`.

Opções do factory:
- `labels.emptyMessage` — exibe parágrafo vazio quando `fields.length === 0` (omitir em production)
- `valueFallback` — texto para valores `null`/`undefined` (ex.: `"—"`)
- `wrapLabels` — envolve rótulos em `<span className="{prefix}-detail-grid__label">` (commercial, lmps)

### `EditableSectionCard`

Seção editável com header (título, hint, ações Editar/Salvar/Cancelar) e conteúdo read/edit.

| Export | Descrição |
|--------|-----------|
| `EditableSectionCard` | Card de seção com toggle leitura/edição |
| `editableSectionCardBemClasses` | BEM kaizen-style (`{prefix}-section-card`) |
| `editableSectionCardTransformometroClasses` | BEM transformometro (`{prefix}-editable-section`) |

Helper: `createDashboardEditableSectionCard({ classNames, labels })`.

### `ReadOnlyField`

Campo somente leitura — modos kaizen (`HelpTooltip` + span) e PAC (`FieldLabel` + ficha/field).

Helpers: `readOnlyFieldKaizenBemClasses`, `readOnlyFieldPacBemClasses`, `createDashboardReadOnlyField`.

### `SelectField` + `SelectControl`

Dropdown single-select com busca opcional. `SelectControl` é o trigger/painel reutilizável (ex.: diagram toolbar).

Helpers: `selectControlBemClasses`, `selectFieldPacClasses`, `selectFieldTransformometroClasses`, `createDashboardSelectField`, `createDashboardSelectControl`.

---

## Estilos base (`styles.css`)

| Classe | Uso |
|--------|-----|
| `delpi-ui-help-tooltip` | Root do tooltip |
| `delpi-ui-help-tooltip__trigger` | Botão ? |
| `delpi-ui-help-tooltip__bubble` | Balão (portal) |
| `delpi-ui-field-label` | Layout label + ? |
| `delpi-ui-tab-cell` | Wrapper aba + ? |
| `delpi-ui-tab` / `delpi-ui-tab--active` | Aba default (override via props) |

Consumidores podem **só** passar `className` nas props sem usar as classes default de aba.

---

## Família `forms` — Lucide icon picker

### `LucideIconPicker`

Painel centralizado para escolher ícones Lucide (lista curada por padrão). Valor em **kebab-case** (ex.: `eye`).

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `value` | `string \| null` | — | Ícone atual (kebab ou Pascal) |
| `onChange` | `(icon: string \| null) => void` | — | `null` remove |
| `onClose` | `() => void` | — | Fecha (botão / após escolher) |
| `curatedOnly` | `boolean` | `true` | Só catálogo de negócio (~50) |
| `maxResults` | `number` | `360` | Limite na lista completa |
| `labels` | `LucideIconPickerLabels` | PT-BR | Textos do painel |

### `LucideIconByName`

Renderiza um ícone Lucide pelo nome.

```ts
import { LucideIconPicker, LucideIconByName } from "@delpi/plugin-ui";
```

Helpers: `resolveLucideIcon`, `CURATED_LUCIDE_ICON_NAMES`, `toKebabCase`, `toPascalCaseFromKebab`.

---

## Consumidores atuais

| Plugin | Componentes usados |
|--------|-------------------|
| `tv-dashboard` | Todos os exports `help` |
| `dashboard-production` | `HelpTooltip`, `FieldLabel` |
| `dashboard-commercial` | `HelpTooltip`, `FieldLabel` |
| `dashboard-engineering` | `HelpTooltip`, `FieldLabel` |
| `customer-experience` | `LucideIconPicker`, `LucideIconByName` |
| `public-hub` | `LucideIconByName` |

Ver [migration-catalog.md](./migration-catalog.md) para plugins pendentes.
