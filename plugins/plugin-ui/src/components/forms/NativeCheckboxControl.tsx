import type { ChangeEvent, ReactNode } from "react";

export type NativeCheckboxControlProps = {
  id?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  /** Rótulo principal (texto ou bloco rico — ex. título + hint). */
  label?: ReactNode;
  /**
   * Alias de `label` — vários plugins passavam o texto como children;
   * sem isso o checkbox aparece sem rótulo (parece “texto invisível” no tema claro).
   */
  children?: ReactNode;
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
  children,
  hint,
  disabled,
  className,
  inputClassName,
  "aria-label": ariaLabel,
}: NativeCheckboxControlProps) {
  const resolvedLabel = label ?? children;
  const copy =
    resolvedLabel || hint ? (
      <span className="delpi-ui-native-checkbox__copy">
        {resolvedLabel ? (
          <span className="delpi-ui-native-checkbox__label">{resolvedLabel}</span>
        ) : null}
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
