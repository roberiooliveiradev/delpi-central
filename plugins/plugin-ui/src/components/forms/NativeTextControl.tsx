import { forwardRef, type ChangeEvent, type InputHTMLAttributes, type KeyboardEvent } from "react";

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
  onFocus?: () => void;
  onKeyDown?: (event: KeyboardEvent<HTMLInputElement>) => void;
  onKeyUp?: (event: KeyboardEvent<HTMLInputElement>) => void;
  autoFocus?: boolean;
  list?: string;
};

/**
 * `<input>` nativo compacto (sem FormFieldShell) — células / FormatPane com label externo.
 */
export const NativeTextControl = forwardRef<HTMLInputElement, NativeTextControlProps>(
  function NativeTextControl(
    {
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
      onFocus,
      onKeyDown,
      onKeyUp,
      autoFocus,
      list,
    },
    ref,
  ) {
    return (
      <input
        ref={ref}
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
        autoFocus={autoFocus}
        list={list}
        onBlur={onBlur}
        onFocus={onFocus}
        onKeyDown={onKeyDown}
        onKeyUp={onKeyUp}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(event.target.value)}
      />
    );
  },
);
