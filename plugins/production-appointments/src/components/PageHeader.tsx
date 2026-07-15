import { createDashboardPageHeader, pageHeaderTitleRowBemClasses } from "@delpi/plugin-ui/index";

export const PageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses("pa", {
    buttonClass: "pa-btn pa-btn--secondary",
  }),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});
