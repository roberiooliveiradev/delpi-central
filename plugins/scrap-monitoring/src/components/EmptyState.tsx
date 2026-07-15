import {
  createDashboardEmptyState,
} from "@delpi/plugin-ui/index";

export const EmptyState = createDashboardEmptyState({
  classNames: {
    root: "sm-card sm-state-box sm-state-box--empty",
    withTitle: true,
  },
  defaultTitle: "Sem refugos no período",
  defaultMessage: "Não há registros de refugo para os filtros selecionados.",
});
