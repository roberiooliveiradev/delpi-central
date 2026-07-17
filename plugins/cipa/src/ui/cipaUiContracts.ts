import {
  dataTableBemClasses,
  statusBadgeBemClasses,
} from "@delpi/plugin-ui/index";

const PREFIX = "cipa";

export const cipaDataTableClassNames = dataTableBemClasses(PREFIX);

export const cipaDataTableLabels = {
  emptyMessage: "Nenhuma ata encontrada para os filtros atuais.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
};

export const cipaStatusBadgeClassNames = statusBadgeBemClasses(PREFIX);
