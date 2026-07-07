import { FieldLabel } from "../help/FieldLabel";

export type FilterCheckboxFieldClassNames = {
  root: string;
  labelRow: string;
  checkboxControl: string;
  checkboxRoot: string;
};

export type FilterCheckboxFieldLabels = {
  defaultCheckboxLabel: string;
};

export type FilterCheckboxFieldProps = {
  id: string;
  label: string;
  hint?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  checkboxLabel?: string;
  disabled?: boolean;
  classNames: FilterCheckboxFieldClassNames;
  labels: FilterCheckboxFieldLabels;
};

export function filterCheckboxFieldBemClasses(prefix: string): FilterCheckboxFieldClassNames {
  return {
    root: `${prefix}-field ${prefix}-field--filter-checkbox`,
    labelRow: `${prefix}-field__label ${prefix}-field__label-row`,
    checkboxRoot: `${prefix}-checkbox`,
    checkboxControl: `${prefix}-checkbox ${prefix}-filter-checkbox-control`,
  };
}

export const filterCheckboxFieldPacClasses = filterCheckboxFieldBemClasses;

export function FilterCheckboxField({
  id,
  label,
  hint,
  checked,
  onChange,
  checkboxLabel,
  disabled = false,
  classNames,
  labels,
}: FilterCheckboxFieldProps) {
  const resolvedCheckboxLabel = checkboxLabel ?? labels.defaultCheckboxLabel;

  return (
    <div className={classNames.root}>
      <span className={classNames.labelRow}>
        <FieldLabel label={label} hint={hint} />
      </span>
      <label className={classNames.checkboxControl} htmlFor={id}>
        <input
          id={id}
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={(event) => onChange(event.target.checked)}
        />
        <span>{resolvedCheckboxLabel}</span>
      </label>
    </div>
  );
}

export type DashboardFilterCheckboxFieldProps = Omit<
  FilterCheckboxFieldProps,
  "classNames" | "labels"
>;

export function createDashboardFilterCheckboxField(config: {
  classNames: FilterCheckboxFieldClassNames;
  labels: FilterCheckboxFieldLabels;
}) {
  return function DashboardFilterCheckboxField(props: DashboardFilterCheckboxFieldProps) {
    return (
      <FilterCheckboxField classNames={config.classNames} labels={config.labels} {...props} />
    );
  };
}
