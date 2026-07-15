import {
  FilterInputField as PluginFilterInputField,
  FilterSelectField as PluginFilterSelectField,
  createFilterBarShell,
  selectControlBemClasses,
  type FilterInputFieldClassNames,
  type FilterInputFieldProps,
  type FilterSelectFieldProps,
} from "@delpi/plugin-ui/index";

const FIELD_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "sm-field",
  fieldLabel: "sm-field__label",
};

const SELECT_CLASS_NAMES = selectControlBemClasses("sm");

export const FilterBarShell = createFilterBarShell({
  prefix: "sm",
  defaultAriaLabel: "Filtros de refugos",
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
      portalScopeClassName="dashboard-scrap-monitoring"
      {...props}
    />
  );
}
