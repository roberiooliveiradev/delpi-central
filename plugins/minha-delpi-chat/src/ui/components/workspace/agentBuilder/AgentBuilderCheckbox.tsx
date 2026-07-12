import type { ChangeEvent, InputHTMLAttributes, ReactNode } from "react";

import { NativeCheckboxControl } from "@delpi/plugin-ui/index";
import "./agentBuilderControls.css";

type AgentBuilderCheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label: ReactNode;
};

export function AgentBuilderCheckbox({
  label,
  className,
  checked,
  defaultChecked: _defaultChecked,
  onChange,
  ...inputProps
}: AgentBuilderCheckboxProps) {
  return (
    <NativeCheckboxControl
      {...inputProps}
      checked={Boolean(checked)}
      className={["mdc-ab-checkbox", className].filter(Boolean).join(" ")}
      label={label}
      onChange={(nextChecked) =>
        onChange?.({ target: { checked: nextChecked } } as ChangeEvent<HTMLInputElement>)
      }
    />
  );
}
