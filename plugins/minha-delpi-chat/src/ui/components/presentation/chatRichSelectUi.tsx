import {
  createDashboardSelectControl,
  selectControlBemClasses,
  type SelectControlLabels,
} from "@delpi/plugin-ui";

const CHAT_RICH_SELECT_LABELS: SelectControlLabels = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção",
  searchAriaLabel: (label) => `Buscar ${label ?? "opções"}`,
};

export const ChatRichSelectControl = createDashboardSelectControl({
  control: selectControlBemClasses("mdc-rich"),
  labels: CHAT_RICH_SELECT_LABELS,
});
