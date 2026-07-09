import { forwardRef, type CSSProperties, type KeyboardEvent } from "react";

export type NativeTextAreaControlProps = {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  className?: string;
  style?: CSSProperties;
  rows?: number;
  placeholder?: string;
  disabled?: boolean;
  readOnly?: boolean;
  maxLength?: number;
  spellCheck?: boolean;
  autoFocus?: boolean;
  "aria-label"?: string;
  onFocus?: () => void;
  onBlur?: () => void;
  onKeyDown?: (event: KeyboardEvent<HTMLTextAreaElement>) => void;
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
      style,
      rows,
      placeholder,
      disabled,
      readOnly,
      maxLength,
      spellCheck,
      autoFocus,
      "aria-label": ariaLabel,
      onFocus,
      onBlur,
      onKeyDown,
    },
    ref,
  ) {
    return (
      <textarea
        ref={ref}
        id={id}
        className={className}
        style={style}
        value={value}
        rows={rows}
        placeholder={placeholder}
        disabled={disabled}
        readOnly={readOnly}
        maxLength={maxLength}
        spellCheck={spellCheck}
        autoFocus={autoFocus}
        aria-label={ariaLabel}
        onFocus={onFocus}
        onBlur={onBlur}
        onKeyDown={onKeyDown}
        onChange={(event) => onChange(event.target.value)}
      />
    );
  },
);
