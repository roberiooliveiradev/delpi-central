import { FieldLabel } from "./HelpTooltip";

type ReadOnlyFieldProps = {
  id?: string;
  label: string;
  hint?: string;
  value?: string | null;
  fullWidth?: boolean;
  multiline?: boolean;
  /** `ficha` = texto puro (modo leitura); `field` = aparência de campo (somente leitura no formulário). */
  appearance?: "ficha" | "field";
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
  appearance = "ficha",
}: ReadOnlyFieldProps) {
  const isFicha = appearance === "ficha";
  const fieldClass = [
    "pac-field",
    isFicha ? "pac-ficha-field" : "pac-readonly-field",
    fullWidth ? "pac-field--full" : "",
    multiline ? (isFicha ? "pac-ficha-field--multiline" : "pac-readonly-field--multiline") : "",
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
        className={isFicha ? "pac-ficha-field__value" : "pac-readonly-field__value"}
        aria-labelledby={labelId}
      >
        {text === "—" ? <span className="pac-muted">{text}</span> : text}
      </p>
    </div>
  );
}
