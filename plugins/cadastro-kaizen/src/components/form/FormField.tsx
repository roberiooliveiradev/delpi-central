import type { ReactNode } from "react";

import { FieldLabel } from "../ui/HelpTooltip";

type BaseFieldProps = {
  id: string;
  label: string;
  hint?: string;
  span?: boolean;
  required?: boolean;
};

function fieldClass(span?: boolean): string {
  return span ? "kz-field kz-span-2" : "kz-field";
}

/** Wrapper genérico: rótulo (com ajuda opcional) + controle. */
export function FormField({
  id,
  label,
  hint,
  span,
  children,
}: BaseFieldProps & { children: ReactNode }) {
  return (
    <div className={fieldClass(span)}>
      <FieldLabel label={label} htmlFor={id} hint={hint} />
      {children}
    </div>
  );
}

type TextFieldProps = BaseFieldProps & {
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "date";
  placeholder?: string;
  maxLength?: number;
  inputMode?: "decimal" | "numeric";
};

export function TextField({
  id,
  label,
  hint,
  span,
  required,
  value,
  onChange,
  type = "text",
  placeholder,
  maxLength,
  inputMode,
}: TextFieldProps) {
  return (
    <FormField id={id} label={label} hint={hint} span={span}>
      <input
        id={id}
        type={type}
        required={required}
        value={value}
        placeholder={placeholder}
        maxLength={maxLength}
        inputMode={inputMode}
        onChange={(event) => onChange(event.target.value)}
      />
    </FormField>
  );
}

type Option = { value: string; label: string };

type SelectFieldProps = BaseFieldProps & {
  value: string;
  onChange: (value: string) => void;
  options: readonly Option[];
  placeholderOption?: string;
};

export function SelectField({
  id,
  label,
  hint,
  span,
  required,
  value,
  onChange,
  options,
  placeholderOption,
}: SelectFieldProps) {
  return (
    <FormField id={id} label={label} hint={hint} span={span}>
      <select
        id={id}
        required={required}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {placeholderOption !== undefined ? <option value="">{placeholderOption}</option> : null}
        {options.map((item) => (
          <option key={item.value} value={item.value}>
            {item.label}
          </option>
        ))}
      </select>
    </FormField>
  );
}

type TextAreaFieldProps = BaseFieldProps & {
  value: string;
  onChange: (value: string) => void;
  rows?: number;
};

export function TextAreaField({
  id,
  label,
  hint,
  span = true,
  value,
  onChange,
  rows,
}: TextAreaFieldProps) {
  return (
    <FormField id={id} label={label} hint={hint} span={span}>
      <textarea
        id={id}
        rows={rows}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </FormField>
  );
}
