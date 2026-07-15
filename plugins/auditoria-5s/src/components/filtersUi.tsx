import {
  FilterInputField as PluginFilterInputField,
  FilterSelectField as PluginFilterSelectField,
  createFilterBarShell,
  delpiUiClass,
  selectControlBemClasses,
  type FilterInputFieldClassNames,
  type FilterInputFieldProps,
  type FilterSelectFieldProps,
} from "@delpi/plugin-ui/index";

function assertPluginUiExport(name: string, value: unknown): void {
  if (value == null) {
    throw new Error(
      `@delpi/plugin-ui não exportou "${name}". Rebuild do remote plugin-ui e hard refresh do portal.`,
    );
  }
}

assertPluginUiExport("FilterInputField", PluginFilterInputField);
assertPluginUiExport("FilterSelectField", PluginFilterSelectField);
assertPluginUiExport("createFilterBarShell", createFilterBarShell);
assertPluginUiExport("selectControlBemClasses", selectControlBemClasses);

/** Dual-class fields do painel analytics (FilterBarShell). */
const FIELD_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: delpiUiClass("a5s-analytics-filter-field", "delpi-ui-filter-box"),
  fieldLabel: "a5s-analytics-filter-field__label",
};

/**
 * Domínio da listagem (`a5s-filters-card`) — não é shell do kit;
 * classes locais de layout do card de filtros da lista.
 */
const LIST_FIELD_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "a5s-filters-card__field",
  fieldLabel: "a5s-filters-card__field-label",
};

const ANALYTICS_SELECT_CLASS_NAMES = selectControlBemClasses("a5s");

export const FilterBarShell = createFilterBarShell({
  prefix: "a5s",
  block: "analytics-filters",
  withGrid: true,
  embeddedByDefault: true,
  defaultAriaLabel: "Filtros do painel de auditoria 5S",
});

export function FilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={FIELD_CLASS_NAMES} {...props} />;
}

export function FilterSelectField(
  props: Omit<FilterSelectFieldProps, "classNames" | "selectClassNames" | "selectLabels">,
) {
  return (
    <PluginFilterSelectField
      classNames={FIELD_CLASS_NAMES}
      selectClassNames={ANALYTICS_SELECT_CLASS_NAMES}
      portalScopeClassName="dashboard-auditoria-5s"
      {...props}
    />
  );
}

export function ListFilterInputField(props: Omit<FilterInputFieldProps, "classNames">) {
  return <PluginFilterInputField classNames={LIST_FIELD_CLASS_NAMES} {...props} />;
}

export function ListFilterSelectField(
  props: Omit<FilterSelectFieldProps, "classNames" | "selectClassNames" | "selectLabels">,
) {
  return (
    <PluginFilterSelectField
      classNames={LIST_FIELD_CLASS_NAMES}
      selectClassNames={ANALYTICS_SELECT_CLASS_NAMES}
      portalScopeClassName="dashboard-auditoria-5s"
      {...props}
    />
  );
}
