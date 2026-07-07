import type { ReactNode } from "react";

import { HelpTooltip } from "@delpi/plugin-ui";

type ReadOnlyFieldProps = {
  label: string;
  value: ReactNode;
  hint?: string;
  wide?: boolean;
  multiline?: boolean;
};

export function ReadOnlyField({ label, value, hint, wide, multiline }: ReadOnlyFieldProps) {
  const isEmpty = value == null || value === "" || value === "—";
  return (
    <div className={`kz-read-field${wide ? " kz-span-2" : ""}`}>
      <span className="kz-read-field__label">
        {label}
        {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} /> : null}
      </span>
      <span
        className={`kz-read-field__value${multiline ? " kz-read-field__value--multiline" : ""}${
          isEmpty ? " kz-read-field__value--empty" : ""
        }`}
      >
        {isEmpty ? "—" : value}
      </span>
    </div>
  );
}
