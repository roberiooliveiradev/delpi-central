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
  return (
    <NativeCheckboxControl
      {...inputProps}
      checked={Boolean(checked)}
      className={["mdc-admin-form-row", className].filter(Boolean).join(" ")}
      label={title}
      hint={hint}
      onChange={(nextChecked) =>
        onChange?.({ target: { checked: nextChecked } } as ChangeEvent<HTMLInputElement>)
      }
    />
  );
}
