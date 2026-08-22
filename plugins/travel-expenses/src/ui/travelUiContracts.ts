import { dataTableBemClasses, statusBadgeBemClasses } from "@delpi/plugin-ui/index";

const PREFIX = "te";

export const travelDataTableClassNames = dataTableBemClasses(PREFIX);

export const travelDataTableLabels = {
  emptyMessage: "Nenhuma prestação encontrada para os filtros atuais.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
};

export const travelStatusBadgeClassNames = statusBadgeBemClasses(PREFIX);
