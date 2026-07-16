import { createDashboardPageHeader, pageHeaderTitleRowBemClasses } from "@delpi/plugin-ui/index";

export const PageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses("sm", {
    buttonClass: "sm-btn sm-btn--secondary",
  }),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});
