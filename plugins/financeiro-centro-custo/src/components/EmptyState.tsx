import {
  createDashboardEmptyState,
  createDashboardLoadingState,
  emptyStateCardBemClasses,
  loadingStateCardBemClasses,
} from "@delpi/plugin-ui/index";

const emptyCard = emptyStateCardBemClasses("fcc");

export const EmptyState = createDashboardEmptyState({
  classNames: {
    root: emptyCard.root,
    withTitle: true,
  },
  defaultTitle: "Nenhum dado encontrado",
  defaultMessage: "Ajuste os filtros ou o período para visualizar resultados.",
});

export const LoadingState = createDashboardLoadingState({
  classNames: loadingStateCardBemClasses("fcc"),
  defaultMessage: "Carregando…",
});
