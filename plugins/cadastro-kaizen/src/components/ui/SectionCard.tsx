import { createDashboardSectionCard, sectionCardKaizenBemClasses } from "@delpi/plugin-ui/index";

export const SectionCard = createDashboardSectionCard({
  classNames: sectionCardKaizenBemClasses("kz"),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});
