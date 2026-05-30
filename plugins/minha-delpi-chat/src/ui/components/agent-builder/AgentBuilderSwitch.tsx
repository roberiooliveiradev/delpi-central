import type { InputHTMLAttributes, ReactNode } from "react";

import "./agent-builder-controls.css";

type AgentBuilderSwitchProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "size"> & {
  label?: ReactNode;
  ariaLabel?: string;
  size?: "default" | "compact";
};

export function AgentBuilderSwitch({
  label,
  ariaLabel,
  size = "default",
  className,
  ...inputProps
}: AgentBuilderSwitchProps) {
  const accessibleLabel = ariaLabel ?? (typeof label === "string" ? label : undefined);

  return (
    <label
      className={[
        "mdc-ab-switch",
        size === "compact" ? "mdc-ab-switch--compact" : null,
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <input type="checkbox" role="switch" aria-label={accessibleLabel} {...inputProps} />
      <span className="mdc-ab-switch__track" aria-hidden="true" />
      {label ? <span className="mdc-ab-switch__label">{label}</span> : null}
      {!label && accessibleLabel ? (
        <span className="mdc-ab-switch__sr-only">{accessibleLabel}</span>
      ) : null}
    </label>
  );
}
