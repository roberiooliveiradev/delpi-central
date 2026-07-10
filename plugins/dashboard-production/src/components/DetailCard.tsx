import { createDashboardDetailCard, detailCardProductionBemClasses } from "@delpi/plugin-ui/index";

export const DetailCard = createDashboardDetailCard({
  classNames: detailCardProductionBemClasses("dp"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});
