import { useId } from "react";

import { FieldLabel } from "../help/FieldLabel";

export type DateFieldClassNames = {
  root: string;
  labelClass: string;
  input?: string;
  wideModifier?: string;
  required?: string;
};

export type DateFieldProps = {
  id?: string;
  label: string;
  hint?: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  disabled?: boolean;
  wide?: boolean;
  className?: string;
  classNames: DateFieldClassNames;
};

export function dateFieldBemClasses(prefix: string): DateFieldClassNames {
  return {
    root: `${prefix}-field`,
    labelClass: `${prefix}-field__label`,
    wideModifier: `${prefix}-span-2`,
    required: `${prefix}-field__required`,
  };
}

export function DateField({
  id,
  label,
  hint,
  value,
  onChange,
  required = false,
  disabled = false,
  wide = false,
  className,
  classNames,
}: DateFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const rootClass = [
    classNames.root,
    wide ? classNames.wideModifier : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass}>
      <FieldLabel
        className={classNames.labelClass}
        label={label}
        hint={hint}
        htmlFor={fieldId}
      />
      <input
        id={fieldId}
        type="date"
        value={value}
        required={required}
        disabled={disabled}
        className={classNames.input}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

export type DashboardDateFieldProps = Omit<DateFieldProps, "classNames">;

export function createDashboardDateField(config: { classNames: DateFieldClassNames }) {
  return function DashboardDateField(props: DashboardDateFieldProps) {
    return <DateField classNames={config.classNames} {...props} />;
  };
}
