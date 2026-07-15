import {
  createDashboardEmptyState,
  createDashboardLoadingState,
  emptyStateCardBemClasses,
  loadingStateCardBemClasses,
} from "@delpi/plugin-ui/index";

export const EmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses("pa"),
  defaultMessage: "Não há apontamentos de produção no período e filtros selecionados.",
});

export const LoadingState = createDashboardLoadingState({
  classNames: loadingStateCardBemClasses("pa"),
  defaultMessage: "Carregando…",
});
