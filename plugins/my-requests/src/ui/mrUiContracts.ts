import { dataTableBemClasses } from "@delpi/plugin-ui/index";

import { MR_UI_PREFIX } from "./mrUi";

export const mrDataTableClassNames = dataTableBemClasses(MR_UI_PREFIX);

export const mrDataTableLabels = {
  emptyMessage: "Nenhuma solicitação encontrada.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
};
