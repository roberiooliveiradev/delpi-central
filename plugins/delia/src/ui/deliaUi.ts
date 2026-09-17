import {
  createDashboardEmptyState,
  createDashboardPageHeader,
  emptyStatePanelBemClasses,
  pageHeaderTitleRowBemClasses,
} from "@delpi/plugin-ui/index";

export const DELIA_ROOT_CLASS = "dashboard-delia";
export const DELIA_PREFIX = "delia";

export const DeliaPageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses(DELIA_PREFIX),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});

export const DeliaEmptyState = createDashboardEmptyState({
  classNames: emptyStatePanelBemClasses(DELIA_PREFIX),
  defaultTitle: "Fundação operacional pronta",
  defaultMessage:
    "Shell standalone da DÉLIA. Capacidades de negócio entram em tarefas posteriores.",
});
