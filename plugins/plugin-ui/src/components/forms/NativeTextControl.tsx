import type { ChangeEvent, InputHTMLAttributes } from "react";

export type NativeTextControlProps = {
  id?: string;
  value: string | number;
  onChange: (value: string) => void;
  type?: "text" | "number" | "url" | "date" | "datetime-local" | "search" | "password" | "month";
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  readOnly?: boolean;
  min?: number | string;
  max?: number | string;
  step?: number | string;
  maxLength?: number;
  className?: string;
  "aria-label"?: string;
  "aria-invalid"?: boolean;
  autoComplete?: InputHTMLAttributes<HTMLInputElement>["autoComplete"];
  spellCheck?: boolean;
  inputMode?: InputHTMLAttributes<HTMLInputElement>["inputMode"];
  onBlur?: () => void;
};

/**
 * `<input>` nativo compacto (sem FormFieldShell) — células / FormatPane com label externo.
 */
export function NativeTextControl({
  id,
  value,
  onChange,
  type = "text",
  placeholder,
  disabled,
  required,
  readOnly,
  min,
  max,
  step,
  maxLength,
  className,
  "aria-label": ariaLabel,
  "aria-invalid": ariaInvalid,
  autoComplete,
  spellCheck,
  inputMode,
  onBlur,
}: NativeTextControlProps) {
  return (
    <input
      id={id}
      className={className}
      type={type}
      value={value}
      placeholder={placeholder}
      disabled={disabled}
      required={required}
      readOnly={readOnly}
      min={min}
      max={max}
      step={step}
      maxLength={maxLength}
      inputMode={inputMode}
      autoComplete={autoComplete}
      spellCheck={spellCheck}
      aria-label={ariaLabel}
      aria-invalid={ariaInvalid}
      onBlur={onBlur}
      onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(event.target.value)}
    />
  );
}
