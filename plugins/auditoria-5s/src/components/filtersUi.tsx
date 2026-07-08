import {
  FilterInputField as PluginFilterInputField,
  FilterSelectField as PluginFilterSelectField,
  createFilterBarShell,
  selectControlBemClasses,
  type FilterInputFieldClassNames,
  type FilterInputFieldProps,
  type FilterSelectFieldProps,
} from "@delpi/plugin-ui";

const FIELD_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "a5s-analytics-filter-field",
  fieldLabel: "a5s-analytics-filter-field__label",
};

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
      {...props}
    />
  );
}
