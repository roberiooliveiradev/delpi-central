# Camada UI — `@delpi/plugin-ui`

O plugin **cadastro-kaizen** concluiu a migração de primitivos duplicados para [`@delpi/plugin-ui`](../../plugin-ui/README.md). Textos PT-BR permanecem em `src/content/helpTooltips.ts`; o pacote compartilhado cuida de layout, acessibilidade e factories BEM com prefixo **`kz`**.

## Padrão de integração

1. **Factory no pacote** — `createDashboard*` / `createKaizenKpiCard` com `classNames` BEM.
2. **Wrapper fino local** — arquivo em `src/components/ui/` (~5–15 linhas).
3. **CSS no plugin** — classes `kz-*` em `src/index.css`; tokens `--delpi-ui-*` no root `.dashboard-cadastro-kaizen`.
4. **Import canônico** — páginas e formulários importam de `../components/ui` (barrel), não de `@delpi/plugin-ui` diretamente (exceto `HelpTooltip` pontual).

Alias Vite (obrigatório):

```ts
// vite.config.ts
"@delpi/plugin-ui": path.resolve(__dirname, "../plugin-ui/src/index.ts"),
```

Estilos base:

```ts
// main.tsx
import "../../plugin-ui/src/styles.css";
import "./index.css";
```

## Wrappers (`src/components/ui/`)

| Arquivo | Factory / export | Uso principal |
|---------|------------------|---------------|
| `kzFormFields.ts` | `createDashboardNativeFormFields` | `TextField`, `SelectField`, `TextAreaField`, `FormFieldShell` |
| `FormGrid.tsx` | `createDashboardFormGrid` | `FormGrid` (`kz-form-grid`), `ReadOnlyGrid` (`kz-read-grid`) |
| `FormActions.tsx` | `createDashboardFormActions` | Rodapé Salvar/Cancelar |
| `SectionCard.tsx` | `createDashboardSectionCard` | Seções estáticas (evidências, ganhos, changelog) |
| `EditableSectionCard.tsx` | `createDashboardEditableSectionCard` | Seções editáveis no detalhe (identificação, estágio, economia) |
| `ReadOnlyField.tsx` | `createDashboardReadOnlyField` | Campos somente leitura no detalhe |
| `DateField.tsx` | `createDashboardDateField` | Inputs `type="date"` |
| `MultiSelectField.tsx` | `createDashboardMultiSelectField` | Filtro de unidade, multiselect genérico |
| `FiltersKit.ts` | `createDashboardFiltersKit` | `FiltersRow`, `FilterInputField`, `FilterSelectField` |
| `KpiCard.tsx` | `createKaizenKpiCard("kz")` | KPIs do painel dashboard |
| `TitleWithHelp.tsx` | `createDashboardTitleWithHelp` | Títulos inline com ? (métricas, versões, upload) |
| `ReadOnlyChipsField.tsx` | composição sobre `ReadOnlyField` | Categorias, participantes (chips) |
| `Modal.tsx` | `createModalShell` | Modais do plugin |
| `StateAlert.tsx` | `createDashboardStateBanner` | Alertas de erro/sucesso |
| `index.ts` | barrel | Import único para páginas |

`KaizenPageHeader` (`src/components/KaizenPageHeader.tsx`) usa `PageHeader` brand do pacote.

`CategoryMultiSelectField` (`src/components/form/`) usa `createDashboardCreatableMultiSelectField`.

`KaizenEvidenceDropzone` usa `createDashboardFileDropzone` com `fileDropzoneKaizenClasses`.

## Páginas migradas

| Página / componente | Componentes plugin-ui |
|---------------------|------------------------|
| `KaizenListPage` | DataTable kit, Pagination, `StateAlert` |
| `KaizenRecordFilters` | `FiltersKit` completo |
| `KaizenDashboardPage` | `KpiCard`, `FiltersRow`, `FilterInputField`, `MultiSelectField` |
| `KaizenDetailPage` | `EditableSectionCard`, `FormGrid`, `ReadOnlyGrid`, `ReadOnlyChipsField`, campos nativos, `SectionCard` |
| `KaizenFormPage` / `KaizenFormFields` | `FormSection` → `SectionCard` + `FormGrid` + campos nativos |
| `KaizenEvidencePanel` | `FormGrid`, campos nativos, `TitleWithHelp`, etapa padrão `SelectField` |
| `KaizenEvidencePendingList` | `SelectField` + `TextAreaField` na fila de upload |
| `KaizenImprovementsPanel` | `TitleWithHelp` + `DateField` (período) |
| `KaizenVersionSwitcher` | `TitleWithHelp` no cabeçalho |

## Permanece local (domínio kaizen)

Não duplicam primitivos do pacote — são regras de negócio ou layout específico:

- `KaizenParticipantsField` (layout de linha nome+papel — domínio)
- `KaizenEvidencePanel` (galeria, preview), `KaizenChangeLog`

## Adicionar um campo novo

1. Texto/hint → `src/content/helpTooltips.ts`.
2. Formulário → usar `TextField` / `SelectField` / `TextAreaField` / `DateField` de `components/ui`.
3. Detalhe somente leitura → `ReadOnlyField` dentro de `ReadOnlyGrid`.
4. Detalhe editável → mesmo campo dentro de `FormGrid` no `editContent` de `EditableSectionCard`.
5. Filtro de lista → `FilterSelectField` ou `FilterInputField` dentro de `FiltersRow`.

**Não** reintroduzir `FieldLabel` + `<input>` inline nas páginas — estender o wrapper ou o factory no pacote se faltar variante.

## Verificação

```bash
cd plugins/plugin-ui && npm test
cd plugins/cadastro-kaizen && npm run build
cd ../.. && python3 scripts/ci/audit_plugin_ui_duplication.py --check --strict
```

## Referências

- [migration-catalog.md](../../plugin-ui/docs/migration-catalog.md) — status global por plugin
- [component-catalog.md](../../plugin-ui/docs/component-catalog.md) — API dos exports
- [plugins-reusable-components.mdc](../../../.cursor/rules/plugins-reusable-components.mdc) — diretriz do monorepo
