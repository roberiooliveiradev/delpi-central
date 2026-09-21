/**
 * @delpi/plugin-ui — componentes React reutilizáveis para plugins MFE.
 *
 * Catálogo: docs/component-catalog.md
 * Como contribuir: docs/contributing.md
 */
export * from "./components/actions";
export * from "./components/help";
export * from "./components/layout";
export * from "./components/navigation";
export * from "./components/feedback";
export * from "./components/data";
export * from "./components/forms";
export * from "./components/preview";
export * from "./components/charts";
export * from "./components/bpmn";
export * from "./components/org";
export * from "./components/shape";
/** Export nomeado — evita tree-shake do remote MF omitir a constante usada por hosts. */
export {
  SHAPE_CORNER_ADJUST_HANDLE,
  separateAdjustmentHandleFromChromeControls,
} from "./components/shape/selectionChromeAdjustSeparation";
export * from "./components/menu";
export * from "./components/signature";
export * from "./components/rich-text";
export * from "./components/ribbon";
export * from "./components/directory";
export * from "./components/document";
export * from "./components/deck";
export * from "./components/collaboration";
export * from "./brand";
export * from "./theme";
/**
 * Export nomeado — Color Family Catalog é consumido por hosts (ex.: chat MFE)
 * sem uso interno no remote; `export *` sozinho pode sumir no tree-shake do MF
 * e o host recebe `resolveColorFamily` undefined → TypeError "X is not a function".
 */
export {
  getColorFamilyDefinition,
  listColorFamilies,
  resolveColorFamily,
} from "./theme/colorFamilyCatalog";
export * from "./utils";
/** Hosts dos portais consomem a saudação sem uso interno no remote. */
export {
  firstNameFromDisplay,
  formatPortalGreeting,
  portalDayPeriodGreeting,
} from "./utils/portalGreeting";
/** Hosts sinalizam refresh sem fetch no kit. */
export { LoadingActivityBadge } from "./components/feedback/LoadingActivityBadge";
/** Hosts consomem chrome de tarefas sem persistência no kit. */
export {
  TaskEditorFrame,
  TaskItemsTable,
  buildTaskWorkspaceHighlights,
} from "./components/tasks";
export type {
  TaskItemActionFlags,
  TaskItemPresentation,
  TaskWorkspaceHighlight,
  TaskWorkspaceSummary,
} from "./components/tasks";
/** Hosts dos portais consomem o chrome de IDD sem uso interno no remote. */
export {
  DepartmentScoreBadge,
  createDashboardDepartmentScoreBadge,
  departmentScoreBadgeBemClasses,
} from "./components/layout/DepartmentScoreBadge";
/** Hosts dos portais consomem o seletor de período sem uso interno no remote. */
export {
  QuickPeriodSelector,
  createDashboardQuickPeriodSelector,
} from "./components/layout/QuickPeriodSelector";
export {
  PERIOD_PRESET_OPTIONS,
  detectPeriodPreset,
  parsePeriodPresetId,
  resolveEffectivePeriodPreset,
  resolvePeriodPreset,
  todayIsoInTimeZone,
} from "./utils/periodPreset";
export * from "./displayFormat";
export * from "./components/displayFormat";
export * from "./hooks";
export * from "./types/chartGranularity";
export * from "./export";
export * from "./overlayLayers";
