import {
  createDashboardEmptyState,
  createDashboardLoadingState,
  emptyStateCardBemClasses,
  loadingStateCardBemClasses,
} from "@delpi/plugin-ui/index";

export const EmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses("cr"),
  defaultMessage: "Nenhum registro encontrado para o período.",
});

export const LoadingState = createDashboardLoadingState({
  classNames: loadingStateCardBemClasses("cr"),
  defaultMessage: "Carregando…",
});
