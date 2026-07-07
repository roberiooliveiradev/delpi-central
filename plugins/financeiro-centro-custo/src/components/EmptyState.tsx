import {
  createDashboardEmptyState,
  createDashboardLoadingState,
  emptyStatePanelBemClasses,
  loadingStatePanelBemClasses,
} from "@delpi/plugin-ui";

export const EmptyState = createDashboardEmptyState({
  classNames: emptyStatePanelBemClasses("fcc"),
  defaultTitle: "Nenhum dado encontrado",
  defaultMessage: "Ajuste os filtros ou o período para visualizar resultados.",
});

export const LoadingState = createDashboardLoadingState({
  classNames: loadingStatePanelBemClasses("fcc"),
  defaultMessage: "Carregando…",
});
