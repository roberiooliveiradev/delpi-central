import { createDashboardTitleWithHelp, titleWithHelpPacClasses } from "@delpi/plugin-ui";

export const TitleWithHelp = createDashboardTitleWithHelp({
  classNames: titleWithHelpPacClasses("pac"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});
