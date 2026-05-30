import type { InputHTMLAttributes, ReactNode } from "react";

import "./agent-builder-controls.css";

type AgentBuilderSwitchProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label?: ReactNode;
  ariaLabel?: string;
};

export function AgentBuilderSwitch({
  label,
  ariaLabel,
  className,
  ...inputProps
}: AgentBuilderSwitchProps) {
  const accessibleLabel = ariaLabel ?? (typeof label === "string" ? label : undefined);

  return (
    <label className={["mdc-ab-switch", className].filter(Boolean).join(" ")}>
      <input type="checkbox" role="switch" aria-label={accessibleLabel} {...inputProps} />
      <span className="mdc-ab-switch__track" aria-hidden="true" />
      {label ? <span className="mdc-ab-switch__label">{label}</span> : null}
      {!label && accessibleLabel ? (
        <span className="mdc-ab-switch__sr-only">{accessibleLabel}</span>
      ) : null}
    </label>
  );
}
