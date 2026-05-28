import type { InputHTMLAttributes, ReactNode } from "react";

import "./agent-builder-controls.css";

type AgentBuilderCheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label: ReactNode;
};

export function AgentBuilderCheckbox({
  label,
  className,
  ...inputProps
}: AgentBuilderCheckboxProps) {
  return (
    <label className={["mdc-ab-checkbox", className].filter(Boolean).join(" ")}>
      <input type="checkbox" {...inputProps} />
      <span className="mdc-ab-checkbox__label">{label}</span>
    </label>
  );
}
