import type { ChangeEvent, InputHTMLAttributes, ReactNode } from "react";

import { NativeSwitchControl } from "@delpi/plugin-ui/index";
import "./agentBuilderControls.css";

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
  checked,
  defaultChecked: _defaultChecked,
  onChange,
  ...inputProps
}: AgentBuilderSwitchProps) {
  const accessibleLabel = ariaLabel ?? (typeof label === "string" ? label : undefined);

  return (
    <NativeSwitchControl
      {...inputProps}
      checked={Boolean(checked)}
      onChange={(nextChecked) =>
        onChange?.({ target: { checked: nextChecked } } as ChangeEvent<HTMLInputElement>)
      }
      aria-label={accessibleLabel}
      className={[
        "mdc-ab-switch",
        size === "compact" ? "mdc-ab-switch--compact" : null,
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      trackClassName="mdc-ab-switch__track"
      label={label}
    />
  );
}
