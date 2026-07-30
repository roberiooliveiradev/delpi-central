import {
  dataTableBemClasses,
  statusBadgeBemClasses,
} from "@delpi/plugin-ui/index";

const PREFIX = "comite-etica-conduta";

export const cecDataTableClassNames = dataTableBemClasses(PREFIX);

export const cecDataTableLabels = {
  emptyMessage: "Nenhuma ata encontrada para os filtros atuais.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
};

export const cecStatusBadgeClassNames = statusBadgeBemClasses(PREFIX);
