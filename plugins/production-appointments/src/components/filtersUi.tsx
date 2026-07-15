import {
  FilterInputField as PluginFilterInputField,
  FilterSelectField as PluginFilterSelectField,
  createFilterBarShell,
  filtersRowBemClasses,
  selectControlBemClasses,
  type FilterInputFieldProps,
  type FilterSelectFieldProps,
} from "@delpi/plugin-ui/index";

const FIELD_CLASS_NAMES = filtersRowBemClasses("pa");
const SELECT_CLASS_NAMES = selectControlBemClasses("pa");

export const FilterBarShell = createFilterBarShell({
  prefix: "pa",
  defaultAriaLabel: "Filtros de apontamento de produção",
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
      selectClassNames={SELECT_CLASS_NAMES}
      portalScopeClassName="dashboard-production-appointments"
      {...props}
    />
  );
}
