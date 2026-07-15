# `@delpi/plugin-ui`

Biblioteca de **componentes React reutilizáveis** para plugins MFE do monorepo Minha DELPI.

Centraliza primitivos de UI que hoje estão duplicados em dezenas de plugins (ex.: `HelpTooltip` em 14+ pastas). Textos em português permanecem em `content/helpTooltips.ts` de cada plugin — este pacote é **só interação, layout e acessibilidade**.

**CSS canônico** (`.delpi-ui-*` em `src/styles/`) é a fonte única: MFEs **não** escrevem CSS de componentes do kit **em hipótese alguma** — só mapeiam tokens `--delpi-ui-*` e layout de página. Detalhes: [docs/architecture.md](./docs/architecture.md) § CSS · regra Cursor `plugins-reusable-components.mdc`.

---

## Documentação

| Recurso | Descrição |
|---------|-----------|
| [docs/README.md](./docs/README.md) | Índice da documentação |
| [docs/architecture.md](./docs/architecture.md) | Estrutura, tokens CSS, integração Vite / MF |
| [docs/module-federation.md](./docs/module-federation.md) | **Remote runtime** — Docker, remotes, rollout |
| [docs/component-catalog.md](./docs/component-catalog.md) | API de cada export + exemplos |
| [docs/contributing.md](./docs/contributing.md) | Como adicionar componentes |
| [plugin-ui.manifest.json](./plugin-ui.manifest.json) | App portal «Catálogo UI» (`./App`) |
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

### Histórico — bundled (descontinuado)

Antes do rollout MF (jul/2026), consumidores usavam alias Vite + `COPY plugin-ui`. **Não usar** em plugins novos. Ver [module-federation.md](./docs/module-federation.md) e [novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md).

---

## App — Catálogo UI

Além da biblioteca (`./index` + `./styles`), o remote expõe **`./App`**: listagem e prévia de **todos** os componentes React visuais (`src/catalog/visualComponents.ts`), com metadados `addedAt`/`updatedAt`, badges Novo/Atualizado e filtros Recentes/Atualizados.

| Item | Valor |
|------|--------|
| Rota portal | `/apps/plugin-ui` |
| Permissão | `plugin-ui.view` |
| Dev | `npm run dev` → http://localhost:5010 |
| Registro | `TOKEN=$(bash infra/scripts/get-dev-token.sh) ./scripts/register-manifest.sh` |
| Smoke | `curl -fsS http://localhost/apps/plugin-ui/assets/remoteEntry.js \| head` |
| Cobertura | `npm test` (ids únicos + 100% `VISUAL_COMPONENTS`) |

Demos: `src/catalog/demos/`. Tabela estilo LMPS: entradas **DataTable** / **DataTableSection**. Stubs aparecem quando ainda falta fixture (shape ribbon, FlowchartEditor, etc.).

---

## Exports atuais

| Export | Função |
|--------|--------|
| `HelpTooltip` | Balão ? ou `wrap` em qualquer elemento |
| `FieldLabel` | Label de formulário + ajuda |
| `SectionHintLabel` | Rótulo de seção (ribbon) + ajuda |
| `TabHintCell` | Aba + ? sem botão aninhado |
| `HintAction` | Botão/controle com balão ao hover |
| `ShapeFillMenu` / `ShapeOutlineMenu` | Menus de cor estilo PowerPoint (ribbon) |
| `ColorDialog` / `ColorPickerPopover` | Paleta tema + diálogo «Mais cores» |
| `ShapeStyleMenu` / `ShapeStyleRibbonStrip` / `ShapeEffectsMenu` | Estilos de tema (galeria Abc ou faixa) e efeitos de forma |
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

**27 MFEs** + `public-hub` consomem via Module Federation (`delpi-plugin-ui`). Rollout concluído — ver [module-federation.md](./docs/module-federation.md).

| Grupo | Plugins |
|-------|---------|
| Referência | `controle-retrabalhos` |
| Dashboards | `dashboard-*` (8) |
| Operacionais | `quality-labels`, `quality-action-plans`, `minha-delpi-chat`, `cadastro-kaizen`, … |
| Shell | `public-hub` (MF plugin-ui; bundled só `tv-dashboard-presentation`) |
| Fora de escopo | `portal` (shell host), `api-delpi-console` (não importa plugin-ui) |

Detalhe por componente: [migration-catalog.md](./docs/migration-catalog.md).

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
