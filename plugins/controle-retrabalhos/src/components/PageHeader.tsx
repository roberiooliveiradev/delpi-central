import { createDashboardPageHeader, pageHeaderTitleRowBemClasses } from "@delpi/plugin-ui";

export const PageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses("cr"),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});
