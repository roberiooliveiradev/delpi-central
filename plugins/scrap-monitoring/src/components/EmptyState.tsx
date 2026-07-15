import {
  createDashboardEmptyState,
  emptyStateCardBemClasses,
} from "@delpi/plugin-ui/index";

const cardEmpty = emptyStateCardBemClasses("sm");

export const EmptyState = createDashboardEmptyState({
  classNames: {
    root: cardEmpty.root,
    withTitle: true,
  },
  defaultTitle: "Sem refugos no período",
  defaultMessage: "Não há registros de refugo para os filtros selecionados.",
});
