import { createDashboardTitleWithHelp, titleWithHelpBemClasses } from "@delpi/plugin-ui";

export const TitleWithHelp = createDashboardTitleWithHelp({
  classNames: titleWithHelpBemClasses("kz"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});
