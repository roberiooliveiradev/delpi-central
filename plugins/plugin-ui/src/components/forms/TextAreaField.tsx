import { useId } from "react";

import { FieldLabel } from "../help/FieldLabel";

import type { TextFieldClassNames } from "./TextField";
import { textFieldBemClasses } from "./TextField";

export type TextAreaFieldClassNames = TextFieldClassNames & {
  controlTextarea: string;
};

export type TextAreaFieldProps = {
  id?: string;
  label: string;
  hint?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  fullWidth?: boolean;
  classNames: TextAreaFieldClassNames;
};

export function textAreaFieldBemClasses(prefix: string): TextAreaFieldClassNames {
  const field = textFieldBemClasses(prefix);
  return {
    ...field,
    controlTextarea: `${field.control} ${prefix}-field__control--textarea`,
  };
}

export const textAreaFieldPacClasses = textAreaFieldBemClasses;

export function TextAreaField({
  id,
  label,
  hint,
  value,
  onChange,
  placeholder,
  rows = 4,
  disabled = false,
  required = false,
  className,
  fullWidth = false,
  classNames,
}: TextAreaFieldProps) {
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
      <textarea
        id={fieldId}
        className={classNames.controlTextarea}
        rows={rows}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}

export type DashboardTextAreaFieldProps = Omit<TextAreaFieldProps, "classNames">;

export function createDashboardTextAreaField(config: { classNames: TextAreaFieldClassNames }) {
  return function DashboardTextAreaField(props: DashboardTextAreaFieldProps) {
    return <TextAreaField classNames={config.classNames} {...props} />;
  };
}
