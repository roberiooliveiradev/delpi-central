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
export * from "./components/markdown";
/**
 * Hosts TV (presentation) importam paint de runs via Index.
 * `export *` sozinho pode sumir no tree-shake MF → React #130 (undefined).
 */
export {
  DeckContentRunsView,
  plainTextFromDeckContentRuns,
  shouldPersistDeckContentRuns,
} from "./components/rich-text/deckContentRuns";
export type {
  DeckContentRun,
  DeckContentRunStyle,
} from "./components/rich-text/deckContentRuns";
export * from "./components/ribbon";
export * from "./components/directory";
export * from "./components/document";
export * from "./components/deck";
export * from "./components/collaboration";
export {
  InteractionRoomPage,
  INTERACTION_ROOM_PAGE_LABELS_PT,
} from "./components/collaboration/InteractionRoomPage";
/**
 * Parser canônico de tokens de imagem markdown (`attachment:`/`attachment:pending:`)
 * usado só por hosts (composer da sala, comentários). `export *` some no tree-shake
 * do remote MF → o host recebe `undefined` → `TypeError: X is not a function`.
 */
export {
  parseMarkdownImages,
  listInlinePendingIdsFromMarkdown,
  listInlineAttachmentIdsFromMarkdown,
  rewriteInlinePendingInMarkdown,
} from "./components/rich-text/markdownImageTokens";
export type { MarkdownImageToken } from "./components/rich-text/markdownImageTokens";
/** Perfil de usuário dos portais — consumido só por hosts MFE. */
export {
  PORTAL_USER_PROFILE_LABELS_PT,
  PortalUserProfilePage,
  createDashboardPortalUserProfilePage,
  portalUserProfileAccessBemClasses,
  portalUserProfilePageBemClasses,
} from "./components/layout/PortalUserProfilePage";
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
/**
 * Hosts montam o boundary no ponto de falha do MFE (sala, comentários).
 * `export *` some no tree-shake do remote → host recebe `undefined`.
 */
export {
  PluginErrorBoundary,
  pluginErrorBoundaryBemClasses,
} from "./components/feedback/PluginErrorBoundary";
/** Hosts consomem chrome de tarefas sem persistência no kit. */
export {
  TaskEditorFrame,
  TaskEmptyState,
  TaskItemsTable,
  TaskSearchField,
  TaskWorklistSection,
  TaskWorkspacePage,
  buildTaskWorkspaceHighlights,
} from "./components/tasks";
export type {
  TaskItemActionFlags,
  TaskItemPresentation,
  TaskWorkspaceHighlight,
  TaskWorkspacePageProps,
  TaskWorkspaceSummary,
  TaskWorkspaceWorklistProps,
} from "./components/tasks";
/** Hosts dos portais consomem o chrome de IDD sem uso interno no remote. */
export {
  DepartmentScoreBadge,
  createDashboardDepartmentScoreBadge,
  departmentScoreBadgeBemClasses,
} from "./components/layout/DepartmentScoreBadge";
/**
 * Hosts (Portal Comercial / Supplies) instanciam estes kits no load do MFE.
 * `export *` some no tree-shake do remote e o host recebe TypeError
 * "X is not a function".
 */
export {
  createDashboardTopBarFavoritesStrip,
} from "./components/layout/TopBarFavoritesStrip";
export {
  createDashboardTopBarUtilityCluster,
} from "./components/layout/TopBarUtilityCluster";
export {
  createDashboardTopBarUserIdentity,
} from "./components/layout/TopBarUserIdentity";
export { createDashboardUserManual } from "./components/layout/UserManual";
export { createDashboardEntityAvatarLabel } from "./components/layout/EntityAvatarLabel";
export { createDashboardEventsSection } from "./components/layout/EventsSection";
export { createDashboardRecentAccessStrip } from "./components/layout/RecentAccessStrip";
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
/**
 * Modais/notices consumidos por hosts administrativos (ex.: Cadastros do
 * Delpi MES) sem uso interno garantido no remote — `export *` sozinho pode
 * sumir no tree-shake do MF e o host recebe `undefined`.
 */
export {
  ModalShell,
  modalShellBemClasses,
} from "./components/feedback/ModalShell";
export type { ModalShellClassNames } from "./components/feedback/ModalShell";
export {
  ConfirmModalPanel,
  confirmModalBemClasses,
} from "./components/feedback/ConfirmModalPanel";
export type { ConfirmModalClassNames } from "./components/feedback/ConfirmModalPanel";
export {
  FloatingNoticeStack,
  floatingNoticeStackBemClasses,
  useFloatingNotices,
} from "./components/feedback/FloatingNoticeStack";
export type {
  FloatingNoticeInput,
  FloatingNoticeItem,
  FloatingNoticeStackClassNames,
} from "./components/feedback/FloatingNoticeStack";
export * from "./hooks";
export * from "./types/chartGranularity";
export * from "./export";
export * from "./overlayLayers";
