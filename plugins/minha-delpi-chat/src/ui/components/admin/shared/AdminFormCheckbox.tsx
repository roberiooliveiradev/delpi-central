import type { ChangeEvent, InputHTMLAttributes, ReactNode } from "react";

import { NativeCheckboxControl } from "@delpi/plugin-ui/index";

type AdminFormCheckboxProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  title: ReactNode;
  hint?: ReactNode;
  className?: string;
};

export function AdminFormCheckbox({
  title,
  hint,
  className,
  checked,
  defaultChecked: _defaultChecked,
  onChange,
  ...inputProps
}: AdminFormCheckboxProps) {
  const useTooltipHint = typeof hint === "string" && hint.trim().length > 0;

  return (
    <NativeCheckboxControl
      {...inputProps}
      checked={Boolean(checked)}
      className={["mdc-admin-form-row", className].filter(Boolean).join(" ")}
      label={title}
      hint={hint}
      hintPlacement={useTooltipHint ? "tooltip" : "inline"}
      hintAriaLabel={typeof title === "string" ? `Ajuda: ${title}` : "Ajuda"}
      onChange={(nextChecked) =>
        onChange?.({ target: { checked: nextChecked } } as ChangeEvent<HTMLInputElement>)
      }
    />
  );
}
