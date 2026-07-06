import { FieldLabel } from "./HelpTooltip";

type DateFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  id?: string;
  hint?: string;
};

export function DateField({ label, value, onChange, id, hint }: DateFieldProps) {
  const inputId = id ?? `tm-date-${label.replace(/\s+/g, "-").toLowerCase()}`;
  return (
    <label className="ds-filter-box" htmlFor={inputId}>
      <FieldLabel label={label} hint={hint} />
      <input
        id={inputId}
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
