import { createDashboardPageHeader, pageHeaderTitleRowBemClasses } from "@delpi/plugin-ui/index";

export const PageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses("fcc"),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});
