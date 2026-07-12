import type { ChangeEvent, ReactNode } from "react";

export type NativeSwitchControlProps = {
  id?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: ReactNode;
  disabled?: boolean;
  className?: string;
  inputClassName?: string;
  trackClassName?: string;
  "aria-label"?: string;
};

/**
 * Switch acessível baseado em checkbox (`role="switch"`) — ActiveToggle / agent builder.
 * O consumidor aplica CSS do track via `className` / `trackClassName`.
 */
export function NativeSwitchControl({
  id,
  checked,
  onChange,
  label,
  disabled,
  className,
  inputClassName,
  trackClassName,
  "aria-label": ariaLabel,
}: NativeSwitchControlProps) {
  return (
    <label
      className={["delpi-ui-native-switch", className].filter(Boolean).join(" ")}
      data-checked={checked ? "true" : "false"}
      data-disabled={disabled ? "true" : "false"}
    >
      <input
        id={id}
        type="checkbox"
        role="switch"
        className={["delpi-ui-native-switch__input", inputClassName].filter(Boolean).join(" ")}
        checked={checked}
        disabled={disabled}
        aria-label={ariaLabel}
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(event.target.checked)}
      />
      <span
        className={["delpi-ui-native-switch__track", trackClassName].filter(Boolean).join(" ")}
        aria-hidden="true"
      />
      {label ? <span className="delpi-ui-native-switch__label">{label}</span> : null}
    </label>
  );
}
