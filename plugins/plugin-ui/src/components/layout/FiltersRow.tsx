import type { InputHTMLAttributes, ReactNode } from "react";
import { useId } from "react";

import { FieldLabel } from "../help/FieldLabel";
import {
  SelectControl,
  selectControlBemClasses,
  type SelectControlClassNames,
  type SelectControlLabels,
} from "../forms/SelectField";

export type FiltersRowClassNames = {
  row: string;
  rowExtended: string;
  rowCompact?: string;
  trailingBox?: string;
};

export type FiltersRowProps = {
  children: ReactNode;
  classNames: FiltersRowClassNames;
  ariaLabel?: string;
  variant?: "default" | "extended";
  compact?: boolean;
  trailing?: ReactNode;
  as?: "section" | "div";
  className?: string;
};

export type FilterInputFieldClassNames = {
  filterBox: string;
  fieldLabel: string;
};

export type FilterInputFieldProps = {
  label: string;
  hint?: string;
  id?: string;
  type: Extract<InputHTMLAttributes<HTMLInputElement>["type"], "month" | "date" | "text" | "search">;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  classNames: FilterInputFieldClassNames;
};

export type FilterSelectOption = {
  value: string;
  label: string;
};

const DEFAULT_FILTER_SELECT_LABELS: SelectControlLabels = {
  searchPlaceholder: "Buscar…",
  emptyOptions: "Nenhuma opção encontrada.",
  searchAriaLabel: (fieldLabel) =>
    fieldLabel ? `Buscar em ${fieldLabel}` : "Buscar opções",
};

export type FilterSelectFieldProps = {
  label: string;
  hint?: string;
  id?: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly FilterSelectOption[];
  placeholderOption?: string;
  disabled?: boolean;
  searchable?: boolean;
  classNames: FilterInputFieldClassNames;
  /** Classes BEM do SelectControl (`{prefix}-select*`). */
  selectClassNames: SelectControlClassNames;
  selectLabels?: SelectControlLabels;
};

export type DashboardFiltersLabels = {
  filtersAriaLabel: string;
};

export type DashboardFiltersKit = {
  FiltersRow: (props: Omit<FiltersRowProps, "classNames" | "ariaLabel"> & { ariaLabel?: string }) => ReactNode;
  FilterInputField: (props: Omit<FilterInputFieldProps, "classNames">) => ReactNode;
  FilterSelectField: (
    props: Omit<FilterSelectFieldProps, "classNames" | "selectClassNames" | "selectLabels">,
  ) => ReactNode;
};

/** Monta classNames BEM `{prefix}-filters-row` dos dashboards departamentais. */
export function filtersRowBemClasses(prefix: string): FiltersRowClassNames & FilterInputFieldClassNames {
  return {
    row: `${prefix}-filters-row`,
    rowExtended: `${prefix}-filters-row ${prefix}-filters-row--extended`,
    rowCompact: `${prefix}-filters-row ${prefix}-filters-row--compact`,
    trailingBox: `${prefix}-filter-box ${prefix}-filter-box--action`,
    filterBox: `${prefix}-filter-box ${prefix}-field`,
    fieldLabel: `${prefix}-field__label`,
  };
}

export function FiltersRow({
  children,
  classNames,
  ariaLabel,
  variant = "default",
  compact = false,
  trailing,
  as = "section",
  className,
}: FiltersRowProps) {
  const baseClass =
    variant === "extended"
      ? classNames.rowExtended
      : compact && classNames.rowCompact
        ? classNames.rowCompact
        : classNames.row;
  const rootClass = [baseClass, className].filter(Boolean).join(" ");
  const Tag = as;

  return (
    <Tag
      className={rootClass}
      {...(Tag === "section" && ariaLabel ? { "aria-label": ariaLabel } : {})}
    >
      {children}
      {trailing
        ? classNames.trailingBox
          ? <div className={classNames.trailingBox}>{trailing}</div>
          : trailing
        : null}
    </Tag>
  );
}

export function FilterInputField({
  label,
  hint,
  id,
  type,
  value,
  onChange,
  disabled = false,
  placeholder,
  classNames,
}: FilterInputFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;

  return (
    <label className={classNames.filterBox} htmlFor={fieldId}>
      <FieldLabel label={label} hint={hint} className={classNames.fieldLabel} />
      <input
        id={fieldId}
        type={type}
        value={value}
        disabled={disabled}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

export function FilterSelectField({
  label,
  hint,
  id,
  value,
  onChange,
  options,
  placeholderOption,
  disabled = false,
  searchable = false,
  classNames,
  selectClassNames,
  selectLabels = DEFAULT_FILTER_SELECT_LABELS,
}: FilterSelectFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const allowEmpty = placeholderOption !== undefined;

  return (
    <div className={classNames.filterBox}>
      <FieldLabel label={label} hint={hint} className={classNames.fieldLabel} htmlFor={fieldId} />
      <SelectControl
        id={fieldId}
        options={options}
        value={value}
        onChange={onChange}
        disabled={disabled}
        searchable={searchable}
        allowEmpty={allowEmpty}
        emptyLabel={placeholderOption}
        placeholder={placeholderOption ?? "Selecione…"}
        ariaLabel={label}
        classNames={selectClassNames}
        labels={selectLabels}
      />
    </div>
  );
}

export function createDashboardFiltersKit(config: {
  prefix: string;
  labels: DashboardFiltersLabels;
}): DashboardFiltersKit {
  const classNames = filtersRowBemClasses(config.prefix);
  const selectClassNames = selectControlBemClasses(config.prefix);

  return {
    FiltersRow({ ariaLabel, ...props }) {
      return (
        <FiltersRow
          classNames={classNames}
          ariaLabel={ariaLabel ?? config.labels.filtersAriaLabel}
          {...props}
        />
      );
    },
    FilterInputField(props) {
      return <FilterInputField classNames={classNames} {...props} />;
    },
    FilterSelectField(props) {
      return (
        <FilterSelectField
          classNames={classNames}
          selectClassNames={selectClassNames}
          {...props}
        />
      );
    },
  };
}

/** Alias de roadmap F2.6 — shell de filtros (linha flex + campos). */
export const FilterBar = FiltersRow;
