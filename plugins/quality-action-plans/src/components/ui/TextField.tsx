type TextFieldProps = {
  id?: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: "text" | "date" | "search";
  disabled?: boolean;
  required?: boolean;
  className?: string;
  fullWidth?: boolean;
};

export function TextField({
  id,
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  disabled = false,
  required = false,
  className,
  fullWidth = false,
}: TextFieldProps) {
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
        {label}
        {required ? <span className="pac-field__required"> *</span> : null}
      </label>
      <input
        id={id}
        type={type}
        className="pac-field__control"
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}
