import { createDashboardEditableSectionCardPac } from "@delpi/plugin-ui/index";

export const EditableSectionCard = createDashboardEditableSectionCardPac({
  prefix: "pac",
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
    edit: "Editar",
    cancel: "Cancelar",
  },
});
