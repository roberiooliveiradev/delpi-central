/**
 * Bindings canônicos do `@delpi/plugin-ui` para o BPMN Modeler (prefixo `bpmnm`).
 *
 * Convenção do monorepo (plugins-reusable-components / visual-design-system):
 * componentes do kit emitem dual-class `{prefix}-* delpi-ui-*`; o CSS visual
 * vem do remote (`preparePluginUiRemote` no bootstrap). O MFE só mapeia
 * tokens `--bpmnm-*` → `--delpi-ui-*` no root `.dashboard-bpmn-modeler`.
 */
import {
  confirmModalBemClasses,
  createDashboardDataCardsGrid,
  createDashboardDataRecordCard,
  createDashboardEmptyState,
  createDashboardFiltersKit,
  createDashboardNavigationCard,
  createDashboardPageHeader,
  createDashboardPageHero,
  createDashboardPreviewDetailCard,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createDashboardTextField,
  createFilterBarShell,
  createHostContainedModalShell,
  emptyStatePanelBemClasses,
  fileDropzoneBemClasses,
  navigationCardBemClasses,
  pageHeaderBrandBemClasses,
  previewDetailCardBemClasses,
  stateBannerBemClasses,
  textFieldBemClasses,
  type FileDropzoneLabels,
} from "@delpi/plugin-ui/index";

export const BPMNM_ROOT_CLASS = "dashboard-bpmn-modeler";

const PREFIX = "bpmnm";

export const BpmnmPageHero = createDashboardPageHero({ prefix: PREFIX });

export const BpmnmPageHeader = createDashboardPageHeader({
  layout: "brand",
  classNames: pageHeaderBrandBemClasses(PREFIX),
  labels: { refresh: "Atualizar", refreshing: "Atualizando…" },
});

export const BpmnmNavigationCard = createDashboardNavigationCard({
  classNames: navigationCardBemClasses(PREFIX),
});

export const BpmnmFilterBarShell = createFilterBarShell({
  prefix: PREFIX,
  embeddedByDefault: true,
  defaultAriaLabel: "Filtrar modelos",
});

export const BpmnmPreviewDetailCard = createDashboardPreviewDetailCard({
  classNames: previewDetailCardBemClasses(PREFIX),
});

export const BpmnmModal = createHostContainedModalShell({
  prefix: PREFIX,
  portalScopeClassName: BPMNM_ROOT_CLASS,
  containedLayout: "dialog",
});

export const bpmnmConfirmModalClasses = confirmModalBemClasses(PREFIX);

export const BpmnmStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(PREFIX),
});

export const BpmnmStatusBadge = createDashboardStatusBadge({ prefix: PREFIX });

export const BpmnmEmptyState = createDashboardEmptyState({
  classNames: emptyStatePanelBemClasses(PREFIX),
  defaultTitle: "Nenhum modelo",
  defaultMessage: "Nenhum item encontrado.",
});

export const BpmnmTextField = createDashboardTextField({
  classNames: textFieldBemClasses(PREFIX),
});

export const BpmnmDataCardsGrid = createDashboardDataCardsGrid({ prefix: PREFIX });

export const BpmnmDataRecordCard = createDashboardDataRecordCard({ prefix: PREFIX });

export const BpmnmFilters = createDashboardFiltersKit({
  prefix: PREFIX,
  labels: { filtersAriaLabel: "Filtrar modelos" },
  portalScopeClassName: BPMNM_ROOT_CLASS,
});

export const bpmnmFileDropzoneClasses = fileDropzoneBemClasses(PREFIX, "file-dropzone");

export const BPMNM_FILE_DROPZONE_LABELS: FileDropzoneLabels = {
  title: "Arraste o arquivo BPMN aqui",
  hint: "ou clique para escolher (.bpmn, .xml)",
};
