import type { ChangeEvent, InputHTMLAttributes, ReactNode } from "react";

import { NativeCheckboxControl } from "@delpi/plugin-ui/index";
import "./agentBuilderControls.css";

type AgentBuilderCheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label: ReactNode;
  hint?: string;
};

export function AgentBuilderCheckbox({
  label,
  hint,
  className,
  checked,
  defaultChecked: _defaultChecked,
  onChange,
  ...inputProps
}: AgentBuilderCheckboxProps) {
  const useTooltipHint = typeof hint === "string" && hint.trim().length > 0;

  return (
    <NativeCheckboxControl
      {...inputProps}
      checked={Boolean(checked)}
      className={["mdc-ab-checkbox", className].filter(Boolean).join(" ")}
      label={label}
      hint={hint}
      hintPlacement={useTooltipHint ? "tooltip" : "inline"}
      hintAriaLabel={typeof label === "string" ? `Ajuda: ${label}` : "Ajuda"}
      onChange={(nextChecked) =>
        onChange?.({ target: { checked: nextChecked } } as ChangeEvent<HTMLInputElement>)
      }
    />
  );
}
