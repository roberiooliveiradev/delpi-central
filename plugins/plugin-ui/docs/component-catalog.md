# Catálogo de componentes

Exports públicos de `@delpi/plugin-ui`. Import único.

**Prévia visual (app):** no portal, rota `/apps/plugin-ui` (permissão `plugin-ui.view`) — expose `./App`. Em desenvolvimento: `cd plugins/plugin-ui && npm run dev` (porta 5010).

O app cobre **todos** os componentes React visuais listados em `src/catalog/visualComponents.ts` (teste de cobertura em `componentRegistry.test.ts`). Demos interativas vivem em `src/catalog/demos/`; o que ainda não tem fixture completa aparece como **stub** com nota.

**Metadados:** cada entrada no inventário declara `addedAt` (e opcionalmente `updatedAt` / `changeNote`). O catálogo mostra badges Novo/Atualizado, filtros Recentes/Atualizados e datas no painel de detalhe. Regra de contribuição: [contributing.md](./contributing.md) § Metadados.

| Família | Exemplos no catálogo |
|---------|----------------------|
| help | HelpTooltip, KeyTip, FieldLabel, TabHintCell… |
| layout | PageHeader, KpiCard, DelpiKpiCard, ChartCard… |
| feedback | EmptyState, ModalShell, DrawerShell… |
| forms | SelectField, DateField, MultiSelectField… |
| **data** | **DataTable**, **DataTableSection**, CompactPagination, ConfigurablePresentationTable… |
| export | TabularExportButtons, DocumentExportActions… |
| charts | ConfigurableSeriesChart, ImpactEffortMatrix, ChartTypeCatalogPanel… |
| preview / diagram / shape / menu | prévias + stubs onde falta fixture |

Tabela estilo **dashboard LMPS**: use a entrada `DataTable` / `DataTableSection` (não a ConfigurablePresentationTable do TV/deck).

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

### `KeyTip`

Balão de atalho (KeyTips Office / Alt+Ctrl). Portal no `body`, flip na viewport, setinha de balão.

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `label` | `ReactNode` | — | Texto do balão (`Ctrl+Z`, `P`, …) |
| `active` | `boolean` | — | Controla visibilidade |
| `placement` | `"top" \| "bottom"` | `"top"` | Preferência; inverte se não couber |
| `offsetX` | `number` | `0` | Desloca no eixo X (evitar sobreposição) |
| `variant` | `"shortcut" \| "letter"` | `"shortcut"` | Letra única mais compacta |
| `portalScopeClassName` | `string?` | — | Escopo MFE (ex.: `dashboard-tv-dashboard`) |

```tsx
<KeyTip label="Ctrl+Z" active={altTipsActive} placement="bottom">
  <button type="button">Desfazer</button>
</KeyTip>

<KeyTip label="P" active={showTabTips} variant="letter" data-td-keytip="P">
  <button type="button" role="tab">Página Inicial</button>
</KeyTip>
```

O consumidor decide **quando** ativar (Alt toggle, tecla F, etc.).

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

### `StatusBadge`

Pill semântico de status (`neutral` | `info` | `success` | `warning` | `danger`). Estilos no plugin via BEM `{prefix}-status-badge--*`.

Helpers: `statusBadgeBemClasses(prefix)`, `createDashboardStatusBadge({ prefix })`.

Consumidor piloto: `strategic-indicators` (`StatusBadge.tsx`).

---

## Família `diagram` — editor de fluxograma BPMN / swimlanes

Editor React Flow headless com faixas, paleta BPMN, import/export Mermaid e exportação PNG. **Textos PT-BR** vêm do plugin via `FlowchartEditorLabels` — o pacote não hardcodeia rótulos.

Peer opcionais: `@xyflow/react`, `mermaid`, `html-to-image`.

Importar estilos: `import "@delpi/plugin-ui/styles.css"` (inclui `diagram.css`).

### `FlowchartEditor`

Componente principal (requer `ReactFlowProvider` interno). Props principais:

| Prop | Tipo | Descrição |
|------|------|-----------|
| `value` / `onChange` | `FlowchartV1` | Estado do diagrama |
| `labels` | `FlowchartEditorLabels` | Textos e aria labels (obrigatório) |
| `readOnly` | `boolean?` | Modo somente leitura |
| `confirm` | `ConfirmDialogOptions?` | Diálogos de confirmação (ex.: remover faixa) |
| `colorMode` | `"light" \| "dark"?` | Tema Mermaid / canvas |
| `shellClassName` | `string?` | Classe do dashboard para tokens CSS (ex.: `dashboard-transformometro`) |

Ref: `FlowchartEditorHandle` (`fitView`, `exportPng`, etc.).

### Subcomponentes e utilitários

| Export | Uso |
|--------|-----|
| `DiagramMermaidPreview` | Prévia Mermaid read-only |
| `DiagramFullscreenFrame` | Shell fullscreen |
| `DiagramLayoutProvider` / `useDiagramEditorLayout` | Layout fill vs. embedded |
| `flowchartToMermaid` / `mermaidToFlowchart` | Conversão bidirecional |
| `exportReactFlowDiagramPng` | Export PNG com faixas |
| `getDiagramFitNodes` / `getDiagramExportNodes` | Fit view e bounds de export |
| `emptyFlowchart`, templates, catálogo BPMN | Tipos e helpers em `./types/diagram` |

Classes shell: `flowchartEditorShellClassName()`, `FLOWCHART_EDITOR_ROOT_CLASS` (`tm-diagram-editor`). Alias de escopo: `.delpi-ui-flowchart-shell, .dashboard-transformometro`.

### Padrão de integração no plugin

Wrapper fino injeta labels, confirm e tema:

```tsx
// transformometro/src/components/diagram/TransformometroFlowchartEditor.tsx
import { FlowchartEditor as BaseFlowchartEditor } from "@delpi/plugin-ui";
import { TRANSFORMOMETRO_FLOWCHART_EDITOR_LABELS } from "../../content/flowchartEditorLabels";

<BaseFlowchartEditor
  labels={TRANSFORMOMETRO_FLOWCHART_EDITOR_LABELS}
  confirm={confirm}
  colorMode={isDark ? "dark" : "light"}
  shellClassName="dashboard-transformometro"
  {...props}
/>
```

Consumidor piloto: `transformometro` (Processo, Revisão, Instância).

---

### `SectionBlock`

Seção com cabeçalho (título, descrição, slot `aside`) e corpo. Útil em dashboards e painéis admin.

Helpers: `sectionBlockBemClasses(prefix)`, `createDashboardSectionBlock({ prefix })`.

Consumidor piloto: `strategic-indicators` (`SectionBlock.tsx`).

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

Estilos canônicos das ações do painel (`Marcar visíveis` / `Limpar`): `delpi-ui-multi-select__*` em `styles/multi-select.css` (não usar `{prefix}-ghost-btn` nas actions — o ghost de toolbar sobrescreve densidade).

### `FiltersRow` / `FilterInputField` / `FilterSelectField` (FilterBar)

Shell da linha de filtros (`{prefix}-filters-row`) e campos label+controle reutilizáveis.

| Export | Descrição |
|--------|-----------|
| `FiltersRow` | `<section>` com `aria-label`, variante `extended`, slot `trailing` |
| `FilterInputField` | Label + `FieldLabel` + input (`month`/`date`/`text`/`search`) |
| `FilterSelectField` | Label + `SelectControl` (painel portado; escopo `.dashboard-*` automático ou `portalScopeClassName`) |
| `FilterBar` | Alias de `FiltersRow` (roadmap F2.6) |

Helpers: `filtersRowBemClasses(prefix)` e `createDashboardFiltersKit({ prefix, labels, portalScopeClassName? })` — retorna `FiltersRow`, `FilterInputField` e `FilterSelectField`.

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

### `TableColumnVisibilityMenu`

Menu da toolbar de tabela para exibir/ocultar colunas (checkboxes). Tokens `--delpi-ui-*` — funciona em claro e escuro.

| Prop | Descrição |
|------|-----------|
| `columns` | `{ key, label }[]` |
| `visibility` | `Record<string, boolean>` |
| `onToggleColumn` / `onReset` | Callbacks |
| `labels` | Textos PT (`trigger`, `panelTitle`, `reset`, `hint`, `columnAriaLabel`) |
| `keepAtLeastOne` | Impede desmarcar a última coluna (default `true`) |

CSS: `styles/table-column-visibility.css`. Consumidor: `pedidos-venda-abertos` (`TableColumnSettings` fino).

### `TreeGuideRails`

Trilhos pontilhados suaves para árvores hierárquicas (estilo explorador de arquivos). Tokens `--delpi-ui-tree-guide-*` / `--delpi-ui-border`.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `depth` | `number` | Profundidade do nó (`0` = raiz, sem guias) |
| `isLastSiblingPath` | `boolean[]` | Por nível ancestral: `true` se aquele nó era o último irmão |
| `className` | `string?` | Classe extra no root |

```tsx
<TreeGuideRails depth={2} isLastSiblingPath={[false, true]} />
```

CSS: `styles/tree-guides.css`. Consumidores: `transformometro` (WBS), `minha-delpi-chat` (árvore de apresentação).

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

**Toolbar compacto:** `ToolbarSelectField` + `ToolbarSelectControl` — rótulo inline + densidade reduzida (`delpi-ui-toolbar-select*` em `styles.css`). Helpers: `selectControlToolbarBemClasses`, `DEFAULT_TOOLBAR_SELECT_LABELS`.

Helpers: `selectControlBemClasses`, `selectFieldPacClasses`, `selectFieldTransformometroClasses`, `createDashboardSelectField`, `createDashboardSelectControl`.

### `ComboboxNumberControl`

Input + lista de presets (escolher ou digitar). Confirma no blur/Enter; seleção na lista aplica na hora. CSS: `styles/combobox-number.css` (`.delpi-ui-combobox-number*`). Use `square` / `compact` na ribbon.

```tsx
<ComboboxNumberControl
  value={fontSize}
  options={[12, 14, 16, 18, 24]}
  clamp={(n) => Math.min(120, Math.max(12, Math.round(n)))}
  aria-label="Tamanho da fonte"
  portalScopeClassName="dashboard-tv-dashboard"
  onChange={setFontSize}
/>
```

### `RangeField`

Campo contínuo canônico: rótulo + slider + input numérico abaixo (digitar). Aceita `displayValue` com `%`/vírgula; valores negativos ficam em tom vermelho no texto e no slider (`.delpi-ui-range-field--negative`). CSS: `styles/range-field.css` (`.delpi-ui-range-field*`).

```tsx
<RangeField
  id="alt-px"
  label="Alt. px"
  value={height}
  min={1}
  max={1080}
  onChange={setHeight}
/>
```

Helper: `parseRangeFieldNumber`. Constante: `RANGE_FIELD_CLASS`.

---

## Estilos base (`styles.css`)

Inclui CSS compartilhados importados em `src/styles/`:

| Arquivo | Escopo |
|---------|--------|
| `select-control.css` / `multi-select.css` | `.delpi-ui-select*` / `.delpi-ui-multi-select*` (Onda 2 — shell canônico; MFE só tokens) |
| `data-table.css` | `DataTable` / `DataTableSection` — `.delpi-ui-table*` / toolbar / search / `data-align` |
| `pagination.css` | `Pagination` / Compact / Nav — `.delpi-ui-pagination*` + `.delpi-ui-ghost-btn` |
| `detail-card.css` | `DetailCard` / `DetailFieldGrid` — `.delpi-ui-detail-card*` / grid (`dt`/`dd`) |

MFEs: definir `--delpi-ui-*` no escopo `.dashboard-*` e **não** reimplementar layout de tabela/paginação/detalhe (Onda 1) nem shell MultiSelect/Select (Onda 2). Chart/KPI/Loading/Filters: Onda 3.

| Classe | Uso |
|--------|-----|
| `delpi-ui-help-tooltip` | Root do tooltip |
| `delpi-ui-help-tooltip__trigger` | Botão ? |
| `delpi-ui-help-tooltip__bubble` | Balão (portal) |
| `delpi-ui-keytip` | Balão KeyTip (atalho) |
| `delpi-ui-keytip--letter` | Variante letra única (F) |
| `delpi-ui-keytip-anchor` | Âncora do KeyTip |
| `delpi-ui-field-label` | Layout label + ? |
| `delpi-ui-tab-cell` | Wrapper aba + ? |
| `delpi-ui-tab` / `delpi-ui-tab--active` | Aba default (override via props) |

Consumidores podem **só** passar `className` nas props sem usar as classes default de aba.

---

## Família `forms` — Lucide icon picker

### `LucideIconPicker`

Painel centralizado para escolher ícones Lucide com **seções** e busca no catálogo completo. Valor em **kebab-case** (ex.: `eye`).

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `value` | `string \| null` | — | Ícone atual (kebab ou Pascal) |
| `onChange` | `(icon: string \| null) => void` | — | `null` remove |
| `onClose` | `() => void` | — | Fecha (botão / após escolher) |
| `curatedOnly` | `boolean` | `false` | Se `true`, busca só no catálogo curado |
| `maxResults` | `number` | `480` | Limite de matches na busca completa |
| `labels` | `LucideIconPickerLabels` | PT-BR | Textos do painel |

Tokens: `--delpi-ui-surface`, `--delpi-ui-text`, `--delpi-ui-border`, `--delpi-ui-muted`, `--delpi-ui-accent` (claro/escuro via tema do plugin).

Helpers: `resolveLucideIcon`, `groupLucideIconsBySection`, `LUCIDE_ICON_SECTIONS`, `CURATED_LUCIDE_ICON_NAMES`, `listLucideIconNames`.

### `LucideIconByName`

Renderiza um ícone Lucide pelo nome.

```ts
import { LucideIconPicker, LucideIconByName } from "@delpi/plugin-ui";
```

---

## Família `charts` — matriz impacto × esforço

Scatter SVG headless para priorização de revisões (Playbook 21 Transformômetro). **Cálculo na API** — o MFE só passa pontos já normalizados.

### `ImpactEffortMatrix`

| Prop | Tipo | Default | Descrição |
|------|------|---------|-----------|
| `points` | `ImpactEffortPoint[]` | — | Coordenadas 0–100 + metadados |
| `activePointId` | `string \| null` | — | Destaque + rótulo |
| `threshold` | `number` | `50` | Divisor dos quadrantes |
| `onPointSelect` | `(point) => void` | — | Clique/teclado em ponto interativo |
| `quadrantLabels` | `ImpactEffortQuadrantLabels` | PT-BR default | Rótulos dos quadrantes |
| `axisLabels` | `ImpactEffortAxisLabels` | Impacto / Esforço | Eixos |
| `classNames` | `ImpactEffortMatrixClassNames` | `delpi-ui-impact-effort-matrix__*` | BEM override |
| `emptyMessage` | `string` | — | Sem pontos visíveis |

Tipos: `ImpactEffortPoint`, `ImpactEffortQuadrant`, `ImpactEffortConfidence`, `ImpactEffortMatrixMode`.

Helpers: `resolveImpactEffortQuadrant`, `clampImpactEffortScore`, `impactEffortMatrixBemClasses`, `impactEffortMatrixTransformometroClasses`.

### `ImpactEffortMatrixLegend`

Lista horizontal dos quatro quadrantes (swatch + rótulo).

```tsx
import {
  ImpactEffortMatrix,
  ImpactEffortMatrixLegend,
  impactEffortMatrixTransformometroClasses,
} from "@delpi/plugin-ui";
import "@delpi/plugin-ui/styles.css";

<ImpactEffortMatrix
  points={scatter}
  activePointId={revisaoId}
  classNames={impactEffortMatrixTransformometroClasses()}
  onPointSelect={(p) => navigateToRevision(p.id)}
/>
<ImpactEffortMatrixLegend />
```

Classes BEM: `delpi-ui-impact-effort-matrix`, `__quadrant--quick-win`, `__point--active`, `__legend`, etc. Alias Transformômetro: classe extra `tm-impact-effort-matrix` no root (tokens); SVG interno permanece `delpi-ui-*`.

---

## Família `preview` — pré-visualização de arquivos

Importar estilos: `import "@delpi/plugin-ui/styles.css"` (ou caminho relativo ao monorepo).

Peer opcionais: `exceljs`, `mammoth` (planilha e DOCX).

### `resolveFilePreviewKind` / `canPreviewFile`

Detecta `image`, `pdf`, `spreadsheet`, `docx`, `text` ou `none` a partir de mime, nome e tipo declarado.

### `useFilePreviewLoader`

Carrega blob/`File`/fetch async e monta estado para `FilePreviewView` (object URL, texto, planilha ExcelJS, DOCX mammoth).

### `FilePreviewView`

Render-only — imagem, PDF, texto, planilha e DOCX com classes `delpi-ui-file-preview*`.

### `DataRouteCatalogPanel`

Catálogo de rotas GET agrupadas por categoria — busca, cards com título + path + método. Usado no painel **Dados** do tv-dashboard.

| Prop | Tipo | Descrição |
|------|------|-----------|
| `items` | `DataRouteCatalogItem[]` | Rotas da API `/data/routes` |
| `onSelect` | `(item) => void` | Callback ao escolher rota |
| `searchPlaceholder` | `string?` | Placeholder da busca |

```tsx
import { DataRouteCatalogPanel } from "@delpi/plugin-ui";
```

### `CenteredScaledPreview`

Encaixa conteúdo arbitrário em um retângulo com escala uniforme (`min(width/refW, height/refH)`) e centralização — equivalente a `object-fit: contain` para miniaturas (filmstrip TV, palco reduzido).

| Prop | Tipo | Descrição |
|------|------|-----------|
| `referenceWidth` / `referenceHeight` | `number` | Tamanho lógico do conteúdo antes do `scale` |
| `className` | `string?` | Container (preenche área pai) |
| `contentClassName` | `string?` | Wrapper escalado |

```tsx
<CenteredScaledPreview referenceWidth={320} referenceHeight={180}>
  <NativeSlideView native={native} />
</CenteredScaledPreview>
```

### `FilePreviewModal`

Modal canônico (`ModalShell` + loader + view + CSS `delpi-ui-file-preview-modal*`). Props principais: `open`, `title`, `onClose`, `source`, `mimeType`, `fileName`, `metaItems`, `afterPreview`, `headerActions`, `previewState`, `labels`.

### `FilePreviewMetaFooter`

Rodapé de metadados (tipo, tamanho, data) — usado automaticamente quando `metaItems` é passado ao modal.

```tsx
import { FilePreviewModal } from "@delpi/plugin-ui";

<FilePreviewModal
  open={open}
  title={fileName}
  onClose={onClose}
  source={() => fetchBlob()}
  mimeType={mime}
  fileName={fileName}
  metaItems={["PDF", "89.9 KB", "09/07/2026, 16:19"]}
/>
```

Todos os MFEs com prévia de anexo usam **`FilePreviewModal`**: `quality-action-plans`, `minha-delpi-chat`, `transformometro`, `cadastro-kaizen`.

---

## Família `shape` — formatação de formas

Paleta estilo PowerPoint: grade tema 10×6, cores padrão, diálogo RGB/hex/transparência, menus de preenchimento/contorno/efeitos/estilo.

| Export | Descrição |
|--------|-----------|
| `ColorThemeGrid` | Grade configurável de cores do tema |
| `ColorStandardRow` | Linha de cores padrão |
| `ColorPickerPopover` | Popover com paleta + «Sem preenchimento» + «Mais cores» |
| `ColorDialog` | Modal com abas Padrão / Personalizar |
| `ShapeFillMenu` | Dropdown de preenchimento |
| `ShapeOutlineMenu` | Dropdown de contorno + espessura |
| `ShapeEffectsMenu` | Efeitos com submenus (shell + callbacks) |
| `ShapeStyleGallery` / `ShapeStyleMenu` | Presets «Abc» |

```tsx
import { ShapeFillMenu, ShapeOutlineMenu } from "@delpi/plugin-ui/index";

<ShapeFillMenu value="#089bdb" onChange={setFill} onNoFill={() => setFill("transparent")} />
```

---

## Consumidores atuais

| Plugin | Componentes usados |
|--------|-------------------|
| `tv-dashboard` | Todos os exports `help` + `ShapeFillMenu`, `ShapeOutlineMenu`, `ShapeStyleMenu`, `ShapeEffectsMenu` |
| `dashboard-production` | `HelpTooltip`, `FieldLabel` |
| `dashboard-commercial` | `HelpTooltip`, `FieldLabel` |
| `dashboard-engineering` | `HelpTooltip`, `FieldLabel` |
| `customer-experience` | `LucideIconPicker`, `LucideIconByName` |
| `public-hub` | `LucideIconByName` |
| `transformometro` (S3+) | `ImpactEffortMatrix`, `ImpactEffortMatrixLegend`, `FilePreviewView`, **`FlowchartEditor`** (via wrapper) |
| `quality-action-plans` | `FilePreviewModal`, `resolveFilePreviewKind` |
| `minha-delpi-chat` | `FilePreviewModal`, `resolveFilePreviewKind` |
| `cadastro-kaizen` | `FilePreviewModal`, `resolveFilePreviewKind` |

Ver [migration-catalog.md](./migration-catalog.md) para plugins pendentes.
