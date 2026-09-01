import type { ReactNode } from "react";
import { FieldLabel } from "@delpi/plugin-ui/index";

type SiAdminFormFieldProps = {
  label: string;
  hint?: string;
  fullWidth?: boolean;
  compact?: boolean;
  children: ReactNode;
};

/** Campo admin SI — rótulo com help do kit sobre o grid existente. */
export function SiAdminFormField({
  label,
  hint,
  fullWidth = false,
  compact = false,
  children,
}: SiAdminFormFieldProps) {
  const className = [
    "si-admin-form-field",
    fullWidth ? "si-admin-form-field--full" : "",
    compact ? "si-admin-form-field--compact" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <label className={className}>
      <FieldLabel label={label} hint={hint} className="si-admin-form-field__label" />
      {children}
    </label>
  );
}
