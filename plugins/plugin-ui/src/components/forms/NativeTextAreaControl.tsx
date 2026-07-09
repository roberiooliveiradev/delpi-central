import { forwardRef } from "react";

export type NativeTextAreaControlProps = {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  className?: string;
  rows?: number;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  maxLength?: number;
  spellCheck?: boolean;
  "aria-label"?: string;
  onFocus?: () => void;
  onBlur?: () => void;
};

/**
 * `<textarea>` nativo compacto (sem FormFieldShell) — editores de domínio (Mermaid, Ishikawa, 5 Whys).
 */
export const NativeTextAreaControl = forwardRef<HTMLTextAreaElement, NativeTextAreaControlProps>(
  function NativeTextAreaControl(
    {
      id,
      value,
      onChange,
      className,
      rows,
      placeholder,
      disabled,
      readOnly,
      maxLength,
      spellCheck,
      "aria-label": ariaLabel,
      onFocus,
      onBlur,
    },
    ref,
  ) {
    return (
      <textarea
        ref={ref}
        id={id}
        className={className}
        value={value}
        rows={rows}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        maxLength={maxLength}
        spellCheck={spellCheck}
        aria-label={ariaLabel}
        onFocus={onFocus}
        onBlur={onBlur}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  },
);
