import {
  createDashboardSelectControl,
  FilterInputField as PluginFilterInputField,
  FilterSelectField as PluginFilterSelectField,
  selectControlBemClasses,
  type FilterInputFieldClassNames,
  type FilterInputFieldProps,
  type FilterSelectFieldProps,
  type SelectControlLabels,
} from "@delpi/plugin-ui";

const SI_SELECT_LABELS: SelectControlLabels = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção encontrada",
  searchAriaLabel: (label) => `Buscar ${label ?? "opção"}`,
};

const INDICATOR_FILTER_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "si-indicator-filter",
  fieldLabel: "si-indicator-filter__label",
};

const REFERENCE_FILTER_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "si-reference-filters__field",
  fieldLabel: "si-reference-filters__label",
};

const PRESENTATION_FILTER_CLASS_NAMES: FilterInputFieldClassNames = {
  filterBox: "si-presentation-topbar__filter",
  fieldLabel: "si-presentation-topbar__filter-label",
};

const SELECT_CLASS_NAMES = selectControlBemClasses("si");

/** SelectControl temático SI — formulários admin, modais e filtros internos. */
export const SiSelectControl = createDashboardSelectControl({
  control: SELECT_CLASS_NAMES,
  labels: SI_SELECT_LABELS,
});

export const SI_VALUE_UNIT_OPTIONS = [
  { value: "", label: "Não informada" },
  { value: "percent", label: "Percentual" },
  { value: "currency", label: "Moeda" },
  { value: "ppm", label: "PPM" },
  { value: "days", label: "Dias" },
  { value: "hours", label: "Horas" },
  { value: "count", label: "Quantidade" },
  { value: "months", label: "Meses" },
  { value: "ratio", label: "Razão" },
] as const;

export function IndicatorFilterInputField(
  props: Omit<FilterInputFieldProps, "classNames">,
) {
  return <PluginFilterInputField classNames={INDICATOR_FILTER_CLASS_NAMES} {...props} />;
}

export function IndicatorFilterSelectField(
  props: Omit<FilterSelectFieldProps, "classNames" | "selectClassNames" | "selectLabels">,
) {
  return (
    <PluginFilterSelectField
      classNames={INDICATOR_FILTER_CLASS_NAMES}
      selectClassNames={SELECT_CLASS_NAMES}
      {...props}
    />
  );
}

export function ReferenceFilterInputField(
  props: Omit<FilterInputFieldProps, "classNames">,
) {
  return <PluginFilterInputField classNames={REFERENCE_FILTER_CLASS_NAMES} {...props} />;
}

export function ReferenceFilterSelectField(
  props: Omit<FilterSelectFieldProps, "classNames" | "selectClassNames" | "selectLabels">,
) {
  return (
    <PluginFilterSelectField
      classNames={REFERENCE_FILTER_CLASS_NAMES}
      selectClassNames={SELECT_CLASS_NAMES}
      {...props}
    />
  );
}

export function PresentationFilterInputField(
  props: Omit<FilterInputFieldProps, "classNames">,
) {
  return <PluginFilterInputField classNames={PRESENTATION_FILTER_CLASS_NAMES} {...props} />;
}

export function PresentationFilterSelectField(
  props: Omit<FilterSelectFieldProps, "classNames" | "selectClassNames" | "selectLabels">,
) {
  return (
    <PluginFilterSelectField
      classNames={PRESENTATION_FILTER_CLASS_NAMES}
      selectClassNames={SELECT_CLASS_NAMES}
      {...props}
    />
  );
}
