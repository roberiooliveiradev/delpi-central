import {
  createDashboardSelectControl,
  selectControlBemClasses,
  type SelectControlClassNames,
  type SelectControlLabels,
} from "./SelectField";

export const FORM_SELECT_PREFIX = "delpi-ui";

export function selectControlFormBemClasses(): SelectControlClassNames {
  return selectControlBemClasses(FORM_SELECT_PREFIX);
}

export const DEFAULT_FORM_SELECT_LABELS: SelectControlLabels = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção encontrada",
  searchAriaLabel: (label) => `Buscar ${label ?? "opção"}`,
};

/**
 * SelectControl com visual canônico de dashboard (trigger + painel).
 * CSS: `styles/select-control.css` (`.delpi-ui-select*`).
 * Para densidade de ribbon/toolbar, passe `className="delpi-ui-select--compact"`.
 */
export const FormSelectControl = createDashboardSelectControl({
  control: selectControlFormBemClasses(),
  labels: DEFAULT_FORM_SELECT_LABELS,
});
