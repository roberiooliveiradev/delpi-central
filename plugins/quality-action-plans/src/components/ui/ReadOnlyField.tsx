import { FieldLabel } from "./HelpTooltip";

type ReadOnlyFieldProps = {
  id?: string;
  label: string;
  hint?: string;
  value?: string | null;
  fullWidth?: boolean;
  multiline?: boolean;
};

function displayValue(value?: string | null): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed : "—";
}

export function ReadOnlyField({
  id,
  label,
  hint,
  value,
  fullWidth = false,
  multiline = false,
}: ReadOnlyFieldProps) {
  const fieldClass = [
    "pac-field",
    "pac-readonly-field",
    fullWidth ? "pac-field--full" : "",
    multiline ? "pac-readonly-field--multiline" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const labelId = id ? `${id}-label` : undefined;
  const text = displayValue(value);

  return (
    <div className={fieldClass}>
      <span className="pac-field__label" id={labelId}>
        <FieldLabel label={label} hint={hint} />
      </span>
      <p
        id={id}
        className="pac-readonly-field__value"
        aria-labelledby={labelId}
      >
        {text === "—" ? <span className="pac-muted">{text}</span> : text}
      </p>
    </div>
  );
}
