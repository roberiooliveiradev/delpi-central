import { FieldLabel } from "./HelpTooltip";

type FilterCheckboxFieldProps = {
  id: string;
  label: string;
  hint?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  checkboxLabel?: string;
  disabled?: boolean;
};

export function FilterCheckboxField({
  id,
  label,
  hint,
  checked,
  onChange,
  checkboxLabel = "Ativar filtro",
  disabled = false,
}: FilterCheckboxFieldProps) {
  return (
    <div className="pac-field pac-field--filter-checkbox">
      <span className="pac-field__label pac-field__label-row">
        <FieldLabel label={label} hint={hint} />
      </span>
      <label className="pac-checkbox pac-filter-checkbox-control" htmlFor={id}>
        <input
          id={id}
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={(event) => onChange(event.target.checked)}
        />
        <span>{checkboxLabel}</span>
      </label>
    </div>
  );
}
