import {
  createDashboardEditableSectionCard,
  editableSectionCardTransformometroClasses,
} from "@delpi/plugin-ui/index";

import { softActionBtnClass } from "../SoftActionButton";

const LABELS = {
  edit: "Editar",
  save: "Salvar",
  saving: "Salvando…",
  cancel: "Cancelar",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const CLASS_NAMES = {
  ...editableSectionCardTransformometroClasses("ds"),
  /** Soft tonal edit CTA (Process Workspace / section cards). */
  ghostButton: softActionBtnClass(),
};

export const EditableSectionCard = createDashboardEditableSectionCard({
  classNames: CLASS_NAMES,
  labels: LABELS,
});
