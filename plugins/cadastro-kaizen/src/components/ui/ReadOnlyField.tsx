import type { ReactNode } from "react";

type ReadOnlyFieldProps = {
  label: string;
  value: ReactNode;
  wide?: boolean;
  multiline?: boolean;
};

export function ReadOnlyField({ label, value, wide, multiline }: ReadOnlyFieldProps) {
  const isEmpty = value == null || value === "" || value === "—";
  return (
    <div className={`kz-read-field${wide ? " kz-span-2" : ""}`}>
      <span className="kz-read-field__label">{label}</span>
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
