import type { InputHTMLAttributes, ReactNode } from "react";
import { useId } from "react";

import { FieldLabel } from "../help/FieldLabel";

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

export type FilterSelectFieldProps = {
  label: string;
  hint?: string;
  id?: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly FilterSelectOption[];
  placeholderOption?: string;
  disabled?: boolean;
  classNames: FilterInputFieldClassNames;
};

export type DashboardFiltersLabels = {
  filtersAriaLabel: string;
};

export type DashboardFiltersKit = {
  FiltersRow: (props: Omit<FiltersRowProps, "classNames" | "ariaLabel"> & { ariaLabel?: string }) => ReactNode;
  FilterInputField: (props: Omit<FilterInputFieldProps, "classNames">) => ReactNode;
  FilterSelectField: (props: Omit<FilterSelectFieldProps, "classNames">) => ReactNode;
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
  classNames,
}: FilterSelectFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;

  return (
    <label className={classNames.filterBox} htmlFor={fieldId}>
      <FieldLabel label={label} hint={hint} className={classNames.fieldLabel} />
      <select
        id={fieldId}
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
      >
        {placeholderOption !== undefined ? <option value="">{placeholderOption}</option> : null}
        {options.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export function createDashboardFiltersKit(config: {
  prefix: string;
  labels: DashboardFiltersLabels;
}): DashboardFiltersKit {
  const classNames = filtersRowBemClasses(config.prefix);

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
      return <FilterSelectField classNames={classNames} {...props} />;
    },
  };
}

/** Alias de roadmap F2.6 — shell de filtros (linha flex + campos). */
export const FilterBar = FiltersRow;
