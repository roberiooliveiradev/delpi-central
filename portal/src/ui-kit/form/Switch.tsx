// portal/src/ui-kit/form/Switch.tsx

import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";
import "./Switch.css";

export type SwitchProps = Omit<
  InputHTMLAttributes<HTMLInputElement>,
  "type" | "size"
> & {
  label?: ReactNode;
};

export const Switch = forwardRef<HTMLInputElement, SwitchProps>(function Switch(
  { label, className, disabled, ...rest },
  ref,
) {
  const classes = [
    "portal-ui-switch",
    disabled ? "portal-ui-switch--disabled" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <label className={classes}>
      <input
        ref={ref}
        type="checkbox"
        role="switch"
        className="portal-ui-switch__input"
        disabled={disabled}
        {...rest}
      />
      <span className="portal-ui-switch__track" aria-hidden="true">
        <span className="portal-ui-switch__thumb" />
      </span>
      {label != null ? <span>{label}</span> : null}
    </label>
  );
});
