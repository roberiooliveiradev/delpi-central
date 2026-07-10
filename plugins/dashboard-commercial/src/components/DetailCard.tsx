import { createDashboardDetailCard, detailCardRichBemClasses } from "@delpi/plugin-ui/index";

export const DetailCard = createDashboardDetailCard({
  classNames: detailCardRichBemClasses("dc"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});
