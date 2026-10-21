import {
  confirmModalBemClasses,
  createDashboardEmptyState,
  createDashboardPageHeader,
  createHostContainedModalShell,
  emptyStatePanelBemClasses,
  formFieldShellBemClasses,
  pageHeaderTitleRowBemClasses,
} from "@delpi/plugin-ui/index";

export const ROOT_CLASS = "dashboard-metalography";
export const PREFIX = "mg";

export const fieldClassNames = formFieldShellBemClasses(PREFIX);
export const confirmClassNames = confirmModalBemClasses(PREFIX);

export const MetalographyPageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses(PREFIX),
  labels: { refresh: "Atualizar", refreshing: "Atualizando…" },
});

export const MetalographyEmpty = createDashboardEmptyState({
  classNames: emptyStatePanelBemClasses(PREFIX),
  defaultTitle: "Nenhum relatório",
  defaultMessage: "Não há relatórios metalográficos para os filtros atuais.",
});

export const MetalographyDialog = createHostContainedModalShell({
  prefix: PREFIX,
  portalScopeClassName: ROOT_CLASS,
  containedLayout: "dialog",
});
