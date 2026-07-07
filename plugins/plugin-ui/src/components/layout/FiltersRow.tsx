import type { InputHTMLAttributes, ReactNode } from "react";

import { FieldLabel } from "../help/FieldLabel";

export type FiltersRowClassNames = {
  row: string;
  rowExtended: string;
};

export type FiltersRowProps = {
  children: ReactNode;
  classNames: FiltersRowClassNames;
  ariaLabel: string;
  variant?: "default" | "extended";
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

export type DashboardFiltersLabels = {
  filtersAriaLabel: string;
};

export type DashboardFiltersKit = {
  FiltersRow: (props: Omit<FiltersRowProps, "classNames" | "ariaLabel"> & { ariaLabel?: string }) => ReactNode;
  FilterInputField: (props: Omit<FilterInputFieldProps, "classNames">) => ReactNode;
};

/** Monta classNames BEM `{prefix}-filters-row` dos dashboards departamentais. */
export function filtersRowBemClasses(prefix: string): FiltersRowClassNames & FilterInputFieldClassNames {
  return {
    row: `${prefix}-filters-row`,
    rowExtended: `${prefix}-filters-row ${prefix}-filters-row--extended`,
    filterBox: `${prefix}-filter-box ${prefix}-field`,
    fieldLabel: `${prefix}-field__label`,
  };
}

export function FiltersRow({
  children,
  classNames,
  ariaLabel,
  variant = "default",
  className,
}: FiltersRowProps) {
  const baseClass = variant === "extended" ? classNames.rowExtended : classNames.row;
  const sectionClass = [baseClass, className].filter(Boolean).join(" ");

  return (
    <section className={sectionClass} aria-label={ariaLabel}>
      {children}
    </section>
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
  return (
    <label className={classNames.filterBox} htmlFor={id}>
      <FieldLabel label={label} hint={hint} className={classNames.fieldLabel} />
      <input
        id={id}
        type={type}
        value={value}
        disabled={disabled}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
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
  };
}

/** Alias de roadmap F2.6 — shell de filtros (linha flex + campos). */
export const FilterBar = FiltersRow;
