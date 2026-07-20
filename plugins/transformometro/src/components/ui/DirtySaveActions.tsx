import { createDashboardDirtySaveActions, formActionsBemClasses } from "@delpi/plugin-ui/index";

/** Rodapé Salvar alinhado — só aparece com dirty (kit FormActions). */
export const DirtySaveActions = createDashboardDirtySaveActions({
  classNames: formActionsBemClasses("ds"),
  primaryButtonClassName: "ds-primary-btn",
});
