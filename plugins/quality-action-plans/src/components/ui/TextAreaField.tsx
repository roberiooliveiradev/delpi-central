import { FieldLabel } from "./HelpTooltip";

type TextAreaFieldProps = {
  id?: string;
  label: string;
  hint?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  fullWidth?: boolean;
};

export function TextAreaField({
  id,
  label,
  hint,
  value,
  onChange,
  placeholder,
  rows = 4,
  disabled = false,
  required = false,
  className,
  fullWidth = false,
}: TextAreaFieldProps) {
  const fieldClass = [
    "pac-field",
    fullWidth ? "pac-field--full" : "",
    className ?? "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={fieldClass}>
      <label className="pac-field__label" htmlFor={id}>
        <FieldLabel label={label} hint={hint} />
        {required ? <span className="pac-field__required"> *</span> : null}
      </label>
      <textarea
        id={id}
        className="pac-field__control pac-field__control--textarea"
        rows={rows}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}
