import type { CatalogFamily } from "./types";

/**
 * Inventário canônico de componentes React visuais exportados por `@delpi/plugin-ui`.
 * O catálogo deve ter uma entrada por `exportName` (teste de cobertura).
 * Helpers BEM, factories `create*`, tipos e constantes não entram aqui.
 *
 * Metadados: ao adicionar export → `addedAt` = hoje; ao mudar API/visual → `updatedAt` + `changeNote` opcional.
 */
export type VisualComponentSpec = {
  family: CatalogFamily;
  exportName: string;
  description?: string;
  /** Primeira aparição pública (ISO date YYYY-MM-DD). */
  addedAt: string;
  /** Última mudança relevante de API/visual (ISO date). Default efetivo = addedAt. */
  updatedAt?: string;
  /** Nota curta opcional (1 linha). */
  changeNote?: string;
};

/** Release inicial do pacote (0.1.0). */
export const PACKAGE_INITIAL_DATE = "2026-07-07";

/** Expansão do catálogo visual + DataTable demos. */
export const CATALOG_EXPAND_DATE = "2026-07-13";

function vc(
  family: CatalogFamily,
  exportName: string,
  meta?: Pick<VisualComponentSpec, "description" | "addedAt" | "updatedAt" | "changeNote">,
): VisualComponentSpec {
  return {
    family,
    exportName,
    addedAt: meta?.addedAt ?? PACKAGE_INITIAL_DATE,
    description: meta?.description,
    updatedAt: meta?.updatedAt,
    changeNote: meta?.changeNote,
  };
}

export const VISUAL_COMPONENTS: VisualComponentSpec[] = [
  // help — pacote 0.1.0
  vc("help", "HelpTooltip"),
  vc("help", "FieldLabel"),
  vc("help", "SectionHintLabel"),
  vc("help", "TabHintCell"),
  vc("help", "HintAction"),
  vc("help", "TitleWithHelp"),
  // layout
  vc("layout", "PageHeader"),
  vc("layout", "PanelCard"),
  vc("layout", "ContentCard"),
  vc("layout", "KpiCard"),
  vc("layout", "DelpiKpiCard"),
  vc("layout", "SimpleKpiCard"),
  vc("layout", "MetricKpiCard"),
  vc("layout", "ChartCard"),
  vc("layout", "ChartToolbar"),
  vc("layout", "ChartGranularityToggle"),
  vc("layout", "FiltersRow"),
  vc("layout", "FilterBar"),
  vc("layout", "FilterBarShell"),
  vc("layout", "FilterInputField"),
  vc("layout", "FilterSelectField", {
    addedAt: CATALOG_EXPAND_DATE,
    changeNote: "Incluído em createDashboardFiltersKit",
  }),
  vc("layout", "SectionCard"),
  vc("layout", "SectionBlock"),
  vc("layout", "EditableSectionCard"),
  vc("layout", "DetailCard"),
  vc("layout", "DetailFieldGrid"),
  vc("layout", "FormGrid"),
  vc("layout", "FormActions"),
  vc("layout", "FormatPaneShell"),
  vc("layout", "FormatPaneSection"),
  vc("layout", "FitText"),
  // feedback
  vc("feedback", "EmptyState"),
  vc("feedback", "LoadingState"),
  vc("feedback", "LoadingActivityCard"),
  vc("feedback", "StateBanner"),
  vc("feedback", "StateBoxPanel"),
  vc("feedback", "InfoStatePanel"),
  vc("feedback", "StatusBadge"),
  vc("feedback", "ModalShell"),
  vc("feedback", "DrawerShell"),
  vc("feedback", "ConfirmModalPanel"),
  // data
  vc("data", "DataTable", {
    addedAt: PACKAGE_INITIAL_DATE,
    updatedAt: CATALOG_EXPAND_DATE,
    changeNote: "Demo no catálogo estilo dashboards LMPS",
  }),
  vc("data", "DataTableSection", {
    addedAt: PACKAGE_INITIAL_DATE,
    updatedAt: CATALOG_EXPAND_DATE,
    changeNote: "Demo no catálogo com busca e paginação",
  }),
  vc("data", "Pagination"),
  vc("data", "CompactPagination"),
  vc("data", "TablePaginationNav"),
  vc("data", "TablePageSizeSelect"),
  vc("data", "TableHeaderCell"),
  vc("data", "TableHeaderContent"),
  vc("data", "ConfigurablePresentationTable"),
  vc("data", "ConfigurableTable"),
  vc("data", "TableStyleRibbonStrip", {
    addedAt: "2026-07-13",
    changeNote: "Galeria Estilos de tabela na ribbon (thumbs + Mais em portal)",
  }),
  vc("data", "DataRouteCatalogPanel"),
  vc("data", "TableColumnVisibilityMenu", {
    addedAt: CATALOG_EXPAND_DATE,
    changeNote: "Menu Colunas / Exibir colunas canônico",
  }),
  vc("data", "TreeGuideRails", {
    addedAt: "2026-07-13",
    changeNote: "Linhas pontilhadas suaves para árvores hierárquicas",
  }),
  // forms
  vc("forms", "SelectField"),
  vc("forms", "SelectControl", {
    addedAt: PACKAGE_INITIAL_DATE,
    updatedAt: CATALOG_EXPAND_DATE,
    changeNote: "Painel portado herda escopo .dashboard-*",
  }),
  vc("forms", "DateField"),
  vc("forms", "TextField"),
  vc("forms", "TextAreaField"),
  vc("forms", "MultiSelectField"),
  vc("forms", "ReadOnlyField"),
  vc("forms", "FileDropzone"),
  vc("forms", "FilterCheckboxField"),
  vc("forms", "FormFieldShell"),
  vc("forms", "FormSelectControl"),
  vc("forms", "ToolbarSelectField"),
  vc("forms", "ToolbarSelectControl"),
  vc("forms", "NativeTextField"),
  vc("forms", "NativeTextAreaField"),
  vc("forms", "NativeSelectField"),
  vc("forms", "NativeTextControl"),
  vc("forms", "NativeTextAreaControl"),
  vc("forms", "NativeSelectControl"),
  vc("forms", "NativeCheckboxControl", {
    addedAt: PACKAGE_INITIAL_DATE,
    updatedAt: CATALOG_EXPAND_DATE,
    changeNote: "flex-direction row explícito; children como alias de label",
  }),
  vc("forms", "NativeRangeControl", {
    addedAt: CATALOG_EXPAND_DATE,
    changeNote: "input type=range canônico para ribbon/inspetor",
  }),
  vc("forms", "NativeSwitchControl", {
    addedAt: PACKAGE_INITIAL_DATE,
    updatedAt: CATALOG_EXPAND_DATE,
    changeNote: "flex-direction row explícito (defesa contra label column do portal)",
  }),
  vc("forms", "ComboboxNumberControl"),
  vc("forms", "EditableTableCell"),
  vc("forms", "LucideIconPicker"),
  vc("forms", "LucideIconGridPanel"),
  vc("forms", "LucideIconByName"),
  // export
  vc("export", "TabularExportButtons"),
  vc("export", "DocumentExportActions"),
  vc("export", "ExcelExportButton"),
  // charts
  vc("charts", "ConfigurableSeriesChart"),
  vc("charts", "LineSeriesChart"),
  vc("charts", "BarSeriesChart"),
  vc("charts", "SeriesChartPrimitive"),
  vc("charts", "ImpactEffortMatrix"),
  vc("charts", "ImpactEffortMatrixLegend"),
  vc("charts", "ChartTypeCatalogPanel"),
  vc("charts", "TableInsertCatalogPanel"),
  // preview
  vc("preview", "FilePreviewModal"),
  vc("preview", "FilePreviewView"),
  vc("preview", "FilePreviewMetaFooter"),
  vc("preview", "CenteredScaledPreview"),
  vc("preview", "SpreadsheetPreview"),
  vc("preview", "DocxPreview"),
  // diagram
  vc("diagram", "FlowchartEditor"),
  vc("diagram", "DiagramMermaidPreview"),
  vc("diagram", "DiagramFullscreenFrame"),
  vc("diagram", "TabPanelTransition"),
  // shape
  vc("shape", "ShapeFillMenu"),
  vc("shape", "ShapeOutlineMenu"),
  vc("shape", "ShapeEffectsMenu"),
  vc("shape", "ShapeShadowMenu"),
  vc("shape", "ShapeStyleMenu"),
  vc("shape", "ShapeStyleRibbonStrip"),
  vc("shape", "ShapeStyleGallery"),
  vc("shape", "ColorDialog"),
  vc("shape", "ColorPickerPopover"),
  vc("shape", "RibbonColorPicker"),
  vc("shape", "ColorThemeGrid"),
  vc("shape", "ColorStandardRow"),
  vc("shape", "ColorSwatch"),
  // menu
  vc("menu", "ContextMenu"),
  vc("menu", "ContextMenuItem"),
  vc("menu", "ContextMenuDivider"),
  vc("menu", "ContextMenuToolbar"),
  vc("menu", "ContextMenuToolbarButton"),
];
