import type { ChangeEvent } from "react";

export type NativeCheckboxControlProps = {
  id?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  className?: string;
  "aria-label"?: string;
};

/**
 * Checkbox nativo compacto (sem FormFieldShell) — toggles de FormatPane / filtros.
 */
export function NativeCheckboxControl({
  id,
  checked,
  onChange,
  label,
  disabled,
  className,
  "aria-label": ariaLabel,
}: NativeCheckboxControlProps) {
  return (
    <label className={["delpi-ui-native-checkbox", className].filter(Boolean).join(" ")}>
      <input
        id={id}
        type="checkbox"
        checked={checked}
        disabled={disabled}
        aria-label={ariaLabel}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(event.target.checked)}
      />
      {label ? <span>{label}</span> : null}
    </label>
  );
}
