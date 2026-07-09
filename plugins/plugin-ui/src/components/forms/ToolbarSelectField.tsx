import {
  createDashboardSelectControl,
  selectControlBemClasses,
  type SelectControlClassNames,
  type SelectControlLabels,
  type SelectOption,
} from "./SelectField";

export const TOOLBAR_SELECT_PREFIX = "delpi-ui-toolbar";

export function selectControlToolbarBemClasses(): SelectControlClassNames {
  return selectControlBemClasses(TOOLBAR_SELECT_PREFIX);
}

export const DEFAULT_TOOLBAR_SELECT_LABELS: SelectControlLabels = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção",
  searchAriaLabel: (label) => `Buscar ${label ?? "opções"}`,
};

export const ToolbarSelectControl = createDashboardSelectControl({
  control: selectControlToolbarBemClasses(),
  labels: DEFAULT_TOOLBAR_SELECT_LABELS,
});

export type ToolbarSelectFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly SelectOption[];
  placeholderOption?: string;
  /** Quando false, não inclui opção vazia inicial. */
  allowEmptyOption?: boolean;
  title?: string;
  className?: string;
  disabled?: boolean;
  searchable?: boolean;
};

/** Select compacto com rótulo inline — toolbars de gráfico/tabela/filtros densos. */
export function ToolbarSelectField({
  label,
  value,
  onChange,
  options,
  placeholderOption = "Todos",
  allowEmptyOption = true,
  title,
  className,
  disabled,
  searchable = false,
}: ToolbarSelectFieldProps) {
  return (
    <label
      className={["delpi-ui-toolbar-select-field", className].filter(Boolean).join(" ")}
      title={title}
    >
      <span className="delpi-ui-toolbar-select-field__label">{label}</span>
      <ToolbarSelectControl
        value={value}
        onChange={onChange}
        options={options}
        allowEmpty={allowEmptyOption}
        emptyLabel={placeholderOption}
        searchable={searchable}
        disabled={disabled}
        ariaLabel={label}
      />
    </label>
  );
}
