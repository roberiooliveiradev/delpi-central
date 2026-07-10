import {
  createDashboardEditableSectionCard,
  editableSectionCardTransformometroClasses,
} from "@delpi/plugin-ui/index";

const LABELS = {
  edit: "Editar",
  save: "Salvar",
  saving: "Salvando…",
  cancel: "Cancelar",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

export const EditableSectionCard = createDashboardEditableSectionCard({
  classNames: editableSectionCardTransformometroClasses("ds"),
  labels: LABELS,
});
