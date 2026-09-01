# Helps e explicações de UI — Administração SI

> **Fonte de verdade (implementação):** [`src/content/helpTooltips.ts`](../src/content/helpTooltips.ts)  
> **Mapa kit:** [PLUGIN-UI-MAP-ADMIN.md](./PLUGIN-UI-MAP-ADMIN.md)  
> **Wireframes:** [WIREFRAMES-ADMIN.md](./WIREFRAMES-ADMIN.md)  
> **Padrão:** `FieldLabel hint={getSiHelp("indicator.branchValueAggregation")}` · `SectionHintLabel` nos títulos de seção  
> **Proibido:** textos de help hardcoded em componentes TSX de formulário.

---

## Como usar no MFE

```tsx
import { SI_HELP, getSiHelp } from "../content/helpTooltips";
import { FieldLabel, SectionHintLabel } from "@delpi/plugin-ui";

<FieldLabel label="Agregação entre filiais" hint={SI_HELP.indicator.branchValueAggregation} />
<SectionHintLabel hint={getSiHelp("department.sectionIdd")}>IDD do departamento</SectionHintLabel>
```

Ícone `?` do kit aparece no hover/focus — ver `FieldLabel` / `SectionHintLabel` em `@delpi/plugin-ui`.

---

## WF-SI-00 — Shell

| Elemento UI | Chave help | Componente kit |
|-------------|------------|----------------|
| Título admin | `shell.pageTitle` | `PageHero` |
| [Atualizar scores] | `shell.refreshSnapshots` | `ActionButton` |
| Última sync | `shell.lastSync` | texto inline / `StateBanner` |
| Atualizado por | `shell.updatedBy` | texto inline |

### Navegação principal

| Item nav | Chave | Componente kit |
|----------|-------|----------------|
| Início | `nav.overview` | `UnderlineNav` |
| Catálogo | `nav.catalog` | `UnderlineNav` |
| Metas | `nav.goals` | `UnderlineNav` |
| Sistema | `nav.system` | `UnderlineNav` |

---

## WF-SI-01 — Início (overview)

| Elemento UI | Chave help | Componente kit |
|-------------|------------|----------------|
| KPI Departamentos | `overview.kpiDepartments` | `SimpleKpiCard` |
| KPI Indicadores | `overview.kpiIndicators` | `SimpleKpiCard` |
| KPI Metas (ano) | `overview.kpiGoalsYear` | `SimpleKpiCard` |
| KPI Pendências | `overview.kpiValidationIssues` | `SimpleKpiCard` |
| Link «Ver pendências» | `overview.actionGoValidation` | `ActionButton` ghost |
| «Novo indicador» | `overview.actionNewIndicator` | `ActionButton` |
| «Novo ano de metas» | `overview.actionNewGoalYear` | `ActionButton` |
| Lista pendências | `overview.pendingIssues` | `AlertQueue` / `WorklistItem` |

---

## WF-SI-02 — Catálogo

### Sub-navegação

| Aba | Chave | Componente kit |
|-----|-------|----------------|
| Estrutura | `nav.tabStructure` | `UnderlineNav` |
| Validação | `nav.tabValidation` | `UnderlineNav` |

### Estrutura (master-detail)

| Elemento UI | Chave help | Componente kit |
|-------------|------------|----------------|
| Busca departamentos | `catalog.searchDepartments` | `FilterInputField` |
| [Novo departamento] | `catalog.newDepartment` | `ActionButton` |
| Lista departamentos | `catalog.departmentList` | `ResizableColumns` col esq |
| Peso dept (drawer) | `department.weightPct` | `NativeTextControl` + `FieldLabel` |
| Agregação dept | `department.aggregationMode` | `SelectControl` |
| Busca indicadores | `catalog.searchIndicators` | `FilterInputField` |
| [Novo indicador] | `catalog.newIndicator` | `ActionButton` |
| Lista indicadores | `catalog.indicatorList` | painel direito |

### Drawer — Departamento

| Seção / campo | Chave | Componente kit |
|---------------|-------|----------------|
| Identificação | `department.sectionIdentity` | `SectionHintLabel` |
| ID técnico | `department.departmentId` | `FieldLabel` |
| Nome | `department.departmentName` | `FieldLabel` |
| Sigla | `department.shortName` | `FieldLabel` |
| IDD | `department.sectionIdd` | `SectionHintLabel` |
| Peso IGD | `department.weightPct` | `FieldLabel` |
| Modo agregação | `department.aggregationMode` | `FieldLabel` |
| Narrativa | `department.sectionNarrative` | `SectionHintLabel` |
| Resumo estratégico | `department.strategicSummary` | `FieldLabel` |
| Headline meta | `department.headlineGoal` | `FieldLabel` |
| Foco de apoio | `department.supportingFocus` | `FieldLabel` |
| Ordem | `department.displayOrder` | `FieldLabel` |
| Ativo | `department.isActive` | `NativeSwitchControl` |

### Drawer — Indicador (passo 1 — essencial)

| Seção / campo | Chave | Componente kit |
|---------------|-------|----------------|
| Essencial | `indicator.sectionEssential` | `SectionHintLabel` |
| ID técnico | `indicator.indicatorId` | `FieldLabel` |
| Nome | `indicator.indicatorName` | `FieldLabel` |
| Peso no dept | `indicator.weightPct` | `FieldLabel` |
| Escopo | `indicator.scopeType` | `FieldLabel` |
| Agregação entre filiais | `indicator.branchValueAggregation` | `FieldLabel` |
| Fonte (source_key) | `indicator.sourceKey` | `FieldLabel` |
| Direção performance | `indicator.performanceDirection` | `FieldLabel` |
| Ativo | `indicator.isActive` | `NativeSwitchControl` |

### Drawer — Indicador (passo 2 — formato)

| Seção / campo | Chave | Componente kit |
|---------------|-------|----------------|
| Formato | `indicator.sectionFormat` | `SectionHintLabel` |
| Unidade lógica | `indicator.valueUnit` | `FieldLabel` |
| Decimais | `indicator.valueDecimals` | `FieldLabel` |
| Prefixo | `indicator.valuePrefix` | `FieldLabel` |
| Sufixo | `indicator.valueSuffix` | `FieldLabel` |
| Descrição estratégica | `indicator.strategicDescription` | `FieldLabel` |
| Ordem | `indicator.displayOrder` | `FieldLabel` |

### Validação

| Elemento UI | Chave help | Componente kit |
|-------------|------------|----------------|
| Filtro ano | `catalog.validationYear` | `FilterSelectField` |
| Filtro departamento | `catalog.validationDepartment` | `FilterSelectField` |
| Só pendências | `catalog.validationOnlyIssues` | `NativeCheckboxControl` |
| Col. Departamento | `catalog.validationColDepartment` | header `DataTable` |
| Col. Agregação dept | `catalog.validationColAggregation` | header |
| Col. Indicador | `catalog.validationColIndicator` | header |
| Col. Escopo | `catalog.validationColScope` | header |
| Col. Metas (C/01/02) | `catalog.validationColGoals` | header |
| Col. Status | `catalog.validationColStatus` | header |
| Col. Apontamentos | `catalog.validationColIssues` | header |
| Painel detalhe issue | `overview.pendingIssues` | split col direita |

---

## WF-SI-03 — Metas anuais

| Elemento UI | Chave help | Componente kit |
|-------------|------------|----------------|
| Lista anos | `goals.yearList` | `ResizableColumns` |
| [Novo ano] | `goals.newYear` | `ActionButton` |
| Duplicar ano | `goals.duplicateYear` | `ActionButton` ghost |
| Preencher faltantes | `goals.fillMissing` | `ActionButton` ghost |
| KPI indicadores ano | `goals.yearSummaryIndicators` | `SimpleKpiCard` |
| KPI metas ativas | `goals.yearSummaryGoals` | `SimpleKpiCard` |
| KPI avisos | `goals.yearSummaryWarnings` | `SimpleKpiCard` |
| Col. Indicador | `goals.goalTableIndicator` | `DataTableSection` |
| Col. Escopo | `goals.goalTableScope` | header |
| Col. Modo | `goals.goalTableMode` | header |
| Col. Valor | `goals.goalTableValue` | header |

### Drawer — Meta analítica (`IndicatorGoalForm`)

| Seção / campo | Chave | Componente kit |
|---------------|-------|----------------|
| Alvo | `goalForm.sectionTarget` | `SectionHintLabel` |
| Indicador | `goalForm.indicatorId` | `FieldLabel` |
| Ano | `goalForm.goalYear` | `FieldLabel` |
| Escopo filial | `goalForm.goalScopeBranch` | `FieldLabel` |
| Valor | `goalForm.sectionValue` | `SectionHintLabel` |
| Rótulo meta | `goalForm.goalLabel` | `FieldLabel` |
| Valor numérico | `goalForm.goalValue` | `FieldLabel` |
| Periodicidade | `goalForm.goalPeriodicity` | `FieldLabel` |
| Modo (padrão/curva) | `goalForm.goalMode` | `FieldLabel` |
| Grade curva mensal | `goalForm.monthlyTargets` | `FormGrid` |
| Vigência | `goalForm.sectionValidity` | `SectionHintLabel` |
| Válido de | `goalForm.validFrom` | `FieldLabel` |
| Válido até | `goalForm.validTo` | `FieldLabel` |
| Observações | `goalForm.notes` | `FieldLabel` |

---

## WF-SI-04 — Sistema

### Parâmetros globais

| Elemento UI | Chave help | Componente kit |
|-------------|------------|----------------|
| Seção parâmetros | `system.sectionParameters` | `EditableSectionCard` |
| Chave | `system.parameterKey` | `FieldLabel` (read-only) |
| Rótulo | `system.parameterLabel` | `FieldLabel` |
| Valor | `system.parameterValue` | `FieldLabel` |

### Governança

| Elemento UI | Chave help | Componente kit |
|-------------|------------|----------------|
| Seção governança | `system.sectionGovernance` | `EditableSectionCard` |
| Título item | `system.governanceLabel` | `FieldLabel` |
| Conteúdo | `system.governanceValue` | `FieldLabel` |
| Observação | `system.governanceObservation` | `FieldLabel` |

### Import / export JSON

| Elemento UI | Chave help | Componente kit |
|-------------|------------|----------------|
| Título bloco | `system.importExportTitle` | `SectionCard` |
| [Exportar JSON] | `system.exportJson` | `ActionButton` |
| Arquivo import | `system.importFile` | `FileDropzone` |
| Modo Substituir | `system.importModeReplace` | radio/checkbox |
| Modo Mesclar | `system.importModeMerge` | radio/checkbox |
| Incluir metas (merge) | `system.importIncludeGoals` | `NativeCheckboxControl` |
| [Pré-visualizar] | `system.importPreview` | `ActionButton` |
| [Aplicar] | `system.importApply` | `ActionButton` primary |

### Auditoria

| Elemento UI | Chave help | Componente kit |
|-------------|------------|----------------|
| Resumo por entidade | `system.auditSummary` | `MetricStrip` |
| Últimas por tipo | `system.auditLatestByEntity` | cards compactos |
| Timeline | `system.auditTimeline` | `Timeline` |
| Filtro entidade | `system.auditEntityFilter` | `FilterSelectField` |
| Solicitações mudança | `system.changeRequests` | `EmptyGuidance` |

---

## Badges e chips (transversal)

| Badge / chip | Chave help | Onde |
|--------------|------------|------|
| Meta C (consolidado) | `badges.goalScopeConsolidated` | `GoalScopeBadges` |
| Meta 01 | `badges.goalScope01` | idem |
| Meta 02 | `badges.goalScope02` | idem |
| Status OK | `badges.severityOk` | validação |
| Info | `badges.severityInfo` | validação |
| Atenção | `badges.severityWarning` | validação |
| Erro | `badges.severityError` | validação |
| Agreg. Automático | `badges.branchAggregationAuto` | select indicador |
| Agreg. Soma | `badges.branchAggregationSum` | select indicador |
| Agreg. Média | `badges.branchAggregationAverage` | select indicador |
| Agreg. Fonte | `badges.branchAggregationSource` | select indicador |

---

## Cobertura e testes

- Chaves indexadas: `listSiHelpKeys()` em `helpTooltips.ts`
- Teste estrutural: `src/content/helpTooltips.structural.test.mjs` — toda chave documentada aqui deve existir no TS e ter texto não vazio (`npx tsx --test src/content/helpTooltips.structural.test.mjs`)
- Ao adicionar campo admin: **1)** chave em `SI_HELP`, **2)** linha neste doc, **3)** linha em `PLUGIN-UI-MAP-ADMIN.md` §3

---

## Índice de chaves (alfabético)

| Chave | Resumo |
|-------|--------|
| `badges.branchAggregationAuto` | Agregação automática por unidade |
| `badges.branchAggregationAverage` | Média 01/02 |
| `badges.branchAggregationSource` | Valor da fonte consolidada |
| `badges.branchAggregationSum` | Soma 01+02 |
| `badges.goalScope01` | Meta filial SC |
| `badges.goalScope02` | Meta filial ES |
| `badges.goalScopeConsolidated` | Meta consolidada |
| `badges.severityError` | Erro validação |
| `badges.severityInfo` | Info validação |
| `badges.severityOk` | OK validação |
| `badges.severityWarning` | Atenção validação |
| `catalog.departmentList` | Lista master dept |
| `catalog.indicatorList` | Lista indicadores |
| `catalog.newDepartment` | CTA novo dept |
| `catalog.newIndicator` | CTA novo indicador |
| `catalog.searchDepartments` | Busca dept |
| `catalog.searchIndicators` | Busca indicador |
| `catalog.validationColAggregation` | Col agregação dept |
| `catalog.validationColDepartment` | Col departamento |
| `catalog.validationColGoals` | Col metas C/01/02 |
| `catalog.validationColIndicator` | Col indicador |
| `catalog.validationColIssues` | Col apontamentos |
| `catalog.validationColScope` | Col escopo |
| `catalog.validationColStatus` | Col status |
| `catalog.validationDepartment` | Filtro dept |
| `catalog.validationOnlyIssues` | Checkbox pendências |
| `catalog.validationYear` | Filtro ano |
| `department.*` | Form departamento (14 chaves) |
| `goalForm.*` | Form meta analítica (14 chaves) |
| `goals.*` | Workspace metas anuais (11 chaves) |
| `indicator.*` | Form indicador (17 chaves) |
| `nav.*` | Navegação (6 chaves) |
| `overview.*` | Início (8 chaves) |
| `shell.*` | Shell (4 chaves) |
| `system.*` | Sistema (18 chaves) |

**Total:** 122 chaves — ver `listSiHelpKeys()` para lista exata gerada do código.
