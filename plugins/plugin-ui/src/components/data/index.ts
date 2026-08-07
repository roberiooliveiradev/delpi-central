export {
  ConfigurablePresentationTable,
  ConfigurableTable,
  type ConfigurablePresentationTableProps,
  type ConfigurableTableProps,
} from "./ConfigurablePresentationTable";

export {
  configurableTableBemClasses,
  configurableTableTvClasses,
  ConfigurableTableClassesProvider,
  useConfigurableTableClasses,
  type ConfigurableTableClassNames,
  type ConfigurableTableClassesProviderProps,
} from "./configurableTableClasses";

export {
  CONFIGURABLE_TABLE_ELEMENT_CATALOG,
  isConfigurableTableElementEnabled,
  setConfigurableTableElementEnabled,
  type ConfigurableTableElementDefinition,
  type ConfigurableTableElementId,
} from "./configurableTableElementCatalog";

export {
  TableStyleGallery,
  TableStyleMenu,
  TableStyleRibbonStrip,
  type TableStyleGalleryLabels,
  type TableStyleGalleryProps,
  type TableStyleMenuProps,
  type TableStylePreset,
  type TableStylePresetCategory,
  type TableStyleRibbonStripProps,
} from "./TableStyleGallery";

export {
  TABLE_PART_DATA_ATTR,
  bindTablePartPointer,
  deleteTablePart,
  findTablePartFromTarget,
  getTablePartState,
  isTablePartRefEqual,
  isTablePartSelected,
  mergeTablePartsWithOptions,
  migrateLegacyTableChromeToFrame,
  normalizeTablePartsForLoad,
  selectedTableColumnIndexes,
  selectedTableRowIndexes,
  parseTablePartRef,
  partsToTableOptions,
  resolveTableFrameStyle,
  resolveTableHeaderCellPaintStyle,
  resolveTableBodyCellPaintStyle,
  resolveTablePartPaintStyle,
  tablePartPaintToCss,
  serializeTablePartRef,
  tableElementPrimaryPartRef,
  tableOptionsToParts,
  tablePartAllowsDelete,
  tablePartAllowsEdit,
  tablePartAllowsStroke,
  resolveTableShapeChromePartRef,
  tablePartCapabilities,
  tablePartDomProps,
  upsertTablePartState,
  applyTablePartStyleToSiblingParts,
  applyTablePartStyleToParts,
  clearTablePartThemePaint,
  type TableGridDimensions,
  type TableInteraction,
  type TablePartCapabilities,
  type TablePartPaintStyle,
  type TablePartRef,
  type TablePartState,
  type TablePartStyle,
  type TablePartsMap,
} from "./configurableTableParts";

export {
  CONFIGURABLE_TABLE_BORDER_STYLE_OPTIONS,
  CONFIGURABLE_TABLE_BORDER_WIDTH_PRESETS,
  CONFIGURABLE_TABLE_TEXT_ALIGN_OPTIONS,
  CONFIGURABLE_TABLE_VALUE_FORMAT_OPTIONS,
  DEFAULT_CONFIGURABLE_TABLE_OPTIONS,
  buildConfigurableTableTotalRow,
  formatConfigurableTableCellValue,
  mergeConfigurableTableOptions,
  presetDefaultConfigurableTableOptions,
  resolveConfigurableTableDisplayOptions,
  configurableTableOptionsCssVars,
  configurableTableOptionsModifierClasses,
  type ConfigurableTableBorderStyle,
  type ConfigurableTableOptions,
  type ConfigurableTablePreset,
  type ConfigurableTableTextAlign,
  type ConfigurableTableValueFormat,
  type PresentationTableColumn,
} from "./configurableTableOptions";

export {
  Pagination,
  TablePageSizeSelect,
  createDashboardPaginationKit,
  paginationBemClasses,
  type DashboardPaginationKit,
  type PaginationClassNames,
  type PaginationHints,
  type PaginationLabels,
  type PaginationProps,
  type TablePageSizeClassNames,
  type TablePageSizeLabels,
  type TablePageSizeSelectProps,
} from "./Pagination";

export {
  CompactPagination,
  createCompactPagination,
  compactPaginationBemClasses,
  type CompactPaginationClassNames,
  type CompactPaginationHints,
  type CompactPaginationLabels,
  type CompactPaginationLayout,
  type CompactPaginationProps,
  type DashboardCompactPaginationProps,
} from "./CompactPagination";

export {
  TablePaginationNav,
  createTablePaginationNav,
  tablePaginationNavBemClasses,
  type DashboardTablePaginationNavProps,
  type TablePaginationNavClassNames,
  type TablePaginationNavLabels,
  type TablePaginationNavProps,
} from "./TablePaginationNav";

export {
  DataTable,
  dataTableBemClasses,
  type DataTableClassNames,
  type DataTableColumn,
  type DataTableColumnWidths,
  type DataTableLabels,
  type DataTableProps,
  type DataTableSelection,
  type DashboardDataTableProps,
} from "./DataTable";

export {
  DataCellValue,
  type DataCellValueProps,
} from "./DataCellValue";

export {
  isCellSelected,
  isColumnSelected,
  isRowSelected,
  primaryColumnKey,
  resolveCellSelection,
  resolveColumnSelection,
  resolveRowSelection,
  selectionFromColumnKey,
  selectionToTsv,
  type DataTableCellRef,
  type DataTableSelectionModifiers,
} from "./dataTableSelection";

export {
  resolveDataCellSemantics,
  type DataCellError,
  type DataCellKind,
  type DataCellSemantics,
  type ResolveDataCellOptions,
} from "./dataCellSemantics";

export {
  autofitDataTableColumn,
  clampColumnWidthPx,
  measureDataTableColumnWidthPx,
  startDataTableColumnResize,
} from "./dataTableColumnResize";

export {
  DataTableSection,
  createDashboardDataTableKit,
  dataTableSectionBemClasses,
  type DashboardDataTableSectionProps,
  type DataTableSectionClassNames,
  type DataTableSectionLabels,
  type DataTableSectionProps,
  type ServerPaginationConfig,
  type ServerSearchConfig,
  type ServerSortConfig,
} from "./DataTableSection";

export {
  buildVisiblePageItems,
  parsePageJumpInput,
  TABLE_PAGE_SIZE_OPTIONS,
  type PageJumpParseResult,
  type PageJumpValidationReason,
  type PaginationPageItem,
} from "../../utils/paginationPages";

export { buildDataTableSearchText } from "../../utils/dataTableSearch";
export { useClientPagination } from "../../utils/useClientPagination";

export {
  DataRouteCatalogPanel,
  primaryDataRouteDisplayKind,
  resolveDataRouteDisplayKinds,
  buildSampleDataRoutePreview,
  mapEnrichedBlockToDataRoutePreview,
  countRequiredParams,
  formatParamHintLine,
  humanizeMetaShape,
  isParamFieldOptional,
  isTemplatedRouteDescription,
  resolveRouteAudienceDescription,
  summarizeRouteParams,
  truncateText,
  type DataRouteCatalogDensity,
  type DataRouteCatalogItem,
  type DataRouteCatalogPanelProps,
  type DataRouteCatalogSuggestion,
  type DataRouteDisplayKind,
  type DataRouteParamFieldSummary,
  type DataRoutePreviewPayload,
  type DataRouteTestParams,
} from "./DataRouteCatalogPanel";

export {
  DATA_ROUTE_CATALOG_CONTENT,
  formatDataRouteSuggestionsTitle,
} from "../../content/dataRouteCatalogContent";

export { DataRouteSamplePreview } from "./DataRouteSamplePreview";

export {
  TableHeaderCell,
  TableHeaderContent,
  createDashboardTableHeaderCell,
  createDashboardTableHeaderContent,
  tableHeaderCellBemClasses,
  tableHeaderCellPacClasses,
  tableHeaderContentBemClasses,
  tableHeaderContentTransformometroClasses,
  type DashboardTableHeaderCellProps,
  type DashboardTableHeaderContentProps,
  type TableHeaderCellClassNames,
  type TableHeaderCellLabels,
  type TableHeaderCellProps,
  type TableHeaderHintPresentation,
  type TableHeaderHintProps,
} from "./TableHeaderCell";

export {
  TableColumnVisibilityMenu,
  type TableColumnVisibilityItem,
  type TableColumnVisibilityMenuLabels,
  type TableColumnVisibilityMenuProps,
} from "./TableColumnVisibilityMenu";

export { DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS } from "./tableColumnVisibilityLabels";

export {
  applyVisibleColumnReorder,
  createDefaultColumnOrder,
  createDefaultColumnVisibility,
  loadColumnVisibilityPreferences,
  reorderColumnKeys,
  saveColumnVisibilityPreferences,
  sanitizeColumnOrder,
  sanitizeColumnVisibility,
  sanitizeColumnVisibilityPreferences,
  type TableColumnVisibilityMap,
  type TableColumnVisibilityPreferences,
} from "../../utils/tableColumnVisibilityPreferences";

export {
  TreeGuideRails,
  type TreeGuideRailsProps,
} from "./TreeGuideRails";

export {
  HorizontalTimeline,
  createDashboardHorizontalTimeline,
  horizontalTimelineBemClasses,
  horizontalTimelinePositionPercent,
  layoutHorizontalTimeline,
  formatClusterCaptionText,
  normalizeTimelineDayKey,
  DEFAULT_HORIZONTAL_TIMELINE_LABELS,
  type DashboardHorizontalTimelineProps,
  type HorizontalTimelineClassNames,
  type HorizontalTimelineCluster,
  type HorizontalTimelineLabels,
  type HorizontalTimelinePoint,
  type HorizontalTimelineProps,
  type HorizontalTimelineTone,
} from "./HorizontalTimeline";

export {
  Timeline,
  createTimeline,
  buildTimelineForest,
  timelineBemClasses,
  timelineMarkerToneClass,
  type DashboardTimelineProps,
  type TimelineClassNames,
  type TimelineItemModel,
  type TimelineLayout,
  type TimelineProps,
  type TimelineTone,
  type TimelineTreeNode,
} from "./Timeline";
export {
  InlineMeter,
  createDashboardInlineMeter,
  inlineMeterBemClasses,
  type DashboardInlineMeterProps,
  type InlineMeterClassNames,
  type InlineMeterProps,
  type InlineMeterSegment,
  type InlineMeterTone,
} from "./InlineMeter";
/** Alias de produto (Account 360 / follow-ups) — mesmo componente Timeline. */
export {
  Timeline as ActivityTimeline,
  createTimeline as createActivityTimeline,
  timelineBemClasses as activityTimelineBemClasses,
} from "./Timeline";
