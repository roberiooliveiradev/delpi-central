import type { ChangeEvent } from "react";

export type NativeSelectOption = {
  value: string;
  label: string;
};

export type NativeSelectControlProps = {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly NativeSelectOption[];
  placeholderOption?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  "aria-label"?: string;
};

/**
 * `<select>` nativo compacto (sem FormFieldShell) — células de tabela / PAC.
 */
export function NativeSelectControl({
  id,
  value,
  onChange,
  options,
  placeholderOption,
  disabled,
  required,
  className,
  "aria-label": ariaLabel,
}: NativeSelectControlProps) {
  return (
    <select
      id={id}
      className={className}
      value={value}
      disabled={disabled}
      required={required}
      aria-label={ariaLabel}
      onChange={(event: ChangeEvent<HTMLSelectElement>) => onChange(event.target.value)}
    >
      {placeholderOption !== undefined ? <option value="">{placeholderOption}</option> : null}
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}
