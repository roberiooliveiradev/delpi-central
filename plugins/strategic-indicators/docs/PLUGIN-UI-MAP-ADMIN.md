# Mapa `@delpi/plugin-ui` — Administração SI

> **Rota:** `/apps/strategic-indicators/settings`  
> **Wireframes:** [WIREFRAMES-ADMIN.md](./WIREFRAMES-ADMIN.md)  
> **Helps:** [HELP-CONTENT-ADMIN.md](./HELP-CONTENT-ADMIN.md) · implementação [`src/content/helpTooltips.ts`](../src/content/helpTooltips.ts)  
> **Catálogo kit:** [`plugins/plugin-ui/docs/component-catalog.md`](../../plugin-ui/docs/component-catalog.md)

Legenda de status:

| Status | Significado |
|--------|-------------|
| **Em uso** | Já consumido via wrapper/factory no MFE |
| **Recomendado** | Substituir UI custom na refatoração enxuta |
| **Proposto** | Layout novo (wireframes) — ainda não no código |
| **N/A** | Domínio SI — permanece componente local escopado |

---

## 1. Inventário por superfície (página de configuração)

### 1.1 Shell e navegação

| Superfície | Componente atual | `@delpi/plugin-ui` | Status | Notas |
|----------|------------------|-------------------|--------|-------|
| Cabeçalho página | `PageHeader` → `PageHeader` | `PageHeader`, `pageHeaderStackBemClasses` | **Em uso** | Migrar para `PageHero` density=`compact` na refatoração |
| Hero redundante | `SettingsHero` (local) | `PageHero` **compact** | **Recomendado** | Remover meta rota/permissão do hero |
| Faixa status | `SettingsStatusStrip` | `StateBanner` ou `LoadingActivityBadge` | **Recomendado** | Uma linha: sync + autor + erro |
| Atualizar scores | `RefreshSnapshotButton` (local) | `ActionButton` variant=`ghost` + `InlineLoadingProgress` | **Recomendado** | Manter lógica API; trocar `<button>` custom |
| Abas (6 pills) | `si-settings-tabbar` CSS | `TopBar` + `UnderlineNav` **ou** nav vertical | **Proposto** | 4 itens: Início · Catálogo · Metas · Sistema |
| Nav lateral admin | — | `UnderlineNav` (vertical slot) / lista custom escopada | **Proposto** | Desktop >1100px — ver WF-SI-00 |
| Mobile nav | tabbar wrap | `UnderlineNav` scroll + sticky | **Proposto** | ≤768px |
| Breadcrumb | — | `PagePath` | Opcional | Se sub-rotas `?tab=catalog&view=validation` |

### 1.2 Aba Início (overview enxuto — proposto)

| Superfície | Atual | Kit | Status |
|----------|-------|-----|--------|
| KPI strip | `SettingsSummaryCards` (3 cards legado) | `MetricStrip` ou 4× `SimpleKpiCard` | **Proposto** |
| Import/export no topo | `AdminConfigImportExportPanel` | mover para Sistema | **Proposto** |
| Cards explicativos | `si-settings-overview-grid` | remover / `EmptyGuidance` link | **Proposto** |
| Pendências validação | — | `AlertQueue` ou `WorklistItem` lista | **Proposto** |
| Ações rápidas | — | `ActionButton` primary + ghost | **Proposto** |
| Loading | `LoadingActivityInline` | `LoadingActivityCard` | **Em uso** |
| Vazio / erro | `InfoState` | `InfoStatePanel` | **Em uso** |

### 1.3 Catálogo — Estrutura (departamentos + indicadores)

| Superfície | Atual | Kit | Status |
|----------|-------|-----|--------|
| Layout master-detail | `si-admin-master-detail` CSS | `ResizableColumns` | **Recomendado** |
| Lista departamentos | `si-admin-list` buttons | `InteractiveDataCard` ou lista escopada | **Recomendado** |
| Lista indicadores | cards + meta spans | `DataRecordCard` / linha densa custom | **Recomendado** |
| Busca dept/indicador | — | `FilterBarShell` + `FilterInputField` | **Proposto** |
| Detalhe departamento | `si-admin-detail-card` | `DetailCard` + `DetailFieldGrid` | **Recomendado** |
| Seção título | `SectionBlock` aninhado | `SectionCard` / `SectionHintLabel` | **Em uso** |
| Drawer CRUD | `DrawerPanel` → `DrawerShell` | `DrawerShell` | **Em uso** |
| Modal confirmação | `SiConfirmModal` → `ModalShell` | `ConfirmModalPanel`, `useConfirmDialogController` | **Em uso** |
| Form campos texto | `SiNativeTextControl` | `NativeTextControl` / `TextField` + `FieldLabel` | **Em uso** |
| Form select | `SiSelectControl` | `SelectControl` via `createDashboardSelectControl` | **Em uso** |
| Form textarea | `SiNativeTextAreaControl` | `NativeTextAreaControl` / `TextAreaField` | **Em uso** |
| Toggle ativo | `ActiveToggle` → `NativeSwitchControl` | `NativeSwitchControl` | **Em uso** |
| Botões ação | `si-settings-editor__button` CSS | `ActionButton` | **Recomendado** |
| Wizard 2 passos indicador | — | `DrawerShell` + steps header local | **Proposto** |
| Accordion dept | — | `EditableSectionCard` colapsável | **Opcional** |

### 1.4 Catálogo — Validação

| Superfície | Atual | Kit | Status |
|----------|-------|-----|--------|
| Filtros ano/depto | `SiSelectControl` + checkbox | `FilterBarShell`, `FilterSelectField`, `NativeCheckboxControl` | **Em uso** / **Recomendado** |
| Tabela validação | CSS grid custom | `DataTable` + `DataTableSection` | **Recomendado** |
| Split lista + detalhe | — | `ResizableColumns` | **Proposto** |
| Badges escopo meta | `GoalScopeBadges` local | `ScopeChipBar` ou badges escopados SI | **N/A** / avaliar kit |
| Severidade | CSS `severity-*` | `StatusBadge` | **Em uso** |
| Empty filtro | `InfoState` | `EmptyState` / `EmptyGuidance` | **Recomendado** |

### 1.5 Metas anuais

| Superfície | Atual | Kit | Status |
|----------|-------|-----|--------|
| Master-detail anos | `AdminGoalsWorkspace` | `ResizableColumns` | **Recomendado** |
| Lista anos | `YearListButton` | `InteractiveDataCard` | **Recomendado** |
| Toolbar bulk | `AdminInlineToolPanel` | `SectionCard` + `FormActions` | **Recomendado** |
| Criar ano lote | `AnnualGoalsWorkspace` | `FormGrid` + campos kit | **Recomendado** |
| Tabela metas ano | custom / parcial `DataTable` | `DataTableSection` (busca + paginação) | **Recomendado** |
| Drawer meta | `IndicatorGoalForm` in drawer | `DrawerShell` + `FormGrid` | **Em uso** |
| Curva mensal grid | CSS local | `FormGrid` + `NativeTextControl` | **Recomendado** |
| Duplicar / fill missing | modais locais | `ConfirmModalPanel` | **Em uso** |

### 1.6 Sistema (global + auditoria + backup)

| Superfície | Atual | Kit | Status |
|----------|-------|-----|--------|
| Parâmetros / governança | `SettingsStructuredEditor` accordion local | `EditableSectionCard` ×2 | **Recomendado** |
| Forms key-value | `SettingsParametersForm` | `FormGrid` + `TextField` | **Recomendado** |
| Alert sucesso/erro | `si-settings-editor__alert` | `StateBox` / `StateBanner` | **Recomendado** |
| Import/export | `AdminConfigImportExportPanel` | `SectionCard` + `FileDropzone` + `DataTable` | **Recomendado** |
| Download JSON | `triggerBlobDownload` | export helper kit | **Em uso** |
| Preview import | `DataTable` wrapper | `DataTable` | **Em uso** |
| Audit resumo | `AuditSummaryPanel` | `SimpleKpiCard` row ou `MetricStrip` | **Recomendado** |
| Audit timeline | `AuditTimelinePanel` | `Timeline` / `ActivityTimeline` | **Recomendado** |
| Change requests | `ChangeRequestsWorkspacePanel` | `EmptyGuidance` + `WorklistItem` | **N/A** (preparatório) |

---

## 2. Mapa completo — exports kit relevantes (por família)

### 2.1 Já usados no MFE SI (admin + shared)

| Export kit | Wrapper SI | Arquivo |
|------------|------------|---------|
| `PageHeader` | `PageHeader` | `ui/components/PageHeader.tsx` |
| `createDashboardSectionBlock` | `SectionBlock` | `ui/components/SectionBlock.tsx` |
| `createInfoStatePanel` | `InfoState` | `ui/components/InfoState.tsx` |
| `createDashboardStatusBadge` | `StatusBadge` | `ui/components/StatusBadge.tsx` |
| `createContentCard` | `Card` | `ui/components/Card.tsx` |
| `createDashboardLoadingActivityCard` | `LoadingActivityInline` | `ui/components/LoadingActivityInline.tsx` |
| `createDashboardLoadingActivityBadge` | `LoadingActivityBadge` | `ui/components/LoadingActivityBadge.tsx` |
| `createDashboardDataTable` | `DataTable` | `ui/components/DataTable.tsx` |
| `DrawerShell` | `DrawerPanel` | `ui/components/DrawerPanel.tsx` |
| `ModalShell` | `Modal` | `ui/components/Modal.tsx` |
| `useConfirmDialogController` + `ConfirmModalPanel` | `SiConfirmModal` | `ui/components/SiConfirmModal.tsx` |
| `createDashboardSelectControl` | `SiSelectControl` | `ui/components/siFiltersUi.tsx` |
| `FilterInputField` / `FilterSelectField` | `*Filter*Field` | `ui/components/siFiltersUi.tsx` |
| `NativeTextControl` etc. | `SiNative*` | `ui/components/siNativeFormFields.ts` |
| `triggerBlobDownload` | bundle export | `data/api/adminConfigBundleApi.ts` |
| `createHostContainedModalShell` | (parcial via SiConfirmModal) | — |

### 2.2 Recomendados na refatoração admin (ainda não wired)

| Família | Export | Uso na config SI |
|---------|--------|------------------|
| layout | `PageHero` | Shell compact — substitui PageHeader + SettingsHero |
| layout | `TopBar` | Container nav + action «Atualizar» |
| layout | `UnderlineNav` | 4 abas ou sub-nav Estrutura/Validação |
| layout | `ResizableColumns` | Master-detail dept/indicador; validação split |
| layout | `DetailCard`, `DetailFieldGrid` | Painel direito do departamento |
| layout | `FormGrid`, `FormActions` | Rodapé drawer meta / indicador |
| layout | `FilterBarShell` | Toolbar validação + metas |
| layout | `MetricStrip`, `SimpleKpiCard` | Início — KPI strip |
| feedback | `ActionButton`, `IconButton` | Substituir `si-settings-editor__button` |
| feedback | `StateBanner`, `StateBox` | Erro/sucesso inline |
| feedback | `EmptyState`, `EmptyGuidance` | Listas vazias |
| feedback | `AlertQueue`, `WorklistItem` | Pendências validação (Início) |
| data | `DataTableSection` | Metas ano + validação com busca |
| data | `Timeline` | Audit timeline |
| data | `InteractiveDataCard` | Lista anos / dept mobile |
| forms | `TextField`, `TextAreaField`, `SelectField` | Com `FieldLabel hint={getSiHelp(...)}` |
| forms | `FileDropzone` | Import JSON |
| help | `FieldLabel`, `SectionHintLabel`, `HelpTooltip` | Todos os formulários admin |
| export | `TabularExportButtons` | Opcional export CSV validação |

### 2.3 Explicitamente N/A (domínio / não admin)

Gráficos (`ConfigurableSeriesChart`), BPMN, organograma membership, `DocumentReader`, `KanbanBoard`, ribbons densas — **fora** do escopo `/settings`.

---

## 3. Matriz superfície × componente kit × help (`SI_HELP`)

Referência rápida — detalhe textual em [HELP-CONTENT-ADMIN.md](./HELP-CONTENT-ADMIN.md).

| WF | Superfície | Componente kit alvo | Chave help |
|----|------------|---------------------|------------|
| SI-00 | Título admin | `PageHero` | `shell.pageTitle` |
| SI-00 | Atualizar | `ActionButton` | `shell.refreshSnapshots` |
| SI-00 | Nav Início | `UnderlineNav` | `nav.overview` |
| SI-00 | Nav Catálogo | `UnderlineNav` | `nav.catalog` |
| SI-00 | Nav Metas | `UnderlineNav` | `nav.goals` |
| SI-00 | Nav Sistema | `UnderlineNav` | `nav.system` |
| SI-01 | KPI deptos | `SimpleKpiCard` | `overview.kpiDepartments` |
| SI-01 | KPI indicadores | `SimpleKpiCard` | `overview.kpiIndicators` |
| SI-01 | KPI metas ano | `SimpleKpiCard` | `overview.kpiGoalsYear` |
| SI-01 | KPI issues | `SimpleKpiCard` | `overview.kpiValidationIssues` |
| SI-02 | Sub-nav Estrutura | `UnderlineNav` | `nav.tabStructure` |
| SI-02 | Sub-nav Validação | `UnderlineNav` | `nav.tabValidation` |
| SI-02 | Agregação filiais | `SelectControl` + `FieldLabel` | `indicator.branchValueAggregation` |
| SI-02 | Filtro validação ano | `FilterSelectField` | `catalog.validationYear` |
| SI-02 | Só pendências | `NativeCheckboxControl` | `catalog.validationOnlyIssues` |
| SI-02-D | Drawer indicador passo 1 | `DrawerShell` + `FormGrid` | `indicator.sectionEssential` |
| SI-03 | Novo ano | `ActionButton` | `goals.newYear` |
| SI-03 | Form meta escopo | `SelectControl` | `goalForm.goalScopeBranch` |
| SI-04 | Import replace | `NativeCheckboxControl`/radio | `system.importModeReplace` |
| SI-04 | Audit timeline | `Timeline` | `system.auditTimeline` |

---

## 4. Plano de adoção (implementação)

| Ordem | Entrega | Kit principal |
|-------|---------|---------------|
| 1 | `helpTooltips.ts` + `FieldLabel` nos forms existentes | help |
| 2 | Shell: `PageHero` + `TopBar` + `UnderlineNav` | layout |
| 3 | Trocar buttons → `ActionButton` | feedback |
| 4 | Master-detail → `ResizableColumns` | layout |
| 5 | Validação → `DataTableSection` + split | data + layout |
| 6 | Início KPI + `AlertQueue` | layout + feedback |

**Gate:** rebuild `plugin-ui` (remote) antes do MFE quando alterar estilos kit — ver `plugins-reusable-components.mdc`.

---

## 5. Anti-padrões (checklist PR)

- [ ] Nenhum CSS `.delpi-ui-*` no MFE SI
- [ ] Helps só via `getSiHelp` / `SI_HELP` — não string no TSX de formulário
- [ ] Drawers/modais confirmação via `DrawerShell` / host-contained modal
- [ ] Overlay filtro/dropdown: portal kit (`AnchoredPanelPortal`) se popover
- [ ] Claro + escuro validados no portal federado
