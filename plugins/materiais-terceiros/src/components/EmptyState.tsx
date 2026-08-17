import {
  createDashboardEmptyState,
  emptyStateCardBemClasses,
} from "@delpi/plugin-ui/index";

export const EmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses("mt"),
  defaultMessage:
    "Informe a filial e um critério (produto, ref. cliente, NF, período ou somente saldo).",
});
