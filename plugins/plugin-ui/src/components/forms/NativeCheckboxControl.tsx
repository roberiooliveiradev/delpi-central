import type { ChangeEvent, ReactNode } from "react";

export type NativeCheckboxControlProps = {
  id?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  /** Rótulo principal (texto ou bloco rico — ex. título + hint). */
  label?: ReactNode;
  /** Texto auxiliar abaixo do label (quando `label` é string simples). */
  hint?: ReactNode;
  disabled?: boolean;
  className?: string;
  inputClassName?: string;
  "aria-label"?: string;
};

/**
 * Checkbox nativo compacto (sem FormFieldShell) — toggles de FormatPane / filtros / admin.
 */
export function NativeCheckboxControl({
  id,
  checked,
  onChange,
  label,
  hint,
  disabled,
  className,
  inputClassName,
  "aria-label": ariaLabel,
}: NativeCheckboxControlProps) {
  const copy =
    label || hint ? (
      <span className="delpi-ui-native-checkbox__copy">
        {label ? <span className="delpi-ui-native-checkbox__label">{label}</span> : null}
        {hint ? <span className="delpi-ui-native-checkbox__hint">{hint}</span> : null}
      </span>
    ) : null;

  return (
    <label className={["delpi-ui-native-checkbox", className].filter(Boolean).join(" ")}>
      <input
        id={id}
        type="checkbox"
        className={inputClassName}
        checked={checked}
        disabled={disabled}
        aria-label={ariaLabel}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(event.target.checked)}
      />
      {copy}
    </label>
  );
}
