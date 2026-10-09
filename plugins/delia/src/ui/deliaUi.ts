import {
  createDashboardEmptyState,
  createDashboardLoadingActivityBadge,
  createDashboardPageHeader,
  createDashboardStatusBadge,
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

export const DeliaStatusBadge = createDashboardStatusBadge({
  prefix: DELIA_PREFIX,
});

/** Indeterminate in-flight indicator — honest about only the pending
 *  POST; never claims which provider/stage is running (doc 69 §12). */
export const DeliaLoadingBadge = createDashboardLoadingActivityBadge({
  prefix: DELIA_PREFIX,
});
