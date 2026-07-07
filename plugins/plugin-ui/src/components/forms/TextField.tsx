import { useId } from "react";

import { FieldLabel } from "../help/FieldLabel";

export type TextFieldClassNames = {
  root: string;
  labelWrapper?: string;
  fieldLabel: string;
  control: string;
  required: string;
  fullWidthModifier?: string;
};

export type TextFieldProps = {
  id?: string;
  label: string;
  hint?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: "text" | "date" | "search";
  disabled?: boolean;
  required?: boolean;
  className?: string;
  fullWidth?: boolean;
  classNames: TextFieldClassNames;
};

export function textFieldBemClasses(prefix: string): TextFieldClassNames {
  return {
    root: `${prefix}-field`,
    labelWrapper: `${prefix}-field__label`,
    fieldLabel: "",
    control: `${prefix}-field__control`,
    required: `${prefix}-field__required`,
    fullWidthModifier: `${prefix}-field--full`,
  };
}

export const textFieldPacClasses = textFieldBemClasses;

export function TextField({
  id,
  label,
  hint,
  value,
  onChange,
  placeholder,
  type = "text",
  disabled = false,
  required = false,
  className,
  fullWidth = false,
  classNames,
}: TextFieldProps) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const rootClass = [
    classNames.root,
    fullWidth ? classNames.fullWidthModifier : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass}>
      <label htmlFor={fieldId} className={classNames.labelWrapper}>
        <FieldLabel className={classNames.fieldLabel || undefined} label={label} hint={hint} />
        {required ? <span className={classNames.required}> *</span> : null}
      </label>
      <input
        id={fieldId}
        type={type}
        className={classNames.control}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

export type DashboardTextFieldProps = Omit<TextFieldProps, "classNames">;

export function createDashboardTextField(config: { classNames: TextFieldClassNames }) {
  return function DashboardTextField(props: DashboardTextFieldProps) {
    return <TextField classNames={config.classNames} {...props} />;
  };
}
