import {
  createDashboardEditableSectionCard,
  editableSectionCardBemClasses,
} from "@delpi/plugin-ui/index";

const LABELS = {
  edit: "Editar",
  save: "Salvar",
  saving: "Salvando…",
  cancel: "Cancelar",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

export const EditableSectionCard = createDashboardEditableSectionCard({
  classNames: editableSectionCardBemClasses("kz"),
  labels: LABELS,
});
